from __future__ import annotations

from pathlib import Path
from uuid import uuid4


REQUIRED_SUBDIRECTORIES = ("plan", "ir", "md", "html", "publish", "logs")


def ensure_external_workspace(
    repo_path: str | Path,
    workspace_root: str | Path | None = None,
    run_id: str | None = None,
) -> Path:
    repo = Path(repo_path).resolve()
    base_root = (
        Path(workspace_root).resolve()
        if workspace_root is not None
        else (repo.parent / ".repodoctify-workspaces").resolve()
    )

    if repo == base_root or repo in base_root.parents:
        raise ValueError("Workspace root must be outside the target repository")

    workspace = base_root / repo.name / (run_id or "run-" + uuid4().hex[:8])

    if repo == workspace or repo in workspace.parents:
        raise ValueError("Workspace must be outside the target repository")

    workspace.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_SUBDIRECTORIES:
        (workspace / name).mkdir(parents=True, exist_ok=True)
    return workspace

