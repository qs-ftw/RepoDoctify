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

Recommended smoke checks (run via the Python runtime directly):

```bash
python -c "
from repodoctify import run_repodoctify
from pathlib import Path
for name in ['python-basic', 'typescript-basic', 'go-basic', 'rust-basic']:
    repo = Path(__file__).parent / name
    result = run_repodoctify(repo, workspace_root=Path('/tmp/repodoctify-workspaces'))
    print(result.workspace)
"
```

For Codex skill testing after installation:

```bash
$repo-doctify
```

Run it from inside one of the example repo directories so the target repository
is unambiguous.
