#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import time
import urllib.parse
import urllib.error
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from feishu_mermaid_inspector import fetch_document_blocks
from feishu_mermaid_postprocessor import (
    build_child_index_lookup,
    build_mermaid_chart_block,
    delete_document_child_range,
    post_json,
)
from repodoctify.feishu import get_json, json_request, patch_json
from lark_mcp_user_token_wrapper import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_STORE_PATH,
    TokenStore,
    ensure_valid_access_token,
    resolve_app_credentials,
)


TEXT_STYLE = {
    "bold": False,
    "inline_code": False,
    "italic": False,
    "strikethrough": False,
    "underline": False,
}

LANGUAGE_MAP = {
    "": 1,
    "text": 1,
    "plaintext": 1,
    "python": 49,
    "py": 49,
    "json": 28,
    "bash": 7,
    "shell": 60,
    "sql": 56,
    "yaml": 67,
    "yml": 67,
    "markdown": 39,
}
HOMEPAGE_ID = "KfzbdXoUBozdPTxERaDcYdS3nOh"
BOARD_THEME = "vibrant_color"
BOARD_POPULATION_MAX_WORKERS = 3


@dataclass(frozen=True)
class TextRunSpec:
    text: str
    inline_code: bool = False
    url: str | None = None
    bold: bool = False


@dataclass(frozen=True)
class TableBlockSpec:
    rows: list[list[list[TextRunSpec]]]


@dataclass(frozen=True)
class CreatedBoardJob:
    board_id: str
    nodes: list[dict]
    create_result: dict

def extract_plain_text(block_item: dict) -> str:
    parts: list[str] = []
    for value in block_item.values():
        if not isinstance(value, dict):
            continue
        elements = value.get("elements")
        if not isinstance(elements, list):
            continue
        for element in elements:
            text_run = element.get("text_run")
            if text_run and text_run.get("content"):
                parts.append(text_run["content"])
    return "".join(parts).strip()


def block_contains_url(block_item: dict, url: str) -> bool:
    encoded = urllib.parse.quote(url, safe="")
    for value in block_item.values():
        if not isinstance(value, dict):
            continue
        elements = value.get("elements")
        if not isinstance(elements, list):
            continue
        for element in elements:
            style = element.get("text_run", {}).get("text_element_style", {})
            link = style.get("link", {})
            if link.get("url") == encoded:
                return True
    return False


def build_text_elements(runs: list[TextRunSpec]) -> list[dict]:
    elements = []
    for run in runs:
        style = dict(TEXT_STYLE)
        if run.inline_code:
            style["inline_code"] = True
        if run.bold:
            style["bold"] = True
        if run.url:
            style["link"] = {"url": urllib.parse.quote(run.url, safe="")}
        elements.append({"text_run": {"content": run.text, "text_element_style": style}})
    return elements


def build_text_block(runs: list[TextRunSpec]) -> dict:
    return {
        "block_type": 2,
        "text": {
            "elements": build_text_elements(runs),
            "style": {"align": 1, "folded": False},
        },
    }


def build_heading_block(level: int, runs: list[TextRunSpec]) -> dict:
    block_type = {1: 3, 2: 4, 3: 5}[level]
    key = {1: "heading1", 2: "heading2", 3: "heading3"}[level]
    return {
        "block_type": block_type,
        key: {
            "elements": build_text_elements(runs),
            "style": {"align": 1, "folded": False},
        },
    }


def build_bullet_block(runs: list[TextRunSpec]) -> dict:
    return {
        "block_type": 12,
        "bullet": {
            "elements": build_text_elements(runs),
            "style": {"align": 1, "folded": False},
        },
    }


def build_ordered_block(runs: list[TextRunSpec], sequence: str) -> dict:
    return {
        "block_type": 13,
        "ordered": {
            "elements": build_text_elements(runs),
            "style": {"align": 1, "folded": False, "sequence": sequence},
        },
    }


def build_code_block(code: str, language: str) -> dict:
    lang = LANGUAGE_MAP.get(language.lower(), 1)
    return {
        "block_type": 14,
        "code": {
            "elements": [{"text_run": {"content": code}}],
            "style": {"language": lang, "wrap": True},
        },
    }


