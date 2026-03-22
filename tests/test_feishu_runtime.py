import json
from pathlib import Path

from repodoctify.feishu_handoff import (
    FeishuPublishMode,
    build_feishu_publish_plan,
    ensure_feishu_dependencies,
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
