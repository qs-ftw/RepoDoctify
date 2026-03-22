# Feishu Operations

Use this reference when the task moves from synthesis into actual Feishu publishing and maintenance.

## Operating Sequence

1. Prepare local markdown or structured content first
2. Publish the smallest stable unit first
3. Capture returned tokens and URLs immediately
4. Repoint index pages after child docs are confirmed
5. Read back the published result before claiming completion

For docsets with a homepage or index:

- publish child docs first
- update the homepage last, after the child URLs are confirmed
- prefer per-doc progress over one black-box full-docset publish when the write path is heavy

## Doc Publication

When doc import is the reliable operation path:

- keep a local markdown source of truth
- import with a short, valid file name if the Feishu API has name-length limits
- when import is creating a user-visible doc, `file_name` should be the intended final title, not the local source file name
- do not include `.md` or similar source extensions in `file_name` unless the user explicitly wants that exact visible title
- keep the user-facing H1 more descriptive than the import file name if needed
- if the imported title lands wrong, do not silently create a second replacement doc by default; first tell the user the title problem and confirm whether duplicating the doc is acceptable

If the task is an update to an existing document and a valid `user_access_token` is available:

- pull the current remote document first and treat it as the merge base
- do not assume the local markdown file is still authoritative if the user may have edited the remote doc manually
- reconcile remote-only edits into the local working draft before any writeback
- prefer editing the existing document in place
- keep the local markdown draft as the source of truth
- decide localized patch vs full-document rewrite intentionally; do not make full rewrite the default
- prefer localized patch for small link fixes, short prose edits, metadata updates, and section-local diagram or table changes
- only fall back to full-document rewrite when most of the document is intentionally changing or when patching would be harder to keep correct than replacing the body
- use block-level replacement carefully and verify the final block tree by readback
- for Mermaid-like client-rendered content, prefer targeted block replacement over full-document churn
- for board-first charts, keep the local placeholder keys as the source of truth and do the board conversion after the doc content lands
- for local Markdown -> docx publication with real tables and controlled block writes, prefer reusing `scripts/publish_python_bridge_doc.py` over rebuilding a one-off block writer

If the task is an update to an existing document and `user_access_token` is not currently stable:

- try user-auth recovery before doing anything else
- prefer the formal localhost auth server in this workspace: `python3 scripts/lark_mcp_localhost_auth_server.py`
- first test `useUAT: true` read access on the target doc
- if MCP reports invalid or expired user auth, generate or surface the authorization link and wait for the user to complete manual authorization
- after the user confirms authorization, retry the target-doc read before attempting any write
- if the local MCP config only has `--oauth`, add `--token-mode user_access_token` before relying on future user-auth sessions
- never fall back to republishing just because auth recovery is needed or the token has expired
- if the user does not authorize, stop and report the blocker

If the task is an update to an existing document and safe in-place editing is not available:

- do not publish a new version unless the user explicitly asks for a separate historical edition
- surface the exact blocker and, when applicable, send the authorization link to the user

## Remote-First Update Rule

For existing docs and homepages, remote state wins over stale local copies.

- first fetch the current remote content
- if the page is link-heavy or structure-sensitive, inspect remote blocks as well, not just flattened raw text
- compare remote state against the local draft before editing
- preserve remote-only user edits unless the user explicitly asks to remove them
- create the new local working draft from the reconciled result, then update the live doc in place

Use this rule especially for:

- homepages and index docs
- docs the user may edit manually in Feishu
- pages whose links or block ordering matter

## Wiki-Oriented Structure

If you can create or maintain true wiki nodes, use the real structure.

If you cannot:

- simulate the tree with one homepage plus linked child docs
- describe the intended wiki hierarchy in the homepage
- clearly state that the current result is “linked docs, not true wiki nodes”

Typical tree progression:

1. homepage or index
2. system overviews
3. chain deep dives
4. subsystem专题

## Authorization-First Rules

For existing documents, auth recovery comes before any publish fallback.

