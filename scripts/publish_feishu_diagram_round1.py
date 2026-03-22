#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.parse
import uuid
from dataclasses import dataclass
from pathlib import Path

from repodoctify.feishu.mermaid import build_mermaid_chart_block, normalize_mermaid
from feishu_mermaid_inspector import (
    extract_remote_mermaid_addons,
    fetch_document_blocks,
)
from feishu_mermaid_postprocessor import (
    build_child_index_lookup,
    post_json,
)
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

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SPEC_FILE = SCRIPT_DIR / "specs" / "publish_feishu_diagram_round1.default.json"


@dataclass(frozen=True)
class BlockSpec:
    kind: str
    text: str | None = None
    mermaid: str | None = None


@dataclass(frozen=True)
class InsertionSpec:
    name: str
    document_id: str
    anchor_substring: str
    position: str
    blocks: tuple[BlockSpec, ...]


def build_block_spec(raw: dict) -> BlockSpec:
    kind = raw.get("kind")
    if kind not in {"heading3", "mermaid"}:
        raise ValueError(f"unsupported block kind: {kind!r}")
    if kind == "heading3":
        text = raw.get("text")
        if not text:
            raise ValueError("heading3 blocks require a non-empty text field")
        return BlockSpec(kind="heading3", text=text)
    mermaid = raw.get("mermaid")
    if not mermaid:
        raise ValueError("mermaid blocks require a non-empty mermaid field")
    return BlockSpec(kind="mermaid", mermaid=mermaid)


def build_insertion_spec(raw: dict) -> InsertionSpec:
    name = raw.get("name")
    document_id = raw.get("document_id")
    anchor_substring = raw.get("anchor_substring")
    position = raw.get("position")
    raw_blocks = raw.get("blocks")
    if not name:
        raise ValueError("spec requires a non-empty name")
    if not document_id:
        raise ValueError(f"spec {name!r} requires document_id")
    if not anchor_substring:
        raise ValueError(f"spec {name!r} requires anchor_substring")
    if position not in {"before", "after"}:
        raise ValueError(f"spec {name!r} position must be 'before' or 'after'")
    if not isinstance(raw_blocks, list) or not raw_blocks:
        raise ValueError(f"spec {name!r} requires a non-empty blocks list")
    return InsertionSpec(
        name=name,
        document_id=document_id,
        anchor_substring=anchor_substring,
        position=position,
        blocks=tuple(build_block_spec(block) for block in raw_blocks),
    )


