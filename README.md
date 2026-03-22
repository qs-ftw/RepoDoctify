# RepoDoctify

`RepoDoctify` is a Codex skill repository. Its job is to turn an unfamiliar code
repository into a structured learning docset.

The repository currently contains:

- the product design spec
- the v1 implementation plan
- the top-level skill contract
- reference documents for repository methodology and rendering rules
- a small Python helper package for shared IR, workspace isolation, repo analysis, planning, composition, and renderers

## Primary Usage

The primary user-facing entrypoint is the Codex skill itself:

- enter Codex CLI and trigger `$repo-doctify`
- or let Codex dispatch `repo-doctify` automatically when the task matches

The Python package in this repo exists to support the skill's internal runtime,
testing, and local verification. It is not the main user contract.

## Release Focus

The current release target is:

- Python + TS/JS repositories first
- Markdown as the default primary deliverable
- low-interruption skill behavior

This repo is not a good fit yet for:

- Feishu-first publishing workflows
- languages outside Python and TS/JS when repo structure is unusual
- deep semantic analysis such as full call graphs or AST-level reasoning

## Intended Default Behavior

With no explicit subcommand, `RepoDoctify` should behave as:

1. plan the docset structure
2. generate shared intermediate results
3. render the full Markdown docset

The default path should also generate:

- a README-style aggregate overview
- a manifest

All generated artifacts should live outside the analyzed repository by default.

## Runtime Surface

The current v1 helper flow is:

1. analyze the target repository
2. build a default docset plan
3. compose a shared IR
4. render Markdown or HTML, or execute RepoDoctify's Feishu publishing path

The main Python compatibility entrypoint is `repodoctify.run_repodoctify(...)`.
The skill-facing runtime entrypoint is `repodoctify.run_repodoctify_request(...)`.

The bundled CLI entrypoints are:

- `python -m repodoctify`
- `repodoctify`

It always writes into an external workspace with these subdirectories:

- `plan/`
- `ir/`
- `md/`
- `html/`
- `publish/`
- `logs/`

The internal harness supports:

- default no-arg behavior -> full Markdown docset
- `plan` -> docset structure only
- `md` -> full Markdown output
- `html` -> full HTML output
- `feishu` -> Feishu handoff

The runtime and harness also support `--reuse-latest` so a later render step can
reuse an existing external workspace and shared IR instead of recomputing from
scratch.

Target repository selection stays low-interruption by default:

- if `--repo` is omitted, the current working directory is treated as the target
- if an explicit repo path is passed, that path wins
- the shared runtime also supports a strict conflict check so skill orchestration can stop early when the requested repo conflicts with the current repo context
- runtime results also record the resolved repo path and the resolution reason so skill orchestration can inspect what happened

## Local Development

Run tests with:

```bash
pytest -v
```

Install the local skill copy with:

```bash
python3 scripts/install_local_skill.py
```

Use the installed skill from Codex CLI with:

```bash
$repo-doctify
```

## Examples

This repository includes lightweight example repos under `examples/`:

- `examples/python-basic`
- `examples/typescript-basic`

Use them to smoke-test installation and output quality without guessing which
repo shape the current release is designed to support first.

The bundled CLI remains useful as an internal developer harness when testing the repo
outside Codex:

```bash
python -m repodoctify --repo /path/to/repo
python -m repodoctify html --repo /path/to/repo --reuse-latest
```

## Output Targets

`RepoDoctify` is designed to support:

- Markdown
- HTML
- Feishu

Feishu output is optional and depends on an external `lark-mcp` installation.

If `lark-mcp` is unavailable, the runtime raises a clear dependency error instead
of blocking Markdown or HTML output.

RepoDoctify owns the Feishu publication plan, update strategy, verification
rules, and bundled helper scripts. `lark-mcp` remains an external dependency
for connectivity only.
