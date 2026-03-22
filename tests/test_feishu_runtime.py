import json
from pathlib import Path

from repodoctify.feishu_handoff import (
    FeishuExecutionMode,
    FeishuPublishMode,
    choose_feishu_update_strategy,
    build_feishu_publish_plan,
    build_feishu_verification_summary,
    ensure_feishu_dependencies,
    probe_feishu_auth_state,
)
from repodoctify.models import DocumentSpec, RepositoryProfile


def test_feishu_runtime_reports_missing_lark_mcp():
    result = ensure_feishu_dependencies(installed_tools=set())
    assert result.ok is False
    assert "lark-mcp" in result.message


def test_feishu_publish_plan_is_owned_by_repodoctify():
    plan = build_feishu_publish_plan(
        RepositoryProfile(repo_label="demo", source_path="/tmp/demo"),
        [DocumentSpec(doc_id="overview", title="Overview", role="overview")],
        manifest_path="/tmp/out/manifest.json",
    )

    assert plan["publisher"] == "repodoctify"
    assert plan["required_dependency"] == "lark-mcp"
    assert plan["document_titles"] == ["Overview"]
    assert plan["documents"][0]["publish_mode"] == FeishuPublishMode.CREATE_NEW.value
    assert "delegate_skill" not in plan


def test_feishu_publish_plan_marks_homepage_last():
    plan = build_feishu_publish_plan(
        RepositoryProfile(repo_label="demo", source_path="/tmp/demo"),
        [
            DocumentSpec(doc_id="homepage", title="Homepage", role="homepage"),
            DocumentSpec(doc_id="overview", title="Overview", role="overview"),
        ],
        manifest_path="/tmp/out/manifest.json",
    )

    assert plan["documents"][0]["doc_id"] == "overview"
    assert plan["documents"][1]["doc_id"] == "homepage"
    assert plan["documents"][1]["publish_mode"] == FeishuPublishMode.UPDATE_HOMEPAGE_LAST.value


def test_feishu_publish_plan_uses_requested_target_doc_ids():
    plan = build_feishu_publish_plan(
        RepositoryProfile(repo_label="demo", source_path="/tmp/demo"),
        [
            DocumentSpec(doc_id="homepage", title="Homepage", role="homepage"),
            DocumentSpec(doc_id="overview", title="Overview", role="overview"),
        ],
        manifest_path="/tmp/out/manifest.json",
        requested_target_doc_ids={
            "homepage": "doc_homepage_123",
            "overview": "doc_overview_456",
        },
    )

    overview_target = plan["documents"][0]
    homepage_target = plan["documents"][1]

    assert overview_target["doc_id"] == "overview"
    assert overview_target["target_document_id"] == "doc_overview_456"
    assert overview_target["target_source"] == "request"
    assert overview_target["publish_mode"] == FeishuPublishMode.UPDATE_IN_PLACE.value
    assert homepage_target["target_document_id"] == "doc_homepage_123"
    assert homepage_target["target_source"] == "request"


def test_feishu_publish_plan_marks_unresolved_execute_targets():
    plan = build_feishu_publish_plan(
        RepositoryProfile(repo_label="demo", source_path="/tmp/demo"),
        [
            DocumentSpec(doc_id="homepage", title="Homepage", role="homepage"),
            DocumentSpec(doc_id="bridge", title="Bridge", role="bridge"),
        ],
        manifest_path="/tmp/out/manifest.json",
        execution_mode=FeishuExecutionMode.EXECUTE,
    )

    bridge_target = next(document for document in plan["documents"] if document["doc_id"] == "bridge")

    assert bridge_target["target_resolution"] == "lookup_required"
    assert bridge_target["execute_ready"] is False
    assert plan["execute_ready"] is False
    assert plan["execute_blockers"] == ["unresolved_target_documents"]


def test_feishu_publish_plan_can_be_saved_as_json(tmp_path):
    plan = build_feishu_publish_plan(
        RepositoryProfile(repo_label="demo", source_path="/tmp/demo"),
        [DocumentSpec(doc_id="overview", title="Overview", role="overview")],
        manifest_path=tmp_path / "manifest.json",
    )

    target = tmp_path / "publish-plan.json"
    target.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    loaded = json.loads(target.read_text(encoding="utf-8"))
    assert loaded["publisher"] == "repodoctify"
    assert loaded["documents"][0]["title"] == "Overview"


def test_choose_feishu_update_strategy_prefers_localized_patch_for_bridge_docs():
    mode = choose_feishu_update_strategy(
        role="bridge",
        target_exists=True,
        structure_changed=False,
        diagrams_changed=True,
        tables_changed=False,
        homepage_refresh_required=False,
    )
    assert mode == FeishuPublishMode.LOCALIZED_PATCH


def test_choose_feishu_update_strategy_uses_full_rewrite_for_table_heavy_changes():
    mode = choose_feishu_update_strategy(
        role="overview",
        target_exists=True,
        structure_changed=True,
        diagrams_changed=False,
        tables_changed=True,
        homepage_refresh_required=False,
    )
    assert mode == FeishuPublishMode.FULL_REWRITE


def test_probe_feishu_auth_state_reports_missing_dependency():
    state = probe_feishu_auth_state(installed_tools=set())
    assert state.recommended_action == "install_lark_mcp"
    assert state.ready_for_execute is False


def test_probe_feishu_auth_state_reports_missing_user_auth_when_required():
    state = probe_feishu_auth_state(
        installed_tools={"lark-mcp"},
        require_user_access_token=True,
        user_token_present=False,
    )
    assert state.recommended_action == "authorize_user_token"
    assert state.ready_for_execute is False


def test_probe_feishu_auth_state_requires_target_resolution_before_execute():
    state = probe_feishu_auth_state(
        installed_tools={"lark-mcp"},
        require_user_access_token=True,
        user_token_present=True,
        user_token_validated=True,
        unresolved_target_documents=True,
    )
    assert state.recommended_action == "resolve_target_doc"
    assert state.auth_blocker == "unresolved_target_document"
    assert state.ready_for_execute is False


def test_feishu_verification_summary_includes_structured_checks():
    plan = build_feishu_publish_plan(
        RepositoryProfile(repo_label="demo", source_path="/tmp/demo"),
        [
            DocumentSpec(doc_id="homepage", title="Homepage", role="homepage"),
            DocumentSpec(doc_id="overview", title="Overview", role="overview"),
        ],
        manifest_path="/tmp/out/manifest.json",
        execution_mode=FeishuExecutionMode.DRY_RUN,
    )

    summary = build_feishu_verification_summary(plan)

    assert summary["execution_mode"] == FeishuExecutionMode.DRY_RUN.value
    assert summary["checks"][0]["check_kind"] == "title"
    assert summary["status"] == "planned"
