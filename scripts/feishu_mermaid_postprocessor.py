#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import lark_mcp_user_token_wrapper as wrapper
from feishu_mermaid_inspector import (
    MERMAID_COMPONENT_TYPE_ID,
    extract_local_mermaid_blocks,
    fetch_document_blocks,
    fetch_tenant_access_token,
    normalize_mermaid,
)


UNTERMINATED_SLASH_LABEL_PATTERN = re.compile(
    r'(?P<node_id>\b[A-Za-z0-9_]+)\[/(?P<label>[^\]\n]*?[^/\]\n])\]'
)


def extract_code_block_text(block_item: dict) -> str:
    code = block_item.get("code") or {}
    elements = code.get("elements") or []
    return "".join(
        element.get("text_run", {}).get("content", "") for element in elements
    ).strip()


def build_child_index_lookup(block_items: list[dict]) -> dict[str, dict]:
    lookup = {}
    for item in block_items:
        parent_id = item.get("block_id")
        children = item.get("children") or []
        for index, child_id in enumerate(children):
            lookup[child_id] = {
                "parent_id": parent_id,
                "index": index,
            }
    return lookup


def sanitize_mermaid_for_feishu(source: str) -> str:
    def replace(match: re.Match) -> str:
        return f'{match.group("node_id")}["/{match.group("label")}"]'

    return UNTERMINATED_SLASH_LABEL_PATTERN.sub(replace, source)


def looks_like_mermaid(source: str) -> bool:
    normalized = normalize_mermaid(source)
    prefixes = (
        "flowchart ",
        "graph ",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram",
        "erDiagram",
        "journey",
        "mindmap",
        "gantt",
        "pie ",
        "gitGraph",
        "timeline",
        "requirementDiagram",
        "quadrantChart",
        "C4Context",
        "C4Container",
        "C4Component",
        "C4Dynamic",
        "C4Deployment",
        "xychart-beta",
    )
    return normalized.startswith(prefixes)


def extract_remote_mermaid_code_blocks(
    block_items: list[dict], local_mermaid_blocks: list[str] | None = None
) -> list[dict]:
    child_lookup = build_child_index_lookup(block_items)
    matched = []
    next_local_index = 0
    normalized_local = (
        [normalize_mermaid(block) for block in local_mermaid_blocks]
        if local_mermaid_blocks is not None
        else None
    )

    for item in block_items:
        if item.get("block_type") != 14:
            continue
        mermaid = extract_code_block_text(item)
        if not mermaid:
            continue
        normalized_remote = normalize_mermaid(mermaid)
        if normalized_local is None:
            if not looks_like_mermaid(mermaid):
                continue
        else:
            if next_local_index >= len(normalized_local):
                break
            if normalized_remote != normalized_local[next_local_index]:
                continue
        placement = child_lookup.get(item["block_id"])
        if not placement:
            continue
        matched.append(
            {
                "block_id": item["block_id"],
                "parent_id": placement["parent_id"],
                "index": placement["index"],
                "mermaid": mermaid,
            }
        )
        if normalized_local is not None:
            next_local_index += 1
    return matched


def build_mermaid_chart_block(
    mermaid: str,
    component_type_id: str = MERMAID_COMPONENT_TYPE_ID,
    theme: str = "default",
    view: str = "chart",
) -> dict:
    mermaid = sanitize_mermaid_for_feishu(mermaid)
    record = json.dumps(
        {"data": mermaid, "theme": theme, "view": view},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return {
        "block_type": 40,
        "add_ons": {
            "component_type_id": component_type_id,
            "record": record,
        },
    }


def plan_mermaid_replacements(
    local_mermaid_blocks: list[str], block_items: list[dict]
) -> list[dict]:
    remote_blocks = extract_remote_mermaid_code_blocks(block_items, local_mermaid_blocks)
    if len(remote_blocks) != len(local_mermaid_blocks):
        raise ValueError(
            "local Mermaid block count does not match remote imported Mermaid code blocks"
        )

    plan = []
    for remote_block in remote_blocks:
        original_index = remote_block["index"]
        plan.append(
            {
                "source_block_id": remote_block["block_id"],
                "parent_id": remote_block["parent_id"],
                "insert_index": original_index,
                "delete_start_index": original_index + 1,
                "delete_end_index": original_index + 2,
                "chart_block": build_mermaid_chart_block(remote_block["mermaid"]),
            }
        )
    return plan


def resolve_current_source_block_position(
    document_id: str,
    source_block_id: str,
    bearer_token: str,
    expected_parent_id: str | None = None,
) -> dict:
    block_items = fetch_document_blocks(document_id, bearer_token)
    placement = build_child_index_lookup(block_items).get(source_block_id)
    if not placement:
        raise RuntimeError(
            f"source Mermaid code block {source_block_id} not found in live document"
        )
    if expected_parent_id and placement["parent_id"] != expected_parent_id:
        raise RuntimeError(
            "source Mermaid code block parent changed unexpectedly: "
            f"{placement['parent_id']} != {expected_parent_id}"
        )
    return placement


def post_json(url: str, data: dict, bearer_token: str) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode())
    if payload.get("code") != 0:
        raise RuntimeError(f"Feishu request failed: {payload}")
    return payload


