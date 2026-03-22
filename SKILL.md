---
name: repo-doctify
description: Use when the user wants to turn a source repository into a structured learning docset with Markdown, HTML, or Feishu outputs, or wants to plan the repository documentation framework first.
---

# RepoDoctify

## Overview

`RepoDoctify` is the top-level product skill for repository knowledge synthesis.

It turns a repository into a structured learning docset for first-time readers,
maintainers, and feature developers, while keeping generated artifacts outside
the analyzed repository by default.

In Codex, the primary way to use this product is as a skill:

- manually trigger it with `$repo-doctify`
- or let Codex dispatch it automatically when the task matches

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

## Explicit Subcommands

- `规划输出框架`
  - produce the docset structure only
- `以 md 形式输出全部内容`
  - render the complete Markdown docset
- `以 html 形式输出全部内容`
  - render the complete HTML docset
- `以飞书形式输出全部内容`
  - publish or update the complete Feishu docset

All output modes should share the same intermediate result.

The bundled Python package and CLI are implementation helpers for the skill
repository itself. They are useful for local verification and internal tooling,
but they are not the primary user-facing invocation path.

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

## Reference Set

Load these references as needed:

- `references/repo-docset-framework.md`
- `references/docset-ir.md`
- `references/markdown-rendering-rules.md`
- `references/html-rendering-rules.md`
- `references/feishu-rendering-handoff.md`

## Ownership Boundary

`RepoDoctify` owns:

- repository-docset methodology
- shared IR semantics
- Markdown and HTML rendering rules
- README aggregation rules
- Feishu handoff rules

`feishu-knowledge-ops` remains the Feishu-specific backend and publication
specialist. `RepoDoctify` should not duplicate Feishu block or publishing logic.
