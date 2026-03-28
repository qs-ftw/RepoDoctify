---
name: repo-doctify
description: Use when the user wants a source repository turned into a structured learning docset with Markdown, HTML, or Feishu outputs, or wants the docset plan first.
---

# RepoDoctify

## Overview

`RepoDoctify` is the top-level product skill for repository knowledge synthesis.

It turns a repository into a structured learning docset for first-time readers,
maintainers, and feature developers, while keeping generated artifacts outside
the analyzed repository by default.

Current strong support is Python and TS/JS. Current structured support is Go,
Rust, and Java. Other repository types should be handled conservatively rather
than treated as deeply understood.

In Codex, the primary way to use this product is as a skill:

- manually trigger it with `$repo-doctify`
- or let Codex dispatch it automatically when the task matches

The recommended explicit invocations are:

- `$repo-doctify plan`
- `$repo-doctify md`
- `$repo-doctify html`
- `$repo-doctify feishu`

## Execution Workflow

When this skill is triggered, use the bundled runtime script to prepare the
analysis, plan, manifest, and prompt bundle first. Then use those files to
author the actual doc content yourself.

Do not invoke `brainstorming` for normal RepoDoctify runs. Repository docset
generation is an execution task against an explicit prompt bundle, not an
open-ended product-design exercise.

Operational rules:

- The system Python (3.9) does not support RepoDoctify's `slots=True` dataclasses.
  Use `uv` to create a temporary Python 3.14 venv inside the skill directory, then
  run the runtime from it:
  ```
  REPO=$(pwd) && cd ~/.codex/skills/repo-doctify && uv venv .venv --python 3.14 && uv run --no-project --python .venv/bin/python - << 'EOF'
  import sys; sys.path.insert(0, '.')
  from repodoctify.runtime import run_repodoctify, COMMAND_RENDER_MD
  from pathlib import Path
  result = run_repodoctify(Path('$REPO'), command=COMMAND_RENDER_MD)
  print(result.workspace)
  EOF
  ```
  Replace `$REPO` with the absolute path to the target repository. Use
  `COMMAND_PLAN` for plan-only mode.
- Prefer reusing the generated workspace for follow-up authoring instead of
  re-reading the repository.
- After the runtime finishes, inspect:
  - `ir/repository-analysis.json`
  - `plan/docset-plan.json`
  - `artifacts/manifest.json`
  - `prompt/packet.json`
  - `prompt/authoring-brief.md`
  - `prompt/write-targets.json`
  - `prompt/document-prompts.json`
  - `prompt/<mode>-output-contract.json`
- Treat `prompt/packet.json` as the source of truth for reading budget and
  priority paths.
- The Python runtime must not author document prose, explanations, summaries,
  or section bodies for the final docset.
- The final Markdown / HTML / Feishu content must be authored by the model from
  repository evidence, plan, and references.
- Once the evidence is sufficient, stop exploring and start writing the output.
- Write files one at a time in the order described by `prompt/write-targets.json`.
- Use `prompt/document-prompts.json` as the single current document task list.
- After each file write, verify the file exists before moving to the next one.
- Do not glob-read every source file. Follow the reading budget first.
- For Markdown mode, you must complete all targets in a single run.
- Do not stop after writing only homepage.

Only ask follow-up questions when the target repository or critical context is
actually unclear. Keep the default behavior low-interruption.

## Default Behavior

If the user triggers `RepoDoctify` without an explicit subcommand, run the
default full local path:

1. plan the output framework
2. generate the shared intermediate result
3. render the complete Markdown docset

This default output should include:

- split Markdown docs
- a README-style aggregate overview
- a manifest

Only ask 1-3 short questions when one of these is missing:

- which repository to analyze
- whether the user's requested repo conflicts with the current working context
- a critical reading goal that would materially change the output

Prefer the current working directory as the target repository when it already
looks like a real repo and the user did not specify another path. If the user
did specify a different repo, prefer the explicit path and only escalate when a
strict conflict check is materially useful.

## Explicit Subcommands

Preferred short commands:

- `plan`
  - produce the docset structure only
- `md`
  - render the complete Markdown docset
- `html`
  - render the complete HTML docset
- `feishu`
  - publish or update the complete Feishu docset

Legacy natural-language aliases are still valid and should be treated as
equivalent:

- `规划输出框架` -> `plan`
- `以 md 形式输出全部内容` -> `md`
- `以 html 形式输出全部内容` -> `html`
- `以飞书形式输出全部内容` -> `feishu`

All output modes should share the same intermediate analysis and plan. The
runtime prepares the prompt bundle; the model generates the final content.

The bundled Python package is an implementation helper for the skill repository itself.
It is useful for local verification and internal tooling, but it is not the primary
user-facing invocation path.

## Authoring Discipline

After runtime preparation, do not stay in open-ended exploration mode.

Follow this sequence:

1. read `prompt/authoring-brief.md`
2. read `prompt/write-targets.json`
3. read `prompt/document-prompts.json`
4. read `prompt/<mode>-output-contract.json`
5. sample only the highest-priority missing evidence, not the whole repo
6. pick one single current document task
7. write that file
8. verify the file exists
9. move to the next document task

This is a one-shot generation flow. Do not treat `homepage.md` as a checkpoint
where you can stop. Continue until every Markdown target declared by
`prompt/write-targets.json` exists.

For Markdown mode, prefer a single multi-file `apply_patch` that creates every
missing Markdown document plus `README.md` in one pass, then run the bulk file
existence check declared in `prompt/write-targets.json`. This reduces the risk
of stopping after the first document.

Do not keep exploring once the evidence is sufficient. The common failure mode
here is spending too long planning a multi-file write and never actually
creating the files.

Treat the runtime's repo resolution rules as the source of truth for skill
execution:

- prefer the current working directory when it already looks like a real repo
- prefer the explicit repo when the user clearly provided one
- allow strict conflict checks to stop early when the current repo context and
  requested repo disagree
- keep the skill-facing runtime request model as the internal orchestration
  boundary instead of growing new public CLI semantics

## Output Isolation Rule

By default, `RepoDoctify` must treat the target repository as read-only input.

Do not write plans, IR caches, Markdown outputs, HTML outputs, publish records,
or temporary render artifacts into the current repository unless the user
explicitly asks for that behavior.

Default outputs belong in a repository-external isolated workspace.

If the user explicitly wants to reuse an existing external workspace, prefer a
safe resume path instead of recomputing plan and IR unnecessarily.

## Dependency Rules

Markdown and HTML paths should not depend on Feishu tooling.

Feishu output depends on an external `lark-mcp` installation. If the user asks
for Feishu output and `lark-mcp` is unavailable, stop and tell the user to
install `lark-mcp` first.

RepoDoctify itself owns the Feishu publication strategy, update rules, and
verification flow. Treat `lark-mcp` as the connectivity dependency, not as the
place where product behavior lives.

## Reference Set

Load these references as needed:

- `references/repo-docset-framework.md`
- `references/docset-ir.md`
- `references/markdown-rendering-rules.md`
- `references/html-rendering-rules.md`
- `references/rendering-rules.md`
- `references/feishu-rendering-handoff.md`
- `references/feishu-runtime-model.md`

## Ownership Boundary

`RepoDoctify` owns:

- repository-docset methodology
- shared IR semantics
- Markdown and HTML authoring rules
- README aggregation rules
- Feishu publishing rules
- Feishu update and verification strategy
- Feishu runtime models for plan-only, dry-run, and execute semantics
- Feishu target-document planning for request-specified existing docs
- Feishu helper scripts that make the skill portable
- prompt-bundle design for model-authored outputs
