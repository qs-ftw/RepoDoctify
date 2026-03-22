from repodoctify.cli import main
from repodoctify.workspace import find_latest_workspace


def _make_repo(tmp_path):
    repo = tmp_path / "cli-demo-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# CLI Demo Repo\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "service.py").write_text("def run():\n    return 'ok'\n", encoding="utf-8")
    return repo


def test_cli_defaults_to_markdown_output(tmp_path):
    repo = _make_repo(tmp_path)

    exit_code = main(["--repo", str(repo), "--run-id", "cli-default"])

    workspace = find_latest_workspace(repo)
    assert exit_code == 0
    assert workspace is not None
    assert (workspace / "prompt" / "md-output-contract.json").exists()


def test_cli_supports_html_alias_and_workspace_reuse(tmp_path):
    repo = _make_repo(tmp_path)

    first_exit_code = main(["--repo", str(repo), "--run-id", "seed"])
    workspace = find_latest_workspace(repo)
    second_exit_code = main(["html", "--repo", str(repo), "--reuse-latest"])

    assert first_exit_code == 0
    assert second_exit_code == 0
    assert workspace is not None
    assert (workspace / "prompt" / "md-output-contract.json").exists()
    assert (workspace / "prompt" / "html-output-contract.json").exists()
