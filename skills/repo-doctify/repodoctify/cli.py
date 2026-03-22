from __future__ import annotations

import argparse
from pathlib import Path

from .runtime import (
    COMMAND_FEISHU,
    COMMAND_HTML,
    COMMAND_PLAN,
    COMMAND_RENDER_MD,
    run_repodoctify,
)


COMMAND_ALIASES = {
    "plan": COMMAND_PLAN,
    "md": COMMAND_RENDER_MD,
    "html": COMMAND_HTML,
    "feishu": COMMAND_FEISHU,
    COMMAND_PLAN: COMMAND_PLAN,
    COMMAND_RENDER_MD: COMMAND_RENDER_MD,
    COMMAND_HTML: COMMAND_HTML,
    COMMAND_FEISHU: COMMAND_FEISHU,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repodoctify")
    parser.add_argument(
        "command",
        nargs="?",
        choices=sorted(COMMAND_ALIASES),
        help="ASCII alias or exact user-facing command label",
    )
    parser.add_argument("--repo", default=".", help="Path to the target repository")
    parser.add_argument("--workspace-root", help="Optional external workspace root")
    parser.add_argument("--public-locator", help="Optional public repository URL")
    parser.add_argument("--run-id", help="Optional explicit run id for new workspaces")
    parser.add_argument(
        "--reuse-latest",
        action="store_true",
        help="Reuse the latest existing external workspace for this repository if one exists",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    normalized_command = COMMAND_ALIASES.get(args.command, COMMAND_RENDER_MD)
    result = run_repodoctify(
        Path(args.repo),
        command=normalized_command,
        workspace_root=args.workspace_root,
        public_locator=args.public_locator,
        run_id=args.run_id,
        reuse_latest=args.reuse_latest,
    )
    print(result.workspace)
    return 0