def build_table_block(row_size: int, column_size: int) -> dict:
    column_width = max(120, 732 // max(1, column_size))
    return {
        "block_type": 31,
        "table": {
            "property": {
                "row_size": row_size,
                "column_size": column_size,
                "column_width": [column_width] * column_size,
            }
        },
    }


def parse_inline_runs(text: str) -> list[TextRunSpec]:
    runs: list[TextRunSpec] = []
    index = 0
    length = len(text)
    while index < length:
        if text[index] == "`":
            end = text.find("`", index + 1)
            if end != -1:
                runs.append(TextRunSpec(text[index + 1 : end], inline_code=True))
                index = end + 1
                continue
        if text[index] == "[":
            match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", text[index:])
            if match:
                runs.append(TextRunSpec(match.group(1), url=match.group(2)))
                index += match.end()
                continue
        next_code = text.find("`", index)
        next_link = text.find("[", index)
        candidates = [pos for pos in (next_code, next_link) if pos != -1]
        next_special = min(candidates) if candidates else length
        if next_special == index:
            runs.append(TextRunSpec(text[index]))
            index += 1
            continue
        runs.append(TextRunSpec(text[index:next_special]))
        index = next_special
    return [run for run in runs if run.text]


def _split_markdown_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _is_markdown_table_delimiter_row(line: str) -> bool:
    cells = _split_markdown_table_row(line)
    if not cells:
        return False
    for cell in cells:
        normalized = cell.replace(" ", "")
        if not re.fullmatch(r":?-{3,}:?", normalized):
            return False
    return True


def create_document(title: str, bearer_token: str) -> str:
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    payload = post_json(url, {"title": title}, bearer_token)
    document_id = payload.get("data", {}).get("document", {}).get("document_id")
    if not document_id:
        raise RuntimeError(f"document create did not return document_id: {payload}")
    return document_id


def create_document_child_blocks(
    document_id: str,
    parent_id: str,
    children: list[dict],
    index: int,
    bearer_token: str,
) -> dict:
    client_token = str(uuid.uuid4())
    query = urllib.parse.urlencode(
        {"document_revision_id": -1, "client_token": client_token}
    )
    url = (
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/"
        f"{parent_id}/children?{query}"
    )
    return post_json(url, {"children": children, "index": index}, bearer_token)

def create_board_nodes(
    board_id: str,
    nodes: list[dict],
    primary_token: str,
    fallback_token: str | None = None,
) -> None:
    query = urllib.parse.urlencode(
        {"client_token": str(uuid.uuid4()), "user_id_type": "open_id"}
    )
    url = f"https://open.feishu.cn/open-apis/board/v1/whiteboards/{board_id}/nodes?{query}"
    try:
        json_request(url, primary_token, method="POST", data={"nodes": nodes})
    except Exception:
        if not fallback_token:
            raise
        json_request(url, fallback_token, method="POST", data={"nodes": nodes})


def list_board_nodes(
    board_id: str,
    primary_token: str,
    fallback_token: str | None = None,
) -> list[dict]:
    url = (
        "https://open.feishu.cn/open-apis/board/v1/whiteboards/"
        f"{board_id}/nodes?{urllib.parse.urlencode({'user_id_type': 'open_id'})}"
    )
    try:
        payload = json_request(url, primary_token)
    except Exception:
        if not fallback_token:
            raise
        payload = json_request(url, fallback_token)
    return payload.get("data", {}).get("nodes", [])


def update_board_theme(
    board_id: str,
    primary_token: str,
    fallback_token: str | None = None,
) -> None:
    url = f"https://open.feishu.cn/open-apis/board/v1/whiteboards/{board_id}/update_theme"
    try:
        json_request(url, primary_token, method="POST", data={"theme": BOARD_THEME})
    except Exception:
        if not fallback_token:
            raise
        json_request(url, fallback_token, method="POST", data={"theme": BOARD_THEME})


def create_board_block_job(
    document_id: str,
    parent_id: str,
    index: int,
    nodes: list[dict],
    bearer_token: str,
    create_block_fn: Callable[[str, str, list[dict], int, str], dict] | None = None,
) -> CreatedBoardJob:
    create_block_fn = create_block_fn or create_document_child_blocks
    response = create_block_fn(
        document_id,
        parent_id,
        [{"block_type": 43, "board": {}}],
        index,
        bearer_token,
    )
    child = response.get("data", {}).get("children", [])[0]
    board_id = child.get("board", {}).get("token")
    if not board_id:
        raise RuntimeError(f"created board block did not return board token: {response}")
    return CreatedBoardJob(board_id=board_id, nodes=nodes, create_result=response)


def _populate_single_board_job(
    board_job: CreatedBoardJob,
    *,
    board_token: str,
    board_fallback_token: str | None,
    create_nodes_fn: Callable[[str, list[dict], str, str | None], None],
    update_theme_fn: Callable[[str, str, str | None], None],
) -> None:
    create_nodes_fn(
        board_job.board_id,
        board_job.nodes,
        board_token,
        board_fallback_token,
    )
    update_theme_fn(
        board_job.board_id,
        board_token,
        board_fallback_token,
    )


def populate_board_jobs(
    board_jobs: list[CreatedBoardJob],
    *,
    board_token: str,
    board_fallback_token: str | None,
    max_workers: int = BOARD_POPULATION_MAX_WORKERS,
    create_nodes_fn: Callable[[str, list[dict], str, str | None], None] | None = None,
    update_theme_fn: Callable[[str, str, str | None], None] | None = None,
) -> None:
    if not board_jobs:
        return
    create_nodes_fn = create_nodes_fn or create_board_nodes
    update_theme_fn = update_theme_fn or update_board_theme
    worker_count = min(max_workers, len(board_jobs))
    if worker_count < 1:
        raise ValueError("max_workers must be at least 1")
    if worker_count == 1:
        for board_job in board_jobs:
            _populate_single_board_job(
                board_job,
                board_token=board_token,
                board_fallback_token=board_fallback_token,
                create_nodes_fn=create_nodes_fn,
                update_theme_fn=update_theme_fn,
            )
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [
            executor.submit(
                _populate_single_board_job,
                board_job,
                board_token=board_token,
                board_fallback_token=board_fallback_token,
                create_nodes_fn=create_nodes_fn,
                update_theme_fn=update_theme_fn,
            )
            for board_job in board_jobs
        ]
        for future in futures:
            future.result()


def batch_update_document_blocks(
    document_id: str,
    requests: list[dict],
    bearer_token: str,
) -> dict:
    client_token = str(uuid.uuid4())
    query = urllib.parse.urlencode(
        {"document_revision_id": -1, "client_token": client_token}
    )
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/batch_update?{query}"
    return patch_json(url, {"requests": requests}, bearer_token)


def parse_markdown(markdown: str) -> tuple[str, list[tuple]]:
    lines = markdown.splitlines()
    blocks: list[tuple] = []
    paragraph: list[str] = []
    title = ""

    def flush_paragraph() -> None:
        if not paragraph:
            return
        text = " ".join(item.strip() for item in paragraph).strip()
        if text:
            blocks.append(("paragraph", text))
        paragraph.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            language = stripped[3:].strip()
            index += 1
            code_lines: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            blocks.append(("code", language, "\n".join(code_lines).rstrip()))
            if index < len(lines):
                index += 1
            continue
        heading_match = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            if level == 1 and not title:
                title = text
            blocks.append(("heading", level, text))
            index += 1
            continue
        if (
            stripped.startswith("|")
            and index + 1 < len(lines)
            and lines[index + 1].strip().startswith("|")
            and _is_markdown_table_delimiter_row(lines[index + 1])
        ):
            flush_paragraph()
            header_cells = _split_markdown_table_row(line)
            column_count = len(header_cells)
            rows = [header_cells]
            index += 2
            while index < len(lines):
                current = lines[index].strip()
                if not current.startswith("|"):
                    break
                cells = _split_markdown_table_row(lines[index])
                if len(cells) < column_count:
                    cells.extend([""] * (column_count - len(cells)))
                elif len(cells) > column_count:
                    cells = cells[:column_count]
                rows.append(cells)
                index += 1
            blocks.append(("table", rows))
            continue
        ordered_match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if ordered_match:
            flush_paragraph()
            blocks.append(("ordered", ordered_match.group(1), ordered_match.group(2).strip()))
            index += 1
            continue
        bullet_match = re.match(r"^\s*-\s+(.*)$", line)
        if bullet_match:
            flush_paragraph()
            blocks.append(("bullet", bullet_match.group(1).strip()))
            index += 1
            continue
        paragraph.append(stripped)
        index += 1

    flush_paragraph()
    if not title:
        raise RuntimeError("markdown does not contain a level-1 title")
    return title, blocks


def blocks_from_markdown(markdown: str) -> tuple[str, list[dict | TableBlockSpec]]:
    title, parsed_blocks = parse_markdown(markdown)
    children: list[dict | TableBlockSpec] = []
    for item in parsed_blocks:
        kind = item[0]
        if kind == "heading":
            _, level, text = item
            children.append(build_heading_block(level, parse_inline_runs(text)))
        elif kind == "paragraph":
            _, text = item
            children.append(build_text_block(parse_inline_runs(text)))
        elif kind == "bullet":
            _, text = item
            children.append(build_bullet_block(parse_inline_runs(text)))
        elif kind == "ordered":
            _, sequence, text = item
            children.append(build_ordered_block(parse_inline_runs(text), sequence))
        elif kind == "code":
            _, language, code = item
            if language.lower() == "mermaid":
                children.append(build_mermaid_chart_block(code))
            else:
                children.append(build_code_block(code, language))
        elif kind == "table":
            _, rows = item
            children.append(
                TableBlockSpec(
                    rows=[
                        [parse_inline_runs(cell) for cell in row]
                        for row in rows
                    ]
                )
            )
        else:
            raise RuntimeError(f"unsupported markdown block kind: {kind}")
    return title, children


def append_table_block(
    document_id: str,
    table_spec: TableBlockSpec,
    insert_index: int,
    bearer_token: str,
) -> dict | None:
    if not table_spec.rows:
        return None

    column_size = max(len(row) for row in table_spec.rows)
    padded_rows: list[list[list[TextRunSpec]]] = []
    for row in table_spec.rows:
        padded = list(row)
        if len(padded) < column_size:
            padded.extend([[] for _ in range(column_size - len(padded))])
        padded_rows.append(padded)

    response = None
    for attempt in range(5):
        try:
            response = create_document_child_blocks(
                document_id=document_id,
                parent_id=document_id,
                children=[build_table_block(len(padded_rows), column_size)],
                index=insert_index,
                bearer_token=bearer_token,
            )
            break
        except urllib.error.HTTPError as error:
            body = error.read().decode(errors="replace")
            is_retryable = error.code == 429 or 500 <= error.code < 600
            if is_retryable and attempt < 4:
                time.sleep(0.5 * (2**attempt))
                continue
            raise RuntimeError(
                "failed to create table block "
                f"at insert_index={insert_index} row_size={len(padded_rows)} "
                f"column_size={column_size} body={body}"
            ) from error
    if response is None:
        raise RuntimeError("failed to create table block: empty response")
    created_table = response.get("data", {}).get("children", [])[0]
    cell_ids = created_table.get("children") or created_table.get("table", {}).get("cells") or []
    return {
        "cell_ids": cell_ids,
        "flat_cells": [cell for row in padded_rows for cell in row],
    }


def _populate_table_cells(
    document_id: str,
    table_specs: list[dict],
    bearer_token: str,
) -> None:
    if not table_specs:
        return

    block_lookup = {
        item["block_id"]: item
        for item in fetch_document_blocks(document_id, bearer_token)
        if item.get("block_id")
    }
    pending_updates: list[dict] = []
    pending_fallback_creates: list[tuple[str, list[TextRunSpec]]] = []
    for table_spec in table_specs:
        for cell_id, runs in zip(table_spec["cell_ids"], table_spec["flat_cells"]):
            existing_cell = block_lookup.get(cell_id, {})
            existing_children = existing_cell.get("children") or []
            if not runs:
                continue
            if existing_children:
                pending_updates.append(
                    {
                        "block_id": existing_children[0],
                        "update_text_elements": {
                            "elements": build_text_elements(runs),
                        },
                    }
                )
                continue
            pending_fallback_creates.append((cell_id, runs))

    batch_size = 50
    for index in range(0, len(pending_updates), batch_size):
        chunk = pending_updates[index : index + batch_size]
        for attempt in range(5):
            try:
                batch_update_document_blocks(
                    document_id=document_id,
                    requests=chunk,
                    bearer_token=bearer_token,
                )
                break
            except urllib.error.HTTPError as error:
                body = error.read().decode(errors="replace")
                is_retryable = error.code == 429 or 500 <= error.code < 600
                if is_retryable and attempt < 4:
                    time.sleep(0.5 * (2**attempt))
                    continue
                raise RuntimeError(
                    "failed to batch update table cell content "
                    f"for chunk_start={index} chunk_size={len(chunk)} body={body}"
                ) from error

    for cell_id, runs in pending_fallback_creates:
        for attempt in range(5):
            try:
                create_document_child_blocks(
                    document_id=document_id,
                    parent_id=cell_id,
                    children=[build_text_block(runs)],
                    index=0,
                    bearer_token=bearer_token,
                )
                break
            except urllib.error.HTTPError as error:
                body = error.read().decode(errors="replace")
                is_retryable = error.code == 429 or 500 <= error.code < 600
                if is_retryable and attempt < 4:
                    time.sleep(0.5 * (2**attempt))
                    continue
                raise RuntimeError(
                    "failed to write table cell content "
                    f"for cell_id={cell_id} body={body}"
                ) from error


def _append_standard_blocks(
    document_id: str,
    children: list[dict],
    insert_index: int,
    bearer_token: str,
    chunk_size: int = 50,
) -> int:
    if not children:
        return insert_index

    groups: list[list[dict]] = []
    current_group: list[dict] = []
    current_list_type: int | None = None
    for child in children:
        block_type = child["block_type"]
        if block_type in {12, 13}:
            if current_list_type == block_type:
                current_group.append(child)
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [child]
                current_list_type = block_type
            continue
        if current_group:
            groups.append(current_group)
        groups.append([child])
        current_group = []
        current_list_type = None
    if current_group:
        groups.append(current_group)

    batches: list[list[dict]] = []
    current_batch: list[dict] = []
    for group in groups:
        has_special_block = any(item["block_type"] in {14, 40} for item in group)
        if has_special_block:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
            batches.append(list(group))
            continue
        if current_batch and len(current_batch) + len(group) > chunk_size:
            batches.append(current_batch)
            current_batch = list(group)
        else:
            current_batch.extend(group)
    if current_batch:
        batches.append(current_batch)

    for chunk in batches:
        for attempt in range(5):
            try:
                create_document_child_blocks(
                    document_id=document_id,
                    parent_id=document_id,
                    children=chunk,
                    index=insert_index,
                    bearer_token=bearer_token,
                )
                break
            except urllib.error.HTTPError as error:
                body = error.read().decode(errors="replace")
                is_retryable = error.code == 429 or 500 <= error.code < 600
                if is_retryable and attempt < 4:
                    time.sleep(0.5 * (2**attempt))
                    continue
                summary = [
                    {
                        "block_type": item["block_type"],
                        "payload_keys": [key for key in item.keys() if key != "block_type"],
                    }
                    for item in chunk
                ]
                raise RuntimeError(
                    "failed to append chunk "
                    f"at insert_index={insert_index} size={len(chunk)} "
                    f"summary={json.dumps(summary, ensure_ascii=False)} "
                    f"body={body}"
                ) from error
        insert_index += len(chunk)
        time.sleep(0.1)
    return insert_index


def append_blocks_to_root(
    document_id: str,
    children: list[dict | TableBlockSpec],
    bearer_token: str,
    chunk_size: int = 50,
) -> None:
    # Current publish paths call this only for a fresh document root or after the root has
    # already been cleared, so we can start at index 0 without an extra read.
    insert_index = 0
    pending_standard_blocks: list[dict] = []
    pending_tables: list[dict] = []
    for child in children:
        if isinstance(child, TableBlockSpec):
            insert_index = _append_standard_blocks(
                document_id=document_id,
                children=pending_standard_blocks,
                insert_index=insert_index,
                bearer_token=bearer_token,
                chunk_size=chunk_size,
            )
            pending_standard_blocks = []
            created_table = append_table_block(
                document_id=document_id,
                table_spec=child,
                insert_index=insert_index,
                bearer_token=bearer_token,
            )
            if created_table:
                pending_tables.append(created_table)
            insert_index += 1
            continue
        pending_standard_blocks.append(child)

    _append_standard_blocks(
        document_id=document_id,
        children=pending_standard_blocks,
        insert_index=insert_index,
        bearer_token=bearer_token,
        chunk_size=chunk_size,
    )

    _populate_table_cells(
        document_id=document_id,
        table_specs=pending_tables,
        bearer_token=bearer_token,
    )


def find_anchor(block_items: list[dict], anchor_substring: str) -> dict:
    child_lookup = build_child_index_lookup(block_items)
    for item in block_items:
        text = extract_plain_text(item)
        if anchor_substring in text:
            placement = child_lookup.get(item["block_id"])
            if placement:
                return {
                    "block_id": item["block_id"],
                    "parent_id": placement["parent_id"],
                    "index": placement["index"],
                    "text": text,
                }
    raise RuntimeError(f"anchor not found: {anchor_substring}")


def heading_exists(block_items: list[dict], text: str) -> bool:
    return any(extract_plain_text(item) == text for item in block_items)


def homepage_entry_exists(block_items: list[dict], url: str) -> bool:
    return any(block_contains_url(item, url) for item in block_items)


def insert_homepage_entry(homepage_id: str, doc_url: str, bearer_token: str, dry_run: bool) -> dict:
    block_items = fetch_document_blocks(homepage_id, bearer_token)
    anchor = find_anchor(block_items, "第一周心智模型篇")
    heading_text = "跨仓读码桥接篇"
    entry_text = "跨仓：先补这 6 个 Python 机制，再读 autopilot-platform-service 和 zaki_webcreator"
    children: list[dict] = []
    if not heading_exists(block_items, heading_text):
        children.append(build_heading_block(3, [TextRunSpec(heading_text)]))
    if not homepage_entry_exists(block_items, doc_url):
        children.append(build_bullet_block([TextRunSpec(entry_text, url=doc_url)]))
    result = {
        "anchor_text": anchor["text"],
        "insert_index": anchor["index"],
        "created_blocks": len(children),
        "doc_url": doc_url,
        "dry_run": dry_run,
    }
    if not dry_run and children:
        create_document_child_blocks(
            document_id=homepage_id,
            parent_id=anchor["parent_id"],
            children=children,
            index=anchor["index"],
            bearer_token=bearer_token,
        )
    after_blocks = fetch_document_blocks(homepage_id, bearer_token)
    result["verification"] = {
        "heading_ok": heading_exists(after_blocks, heading_text),
        "link_ok": homepage_entry_exists(after_blocks, doc_url),
    }
    return result


def publish(markdown_path: Path, homepage_id: str, dry_run: bool) -> dict:
    markdown = markdown_path.read_text(encoding="utf-8")
    title, children = blocks_from_markdown(markdown)

    args = argparse.Namespace(
        app_id=None,
        app_secret=None,
        domain=None,
        config_path=str(DEFAULT_CONFIG_PATH),
    )
    store = TokenStore(DEFAULT_STORE_PATH)
    credentials = resolve_app_credentials(args)
    bearer_token = ensure_valid_access_token(store, credentials)

    result = {
        "title": title,
        "markdown_path": str(markdown_path),
        "block_count": len(children),
        "dry_run": dry_run,
    }
    if dry_run:
        return result

    document_id = create_document(title, bearer_token)
    append_blocks_to_root(document_id, children, bearer_token)
    doc_url = f"https://aigccode.feishu.cn/docx/{document_id}"

    new_doc_blocks = fetch_document_blocks(document_id, bearer_token)
    result["document_id"] = document_id
    result["doc_url"] = doc_url
    result["doc_verification"] = {
        "has_heading": heading_exists(new_doc_blocks, title),
        "has_summary_section": any(
            "为什么要先补这一层" in extract_plain_text(item) for item in new_doc_blocks
        ),
    }
    result["homepage"] = insert_homepage_entry(homepage_id, doc_url, bearer_token, dry_run=False)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the cross-repo Python reading bridge doc to Feishu.")
    parser.add_argument(
        "--markdown",
        default="feishu_cross_repo_python_reading_bridge.md",
        help="Path to the local markdown draft",
    )
    parser.add_argument(
        "--homepage-id",
        default=HOMEPAGE_ID,
        help="Existing homepage document id to update in place",
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse locally without writing to Feishu")
    args = parser.parse_args()

    result = publish(Path(args.markdown), args.homepage_id, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