- token expiry is an authorization event, not a republish trigger
- permission denial on a user-owned doc is a verification signal, not a reason to fork the doc
- when blocked, send the authorization link and wait for the user
- resume only after the user confirms authorization
- if the user explicitly wants a new edition, record that as a separate decision instead of treating it as the default failure path

## user_access_token Recovery Pattern

Use this order for user-owned doc maintenance:

1. Probe `useUAT: true` read access on the target doc
2. If the probe fails, surface the authorization link and wait for the user
3. After the user confirms authorization, re-run the same read probe
4. Only after a successful read, attempt the intended write path
5. If using a local script, pass the refreshed `user_access_token` explicitly when supported
6. Verify the target doc actually changed

## Preferred localhost Authorization Pattern

Use the formal localhost auth server as the default recovery path instead of ad hoc OAuth retries.

Preferred sequence:

1. Run `python3 scripts/lark_mcp_localhost_auth_server.py`
2. Send `http://localhost:3000/authorize` to the user
3. Let the browser round-trip back to `http://localhost:3000/callback`
4. After the user finishes approval, verify the stored token with `python3 scripts/lark_mcp_user_token_wrapper.py whoami`
5. Probe the actual target doc again with `useUAT: true`
6. Only after the target-doc probe succeeds, resume block writes, doc updates, wiki changes, bitable edits, or permission operations
7. If the localhost server cannot be used, fall back to `python3 scripts/lark_mcp_user_token_wrapper.py authorize-url`, send that URL, then run `python3 scripts/lark_mcp_user_token_wrapper.py exchange-url --url '<callback-url>'` after the user returns the callback URL

Local persistence details that matter:

- token store: `~/.local/state/lark-mcp-user-token.json`
- callback default: `http://localhost:3000/callback`
- localhost entrypoint: `http://localhost:3000/authorize`
- do not assume a stored token is usable until `whoami` and a real target-doc probe both succeed
- if the localhost server is not running, do not send the bare localhost URL
- if the wrapper says there is no pending authorization context, restart the localhost server or generate a fresh `authorize-url` instead of trying to reuse an old callback
- if refresh fails or the access token is missing, restart from the localhost auth server or `authorize-url`; do not republish docs as a workaround

## user_access_token Pitfalls

Observed pitfalls that should change how you operate:

- tenant auth and user auth are not interchangeable
  - tenant auth can succeed on app-owned docs while failing with `403 / 1770032 forBidden` on user-owned docs
- `useUAT: true` is not enough by itself
  - always verify against the actual target doc you intend to modify
- an empty or omitted explicit token can silently push tooling back onto tenant auth
  - if a script supports `--token`, make sure the value is present and non-empty
- successful raw-content readback does not prove block-level write permission
  - validate the specific write path when changing blocks, diagrams, or hyperlinks
- successful raw-content readback also does not prove you captured the current link structure
  - index pages may require block-level inspection because raw text strips hyperlink targets
- do not hide auth problems behind republishing
  - that creates version sprawl and dodges the real permission issue instead of fixing it
- do not treat a local markdown draft as safe overwrite material for an existing doc
  - the user may have changed the remote page after the last export or publish
- `whoami` proves local token metadata exists, not that the intended doc write will succeed
  - always pair token validation with a real read or write probe on the exact target doc

## Verification Checklist

After any publication:

- confirm the title
- confirm the major sections
- confirm link targets if the page is an index
- confirm diagram blocks if diagrams were added
- confirm returned URL and token were recorded

Use this stronger matrix when the page depended on special block types:

| Concern | What to verify |
| --- | --- |
| In-place update safety | Same document id and URL are still in use |
| Title | `raw_content` or equivalent readback still contains the intended title |
| Tables | `raw_content` has no leftover pipe-table delimiters and block readback contains real `31/32` table blocks |
| Mermaid | Remote block tree contains the expected Mermaid chart blocks and no stale imported code block when conversion was intended |
| Board | Remote block tree contains the expected `block_type=43` blocks and each board has real nodes, not an empty placeholder |
| Homepage / index | Child-doc links still point to the intended live docs |
| Remote-only edits | Any remote edits the user wanted preserved are still present after writeback |

