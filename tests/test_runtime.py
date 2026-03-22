import json

import pytest

from repodoctify.targeting import TargetRepoDecision
from repodoctify.runtime import (
    COMMAND_FEISHU,
    COMMAND_HTML,
    COMMAND_PLAN,
    COMMAND_RENDER_MD,
    RepoDoctifyRequest,
    resolve_repo_decision,
    run_repodoctify,
    run_repodoctify_request,
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
    assert result.resolved_repo_path == repo.resolve()
    assert result.repo_resolution_reason == "explicit_repo"


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


def test_runtime_can_reuse_existing_workspace(tmp_path):
    repo = _make_repo(tmp_path)

    first_result = run_repodoctify(repo, run_id="seed")
    second_result = run_repodoctify(repo, command=COMMAND_HTML, reuse_latest=True)

    assert second_result.workspace == first_result.workspace
    assert (first_result.workspace / "md" / "README.md").exists()
    assert (first_result.workspace / "html" / "index.html").exists()


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
        (result.workspace / "publish" / "feishu-publish-plan.json").read_text(encoding="utf-8")
    )
    assert payload["publisher"] == "repodoctify"
    assert payload["required_dependency"] == "lark-mcp"
    assert payload["document_titles"]
    assert (result.workspace / "publish" / "verification-summary.json").exists()


def test_runtime_resolves_current_repo_by_default(tmp_path):
    repo = _make_repo(tmp_path)

    decision = resolve_repo_decision(current_dir=repo)

    assert isinstance(decision, TargetRepoDecision)
    assert decision.repo_path == repo.resolve()
    assert decision.should_ask is False
    assert decision.reason == "current_dir_repo"


def test_runtime_flags_repo_conflict_in_strict_mode(tmp_path):
    current_repo = _make_repo(tmp_path)
    requested_repo = tmp_path / "other-repo"
    requested_repo.mkdir()
    (requested_repo / "README.md").write_text("# Other Repo\n", encoding="utf-8")

    decision = resolve_repo_decision(
        current_dir=current_repo,
        requested_repo=requested_repo,
        strict_conflict_check=True,
    )

    assert decision.should_ask is True
    assert decision.reason == "repo_conflict"


def test_runtime_rejects_conflicting_repo_execution_in_strict_mode(tmp_path):
    current_repo = _make_repo(tmp_path)
    requested_repo = tmp_path / "requested-repo"
    requested_repo.mkdir()
    (requested_repo / "README.md").write_text("# Requested Repo\n", encoding="utf-8")
    (requested_repo / "src").mkdir()
    (requested_repo / "src" / "app.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")

    with pytest.raises(ValueError, match="conflicts"):
        run_repodoctify(
            requested_repo,
            current_dir=current_repo,
            strict_conflict_check=True,
            run_id="strict-conflict",
        )


def test_run_repodoctify_request_supports_skill_facing_execution(tmp_path):
    repo = _make_repo(tmp_path)

    request = RepoDoctifyRequest(
        requested_repo=repo,
        current_dir=tmp_path,
        command=COMMAND_RENDER_MD,
        run_id="request-default",
    )

    result = run_repodoctify_request(request)

    assert result.command == COMMAND_RENDER_MD
    assert result.resolved_repo_path == repo.resolve()
    assert result.repo_resolution_reason == "explicit_repo"
    assert (result.workspace / "md" / "README.md").exists()
