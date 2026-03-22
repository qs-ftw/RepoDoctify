# Bitable And Permissions

Use this reference when the task includes knowledge indexing, operational tracking, or collaborator access.

## Bitable Design Principles

Design fields before records. A bad schema creates cleanup work later.

Prefer fields that help both humans and future maintenance:

- title or topic
- system or domain
- document type
- status
- owner
- source of truth
- Feishu URL
- last verified date
- notes or risks

## Common Knowledge-Index Table Pattern

Recommended baseline fields:

- `Title`
- `Domain`
- `Doc Type`
- `Depth`
- `Status`
- `Owner`
- `Source Authority`
- `Feishu URL`
- `Last Verified On`
- `Notes`

Useful enumerations:

- `Doc Type`: homepage, overview, deep dive, wiki node, ops note
- `Depth`: onboarding, overview, deep dive, reference
- `Status`: draft, published, republished, stale, archived
- `Source Authority`: code-verified, mixed, historical-only

## Record Update Rules

When adding or updating records:

- keep URLs current
- update verification date when the content was rechecked
- avoid free-form status values if a select field is available
- record whether a page is current or superseded

## Permission Principles

Use least privilege by default.

Common roles:

- viewer: can read, not edit
- editor: can maintain content
- owner or manager: can manage structure and collaboration

Before changing permissions:

- identify who needs access
- identify whether access is temporary or durable
- confirm whether the object is a doc, wiki space, or bitable

## Permission Change Workflow

1. Identify the exact target object
2. Identify the collaborator type and desired role
3. Apply the narrowest sufficient permission
4. Record what changed
5. Report anything that still requires manual confirmation

## Operational Notes

- Some APIs can add collaborators but still leave client-side verification to a follow-up check.
- If a permission action succeeds but you cannot independently verify the final ACL, say so explicitly.
- If the task includes both publication and access setup, publish first and permission second so the final links are stable.
