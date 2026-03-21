from repodoctify.feishu_handoff import build_feishu_handoff_payload, ensure_feishu_dependencies
from repodoctify.models import DocumentSpec, RepositoryProfile


def test_feishu_handoff_reports_missing_lark_mcp():
    result = ensure_feishu_dependencies(installed_tools=set())
    assert result.ok is False
    assert "lark-mcp" in result.message


def test_feishu_handoff_builds_delegate_payload():
    payload = build_feishu_handoff_payload(
        RepositoryProfile(repo_label="demo", source_path="/tmp/demo"),
        [DocumentSpec(doc_id="overview", title="Overview", role="overview")],
        manifest_path="/tmp/out/manifest.json",
    )
    assert payload["delegate_skill"] == "feishu-knowledge-ops"
    assert payload["required_dependency"] == "lark-mcp"
    assert payload["document_titles"] == ["Overview"]
