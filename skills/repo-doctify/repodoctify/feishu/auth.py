from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class FeishuAuthState:
    dependency_available: bool
    needs_user_access_token: bool
    user_token_present: bool
    user_token_validated: bool
    target_doc_probe_attempted: bool
    ready_for_execute: bool
    recommended_action: str
    auth_blocker: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def probe_feishu_auth_state(
    installed_tools: set[str] | None,
    require_user_access_token: bool = False,
    user_token_present: bool = False,
    user_token_validated: bool = False,
    target_doc_probe_attempted: bool = False,
    unresolved_target_documents: bool = False,
) -> FeishuAuthState:
    tools = set(installed_tools or set())
    dependency_available = "lark-mcp" in tools
    if not dependency_available:
        return FeishuAuthState(
            dependency_available=False,
            needs_user_access_token=require_user_access_token,
            user_token_present=False,
            user_token_validated=False,
            target_doc_probe_attempted=False,
            ready_for_execute=False,
            recommended_action="install_lark_mcp",
            auth_blocker="missing_dependency",
        )

    if require_user_access_token and not user_token_present:
        return FeishuAuthState(
            dependency_available=True,
            needs_user_access_token=True,
            user_token_present=False,
            user_token_validated=False,
            target_doc_probe_attempted=False,
            ready_for_execute=False,
            recommended_action="authorize_user_token",
            auth_blocker="missing_user_token",
        )

    if require_user_access_token and user_token_present and not user_token_validated:
        return FeishuAuthState(
            dependency_available=True,
            needs_user_access_token=True,
            user_token_present=True,
            user_token_validated=False,
            target_doc_probe_attempted=target_doc_probe_attempted,
            ready_for_execute=False,
            recommended_action="probe_target_doc",
            auth_blocker="token_not_validated",
        )

    if require_user_access_token and user_token_validated and unresolved_target_documents:
        return FeishuAuthState(
            dependency_available=True,
            needs_user_access_token=True,
            user_token_present=True,
            user_token_validated=True,
            target_doc_probe_attempted=target_doc_probe_attempted,
            ready_for_execute=False,
            recommended_action="resolve_target_doc",
            auth_blocker="unresolved_target_document",
        )

    ready_action = "ready_for_execute" if user_token_validated else "ready_for_dry_run"
    return FeishuAuthState(
        dependency_available=True,
        needs_user_access_token=require_user_access_token,
        user_token_present=user_token_present,
        user_token_validated=user_token_validated,
        target_doc_probe_attempted=target_doc_probe_attempted,
        ready_for_execute=user_token_validated or not require_user_access_token,
        recommended_action=ready_action,
        auth_blocker=None,
    )
