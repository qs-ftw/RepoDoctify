# Feishu Rendering Handoff

`RepoDoctify` owns Feishu publishing logic directly.

## Ownership Boundary

`RepoDoctify` owns:

- repository methodology
- shared IR semantics
- renderer-neutral document meaning
- Feishu publish planning
- Feishu document structure details
- block mapping strategy
- table, Mermaid, and board specifics
- publication flow
- readback verification

## Dependency Rule

Feishu output depends on external `lark-mcp`.

If `lark-mcp` is not available, `RepoDoctify` should stop and tell the user to
install it before trying Feishu output again.

## Publish Plan

The Feishu publish path should provide at least:

- repository label
- manifest path
- document count
- document titles
- document publish modes
- verification checks
