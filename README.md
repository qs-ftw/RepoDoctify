# RepoDoctify

`RepoDoctify` is a portable repository-docset skill source. Its job is to turn
an unfamiliar code repository into a structured learning docset.

The repository currently contains:

- the product design spec
- the v1 implementation plan
- the canonical portable skill source at `skills/repo-doctify/`
- reference documents for repository methodology and rendering rules
- a small Python helper package for workspace isolation, repo analysis, docset planning, prompt-bundle preparation, and Feishu handoff

## Primary Usage

The primary user-facing entrypoint is the Codex skill itself:

- enter Codex CLI and trigger `$repo-doctify`
- use `$repo-doctify plan|md|html|feishu` for explicit output modes
- or let Codex dispatch `repo-doctify` automatically when the task matches

The Python package in this repo exists to support the skill's internal runtime,
testing, and local verification. It is not allowed to synthesize final document
prose as if it were the skill itself.

## Release Focus

The current release target is:

- Python + TS/JS repositories first
- Go, Rust, and Java repositories with structured but more conservative support
- Markdown as the default primary deliverable
- low-interruption skill behavior

This repo is not a good fit yet for:

- Feishu-first publishing workflows
- languages outside Python, TS/JS, Go, Rust, and Java when repo structure is unusual
- deep semantic analysis such as full call graphs or AST-level reasoning

## Intended Default Behavior

With no explicit subcommand, `RepoDoctify` should behave as:

1. plan the docset structure
2. generate shared intermediate results
3. prepare the Markdown authoring prompt bundle
4. let the model generate the final Markdown docset from that bundle

The default path should also generate:

- a README-style aggregate overview
- a manifest

All generated artifacts should live outside the analyzed repository by default.

## Install And Use

Run tests with:

```bash
pytest -v
```

For local platform installs, use:

```bash
python3 scripts/install_local_skill.py --platform claude  # default
python3 scripts/install_local_skill.py --platform codex
python3 scripts/install_local_skill.py --platform trae
```

This installs from the canonical skill source at `skills/repo-doctify/`.

Restart your assistant after installation so it reloads the skill registry.

Recommended skill entrypoints on every platform:

```bash
$repo-doctify
$repo-doctify plan
$repo-doctify md
$repo-doctify html
$repo-doctify feishu
```

For Codex remote installation, the intended low-parameter path is:

```text
$skill-installer install https://github.com/qs-ftw/RepoDoctify/tree/main/skills/repo-doctify
```

For Claude Code distribution, build the release bundles and use the generated
directory or zip package under `dist/release/claude/`.

For Trae distribution, build the release bundles and use either:

- `dist/release/trae/skills/repo-doctify/`
- `dist/release/trae/rules/repo-doctify.md`

## Examples

This repository includes lightweight example repos under `examples/`:

- `examples/python-basic`
- `examples/typescript-basic`
- `examples/go-basic`
- `examples/rust-basic`

Use them to smoke-test installation and output quality without guessing which
repo shape the current release is designed to support first.

Current support quality is:

- strong support: Python, TypeScript, JavaScript
- structured support: Go, Rust, Java
- fallback support: generic repositories with conservative reading guidance

Build all release bundles with:

```bash
python3 scripts/build_release_bundles.py
```

## Output Targets

`RepoDoctify` is designed to support:

- Markdown
- HTML
- Feishu

Feishu output is optional and depends on an external `lark-mcp` installation.

If `lark-mcp` is unavailable, the runtime raises a clear dependency error instead
of blocking Markdown or HTML prompt-bundle preparation.

RepoDoctify owns the Feishu publication plan, update strategy, verification
rules, and bundled helper scripts. `lark-mcp` remains an external dependency
for connectivity only.

The Feishu runtime now distinguishes:

- `plan_only` for publish planning
- `dry_run` for execution-ready validation without remote writes
- `execute` for the future remote-write path

The Feishu request model also supports explicit existing-document targeting
through `feishu_target_doc_ids`, so a caller can tell RepoDoctify which logical
doc should update which existing Feishu document instead of relying only on
title- or role-based defaults.
