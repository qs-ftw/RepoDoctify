from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPO_MARKERS = (
    ".git",
    "README.md",
    "README.rst",
    "pyproject.toml",
    "package.json",
    "setup.py",
    "Cargo.toml",
    "go.mod",
)


@dataclass(slots=True)
class TargetRepoDecision:
    repo_path: Path
    should_ask: bool
    reason: str
    question: str = ""


def resolve_target_repo(
    current_dir: str | Path,
    requested_repo: str | Path | None = None,
    strict_conflict_check: bool = False,
) -> TargetRepoDecision:
    current_repo = Path(current_dir).resolve()
    explicit_repo = Path(requested_repo).resolve() if requested_repo is not None else None

    if explicit_repo is not None:
        if strict_conflict_check and _looks_like_repo(current_repo) and explicit_repo != current_repo:
            return TargetRepoDecision(
                repo_path=explicit_repo,
                should_ask=True,
                reason="repo_conflict",
                question=(
                    f"Requested repo `{explicit_repo}` conflicts with the current repository "
                    f"`{current_repo}`. Continue with the requested repo?"
                ),
            )
        return TargetRepoDecision(
            repo_path=explicit_repo,
            should_ask=False,
            reason="explicit_repo",
        )

    if _looks_like_repo(current_repo):
        return TargetRepoDecision(
            repo_path=current_repo,
            should_ask=False,
            reason="current_dir_repo",
        )

    return TargetRepoDecision(
        repo_path=current_repo,
        should_ask=False,
        reason="current_dir_fallback",
    )


def _looks_like_repo(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    return any((path / marker).exists() for marker in REPO_MARKERS)
