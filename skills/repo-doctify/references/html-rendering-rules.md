# HTML Rendering Rules

HTML rendering should preserve the same document structure as Markdown while
optimizing for browser reading.

## Required v1 Behavior

- emit an `index.html`
- emit one page per document
- include basic navigation
- render code blocks safely
- render tables and Mermaid blocks in readable fallback form

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

