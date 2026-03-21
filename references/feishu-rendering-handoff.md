# Feishu Rendering Handoff

`RepoDoctify` does not implement Feishu-specific publication logic directly.

## Ownership Boundary

`RepoDoctify` owns:

- repository methodology
- shared IR semantics
- renderer-neutral document meaning
- Feishu handoff contract

`feishu-knowledge-ops` owns:

- Feishu document structure details
- block mapping
- table and chart specifics
- publication flow
- readback verification

## Dependency Rule

Feishu output depends on external `lark-mcp`.

If `lark-mcp` is not available, `RepoDoctify` should stop and tell the user to
install it before trying Feishu output again.

## Handoff Payload

The Feishu handoff should provide at least:

- repository label
- manifest path
- document count
- document titles
- the fact that publication is delegated to `feishu-knowledge-ops`

