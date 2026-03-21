from pathlib import Path


def test_repo_has_basic_project_files():
    assert Path("pyproject.toml").exists()
    assert Path("README.md").exists()
    assert Path("repodoctify/__init__.py").exists()


def test_skill_declares_default_behavior_and_subcommands():
    text = Path("SKILL.md").read_text(encoding="utf-8")
    assert "RepoDoctify" in text
    assert "Default Behavior" in text
    assert "规划输出框架" in text
    assert "以 md 形式输出全部内容" in text
    assert "以 html 形式输出全部内容" in text
    assert "以飞书形式输出全部内容" in text
    assert "lark-mcp" in text


def test_repo_owns_reference_set():
    for rel in [
        "references/repo-docset-framework.md",
        "references/docset-ir.md",
        "references/markdown-rendering-rules.md",
        "references/html-rendering-rules.md",
        "references/feishu-rendering-handoff.md",
    ]:
        assert Path(rel).exists(), rel


def test_local_install_helper_exists():
    assert Path("scripts/install_local_skill.py").exists()

