from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4


REQUIRED_SUBDIRECTORIES = ("plan", "ir", "md", "html", "publish", "logs")
WORKSPACE_METADATA_FILE = "workspace-metadata.json"


def resolve_workspace_root(
    repo_path: str | Path,
    workspace_root: str | Path | None = None,
) -> Path:
    repo = Path(repo_path).resolve()
    base_root = (
        Path(workspace_root).resolve()
        if workspace_root is not None
        else (repo.parent / ".repodoctify-workspaces").resolve()
    )
    if repo == base_root or repo in base_root.parents:
        raise ValueError("Workspace root must be outside the target repository")
    return base_root


def ensure_external_workspace(
    repo_path: str | Path,
    workspace_root: str | Path | None = None,
    run_id: str | None = None,
) -> Path:
    repo = Path(repo_path).resolve()
    base_root = resolve_workspace_root(repo, workspace_root=workspace_root)
    workspace = base_root / repo.name / (run_id or "run-" + uuid4().hex[:8])

    if repo == workspace or repo in workspace.parents:
        raise ValueError("Workspace must be outside the target repository")

    workspace.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_SUBDIRECTORIES:
        (workspace / name).mkdir(parents=True, exist_ok=True)
    return workspace


def write_workspace_metadata(workspace: str | Path, repo_path: str | Path) -> Path:
    workspace_path = Path(workspace).resolve()
    repo = Path(repo_path).resolve()
    metadata_path = workspace_path / WORKSPACE_METADATA_FILE
    metadata = {
        "repo_label": repo.name,
        "source_path": str(repo),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata_path


def find_latest_workspace(
    repo_path: str | Path,
    workspace_root: str | Path | None = None,
) -> Path | None:
    repo = Path(repo_path).resolve()
    base_root = resolve_workspace_root(repo, workspace_root=workspace_root)
    repo_root = base_root / repo.name
    if not repo_root.exists() or not repo_root.is_dir():
        return None

    candidates: list[Path] = []
    for entry in repo_root.iterdir():
        if not entry.is_dir():
            continue
        metadata_path = entry / WORKSPACE_METADATA_FILE
        if metadata_path.exists():
            try:
                payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if payload.get("source_path") != str(repo):
                continue
        candidates.append(entry)

    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)
