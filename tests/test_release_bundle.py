from pathlib import Path

from repodoctify.runtime import run_repodoctify


def test_release_bundle_includes_example_repos():
    assert Path("examples/python-basic").exists()
    assert Path("examples/typescript-basic").exists()
    assert Path("examples/go-basic").exists()
    assert Path("examples/rust-basic").exists()
    assert Path("examples/README.md").exists()


def test_python_example_repo_smoke_generates_markdown(tmp_path):
    repo = Path("examples/python-basic").resolve()

    result = run_repodoctify(repo, workspace_root=tmp_path / "workspaces", run_id="py-example")

    readme = (result.workspace / "md" / "README.md").read_text(encoding="utf-8")
    code_path = (result.workspace / "md" / "code-reading-path.md").read_text(encoding="utf-8")
    assert "python-basic" in readme
    assert "src/python_basic/cli.py" in code_path
    assert "tests/test_cli.py" in code_path


def test_typescript_example_repo_smoke_generates_markdown(tmp_path):
    repo = Path("examples/typescript-basic").resolve()

    result = run_repodoctify(repo, workspace_root=tmp_path / "workspaces", run_id="ts-example")

    overview = (result.workspace / "md" / "overview.md").read_text(encoding="utf-8")
    stack = (result.workspace / "md" / "stack-and-entrypoints.md").read_text(encoding="utf-8")
    assert "typescript" in overview.lower()
    assert "src/index.ts" in stack
    assert "package_manager" in stack


def test_go_example_repo_smoke_generates_markdown(tmp_path):
    repo = Path("examples/go-basic").resolve()

    result = run_repodoctify(repo, workspace_root=tmp_path / "workspaces", run_id="go-example")

    overview = (result.workspace / "md" / "overview.md").read_text(encoding="utf-8")
    stack = (result.workspace / "md" / "stack-and-entrypoints.md").read_text(encoding="utf-8")
    assert "go" in overview.lower()
    assert "cmd/server/main.go" in stack
    assert "go.mod" in stack


def test_rust_example_repo_smoke_generates_markdown(tmp_path):
    repo = Path("examples/rust-basic").resolve()

    result = run_repodoctify(repo, workspace_root=tmp_path / "workspaces", run_id="rust-example")

    overview = (result.workspace / "md" / "overview.md").read_text(encoding="utf-8")
    code_path = (result.workspace / "md" / "code-reading-path.md").read_text(encoding="utf-8")
    assert "rust" in overview.lower()
    assert "Cargo.toml" in code_path
    assert "src/main.rs" in code_path or "src/lib.rs" in code_path
