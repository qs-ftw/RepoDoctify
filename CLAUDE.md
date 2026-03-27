# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RepoDoctify is a **portable AI assistant skill** (not a standalone app). It ships as a skill bundle for Codex, Claude Code, and Trae. Its job is to turn an unfamiliar code repository into a structured learning docset (Markdown, HTML, or Feishu).

The Python package in this repo is the skill's **internal runtime** — it prepares prompts and IR but **must not synthesize final document prose**. The canonical skill source lives at `skills/repo-doctify/`.

Python >= 3.11 is required.

## Primary Usage

The primary entrypoint is the **AI assistant skill** (not the Python CLI):

```bash
$repo-doctify                        # Default: Markdown docset
$repo-doctify plan                   # Docset structure only
$repo-doctify md                      # Markdown prompt bundle
$repo-doctify html                    # HTML prompt bundle
$repo-doctify feishu                  # Feishu publish bundle
```

## Development Commands

**Requires Python >= 3.11.** Tests will fail on Python 3.9/3.10. Use `uv venv --python 3.14` to set up a test environment if needed.

```bash
# Run tests (requires Python 3.11+)
PYTHONPATH=. /path/to/py3.14/bin/python -m pytest tests/ -v

# Install skill to platform (canonical source: skills/repo-doctify/)
python3 scripts/install_local_skill.py --platform claude  # default
python3 scripts/install_local_skill.py --platform codex
python3 scripts/install_local_skill.py --platform trae

# Build release bundles
python3 scripts/build_release_bundles.py
# Output: dist/release/{codex,claude,trae}/
```

## Release Scope

**Good fit:**
- Python, TypeScript/JavaScript repositories (strong support)
- Go, Rust, Java repositories (structured support)
- Generic repos (conservative fallback guidance)
- Markdown as the default primary deliverable

**Not yet good fit:**
- Feishu-first publishing workflows
- Languages outside Python, TS/JS, Go, Rust, Java with unusual structure
- Deep semantic analysis (full call graphs, AST-level reasoning)

## Architecture

```
User Request ($repo-doctify skill)
    │
    ▼
targeting.py     ── resolve which repo to analyze
    │
    ▼
analysis.py      ── scan repo structure, detect language/tooling
    │
    ▼
planning.py      ── generate docset plan (8 blueprint documents)
    │
    ▼
prompting.py     ── build authoring prompt bundle
    │
    ▼
External Workspace (.repodoctify-workspaces/, in parent of target repo)
  ├── ir/           repository-analysis.json
  ├── plan/         docset-plan.json
  ├── artifacts/   manifest.json
  ├── prompt/       packet.json, authoring-brief.md, write-targets.json,
  │                  document-prompts.json, <mode>-output-contract.json
  ├── md/           final Markdown output
  ├── html/         final HTML output
  └── publish/      Feishu-specific output
    │
    ▼
AI Model Authors Final Docset Content
```

## Key Modules

| File | Purpose |
|------|---------|
| `runtime.py` | Main orchestration: `run_repodoctify()`, `run_repodoctify_request()` |
| `analysis.py` | Scans repo structure, detects language/tooling, test layout |
| `planning.py` | Generates 8-type docset skeleton |
| `prompting.py` | Creates model-facing authoring contracts (prompt bundle) |
| `workspace.py` | Creates/manages `.repodoctify-workspaces/` |
| `targeting.py` | Resolves target repository path with conflict detection |
| `manifest.py` | Builds docset manifest from analysis + plan |
| `models.py` | Dataclasses: `RepositoryProfile`, `DocsetPlan`, `DocumentSpec`, etc. |

## Symlink Layout

Most top-level dirs are **symlinks** into `skills/repo-doctify/`: `repodoctify/`, `examples/`, `references/`. The `tests/` directory at the repo root is an independent copy used by pytest (configured via `pythonpath = ["."]` in pyproject.toml). Canonical source for everything else is always `skills/repo-doctify/`.

## Output Isolation

All output goes to `.repodoctify-workspaces/` in the **parent directory** of the target repository — never inside the target repo itself.

## Docset Blueprint (8 Document Types)

1. `homepage` — learning entry point
2. `overview` — what the repo does
3. `code-reading-path` — main anchor chain to follow first
4. `stack-and-entrypoints` — entry points, runtime, tech stack
5. `bridge-topics` — cross-cutting mechanisms that confuse readers
6. `module-map` — core directories and module responsibilities
7. `evidence-guide` — evidence for behavior/boundary judgment
8. `development-guide` — how to start making changes

## Feishu Publish Modes

- `plan_only` — publish planning without remote writes
- `dry_run` — execution-ready validation without remote writes
- `execute` — remote write path (future)

Feishu requires `lark-mcp` as an external dependency. If unavailable, the runtime raises a clear error instead of blocking Markdown/HTML preparation.

## Development & Validation Workflow

### Iteration Cycle

1. **Develop** — implement the feature or fix.
2. **Test gate** — only if scripts or tool-level code was touched:
   - If changed: add or update tests in `tests/`, then `pytest -v`
   - If not changed: skip tests
3. **End-of-round verification** — run Codex against a real target repo to validate output quality.
4. **Stop and present results** — user reviews the generated docset, gives structured feedback.
5. **Next round** — incorporate feedback, repeat.

### End-of-Round Verification Procedure

Target repo: `/Users/qiangshenggao/project/github/pypto-autograd`

Steps:

```bash
# 1. Install the updated skill
python3 scripts/install_local_skill.py --platform codex

# 2. Launch codex in the target repo
cd /Users/qiangshenggao/project/github/pypto-autograd
codex

# 3. Inside codex, trigger the skill
$repo-doctify md

# 4. Codex will write the docset to .repodoctify-workspaces/ inside the
#    parent directory of the target repo. Stop here and report the workspace path.
```

Then stop and report:
- The workspace path
- The 8 generated documents and their sizes
- Any observable quality issues or runtime errors

User reviews the output and provides structured feedback before the next round begins.

### What Triggers the Test Gate

| Changed | Run tests? |
|---------|-----------|
| `scripts/*.py` | Yes — add/update tests |
| `repodoctify/runtime.py`, `workspace.py`, `targeting.py` | Yes |
| `repodoctify/analysis.py`, `planning.py`, `prompting.py` | Yes |
| `repodoctify/manifest.py`, `models.py`, `utils.py` | Yes |
| `repodoctify/feishu/*.py`, `feishu_handoff.py` | Yes |
| Reference documents (`references/*.md`) | No |
| `README.md`, `CLAUDE.md`, `SKILL.md` | No |
| `tests/test_cli.py` | Removed — CLI no longer exists |

## Reference Documents

Located in `references/` (symlinked from `skills/repo-doctify/references/`):
- `repo-docset-framework.md` — seven-layer docset framework, code anchor chains, reading routes
- `docset-ir.md` — intermediate representation schema
- `markdown-rendering-rules.md` / `html-rendering-rules.md` — output rules
- `feishu-rendering-handoff.md` — Feishu publishing ownership boundaries
- `feishu-runtime-model.md` — Feishu execution modes
- `content-patterns.md` — source hierarchy, homepage/overview patterns
