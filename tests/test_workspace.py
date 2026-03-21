from pathlib import Path

import pytest

from repodoctify.workspace import ensure_external_workspace


def test_workspace_defaults_outside_target_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    workspace = ensure_external_workspace(repo)
    assert repo not in workspace.parents
    assert workspace != repo
    for name in ["plan", "ir", "md", "html", "publish", "logs"]:
        assert (workspace / name).exists()


def test_workspace_rejects_repo_internal_root(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(ValueError):
        ensure_external_workspace(repo, workspace_root=repo / "out")

