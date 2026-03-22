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
