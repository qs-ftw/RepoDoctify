#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PLATFORM_TARGETS = {
    "codex": Path.home() / ".codex" / "skills" / "repo-doctify",
    "claude": Path.home() / ".claude" / "skills" / "repo-doctify",
    "trae": Path.home() / ".trae" / "skills" / "repo-doctify",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="install_local_skill.py")
    parser.add_argument(
        "--platform",
        choices=sorted(PLATFORM_TARGETS),
        default="codex",
        help="Local assistant platform to install into",
    )
    return parser


def _copy_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"),
    )


def main() -> None:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    skill_root = repo_root / "skills" / "repo-doctify"
    target = PLATFORM_TARGETS[args.platform]
    _copy_tree(skill_root, target)
    print(f"Installed repo-doctify to {target}")
    if args.platform == "trae":
        trae_rule_src = repo_root / "platform" / "trae" / "rules" / "repo-doctify.md"
        trae_rule_dst = Path.home() / ".trae" / "rules" / "repo-doctify.md"
        trae_rule_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(trae_rule_src, trae_rule_dst)
        print(f"Installed Trae rule companion to {trae_rule_dst}")
    restart_target = {
        "codex": "Codex",
        "claude": "Claude Code",
        "trae": "Trae",
    }[args.platform]
    print(f"Restart {restart_target} to pick up the updated skill.")


if __name__ == "__main__":
    main()