def delete_json(url: str, data: dict, bearer_token: str) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        },
        method="DELETE",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode())
    if payload.get("code") != 0:
        raise RuntimeError(f"Feishu request failed: {payload}")
    return payload


def create_document_child_block(
    document_id: str,
    parent_id: str,
    child: dict,
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
    return post_json(url, {"children": [child], "index": index}, bearer_token)


def delete_document_child_range(
    document_id: str,
    parent_id: str,
    start_index: int,
    end_index: int,
    bearer_token: str,
) -> dict:
    client_token = str(uuid.uuid4())
    query = urllib.parse.urlencode(
        {"document_revision_id": -1, "client_token": client_token}
    )
    url = (
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/"
        f"{parent_id}/children/batch_delete?{query}"
    )
    return delete_json(
        url,
        {"start_index": start_index, "end_index": end_index},
        bearer_token,
    )


def apply_replacement_plan(
    document_id: str, replacements: list[dict], bearer_token: str
) -> list[dict]:
    results = []
    for replacement in replacements:
        create_result = create_document_child_block(
            document_id=document_id,
            parent_id=replacement["parent_id"],
            child=replacement["chart_block"],
            index=replacement["insert_index"],
            bearer_token=bearer_token,
        )
        delete_result = None
        last_error = None
        for attempt in range(3):
            try:
                live_position = resolve_current_source_block_position(
                    document_id=document_id,
                    source_block_id=replacement["source_block_id"],
                    bearer_token=bearer_token,
                    expected_parent_id=replacement["parent_id"],
                )
                delete_result = delete_document_child_range(
                    document_id=document_id,
                    parent_id=live_position["parent_id"],
                    start_index=live_position["index"],
                    end_index=live_position["index"] + 1,
                    bearer_token=bearer_token,
                )
                break
            except (RuntimeError, urllib.error.HTTPError) as error:
                last_error = error
                if attempt == 2:
                    raise
                time.sleep(0.5)
        if delete_result is None and last_error is not None:
            raise last_error
        results.append(
            {
                "source_block_id": replacement["source_block_id"],
                "create_result": create_result,
                "delete_result": delete_result,
            }
        )
    return results


def resolve_bearer_token(
    explicit_token: str | None, credentials: wrapper.AppCredentials
) -> tuple[str, str]:
    if explicit_token:
        return explicit_token, "explicit"
    return fetch_tenant_access_token(credentials.app_id, credentials.app_secret), "tenant"


def build_plan_report(
    local_markdown_path: str | Path,
    document_id: str,
    credentials: wrapper.AppCredentials,
    explicit_token: str | None = None,
) -> tuple[dict, str]:
    local_markdown = Path(local_markdown_path).read_text(encoding="utf-8")
    local_mermaid_blocks = extract_local_mermaid_blocks(local_markdown)
    bearer_token, token_source = resolve_bearer_token(explicit_token, credentials)
    remote_items = fetch_document_blocks(document_id, bearer_token)
    replacements = plan_mermaid_replacements(local_mermaid_blocks, remote_items)
    return (
        {
            "document_id": document_id,
            "local_markdown_path": str(local_markdown_path),
            "token_source": token_source,
            "local_mermaid_count": len(local_mermaid_blocks),
            "replacement_count": len(replacements),
            "replacements": replacements,
        },
        bearer_token,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert imported Feishu Mermaid code blocks into rendered chart add-on blocks."
        )
    )
    parser.add_argument("--markdown", required=True, help="Path to the local markdown draft")
    parser.add_argument("--document-id", required=True, help="Feishu docx document id")
    parser.add_argument(
        "--token",
        help="Optional explicit Feishu bearer token. Defaults to a tenant token from Codex config.",
    )
    parser.add_argument("--app-id", help="Explicit Feishu app id override.")
    parser.add_argument("--app-secret", help="Explicit Feishu app secret override.")
    parser.add_argument("--domain", help="Explicit Feishu domain override.")
    parser.add_argument(
        "--config-path",
        default=str(wrapper.DEFAULT_CONFIG_PATH),
        help="Codex config path used to infer Feishu app credentials.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the replacement plan instead of only printing a dry-run report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    credentials = wrapper.resolve_app_credentials(args)
    report, bearer_token = build_plan_report(
        local_markdown_path=args.markdown,
        document_id=args.document_id,
        credentials=credentials,
        explicit_token=args.token,
    )
    if args.apply:
        report["apply_results"] = apply_replacement_plan(
            document_id=args.document_id,
            replacements=report["replacements"],
            bearer_token=bearer_token,
        )
        report["mode"] = "apply"
    else:
        report["mode"] = "dry-run"
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
