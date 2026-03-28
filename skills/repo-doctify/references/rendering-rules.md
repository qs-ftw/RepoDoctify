# Rendering Rules

Shared rendering rules for all output formats (Markdown, HTML, Feishu).

## General Principles

| Principle | Rule |
|-----------|------|
| Core judgment | Diagrams lower the cost of understanding relationships and flows; tables lower the cost of comparison and lookup. |
| Selection priority | First determine whether the reader is stuck on "process relationships" or "information comparison", then decide which to use. |
| Quantity control | Do not chase quantity; one high-quality diagram is better than three loose ones; 1-2 diagrams per document is the normal range. |
| Accompanying requirement | Never place a diagram or table naked — follow it with 1-3 sentences of explanation that connect it to the source code or key concept. |

## When to Use Diagrams

Use Mermaid diagrams intentionally. Most technical learning docs should include 1-2 diagrams per document, not more.

Do not add a diagram just because a topic exists. Only add one when it genuinely clarifies a relationship or sequence that would otherwise require reading several paragraphs to reconstruct.

Place the diagram immediately after the heading that introduces the concept it illustrates, not at the end of the document.

When multiple diagram types could apply, pick the one that matches the **primary** purpose of that document — do not include all of them in a single document.

| Trigger | Diagram Type | Example |
|---------|-------------|---------|
| Homepage or study index: overview of all topics and reading routes | `mindmap` | homepage recommended reading path |
| Cross-module call chain, request/response, polling, callbacks, external collaboration | `sequenceDiagram` | API request → parse → generate → output full sequence |
| Data entity relationships, state transitions, config-to-output mapping | `erDiagram` | config fields → intermediate variables → output artifacts |
| Module or class responsibility boundaries and collaboration | `classDiagram` | module-map showing package duties and dependencies |
| One clear multi-stage process chain (init, build, config, shutdown) | `flowchart` | code-reading-path main chain wiring |
| Time windows, phase scheduling, or timeout mechanisms are the explicit focus | `gantt` | polling windows, async phase timelines |
| Stable proportional relationships that genuinely aid understanding | `pie` | resource composition, issue distribution (not a default) |

### Diagram Naming and Accompanying Text

- Keep node labels short; prefer names the reader can immediately understand. Keep code keywords only when necessary.
- Each diagram should tell one primary story.
- **After every diagram**, add a "takeaway" or "reading hint" that helps the reader connect the diagram back to source code.
- Diagrams do not replace code — they tell the reader where to start reading code.
- Prefer pairing a diagram with 1-2 source anchor references immediately after it.
- If the main difficulty is a noun list, tech stack index, or field mapping, a diagram would make it more confusing — use a table or list instead.

### Flowchart Orientation

`flowchart LR` (left-to-right) renders nodes side by side. If the chain has 5 or more steps (A → B → C → D → E → F), nodes become visually cramped and hard to read. When a flowchart chain is long, prefer `flowchart TD` (top-down) so nodes stack vertically and breathe.

Rule of thumb: if the chain would not fit comfortably on a phone screen in landscape, switch to TD.

## When to Use Tables

| Trigger | Table Type | Example |
|---------|-----------|---------|
| Multiple objects that all answer the same set of questions | structured table | tech stack, glossary, role mapping |
| Fast lookup of concepts, mechanisms, or entry points | reference table | mechanism index, file anchors |
| Navigation index across many documents with long titles | index table | document directory, reading guide |
| Fields, configurations, or attributes that belong together | attribute table | config fields, API parameters |

### Table Design Rules

- One table serves one question — do not mix "purpose, flow, conclusion, code, and risks" into the same table.
- Keep columns to 3-4; wider tables reduce readability.
- Cell content should be short and scannable.
- Do not put large code blocks inside tables — place code as a separate snippet after the table.
- If a table's rendered form is unstable in the target format, prefer "heading + fixed-field sections" (structured sections) over a loose nested list.
- Link to official docs and downstream entries directly from table cells when applicable.

## Quick Decision Table

| If what you need to express is… | Prefer |
|--------------------------------|--------|
| A request flowing through multiple systems | `sequenceDiagram` |
| A system internally advancing through stages | `flowchart` |
| Entities or objects binding to each other | `erDiagram` |
| Class and service responsibility boundaries | `classDiagram` |
| Homepage reading tree and knowledge hierarchy | `mindmap` |
| Role or purpose comparison of multiple technical items | table |
| Mechanism reference cards (short, indexed) | table or structured sections |
| Document entry points and navigation index | table or linked sections |

## Feishu-Specific Notes

Diagrams and tables in Feishu should prefer rendered form (not code blocks) where the platform supports it. When updating existing user-owned docs, prefer in-place updates to creating new version-overwriting doc instances.
