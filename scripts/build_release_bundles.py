#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path
import zipfile


def _copy_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"),
    )


def _zip_dir(source_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_dir():
                continue
            archive.write(path, path.relative_to(source_dir.parent))


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    skill_root = repo_root / "skills" / "repo-doctify"
    dist_root = repo_root / "dist" / "release"
    if dist_root.exists():
        shutil.rmtree(dist_root)

    codex_root = dist_root / "codex" / "repo-doctify"
    claude_root = dist_root / "claude" / "repo-doctify"
    trae_skill_root = dist_root / "trae" / "skills" / "repo-doctify"
    trae_rule_root = dist_root / "trae" / "rules"

    _copy_tree(skill_root, codex_root)
    _copy_tree(skill_root, claude_root)
    _copy_tree(skill_root, trae_skill_root)

    trae_rule_root.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        repo_root / "platform" / "trae" / "rules" / "repo-doctify.md",
        trae_rule_root / "repo-doctify.md",
    )
    _zip_dir(claude_root, dist_root / "claude" / "repo-doctify.zip")

    print(f"Built release bundles under {dist_root}")


if __name__ == "__main__":
    main()
