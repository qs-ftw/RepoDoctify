from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path

from ..models import DocumentSpec, RepositoryProfile


class FeishuExecutionMode(str, Enum):
    PLAN_ONLY = "plan_only"
    DRY_RUN = "dry_run"
    EXECUTE = "execute"


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
    requires_user_auth: bool = False


@dataclass(slots=True)
class FeishuVerificationCheck:
    check_kind: str
    required: bool
    reason: str


@dataclass(slots=True)
class FeishuVerificationPlan:
    checks: list[FeishuVerificationCheck]


def choose_feishu_update_strategy(
    role: str,
    target_exists: bool,
    structure_changed: bool,
    diagrams_changed: bool,
    tables_changed: bool,
    homepage_refresh_required: bool,
) -> FeishuPublishMode:
    if role == "homepage" or homepage_refresh_required:
        return FeishuPublishMode.UPDATE_HOMEPAGE_LAST
    if not target_exists:
        return FeishuPublishMode.CREATE_NEW
    if structure_changed or tables_changed:
        return FeishuPublishMode.FULL_REWRITE
    if role in {"bridge", "development_guide", "boundary_guide"} or diagrams_changed:
        return FeishuPublishMode.LOCALIZED_PATCH
    return FeishuPublishMode.UPDATE_IN_PLACE


def build_feishu_publish_plan(
    profile: RepositoryProfile,
    docs: list[DocumentSpec],
    manifest_path: str | Path,
    execution_mode: FeishuExecutionMode = FeishuExecutionMode.PLAN_ONLY,
) -> dict:
    targets = [_target_for_document(doc) for doc in docs]
    ordered_targets = _order_targets(targets)
    verification = _build_verification_plan(ordered_targets)
    return {
        "publisher": "repodoctify",
        "required_dependency": "lark-mcp",
        "execution_mode": execution_mode.value,
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
                "requires_user_auth": target.requires_user_auth,
            }
            for target in ordered_targets
        ],
        "verification": {
            "checks": [asdict(check) for check in verification.checks],
        },
    }


def build_feishu_verification_summary(plan: dict) -> dict:
    return {
        "publisher": plan["publisher"],
        "execution_mode": plan["execution_mode"],
        "document_count": plan["document_count"],
        "checks": list(plan.get("verification", {}).get("checks", [])),
        "status": "planned",
    }


def _target_for_document(document: DocumentSpec) -> FeishuPublishTarget:
    mode = choose_feishu_update_strategy(
        role=document.role,
        target_exists=document.role != "overview",
        structure_changed=document.role in {"stack", "module_map"},
        diagrams_changed=document.role in {"bridge", "stack"},
        tables_changed=document.role in {"boundary_guide"},
        homepage_refresh_required=document.role == "homepage",
    )
    if mode == FeishuPublishMode.UPDATE_HOMEPAGE_LAST:
        return FeishuPublishTarget(
            doc_id=document.doc_id,
            title=document.title,
            publish_mode=mode,
            update_strategy="child_docs_first",
            verify_as="homepage",
            requires_user_auth=True,
        )
    strategy = {
        FeishuPublishMode.LOCALIZED_PATCH: "remote_first_patch",
        FeishuPublishMode.FULL_REWRITE: "remote_first_rewrite",
        FeishuPublishMode.UPDATE_IN_PLACE: "remote_first_update",
        FeishuPublishMode.CREATE_NEW: "remote_first_create",
    }[mode]
    return FeishuPublishTarget(
        doc_id=document.doc_id,
        title=document.title,
        publish_mode=mode,
        update_strategy=strategy,
        verify_as="standard_doc",
        requires_user_auth=mode != FeishuPublishMode.CREATE_NEW,
    )


def _order_targets(targets: list[FeishuPublishTarget]) -> list[FeishuPublishTarget]:
    homepage_targets = [target for target in targets if target.publish_mode == FeishuPublishMode.UPDATE_HOMEPAGE_LAST]
    ordinary_targets = [target for target in targets if target.publish_mode != FeishuPublishMode.UPDATE_HOMEPAGE_LAST]
    return ordinary_targets + homepage_targets


def _build_verification_plan(targets: list[FeishuPublishTarget]) -> FeishuVerificationPlan:
    checks = [
        FeishuVerificationCheck("title", True, "confirm the visible title stayed correct"),
        FeishuVerificationCheck("section_presence", True, "confirm major sections landed"),
        FeishuVerificationCheck("homepage_links", True, "confirm homepage or index links were refreshed"),
        FeishuVerificationCheck("diagram_blocks", True, "confirm Mermaid or board blocks match the selected strategy"),
    ]
    if any(target.publish_mode == FeishuPublishMode.LOCALIZED_PATCH for target in targets):
        checks.append(
            FeishuVerificationCheck(
                "remote_content_preserved",
                True,
                "confirm localized patch preserved remote-only content outside edited sections",
            )
        )
    if any(target.publish_mode == FeishuPublishMode.FULL_REWRITE for target in targets):
        checks.append(
            FeishuVerificationCheck(
                "same_document_id",
                False,
                "confirm rewrite strategy did not unexpectedly fork the document when in-place update was intended",
            )
        )
    return FeishuVerificationPlan(checks=checks)
