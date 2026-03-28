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

- what is included
- why the docset exists
- how to read it
- which reading route fits which goal

Keep it navigation-first. Avoid long theory before the reader can see where to
go next.

## Overview Pattern

The overview should answer:

- what kind of repository this is
- what language and tooling signals matter
- what the main source surfaces are
- how the repo should be read at a high level

Avoid generic “this project does X” filler if the repo structure can say
something more concrete.

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

## Overview Document Template

Answer these questions:

1. What the repository solves and its boundaries
2. Its primary responsibilities
3. How a newcomer should read it
4. What each main module owns
5. What each key technology does in this repo (use the Tech Stack Pattern, not bare nouns)
6. One high-value diagram
7. Common misconceptions
8. What to read next

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
