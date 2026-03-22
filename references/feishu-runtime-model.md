# Feishu Runtime Model

Use this reference when changing RepoDoctify's Feishu runtime behavior rather
than only its publication guidance.

## Core Runtime Layers

RepoDoctify's Feishu path is split into:

1. request and command selection
2. auth-state probing
3. publish-plan generation
4. verification-plan generation
5. optional execute-time adapters

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

The runtime may serialize these into JSON outputs, but internal code should use
typed models first and dicts second.

## Decision Principles

- prefer `localized_patch` for small in-place updates and section-local diagram edits
- prefer `full_rewrite` for table-heavy or structure-heavy changes
- update homepage or index docs last after child docs are stable
- keep auth blockers explicit and machine-readable
- keep verification checks structured so later execute-time readback can reuse them