def load_specs_from_file(spec_file: str | Path) -> tuple[InsertionSpec, ...]:
    payload = json.loads(Path(spec_file).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        raw_specs = payload
    elif isinstance(payload, dict) and isinstance(payload.get("specs"), list):
        raw_specs = payload["specs"]
    else:
        raise ValueError("spec file must be a JSON array or an object with a 'specs' array")
    specs = tuple(build_insertion_spec(spec) for spec in raw_specs)
    if not specs:
        raise ValueError("spec file did not contain any specs")
    return specs


def select_specs(
    specs: tuple[InsertionSpec, ...], wanted_names: list[str] | None = None
) -> tuple[InsertionSpec, ...]:
    if not wanted_names:
        return specs
    wanted = set(wanted_names)
    selected = tuple(spec for spec in specs if spec.name in wanted)
    if len(selected) != len(wanted):
        known = ", ".join(spec.name for spec in specs)
        missing = ", ".join(sorted(wanted - {spec.name for spec in selected}))
        raise SystemExit(f"unknown spec(s): {missing}; known: {known}")
    return selected


def describe_spec_source(spec_file: str | None) -> str:
    if spec_file:
        return str(Path(spec_file))
    return str(DEFAULT_SPEC_FILE)


def build_heading3_block(text: str) -> dict:
    return {
        "block_type": 5,
        "heading3": {
            "elements": [
                {
                    "text_run": {
                        "content": text,
                        "text_element_style": dict(TEXT_STYLE),
                    }
                }
            ],
            "style": {"align": 1, "folded": False},
        },
    }


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
            if not text_run:
                continue
            content = text_run.get("content")
            if content:
                parts.append(content)
    return "".join(parts).strip()


def find_anchor(block_items: list[dict], anchor_substring: str) -> dict:
    placement_lookup = build_child_index_lookup(block_items)
    for item in block_items:
        text = extract_plain_text(item)
        if not text or anchor_substring not in text:
            continue
        placement = placement_lookup.get(item["block_id"])
        if placement:
            return {
                "block_id": item["block_id"],
                "parent_id": placement["parent_id"],
                "index": placement["index"],
                "text": text,
            }
    raise RuntimeError(f"anchor not found: {anchor_substring}")


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


def mermaid_exists(block_items: list[dict], mermaid: str) -> bool:
    expected = normalize_mermaid(mermaid)
    for item in extract_remote_mermaid_addons(block_items):
        if normalize_mermaid(item["mermaid"]) == expected:
            return True
    return False


def heading_exists(block_items: list[dict], text: str) -> bool:
    return any(extract_plain_text(item) == text for item in block_items)


def build_payload_blocks(spec: InsertionSpec, current_blocks: list[dict]) -> list[dict]:
    children: list[dict] = []
    for block in spec.blocks:
        if block.kind == "heading3":
            assert block.text is not None
            if heading_exists(current_blocks, block.text):
                continue
            children.append(build_heading3_block(block.text))
            continue
        if block.kind == "mermaid":
            assert block.mermaid is not None
            if mermaid_exists(current_blocks, block.mermaid):
                continue
            children.append(build_mermaid_chart_block(block.mermaid))
            continue
        raise ValueError(f"unsupported block kind: {block.kind}")
    return children


def verify_spec(spec: InsertionSpec, block_items: list[dict]) -> dict:
    verification = {"name": spec.name, "document_id": spec.document_id}
    for block in spec.blocks:
        if block.kind == "heading3":
            verification["heading_ok"] = heading_exists(block_items, block.text or "")
        elif block.kind == "mermaid":
            verification["mermaid_ok"] = mermaid_exists(block_items, block.mermaid or "")
    return verification


def apply_spec(spec: InsertionSpec, bearer_token: str, dry_run: bool) -> dict:
    before_blocks = fetch_document_blocks(spec.document_id, bearer_token)
    anchor = find_anchor(before_blocks, spec.anchor_substring)
    insert_index = anchor["index"] + 1 if spec.position == "after" else anchor["index"]
    children = build_payload_blocks(spec, before_blocks)
    result = {
        "name": spec.name,
        "document_id": spec.document_id,
        "anchor_text": anchor["text"],
        "anchor_index": anchor["index"],
        "insert_index": insert_index,
        "planned_blocks": [block.kind for block in spec.blocks],
        "created_blocks": len(children),
        "dry_run": dry_run,
    }
    if dry_run or not children:
        after_blocks = before_blocks
    else:
        create_document_child_blocks(
            document_id=spec.document_id,
            parent_id=anchor["parent_id"],
            children=children,
            index=insert_index,
            bearer_token=bearer_token,
        )
        after_blocks = fetch_document_blocks(spec.document_id, bearer_token)
    result["verification"] = verify_spec(spec, after_blocks)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Insert Mermaid diagrams into existing Feishu docs."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only resolve anchors and verification state; do not write blocks.",
    )
    parser.add_argument(
        "--name",
        action="append",
        help="Run only the named spec. Can be passed multiple times.",
    )
    parser.add_argument(
        "--spec-file",
        help=(
            "Optional JSON file that defines specs. Defaults to the bundled spec file. "
            "Accepts either a top-level array or an object with a 'specs' array."
        ),
    )
    parser.add_argument(
        "--list-specs",
        action="store_true",
        help="Print the available spec names and exit.",
    )
    parser.add_argument(
        "--app-id",
        help="Explicit Feishu app id override.",
    )
    parser.add_argument(
        "--app-secret",
        help="Explicit Feishu app secret override.",
    )
    parser.add_argument(
        "--domain",
        help="Explicit Feishu domain override.",
    )
    parser.add_argument(
        "--config-path",
        default=str(DEFAULT_CONFIG_PATH),
        help="Codex config path used to infer Feishu app credentials.",
    )
    parser.add_argument(
        "--store-path",
        default=str(DEFAULT_STORE_PATH),
        help="Local store path for the persisted user token.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec_source = Path(args.spec_file) if args.spec_file else DEFAULT_SPEC_FILE
    specs = load_specs_from_file(spec_source)
    selected = select_specs(specs, args.name)

    if args.list_specs:
        payload = {
            "source": describe_spec_source(str(spec_source)),
            "spec_names": [spec.name for spec in specs],
            "selected_names": [spec.name for spec in selected],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    credentials = resolve_app_credentials(args)
    store = TokenStore(args.store_path)
    bearer_token = ensure_valid_access_token(store=store, credentials=credentials)

    reports = [apply_spec(spec, bearer_token=bearer_token, dry_run=args.dry_run) for spec in selected]
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
