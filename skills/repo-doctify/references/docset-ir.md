# Docset IR

`RepoDoctify` uses a prompt-friendly intermediate representation centered on
repository analysis, docset planning, and output contracts.

## Goals

The intermediate layer exists so Markdown, HTML, and Feishu generation can
share the same repository evidence, planning decisions, and output contracts.

The intermediate layer should capture:

- repository profile
- code-anchor chains
- document inventory
- document roles and titles
- reading routes
- output contracts
- manifest relationships

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

### Prompt Bundle

Stores the model-facing authoring contract:

- mode
- required input file paths
- reference documents to load
- expected outputs
- authoring rules
- non-goals
- manifest snapshot

## Current Runtime Serialization

The current runtime writes:

- `ir/repository-analysis.json`
- `plan/docset-plan.json`
- `artifacts/manifest.json`
- `prompt/packet.json`
- `prompt/<mode>-output-contract.json`
- `prompt/authoring-brief.md`

The runtime-facing request/response boundary also keeps repo-resolution
semantics explicit:

- request object carries current repo context, requested repo, and execution mode
- run result carries resolved repo path and resolution reason

These files are reusable across Markdown, HTML, and Feishu generation paths.
The final prose is authored by the model, not synthesized by Python helpers.
