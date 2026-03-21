#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    target = Path.home() / ".codex" / "skills" / "RepoDoctify"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(
        repo_root,
        target,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc"),
    )
    print(f"Installed RepoDoctify to {target}")


if __name__ == "__main__":
    main()

