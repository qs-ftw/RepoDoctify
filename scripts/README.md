# Feishu Knowledge Ops Scripts

These helpers ship with `feishu-knowledge-ops` so the skill can be copied to another machine without depending on a workspace-specific `tools/` directory.

## Auth Helpers

- `lark_mcp_user_token_wrapper.py`
  - Generates an OAuth authorize URL
  - Exchanges callback URLs into a persisted `user_access_token`
  - Refreshes stored user tokens
  - Can launch `lark-mcp` with an injected `user_access_token`
- `lark_mcp_localhost_auth_server.py`
  - Runs a local OAuth helper at `http://localhost:3000/authorize`
  - Stores the resulting token in `~/.local/state/lark-mcp-user-token.json`

Both scripts default to reading Feishu app credentials from `~/.codex/config.toml`.

## Mermaid Helpers

- `feishu_mermaid_inspector.py`
  - Compares local Mermaid fences with remote Feishu rendered Mermaid blocks
- `feishu_mermaid_postprocessor.py`
  - Converts imported Mermaid code blocks into rendered Feishu Mermaid blocks
- `publish_feishu_diagram_round1.py`
  - Inserts `heading3 + rendered Mermaid` blocks at anchors in existing docs

## Docx Publisher

- `publish_python_bridge_doc.py`
  - Publishes Feishu-friendly Markdown into a docx document through block APIs
  - Supports real docx table blocks instead of raw Markdown pipe tables
  - Uses larger block batches plus table-cell `batch_update` to reduce full-rewrite request count
  - Can still be reused as a library by workspace-specific publishers

## `publish_feishu_diagram_round1.py` Modes

Default behavior:

- Uses the bundled default spec file at `scripts/specs/publish_feishu_diagram_round1.default.json`
- Keeps compatibility with the current workspace's known document batch

Portable behavior:

- Pass `--spec-file <path>` to load specs from JSON
- If omitted, the script loads the bundled default spec file automatically
- Use `--list-specs` to inspect available spec names before publishing
- Use `--name <spec-name>` one or more times to select a subset

Example commands:

```bash
python3 scripts/publish_feishu_diagram_round1.py --list-specs
python3 scripts/publish_feishu_diagram_round1.py --dry-run
python3 scripts/publish_feishu_diagram_round1.py --spec-file scripts/examples/publish_feishu_diagram_round1.example.json --list-specs
python3 scripts/publish_feishu_diagram_round1.py --spec-file scripts/examples/publish_feishu_diagram_round1.example.json --name demo-sequence --dry-run
```

## Spec File Format

The script accepts either:

- a top-level JSON array of spec objects
- or an object with a `specs` array

Each spec object must contain:

- `name`
- `document_id`
- `anchor_substring`
- `position`
  - `before` or `after`
- `blocks`
  - each block must be either:
  - `{"kind": "heading3", "text": "..."}`
  - `{"kind": "mermaid", "mermaid": "..."}`

See `examples/publish_feishu_diagram_round1.example.json` for a ready-to-copy template.
