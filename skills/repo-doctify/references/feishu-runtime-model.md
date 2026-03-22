# Feishu Runtime Model

Use this reference when changing RepoDoctify's Feishu runtime behavior rather
than only its publication guidance.

## Core Runtime Layers

RepoDoctify's Feishu path is split into:

1. request and command selection
2. target-document selection
3. auth-state probing
4. publish-plan generation
5. verification-plan generation
6. optional execute-time adapters

Keep these layers explicit instead of merging everything into one publisher
script.

## Execution Modes

Current execution modes are:

- `plan_only`
- `dry_run`
- `execute`

Use them as runtime semantics, not just as CLI wording.

## Key Structured Models

- `FeishuPublishMode`
- `FeishuPublishTarget`
- `FeishuVerificationCheck`
- `FeishuVerificationPlan`
- `FeishuAuthState`

`RepoDoctifyRequest` may also carry `feishu_target_doc_ids`, a mapping from
logical doc ids such as `homepage` or `overview` to existing Feishu document ids.
When present, the publish plan should surface:

- `target_document_id`
- `target_source`
- `target_lookup_key`

This keeps request-driven existing-doc updates explicit instead of hiding them
behind title matching or ad-hoc script arguments.

The runtime may serialize these into JSON outputs, but internal code should use
typed models first and dicts second.

## Decision Principles

- prefer `localized_patch` for small in-place updates and section-local diagram edits
- prefer `full_rewrite` for table-heavy or structure-heavy changes
- update homepage or index docs last after child docs are stable
- prefer explicit request-provided target doc ids over implicit lookup when updating known existing docs
- keep auth blockers explicit and machine-readable
- keep verification checks structured so later execute-time readback can reuse them
