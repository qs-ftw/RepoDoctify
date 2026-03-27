from pathlib import Path
import subprocess

SKILL_ROOT = Path("skills/repo-doctify")


def test_repo_has_basic_project_files():
    assert Path("pyproject.toml").exists()
    assert Path("README.md").exists()
    assert SKILL_ROOT.exists()
    assert (SKILL_ROOT / "SKILL.md").exists()
    assert Path("repodoctify/__init__.py").exists()


def test_skill_declares_default_behavior_and_subcommands():
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "name: repo-doctify" in text
    assert "RepoDoctify" in text
    assert "Default Behavior" in text
    assert "$repo-doctify plan" in text
    assert "$repo-doctify md" in text
    assert "$repo-doctify html" in text
    assert "$repo-doctify feishu" in text
    assert "Legacy natural-language aliases" in text
    assert "`plan`" in text
    assert "`md`" in text
    assert "`html`" in text
    assert "`feishu`" in text
    assert "规划输出框架" in text
    assert "以 md 形式输出全部内容" in text
    assert "以 html 形式输出全部内容" in text
    assert "以飞书形式输出全部内容" in text
    assert "lark-mcp" in text
    assert "$repo-doctify" in text
    assert "Only ask" in text or "only ask" in text
    assert "1-3" in text or "1 to 3" in text
    assert "feishu-knowledge-ops" not in text
    description_line = next(line for line in text.splitlines() if line.startswith("description:"))
    assert len(description_line.removeprefix("description: ").strip()) <= 200


def test_repo_owns_reference_set():
    for rel in [
        "skills/repo-doctify/references/repo-docset-framework.md",
        "skills/repo-doctify/references/content-patterns.md",
        "skills/repo-doctify/references/bitable-and-permissions.md",
        "skills/repo-doctify/references/docset-ir.md",
        "skills/repo-doctify/references/feishu-operations.md",
        "skills/repo-doctify/references/feishu-runtime-model.md",
        "skills/repo-doctify/references/markdown-rendering-rules.md",
        "skills/repo-doctify/references/html-rendering-rules.md",
        "skills/repo-doctify/references/feishu-rendering-handoff.md",
    ]:
        assert Path(rel).exists(), rel


def test_local_install_helper_exists():
    assert Path("scripts/install_local_skill.py").exists()
    assert Path("scripts/build_release_bundles.py").exists()
    assert (SKILL_ROOT / "scripts/publish_python_bridge_doc.py").exists()
    assert (SKILL_ROOT / "scripts/publish_feishu_diagram_round1.py").exists()
    assert (SKILL_ROOT / "scripts/feishu_mermaid_inspector.py").exists()
    assert (SKILL_ROOT / "scripts/feishu_mermaid_postprocessor.py").exists()
    assert (SKILL_ROOT / "scripts/lark_mcp_localhost_auth_server.py").exists()
    assert (SKILL_ROOT / "scripts/lark_mcp_user_token_wrapper.py").exists()


def test_feishu_script_wrapper_uses_repodoctify_library():
    text = (SKILL_ROOT / "scripts/publish_feishu_diagram_round1.py").read_text(encoding="utf-8")
    assert "repodoctify.feishu" in text
    bridge_text = (SKILL_ROOT / "scripts/publish_python_bridge_doc.py").read_text(encoding="utf-8")
    assert "repodoctify.feishu" in bridge_text
    inspector_text = (SKILL_ROOT / "scripts/feishu_mermaid_inspector.py").read_text(encoding="utf-8")
    assert "repodoctify.feishu" in inspector_text
    postprocessor_text = (SKILL_ROOT / "scripts/feishu_mermaid_postprocessor.py").read_text(encoding="utf-8")
    assert "repodoctify.feishu" in postprocessor_text


def test_install_helper_targets_skill_directory_name():
    text = Path("scripts/install_local_skill.py").read_text(encoding="utf-8")
    assert '".codex" / "skills" / "repo-doctify"' in text
    assert '".claude" / "skills" / "repo-doctify"' in text
    assert '".trae" / "skills" / "repo-doctify"' in text
    assert 'platform" / "trae" / "rules" / "repo-doctify.md"' in text
    assert '"codex": "Codex"' in text
    assert '"claude": "Claude Code"' in text
    assert '"trae": "Trae"' in text


def test_readme_describes_skill_first_usage():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "$repo-doctify" in text
    assert "$repo-doctify plan" in text
    assert "$repo-doctify md" in text
    assert "$repo-doctify html" in text
    assert "$repo-doctify feishu" in text
    assert "skills/repo-doctify/" in text
    assert "tree/main/skills/repo-doctify" in text
    assert "--platform codex" in text
    assert "--platform claude" in text
    assert "--platform trae" in text
    assert "dist/release/claude/" in text
    assert "dist/release/trae/skills/repo-doctify/" in text
    assert "portable repository-docset skill source" in text
    assert "Python + TS/JS" in text
    assert "Go, Rust, and Java" in text
    assert "not a good fit yet" in text or "not supported yet" in text
    assert "examples/" in text


def test_skill_declares_runtime_script_execution_path():
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "run_repodoctify" in text
    assert "The Python runtime must not author document prose" in text
    assert "write-targets.json" in text
    assert "document-prompts.json" in text
    assert "Write files one at a time" in text
    assert "Do not keep exploring once the evidence is sufficient" in text
    assert "Do not glob-read every source file" in text
    assert "Do not invoke `brainstorming`" in text
    assert "single current document task" in text
    assert "Do not stop after writing only homepage" in text
    assert "must complete all targets in a single run" in text
    assert "single multi-file `apply_patch`" in text
    assert "bulk file" in text
    assert "existence check" in text


def test_feishu_ownership_reference_points_to_repodoctify():
    text = (SKILL_ROOT / "references/feishu-rendering-handoff.md").read_text(encoding="utf-8")
    assert "RepoDoctify" in text
    assert "owns Feishu-specific publication logic" in text or "owns Feishu publishing logic" in text
    assert "feishu-knowledge-ops" not in text
