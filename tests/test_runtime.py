import json

import pytest

from repodoctify.runtime import (
    COMMAND_FEISHU,
    COMMAND_HTML,
    COMMAND_PLAN,
    COMMAND_RENDER_MD,
    run_repodoctify,
)


def _make_repo(tmp_path):
    repo = tmp_path / "sample-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Sample Repo\n\nA demo repository.\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")
    return repo


def test_default_run_writes_markdown_outputs_to_external_workspace(tmp_path):
    repo = _make_repo(tmp_path)

    result = run_repodoctify(repo, run_id="default")

    assert result.command == COMMAND_RENDER_MD
    assert repo not in result.workspace.parents
    assert (result.workspace / "plan" / "docset-plan.json").exists()
    assert (result.workspace / "ir" / "docset-ir.json").exists()
    assert (result.workspace / "md" / "README.md").exists()
    assert (result.workspace / "md" / "manifest.json").exists()
    assert not (repo / ".repodoctify-workspaces").exists()

    manifest = json.loads((result.workspace / "md" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["repo_label"] == "sample-repo"
    assert manifest["documents"]


def test_plan_command_stops_before_rendering_outputs(tmp_path):
    repo = _make_repo(tmp_path)

    result = run_repodoctify(repo, command=COMMAND_PLAN, run_id="plan-only")

    assert result.command == COMMAND_PLAN
    assert (result.workspace / "plan" / "docset-plan.json").exists()
    assert not (result.workspace / "ir" / "docset-ir.json").exists()
    assert list((result.workspace / "md").iterdir()) == []
    assert list((result.workspace / "html").iterdir()) == []


def test_html_command_writes_html_pages(tmp_path):
    repo = _make_repo(tmp_path)

    result = run_repodoctify(repo, command=COMMAND_HTML, run_id="html")

    assert result.command == COMMAND_HTML
    assert (result.workspace / "plan" / "docset-plan.json").exists()
    assert (result.workspace / "ir" / "docset-ir.json").exists()
    assert (result.workspace / "html" / "index.html").exists()
    assert (result.workspace / "html" / "homepage.html").exists()


def test_feishu_command_requires_lark_mcp(tmp_path):
    repo = _make_repo(tmp_path)

    with pytest.raises(RuntimeError, match="lark-mcp"):
        run_repodoctify(repo, command=COMMAND_FEISHU, installed_tools=set(), run_id="feishu-missing")


def test_feishu_command_writes_handoff_when_dependencies_present(tmp_path):
    repo = _make_repo(tmp_path)

    result = run_repodoctify(
        repo,
        command=COMMAND_FEISHU,
        installed_tools={"lark-mcp"},
        run_id="feishu-ready",
    )

    payload = json.loads(
        (result.workspace / "publish" / "feishu-handoff.json").read_text(encoding="utf-8")
    )
    assert payload["delegate_skill"] == "feishu-knowledge-ops"
    assert payload["required_dependency"] == "lark-mcp"
    assert payload["document_titles"]