Accept plain-text readback of Mermaid blocks as proof of import if rendering is client-dependent.

After any in-place update on a user-owned doc:

- confirm the target doc is still the same document id
- confirm the intended section or block changed
- confirm the write used refreshed user auth rather than an accidental tenant fallback
- if the operation depended on an explicit token, record that fact for future maintenance
- if the page existed before the update, confirm the remote-only edits you intended to preserve are still present

## Full-Rewrite Churn Control

If a full-document rewrite is unavoidable, optimize request count before treating the operation as “Feishu write latency”.

- create ordinary root-level blocks in larger batches instead of tiny default chunks when the payload shape is simple
- create all real table blocks first, then use one consolidated readback to map generated cells instead of reading after every table
- when a table cell already contains the default empty paragraph block, prefer `batch_update` on that existing child block over `delete + create`
- keep fallback `create` only for cells that truly have no writable default child block

This matters because table-heavy docs can turn one small textual change into hundreds of block operations if each cell is rewritten independently.

## Mermaid Operations

When a Feishu doc contains Mermaid-style diagrams:

- keep the local markdown Mermaid block as the source of truth
- diagnose first, then mutate
- prefer targeted block replacement over rebuilding the whole doc
- prefer rendered Mermaid add-on blocks over fenced code blocks when the user expects charts inside Feishu

### Choosing Mermaid Types In Feishu

Feishu has proven support in this workspace for at least:

- `flowchart`
- `sequenceDiagram`
- `erDiagram`
- `classDiagram`
- `mindmap`
- `gantt`
- `pie`

Use them intentionally:

- homepage or study index: `mindmap`
- request, trace, polling, callback, cross-repo flow: `sequenceDiagram`
- main data or state relationships: `erDiagram`
- service or class responsibility map: `classDiagram`
- one clear local stage chain: `flowchart`

Most technical learning docs should still stop at 1-2 diagrams.

### Inspect First

If the skill-local helpers are available:

- use `scripts/feishu_mermaid_inspector.py` to compare local Mermaid against remote Feishu add-on blocks
- use `scripts/feishu_mermaid_postprocessor.py` to plan or apply code-block to chart-block replacement
- use `scripts/publish_feishu_diagram_round1.py` as the current proven pattern for anchor-based in-place insertion of `heading3 + rendered Mermaid` into existing user-owned docs

### Insert Or Convert Mermaid

For rendered Mermaid in Feishu docx blocks:

- use `block_type=40`
- use `add_ons.component_type_id=blk_631fefbbae02400430b8f9f4`
- use `add_ons.record` as JSON with:
  - `data`: Mermaid source
  - `theme`: `default`
  - `view`: `chart`

If Mermaid was imported as a code block:

- locate the original `block_type=14` block under the correct parent/index
- insert the rendered chart block at the same index
- delete the old code block immediately after insertion

If the task is to enrich an existing doc without rewriting the full page:

- fetch the remote block tree first
- find the target section by stable heading or paragraph substring
- insert the new `heading3` and `block_type=40` Mermaid add-on at that anchor
- read back the block tree and confirm the new order is exactly where intended

### Proven Workspace Script

Current reusable script:

- path: `scripts/publish_feishu_diagram_round1.py`
- purpose: batch in-place insertion of Mermaid add-on blocks into existing Feishu docs
- bundled default spec file: `scripts/specs/publish_feishu_diagram_round1.default.json`
- portable input mode: pass `--spec-file <json>` to load specs from a local JSON file instead of the bundled default batch

What it already proves in this workspace:

