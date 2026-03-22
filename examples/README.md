# RepoDoctify Examples

These example repositories are intentionally small. They exist to demonstrate
the current release target for `repo-doctify` and to make smoke testing
repeatable.

Included examples:

- `python-basic`
  - small Python package layout
  - includes `README.md`, `pyproject.toml`, `src/`, and `tests/`
- `typescript-basic`
  - small TypeScript package layout
  - includes `README.md`, `package.json`, `tsconfig.json`, and `src/`
- `go-basic`
  - small Go module layout
  - includes `README.md`, `go.mod`, `cmd/`, `internal/`, and `tests/`
- `rust-basic`
  - small Rust crate layout
  - includes `README.md`, `Cargo.toml`, `src/`, and `tests/`

Recommended smoke checks:

```bash
python -m repodoctify --repo examples/python-basic --workspace-root /tmp/repodoctify-workspaces
python -m repodoctify --repo examples/typescript-basic --workspace-root /tmp/repodoctify-workspaces
python -m repodoctify --repo examples/go-basic --workspace-root /tmp/repodoctify-workspaces
python -m repodoctify --repo examples/rust-basic --workspace-root /tmp/repodoctify-workspaces
```

For Codex skill testing after installation:

```bash
$repo-doctify
```

Run it from inside one of the example repo directories so the target repository
is unambiguous.
