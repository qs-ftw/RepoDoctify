# Markdown Rendering Rules

Markdown is the primary v1 renderer.

## Default Output

The default no-argument path must produce:

- split Markdown docs
- `README.md`
- `manifest.json`

These outputs must be derived from the shared IR.

## README Rules

The README aggregate should:

- identify the repository
- list generated documents
- link to split Markdown docs
- act as the local overview entrypoint

The README must not be an empty placeholder.

## Document Rules

Use:

- `#` for the document title
- `##` for section titles
- numbered lists for ordered reading paths
- tables only when horizontal comparison is the point

## Code and Diagram Rules

- code anchors use fenced code blocks
- Mermaid blocks remain fenced as `mermaid`
- callouts and summaries can degrade to blockquotes

