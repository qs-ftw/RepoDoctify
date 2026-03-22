from pathlib import Path

from repodoctify.targeting import TargetRepoDecision, resolve_target_repo


def test_resolve_target_repo_prefers_current_repo_without_questions(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")

    decision = resolve_target_repo(current_dir=repo)

    assert isinstance(decision, TargetRepoDecision)
    assert decision.repo_path == repo.resolve()
    assert decision.should_ask is False
    assert decision.reason == "current_dir_repo"


def test_resolve_target_repo_uses_requested_repo_when_explicit(tmp_path):
    current_repo = tmp_path / "current"
    requested_repo = tmp_path / "requested"
    current_repo.mkdir()
    requested_repo.mkdir()
    (current_repo / "README.md").write_text("# Current\n", encoding="utf-8")
    (requested_repo / "README.md").write_text("# Requested\n", encoding="utf-8")

    decision = resolve_target_repo(current_dir=current_repo, requested_repo=requested_repo)

    assert decision.repo_path == requested_repo.resolve()
    assert decision.should_ask is False
    assert decision.reason == "explicit_repo"


def test_resolve_target_repo_flags_conflict_for_follow_up(tmp_path):
    current_repo = tmp_path / "current"
    requested_repo = tmp_path / "requested"
    current_repo.mkdir()
    requested_repo.mkdir()
    (current_repo / "README.md").write_text("# Current\n", encoding="utf-8")
    (requested_repo / "README.md").write_text("# Requested\n", encoding="utf-8")

    decision = resolve_target_repo(
        current_dir=current_repo,
        requested_repo=requested_repo,
        strict_conflict_check=True,
    )

    assert decision.should_ask is True
    assert decision.reason == "repo_conflict"
    assert "conflicts" in decision.question
