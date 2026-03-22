from pathlib import Path

from repodoctify.analysis import analyze_repository
from repodoctify.composer import compose_docset
from repodoctify.planning import build_default_docset_plan


def test_python_docs_explain_why_to_read_files_and_where_to_change(tmp_path):
    repo = tmp_path / "python-service"
    repo.mkdir()
    (repo / "README.md").write_text("# Python Service\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='python-service'\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "python_service").mkdir()
    (repo / "src" / "python_service" / "cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_cli.py").write_text("def test_main():\n    assert True\n", encoding="utf-8")

    analysis = analyze_repository(repo)
    docs = compose_docset(analysis, build_default_docset_plan(analysis))
    code_path = next(doc for doc in docs if doc.doc_id == "code-reading-path")
    dev_guide = next(doc for doc in docs if doc.doc_id == "development-guide")

    code_text = "\n".join(item for section in code_path.sections for item in section.body)
    dev_text = "\n".join(item for section in dev_guide.sections for item in section.body)

    assert "why" in code_text.lower() or "capture the repository contract" in code_text
    assert "src/python_service/cli.py" in code_text
    assert "tests/test_cli.py" in code_text
    assert "follow" in code_text.lower()
    assert "entrypoint" in code_text.lower()
    assert "smallest ownership surface" in dev_text
    assert "change" in dev_text.lower()


def test_typescript_workspace_repo_gets_bridge_and_debug_guidance(tmp_path):
    repo = tmp_path / "workspace-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Workspace Repo\n", encoding="utf-8")
    (repo / "package.json").write_text(
        '{"name":"workspace-repo","workspaces":["apps/*","packages/*"],"scripts":{"build":"tsc"}}',
        encoding="utf-8",
    )
    (repo / "tsconfig.json").write_text("{}", encoding="utf-8")
    (repo / "apps").mkdir()
    (repo / "apps" / "web").mkdir(parents=True)
    (repo / "apps" / "web" / "main.ts").write_text("console.log('web')\n", encoding="utf-8")
    (repo / "packages").mkdir()
    (repo / "packages" / "shared").mkdir(parents=True)
    (repo / "packages" / "shared" / "index.ts").write_text("export const x = 1;\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "main.test.ts").write_text("it('main',()=>{})\n", encoding="utf-8")

    analysis = analyze_repository(repo)
    docs = compose_docset(analysis, build_default_docset_plan(analysis))
    bridge = next(doc for doc in docs if doc.doc_id == "bridge-topics")
    dev_guide = next(doc for doc in docs if doc.doc_id == "development-guide")

    bridge_text = "\n".join(item for section in bridge.sections for item in section.body)
    dev_text = "\n".join(item for section in dev_guide.sections for item in section.body)

    assert "workspace" in bridge_text.lower()
    assert "package scripts" in bridge_text.lower() or "source entrypoints" in bridge_text.lower()
    assert "tests" in dev_text.lower()
    assert "entrypoint" in dev_text.lower()


def test_python_docs_include_concrete_chain_guidance(tmp_path):
    repo = tmp_path / "python-chain-docs"
    repo.mkdir()
    (repo / "README.md").write_text("# Python Chain Docs\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='python-chain-docs'\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "python_chain_docs").mkdir()
    (repo / "src" / "python_chain_docs" / "cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    (repo / "src" / "python_chain_docs" / "service.py").write_text("def run():\n    return 'ok'\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_cli.py").write_text("def test_main():\n    assert True\n", encoding="utf-8")

    analysis = analyze_repository(repo)
    docs = compose_docset(analysis, build_default_docset_plan(analysis))
    code_path = next(doc for doc in docs if doc.doc_id == "code-reading-path")

    code_text = "\n".join(item for section in code_path.sections for item in section.body)

    assert "README.md" in code_text
    assert "src/python_chain_docs/cli.py" in code_text
    assert "tests/test_cli.py" in code_text
    assert "follow this chain" in code_text.lower() or "follow `" in code_text.lower()
