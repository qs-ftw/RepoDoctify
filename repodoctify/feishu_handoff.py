from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil

from .models import DocumentSpec, RepositoryProfile


@dataclass(slots=True)
class FeishuDependencyResult:
    ok: bool
    message: str
    missing: tuple[str, ...] = ()


def _detected_tools() -> set[str]:
    detected: set[str] = set()
    env_value = os.environ.get("REPODOCTIFY_AVAILABLE_TOOLS", "")
    for item in env_value.split(","):
        item = item.strip()
        if item:
            detected.add(item)
    if shutil.which("lark-mcp") or shutil.which("lark_mcp"):
        detected.add("lark-mcp")
    return detected


def ensure_feishu_dependencies(installed_tools: set[str] | None = None) -> FeishuDependencyResult:
    tools = _detected_tools() if installed_tools is None else set(installed_tools)
    if "lark-mcp" in tools:
        return FeishuDependencyResult(
            ok=True,
            message="Feishu output dependencies available.",
        )
    return FeishuDependencyResult(
        ok=False,
        message=(
            "Feishu output depends on lark-mcp, but it is not available in the current "
            "environment. Install and configure lark-mcp before using the Feishu output command."
        ),
        missing=("lark-mcp",),
    )


def build_feishu_handoff_payload(
    profile: RepositoryProfile,
    docs: list[DocumentSpec],
    manifest_path: str | Path,
) -> dict:
    return {
        "delegate_skill": "feishu-knowledge-ops",
        "required_dependency": "lark-mcp",
        "repo_label": profile.repo_label,
        "manifest_path": str(manifest_path),
        "document_count": len(docs),
        "document_titles": [doc.title for doc in docs],
    }

