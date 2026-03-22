#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _repo_root() -> Path:
    return _skill_root().parents[1]


def _ensure_import_path() -> None:
    skill_root = _skill_root()
    repo_root = _repo_root()
    for candidate in (skill_root, repo_root):
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_repodoctify.py")
    parser.add_argument("command", nargs="?", choices=("plan", "md", "html", "feishu"), default="md")
    parser.add_argument("--repo", default=".", help="Target repository path")
    parser.add_argument("--workspace-root", help="Optional external workspace root")
    parser.add_argument("--public-locator", help="Optional public repository URL")
    parser.add_argument("--run-id", help="Optional explicit run id")
    parser.add_argument("--current-dir", help="Optional current working directory for strict conflict resolution")
    parser.add_argument("--reuse-latest", action="store_true", help="Reuse the latest workspace for this repo")
    parser.add_argument("--strict-conflict-check", action="store_true", help="Fail on current-dir/repo conflicts")
    parser.add_argument(
        "--installed-tool",
        action="append",
        default=[],
        help="Declare installed external tools such as lark-mcp",
    )
    return parser


def main() -> int:
    _ensure_import_path()
    from repodoctify.runtime import (
        COMMAND_FEISHU,
        COMMAND_HTML,
        COMMAND_PLAN,
        COMMAND_RENDER_MD,
        run_repodoctify,
    )

    args = build_parser().parse_args()
    command_map = {
        "plan": COMMAND_PLAN,
        "md": COMMAND_RENDER_MD,
        "html": COMMAND_HTML,
        "feishu": COMMAND_FEISHU,
    }
    result = run_repodoctify(
        repo_path=Path(args.repo),
        command=command_map[args.command],
        workspace_root=args.workspace_root,
        public_locator=args.public_locator,
        installed_tools=set(args.installed_tool),
        run_id=args.run_id,
        reuse_latest=args.reuse_latest,
        current_dir=args.current_dir,
        strict_conflict_check=args.strict_conflict_check,
    )
    print(result.workspace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
