# HTML Rendering Rules

HTML rendering should preserve the same document structure as Markdown while
optimizing for browser reading.

## Required v1 Behavior

- emit an `index.html`
- emit one page per document
- include basic navigation
- render code blocks safely
- render tables and Mermaid blocks in readable fallback form

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

## Index Page

The index page should:

- show the repository label
- list the generated documents
- link to each document page

## Document Pages

Each page should include:

- a page title
- a link back to the index
- section content in reading order

## v1 Priority

Readable and stable is more important than theme complexity.

