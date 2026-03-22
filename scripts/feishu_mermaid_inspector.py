#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from repodoctify.feishu import (
    AppCredentials,
    DEFAULT_CONFIG_PATH,
    fetch_document_blocks,
    fetch_tenant_access_token,
    resolve_app_credentials,
)


MERMAID_COMPONENT_TYPE_ID = "blk_631fefbbae02400430b8f9f4"
MERMAID_FENCE_PATTERN = re.compile(r"```mermaid\s*\n(.*?)```", re.S)


def extract_local_mermaid_blocks(markdown: str) -> list[str]:
    return [block.strip() for block in MERMAID_FENCE_PATTERN.findall(markdown)]


def extract_remote_mermaid_addons(
    block_items: list[dict], component_type_id: str = MERMAID_COMPONENT_TYPE_ID
) -> list[dict]:
    addons = []
    for item in block_items:
        if item.get("block_type") != 40:
            continue
        add_ons = item.get("add_ons") or {}
        if add_ons.get("component_type_id") != component_type_id:
            continue
        record_raw = add_ons.get("record")
        if not record_raw:
            continue
        record = json.loads(record_raw)
        mermaid = record.get("data")
        if not mermaid:
            continue
        addons.append(
            {
                "block_id": item["block_id"],
                "component_type_id": add_ons.get("component_type_id"),
                "mermaid": mermaid,
                "theme": record.get("theme"),
                "view": record.get("view"),
            }
        )
    return addons


def normalize_mermaid(source: str) -> str:
    return re.sub(r"\s+", " ", source.replace("\xa0", " ")).strip()


def compare_mermaid_blocks(local_blocks: list[str], remote_blocks: list[dict]) -> dict:
    matches = []
    for index, local_block in enumerate(local_blocks):
        remote_mermaid = remote_blocks[index]["mermaid"] if index < len(remote_blocks) else ""
        matches.append(
            {
                "index": index,
                "match": normalize_mermaid(local_block) == normalize_mermaid(remote_mermaid),
            }
        )
    return {
        "local_count": len(local_blocks),
        "remote_count": len(remote_blocks),
        "all_match": len(local_blocks) == len(remote_blocks)
        and all(item["match"] for item in matches),
        "matches": matches,
    }


def resolve_bearer_token(
    explicit_token: str | None, credentials: AppCredentials
) -> tuple[str, str]:
    if explicit_token:
        return explicit_token, "explicit"
    return fetch_tenant_access_token(credentials.app_id, credentials.app_secret), "tenant"


def build_report(
    local_markdown_path: str | Path,
    document_id: str,
    credentials: wrapper.AppCredentials,
    explicit_token: str | None = None,
) -> dict:
    local_markdown = Path(local_markdown_path).read_text(encoding="utf-8")
    local_blocks = extract_local_mermaid_blocks(local_markdown)
    bearer_token, token_source = resolve_bearer_token(explicit_token, credentials)
    remote_items = fetch_document_blocks(document_id, bearer_token)
    remote_blocks = extract_remote_mermaid_addons(remote_items)
    comparison = compare_mermaid_blocks(local_blocks, remote_blocks)
    return {
        "document_id": document_id,
        "local_markdown_path": str(local_markdown_path),
        "token_source": token_source,
        "remote_mermaid_component_type_ids": sorted(
            {block["component_type_id"] for block in remote_blocks}
        ),
        "remote_chart_block_ids": [block["block_id"] for block in remote_blocks],
        **comparison,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect local Mermaid markdown blocks against a live Feishu docx block tree."
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
        default=str(DEFAULT_CONFIG_PATH),
        help="Codex config path used to infer Feishu app credentials.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    credentials = resolve_app_credentials(args)
    report = build_report(
        local_markdown_path=args.markdown,
        document_id=args.document_id,
        credentials=credentials,
        explicit_token=args.token,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
