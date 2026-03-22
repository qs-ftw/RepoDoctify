from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
import shutil

from .models import DocumentSpec, RepositoryProfile


@dataclass(slots=True)
class FeishuDependencyResult:
    ok: bool
    message: str
    missing: tuple[str, ...] = ()


class FeishuPublishMode(str, Enum):
    CREATE_NEW = "create_new"
    UPDATE_IN_PLACE = "update_in_place"
    LOCALIZED_PATCH = "localized_patch"
    FULL_REWRITE = "full_rewrite"
    UPDATE_HOMEPAGE_LAST = "update_homepage_last"


@dataclass(slots=True)
class FeishuPublishTarget:
    doc_id: str
    title: str
    publish_mode: FeishuPublishMode
    update_strategy: str
    verify_as: str


@dataclass(slots=True)
class FeishuVerificationPlan:
    checks: list[str]


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


def build_feishu_publish_plan(
    profile: RepositoryProfile,
    docs: list[DocumentSpec],
    manifest_path: str | Path,
) -> dict:
    targets = [_target_for_document(doc) for doc in docs]
    ordered_targets = _order_targets(targets)
    verification = _build_verification_plan(ordered_targets)
    return {
        "publisher": "repodoctify",
        "required_dependency": "lark-mcp",
        "repo_label": profile.repo_label,
        "manifest_path": str(manifest_path),
        "document_count": len(docs),
        "document_titles": [target.title for target in ordered_targets],
        "documents": [
            {
                "doc_id": target.doc_id,
                "title": target.title,
                "publish_mode": target.publish_mode.value,
                "update_strategy": target.update_strategy,
                "verify_as": target.verify_as,
            }
            for target in ordered_targets
        ],
        "verification": {
            "checks": verification.checks,
        },
    }


def build_feishu_verification_summary(plan: dict) -> dict:
    return {
        "publisher": plan["publisher"],
        "document_count": plan["document_count"],
        "checks_planned": list(plan.get("verification", {}).get("checks", [])),
        "status": "planned",
    }


def _target_for_document(document: DocumentSpec) -> FeishuPublishTarget:
    if document.role == "homepage":
        return FeishuPublishTarget(
            doc_id=document.doc_id,
            title=document.title,
            publish_mode=FeishuPublishMode.UPDATE_HOMEPAGE_LAST,
            update_strategy="child_docs_first",
            verify_as="homepage",
        )
    if document.role in {"bridge", "development_guide", "boundary_guide"}:
        mode = FeishuPublishMode.LOCALIZED_PATCH
        strategy = "remote_first_patch"
    else:
        mode = FeishuPublishMode.CREATE_NEW
        strategy = "remote_first_create"
    return FeishuPublishTarget(
        doc_id=document.doc_id,
        title=document.title,
        publish_mode=mode,
        update_strategy=strategy,
        verify_as="standard_doc",
    )


def _order_targets(targets: list[FeishuPublishTarget]) -> list[FeishuPublishTarget]:
    homepage_targets = [target for target in targets if target.publish_mode == FeishuPublishMode.UPDATE_HOMEPAGE_LAST]
    ordinary_targets = [target for target in targets if target.publish_mode != FeishuPublishMode.UPDATE_HOMEPAGE_LAST]
    return ordinary_targets + homepage_targets


def _build_verification_plan(targets: list[FeishuPublishTarget]) -> FeishuVerificationPlan:
    checks = [
        "confirm target document ids or newly created document ids are recorded",
        "confirm readback preserves intended titles and major sections",
        "confirm homepage or index links are updated after child docs land",
        "confirm diagram and table blocks match the selected publish strategy",
    ]
    if any(target.publish_mode == FeishuPublishMode.LOCALIZED_PATCH for target in targets):
        checks.append("confirm localized patch preserved remote-only content outside the edited section")
    return FeishuVerificationPlan(checks=checks)
