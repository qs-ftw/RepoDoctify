# Content Patterns

Use these patterns when RepoDoctify turns a code repository into a learning
docset.

## Source Hierarchy

Prefer sources in this order unless the user gives a stronger instruction:

1. source code and first-party implementation artifacts
2. current repository docs such as `README.md` and `docs/`
3. tests and executable evidence
4. older or secondary background materials

If sources disagree, keep the higher-priority source as truth and label the
lower-priority one as context only.

## Homepage Pattern

The homepage should answer:

- what this repository does (one to two sentences, the canonical definition)
- what is included in the docset
- how to read it (reading routes by reader goal)
- which reading route fits which goal

Keep it navigation-first. Avoid long theory before the reader can see where to
go next.

## Overview Pattern

The overview should answer:

- what kind of repository this is
- what language and tooling signals matter
- what the main source surfaces are
- how the repo should be read at a high level

Note: overview content is now merged into homepage's "仓库做什么" section. The homepage document is the canonical location for the one-sentence repository definition and boundary statement.

## Code Reading Pattern

When generating a “先看哪些文件” style section:

- prefer numbered lists over tables
- use real repo-relative paths
- prefer files over directories when concrete file anchors are available
- order the list from human-facing contract to main source to tests to config

## Evidence Pattern

When explaining confidence:

- say whether README, tests, docs, and config are strong, medium, or weak
- point to the specific files that provide the evidence
- prefer tests over comments when they disagree

## Tech Stack Pattern

Do not leave tech stack sections as raw nouns.

For each important signal, explain:

1. the technology or signal
2. why it matters in this repository
3. which file exposed that signal

## Bridge Topic Pattern

Generate bridge topics only when they are likely to block first-time reading.

Good candidates:

- workspace boundaries
- packaging or runtime entrypoints
- config propagation
- tests as authority
- docs-source mismatch

### Validity Markers

When older materials conflict with current source of truth, label the gap explicitly near the relevant claim rather than in a disclaimer at the end:

| Marker | Meaning | When to use |
|--------|---------|-------------|
| `已被源码验证` | Conclusion confirmed by source code or first-party evidence | Primary conclusions |
| `部分吻合，需注意差异` | Older material overlaps but details differ | Supplementary older materials |
| `疑似过期，仅供背景参考` | May no longer be accurate | Resource library, historical wiki |

## Main Chain Document Template

Answer these questions:

1. Which chain does this doc explain
2. Which files to read first (ordered: contract → main source → tests → config)
3. One primary diagram (flowchart for process chains, sequenceDiagram for call chains)
4. The chain explained stage by stage
5. 1-2 source anchors with 1-4 sentences of explanation each
6. Where the chain most often breaks
7. What to read next

## Source Anchor Rules

Add source snippets when abstract description is insufficient. Good candidates:

- startup and initialization
- routing registration
- call chain or generation chain handoffs
- state writeback
- timeout, retry, rollback
- trace propagation
- permission boundaries

Source anchor rules:

| Aspect | Rule |
|--------|------|
| Length | Short — reader can scan in 1 minute |
| Purpose | Explain one mechanism, not dump a file |
| Accompanying text | 1-4 sentences after the snippet |
| Value | Point to "why this matters" and "where to continue reading" |

Never leave a source anchor naked. Always pair it with a sentence that tells the reader where to look next.

## Inter-Document Linking

When a document references another learning doc in this docset — especially navigation sentences like "next read X", "return to overview", or "see also Y" — make the title a live hyperlink. Do not leave navigation links as plain text.

Apply this to homepage reading routes, bridge doc return paths, and "next to read" recommendations.

## Public Repository URLs

In user-visible learning docs, prefer public git repository URLs over local absolute paths.

Use:

- the public git URL
- quick entry points
- Git links

Do not surface `/root/...` or other local absolute paths as primary entry points.

## Tech Stack Table Format

Prefer a structured table over prose lists for tech stack sections:

| Technology | Role in this repo | Key file | Official docs |
|------------|-------------------|---------|---------------|
| FastAPI | HTTP API surface | `api.py` | [link] |

