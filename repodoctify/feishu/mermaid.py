from __future__ import annotations

import json
import re


MERMAID_COMPONENT_TYPE_ID = "blk_631fefbbae02400430b8f9f4"
UNTERMINATED_SLASH_LABEL_PATTERN = re.compile(
    r'(?P<node_id>\b[A-Za-z0-9_]+)\[/(?P<label>[^\]\n]*?[^/\]\n])\]'
)


def normalize_mermaid(source: str) -> str:
    return "\n".join(line.rstrip() for line in source.strip().splitlines())


def sanitize_mermaid_for_feishu(source: str) -> str:
    def replace(match: re.Match) -> str:
        return f'{match.group("node_id")}["/{match.group("label")}"]'

    return UNTERMINATED_SLASH_LABEL_PATTERN.sub(replace, source)


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
