from pathlib import Path
import subprocess
import zipfile

from repodoctify.runtime import run_repodoctify

SKILL_ROOT = Path("skills/repo-doctify")


def test_release_bundle_includes_example_repos():
    assert (SKILL_ROOT / "examples/python-basic").exists()
    assert (SKILL_ROOT / "examples/typescript-basic").exists()
    assert (SKILL_ROOT / "examples/go-basic").exists()
    assert (SKILL_ROOT / "examples/rust-basic").exists()
    assert (SKILL_ROOT / "examples/README.md").exists()


def test_python_example_repo_smoke_generates_prompt_bundle(tmp_path):
    repo = (SKILL_ROOT / "examples/python-basic").resolve()

    result = run_repodoctify(repo, workspace_root=tmp_path / "workspaces", run_id="py-example")

    packet = (result.workspace / "prompt" / "packet.json").read_text(encoding="utf-8")
    brief = (result.workspace / "prompt" / "authoring-brief.md").read_text(encoding="utf-8")
    assert "python-basic" in packet
    assert "src/python_basic/cli.py" in brief
    assert "tests/test_cli.py" in brief


def test_typescript_example_repo_smoke_generates_prompt_bundle(tmp_path):
    repo = (SKILL_ROOT / "examples/typescript-basic").resolve()

    result = run_repodoctify(repo, workspace_root=tmp_path / "workspaces", run_id="ts-example")

    packet = (result.workspace / "prompt" / "packet.json").read_text(encoding="utf-8")
    brief = (result.workspace / "prompt" / "authoring-brief.md").read_text(encoding="utf-8")
    assert '"mode": "md"' in packet
    assert "src/index.ts" in brief
    assert "package.json" in brief


def test_go_example_repo_smoke_generates_prompt_bundle(tmp_path):
    repo = (SKILL_ROOT / "examples/go-basic").resolve()

    result = run_repodoctify(repo, workspace_root=tmp_path / "workspaces", run_id="go-example")

    brief = (result.workspace / "prompt" / "authoring-brief.md").read_text(encoding="utf-8")
    assert "`go`" in brief
    assert "cmd/server/main.go" in brief
    assert "go.mod" in brief


def test_rust_example_repo_smoke_generates_prompt_bundle(tmp_path):
    repo = (SKILL_ROOT / "examples/rust-basic").resolve()

    result = run_repodoctify(repo, workspace_root=tmp_path / "workspaces", run_id="rust-example")

    brief = (result.workspace / "prompt" / "authoring-brief.md").read_text(encoding="utf-8")
    assert "`rust`" in brief
    assert "Cargo.toml" in brief
    assert "src/main.rs" in brief or "src/lib.rs" in brief


def test_build_release_bundles_generates_platform_outputs(tmp_path):
    subprocess.run(
        ["python3", "scripts/build_release_bundles.py"],
        check=True,
        cwd=Path.cwd(),
    )

    codex_skill = Path("dist/release/codex/repo-doctify")
    claude_skill = Path("dist/release/claude/repo-doctify")
    claude_zip = Path("dist/release/claude/repo-doctify.zip")
    trae_skill = Path("dist/release/trae/skills/repo-doctify")
    trae_rule = Path("dist/release/trae/rules/repo-doctify.md")

    assert (codex_skill / "SKILL.md").exists()
    assert (claude_skill / "SKILL.md").exists()
    assert (trae_skill / "SKILL.md").exists()
    assert trae_rule.exists()
    assert claude_zip.exists()

    with zipfile.ZipFile(claude_zip) as archive:
        names = archive.namelist()
    assert "repo-doctify/SKILL.md" in names