- reads and refreshes persisted `user_access_token` via `scripts/lark_mcp_user_token_wrapper.py`
- pulls live block trees before mutation
- finds insertion points by anchor substring
- inserts `heading3` and `block_type=40` rendered Mermaid blocks
- avoids duplicate insertion when the same heading or Mermaid payload already exists
- verifies the result by live readback

Useful commands:

- inspect built-in spec names:
  - `python3 scripts/publish_feishu_diagram_round1.py --list-specs`
- dry run all specs:
  - `python3 scripts/publish_feishu_diagram_round1.py --dry-run`
- publish all specs:
  - `python3 scripts/publish_feishu_diagram_round1.py`
- publish one named spec:
  - `python3 scripts/publish_feishu_diagram_round1.py --name trace-sequence`
- inspect a portable JSON spec file:
  - `python3 scripts/publish_feishu_diagram_round1.py --spec-file scripts/examples/publish_feishu_diagram_round1.example.json --list-specs`
- dry run one external spec:
  - `python3 scripts/publish_feishu_diagram_round1.py --spec-file scripts/examples/publish_feishu_diagram_round1.example.json --name demo-sequence --dry-run`

Treat this script as a reference implementation for future localized Mermaid enrichment jobs. Adapt the spec table and anchors instead of rewriting the whole Feishu update flow from scratch.

### Repair Broken Mermaid

If a rendered block exists but does not display correctly:

- read back the remote add-on payload
- if the remote record has `view="codeChart"`, treat it as a parse-failure chart and repair it
- compare local Mermaid syntax against a known-good rendering or a local Mermaid parser when available
- replace the broken rendered block in place with a corrected `view="chart"` block

### Syntax Guardrails

Before writing Mermaid to Feishu:

- normalize obvious invalid shorthand that Feishu/Mermaid rejects
- current proven fix:
  - invalid: `ID[/label]`
  - valid replacement: `ID["/label"]`
- do not rewrite already valid shorthand such as `ID[/label/]`

### Verification After Mermaid Changes

After any Mermaid insertion or repair:

- verify remote block count and ids
- verify the rendered block uses `view="chart"`
- verify the original Mermaid code block is gone when conversion was intended
- compare local Mermaid and remote stored Mermaid semantically
- if a heading was inserted with the chart, verify block adjacency so the chart landed under the intended section rather than elsewhere in the page

## Board Placeholder Operations

When the local source uses board placeholders:

- keep the markdown source explicit, for example:

```board
layered_architecture
```

- treat the fenced key as the local source of truth for that board
- let the publish path land the markdown first, even if the placeholder temporarily becomes a normal code block
- then replace the imported code block with a real `block_type=43` board block
- create the board nodes from the matched builder
- set the board theme explicitly if the workspace has a proven preferred theme

Good operational rules:

- use stable semantic keys, not free-form prose
- keep the builder registry small and reusable
- prefer adding a new shared key only after it has proven useful in more than one article or repo family
- if the board is article-specific and unlikely to recur, keep that builder local to the current publisher rather than polluting the shared skill

After board conversion:

- verify the expected number of board blocks
- verify each board has non-empty node content
- verify the surrounding heading and explanatory paragraph are still adjacent to the board block as intended

## Slow Update Triage

Do not assume a quiet publish process is hung just because it has no progress output.

Observed slow path in this workspace:

- real table blocks can dominate write time
- table-heavy docs may spend most of the total update on table creation and table-cell child writes rather than on diagrams or auth

When a publish appears stuck:

1. split the flow into `body replace -> diagram replace -> readback`
2. time each phase separately
3. determine whether the slow phase is docx block writing, board/Mermaid replacement, or verification
4. only change auth or publication strategy after you know which phase is actually slow

For large docsets:

- prefer per-doc progress logging
- publish child docs first
- save homepage update for last

## Reporting Limits

Always report limits such as:

- no true wiki-tree creation support
- no safe in-place edit support
- in-place edit requires valid user auth
- user authorization is pending and work is paused for manual completion
- no direct permission proof if the tool only accepted the mutation request
- partial automation with remaining manual follow-up
