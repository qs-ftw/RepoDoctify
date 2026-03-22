# Repository Docset Framework

Use this reference when the task is to convert a source repository into a
reusable study docset instead of a one-off summary.

## Core Principle

Organize the docset by reader obstacles, not by directory structure.

Good repository docsets answer, in order:

1. what this repository is for
2. what the main chain is
3. which hidden mechanisms block first-time reading
4. what each critical module owns
5. where the real boundaries are
6. how to safely change it

## Seven Layers

Use this as the default skeleton:

1. homepage or index
2. overview
3. main-chain doc
4. bridge docs
5. module deep dives
6. boundary and evidence guide
7. development and maintenance guide

The layers are responsibilities, not mandatory file counts.

## Default Docset Sizes

- small repos: 5-7 docs
- medium repos: 8-12 docs
- large repos: 12-16 docs

Collapse layers when the repository is small or repetitive.

When RepoDoctify is operating in “multi-repo first usable” mode, it should not
emit the exact same document list for every repo. The framework remains stable,
but the concrete doc count should adapt to repository complexity.

## Bridge-Doc Selection

Write bridge docs for concepts that are:

- cross-cutting
- easy to misunderstand
- more conceptual than module-local
- likely to recur across multiple files

Typical bridge topics include:

- dependency expansion
- closure or config propagation
- validation and lowering
- cache or writeback behavior
- permission and auth propagation

## Module-Doc Split Rules

Split a dedicated module deep dive when:

- the module owns a stable contract
- the module translates between layers
- failures localize there often
- adjacent changes are unsafe without understanding it

## Default Reading Routes

Every repository docset should support:

- 30-minute orientation
- first-day maintenance onboarding
- module deep-dive route
- feature-development route
