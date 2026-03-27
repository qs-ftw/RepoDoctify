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
- real repo-relative file paths when naming code anchors or reading order

Prefer numbered lists over tables for “先看哪些文件” style sections unless the
content is genuinely comparative.

## Code and Diagram Rules

- code anchors use fenced code blocks
- Mermaid blocks remain fenced as `mermaid`
- callouts and summaries can degrade to blockquotes

### When to Use Diagrams

Use Mermaid diagrams intentionally. Most technical learning docs should include 1-2 diagrams per document, not more.

Choose diagram type by purpose:

- homepage or study index: `mindmap`
- request, trace, polling, callback, cross-repo flow: `sequenceDiagram`
- main data or state relationships: `erDiagram`
- service or class responsibility map: `classDiagram`
- one clear local stage chain (e.g. build, init, shutdown, config flow): `flowchart`

Do not add a diagram just because a topic exists. Only add one when it genuinely clarifies a relationship or sequence that would otherwise require reading several paragraphs to reconstruct.

When a diagram would help, place it immediately after the heading that introduces the concept it illustrates, not at the end of the document.
