from pathlib import Path


def test_repo_has_basic_project_files():
    assert Path("pyproject.toml").exists()
    assert Path("README.md").exists()
    assert Path("repodoctify/__init__.py").exists()


def test_skill_declares_default_behavior_and_subcommands():
    text = Path("SKILL.md").read_text(encoding="utf-8")
    assert "name: repo-doctify" in text
    assert "RepoDoctify" in text
    assert "Default Behavior" in text
    assert "规划输出框架" in text
    assert "以 md 形式输出全部内容" in text
    assert "以 html 形式输出全部内容" in text
    assert "以飞书形式输出全部内容" in text
    assert "lark-mcp" in text
    assert "$repo-doctify" in text
    assert "Only ask" in text or "only ask" in text
    assert "1-3" in text or "1 to 3" in text
    assert "feishu-knowledge-ops" not in text


def test_repo_owns_reference_set():
    for rel in [
        "references/repo-docset-framework.md",
        "references/content-patterns.md",
        "references/bitable-and-permissions.md",
        "references/docset-ir.md",
        "references/feishu-operations.md",
        "references/feishu-runtime-model.md",
        "references/markdown-rendering-rules.md",
        "references/html-rendering-rules.md",
        "references/feishu-rendering-handoff.md",
    ]:
        assert Path(rel).exists(), rel


def test_local_install_helper_exists():
    assert Path("scripts/install_local_skill.py").exists()
    assert Path("scripts/publish_python_bridge_doc.py").exists()
    assert Path("scripts/publish_feishu_diagram_round1.py").exists()
    assert Path("scripts/feishu_mermaid_inspector.py").exists()
    assert Path("scripts/feishu_mermaid_postprocessor.py").exists()
    assert Path("scripts/lark_mcp_localhost_auth_server.py").exists()
    assert Path("scripts/lark_mcp_user_token_wrapper.py").exists()


def test_feishu_script_wrapper_uses_repodoctify_library():
    text = Path("scripts/publish_feishu_diagram_round1.py").read_text(encoding="utf-8")
    assert "repodoctify.feishu" in text
    bridge_text = Path("scripts/publish_python_bridge_doc.py").read_text(encoding="utf-8")
    assert "repodoctify.feishu" in bridge_text


def test_install_helper_targets_skill_directory_name():
    text = Path("scripts/install_local_skill.py").read_text(encoding="utf-8")
    assert '".codex" / "skills" / "repo-doctify"' in text


def test_readme_describes_skill_first_usage():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "$repo-doctify" in text
    assert "Codex skill" in text
    assert "Python + TS/JS" in text
    assert "not a good fit yet" in text or "not supported yet" in text
    assert "examples/" in text
    assert "feishu-knowledge-ops" not in text


def test_feishu_ownership_reference_points_to_repodoctify():
    text = Path("references/feishu-rendering-handoff.md").read_text(encoding="utf-8")
    assert "RepoDoctify" in text
    assert "owns Feishu-specific publication logic" in text or "owns Feishu publishing logic" in text
    assert "feishu-knowledge-ops" not in text
