# Docset IR

`RepoDoctify` uses a renderer-neutral intermediate representation called
`Docset IR`.

## Goals

The IR exists so Markdown, HTML, and Feishu outputs can share the same
repository knowledge content.

The IR should capture:

- repository profile
- code-anchor chains
- document structure
- section structure
- renderer-neutral links
- README aggregation relationships

## Dataclasses

### `RepositoryProfile`

Stores repository-wide metadata:

- `repo_label`
- `source_path`
- `public_locator`
- `primary_audience`
- `source_authority_notes`

### `CodeAnchorChain`

Stores one structured reading or change path:

- `label`
- `chain_kind`
- `entry_anchor`
- `implementation_anchor`
- `test_anchor`
- `config_anchor`
- `contract_anchor`

### `DocsetPlan`

Stores docset-wide planning semantics:

- document list
- document titles
- document roles
- reading routes
- README aggregation strategy

### `DocumentSpec`

Stores one document's identity and purpose:

- `doc_id`
- `title`
- `role`
- `question_answered`
- `target_reader`
- `sections`
- `next_reads`

### `SectionNode`

Stores one renderer-neutral content block:

- `kind`
- `title`
- `body`
- `metadata`

Supported v1 kinds include:

- `paragraph`
- `numbered_list`
- `comparison_table`
- `code_anchor`
- `mermaid`
- `callout`
- `summary`

### `CrossLinkMap`

Stores renderer-neutral cross-document links:

- homepage links
- next-read links
- reading-route links
- aggregate README links

## README Aggregation

README aggregation is not a separate content source. It is a view derived from
the same IR used by the other renderers.

## Current Runtime Serialization

The current runtime writes a single `docset-ir.json` file containing:

- `repository_profile`
- `docset_plan`
- `documents`

The runtime-facing request/response boundary also keeps repo-resolution
semantics explicit:

- request object carries current repo context, requested repo, and execution mode
- run result carries resolved repo path and resolution reason

That file is renderer-neutral and is meant to be reusable across Markdown,
HTML, and Feishu output paths.