Rules:
- One row per significant dependency (runtime, database, message queue, observability, AI orchestration)
- Do not list every transitive dependency
- Link to official docs, not random blog posts
- Avoid repeating upstream marketing copy

## Document Question Lens

Every document answers exactly one question. Use the question as your **scope lens**:
if content does not answer the document's question, it belongs in another doc — cross-link it.

| Document | Question (lens) | In scope | Out of scope |
|---|---|---|---|
| homepage | "What does this repo do and where do I start?" | Repo purpose & boundaries, doc index, reading routes | Call chain details, entry assembly, module internals |
| code-reading-path | "How does the chain flow from entry to output?" | Call order, data handoffs, where chain branches | Module isolation responsibilities, entry assembly |
| stack-and-entrypoints | "How do I invoke it and what does it depend on?" | API/CLI/assembly entry, runtime constraints, tech stack | Chain flow, module responsibilities |
| module-map | "What does each module own in isolation?" | Module isolation responsibilities, collaboration interface | Chain flow, entry assembly |
| development-guide | "How do I safely make a targeted change?" | Change path by file type, risk zones, local verification | Module internals, call chains |
| bridge-topics | "Which mechanisms confuse newcomers?" | Cross-module mechanisms, registration vs. call site | Module internals, call chains |
| evidence-guide | "What evidence should I trust?" | Evidence types, boundary inference, doc/code gaps | Chain flow, module internals |

## Overlap Review Pattern

After generating all documents, run a self-check before declaring completion.

**Review scope**: Adjacent document pairs — not every pair, only those likely to share content:

- homepage ↔ code-reading-path
- code-reading-path ↔ module-map
- stack-and-entrypoints ↔ code-reading-path

**Check method**: For each paragraph, ask: "Does this paragraph primarily answer its own document's question, or does it answer a different document's question?"

**Fix strategy** (in priority order):

1. **Cut and link**: Remove the duplicate from the non-owner doc; add a cross-link to the owning doc instead.
2. **Rewrite to a sub-question**: Reframe the paragraph to answer a question unique to its own document.
3. **Narrow the framing**: If the content is genuinely relevant to both docs, narrow each occurrence so they address different aspects.

**Never**: copy the same paragraph into both docs to "ensure consistency" — that creates duplication, not consistency.

## Document Templates

### Homepage Template

Required sections (answer the question "What does this repo do and where do I start?"):

1. **仓库做什么** — One to two sentences on the repo's core responsibility and scope. This is the canonical definition for the whole docset.
2. **文档索引** — Table of all docs in this docset with the question each answers; use relative links.
3. **推荐阅读路线** — Named by reader goal (e.g., "want a quick mental model" / "preparing to maintain"), not by copying other docs' file lists.

### Code Reading Path Template

Required sections (answer the question "How does the chain flow from entry to output?"):

1. **主链概览** — One high-level chain view; use a flowchart, not a module-responsibility table.
2. **主链细节** — Call order and data handoffs along the chain; use call-chain lens, not module-lens.
3. **测试链路** — How backward correctness is verified.
4. **优先入口文件** — Ordered file list; this and homepage's reading route are different levels of information.

### Module Map Template

Required sections (answer the question "What does each module own in isolation and how do they collaborate?"):

1. **模块总览** — Directory tree and package layout.
2. **模块职责表** — Each module in isolation: input, output, purpose; this is the canonical table — code-reading-path must link here, not copy.
3. **协作接口** — How modules call each other; describe collaboration patterns, not internal implementation.

### Bridge Topics Template

Required sections (answer the question "Which cross-module mechanisms confuse newcomers?"):

1. **桥接机制清单** — List cross-module mechanisms only if they are genuinely likely to confuse; do not force a bridge chapter.
2. **误解高发点** — Where misunderstandings are most likely to occur.
3. **调试入口** — Where to look when things go wrong.

### Evidence Guide Template

Required sections (answer the question "What evidence should I trust?"):

1. **证据来源清单** — Test files, benchmarks, assertions, logs.
2. **边界推断方法** — How to infer behavior from evidence.
3. **文档偏差处理** — What to do when docs disagree with code.


