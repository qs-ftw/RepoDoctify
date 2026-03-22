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
    assert "shared" in dev_text.lower() or "package" in dev_text.lower()


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


def test_development_guide_includes_debug_and_change_boundary_guidance(tmp_path):
    repo = tmp_path / "python-debug-guidance"
    repo.mkdir()
    (repo / "README.md").write_text("# Python Debug Guidance\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='python-debug-guidance'\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "python_debug_guidance").mkdir()
    (repo / "src" / "python_debug_guidance" / "cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    (repo / "src" / "python_debug_guidance" / "service.py").write_text("def run():\n    return 'ok'\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_service.py").write_text("def test_service():\n    assert True\n", encoding="utf-8")

    analysis = analyze_repository(repo)
    docs = compose_docset(analysis, build_default_docset_plan(analysis))
    dev_guide = next(doc for doc in docs if doc.doc_id == "development-guide")
    evidence = next(doc for doc in docs if doc.doc_id == "evidence-guide")

    dev_text = "\n".join(item for section in dev_guide.sections for item in section.body)
    evidence_text = "\n".join(item for section in evidence.sections for item in section.body)

    assert "debug" in dev_text.lower()
    assert "change boundary" in dev_text.lower()
    assert "test anchor" in evidence_text.lower() or "regression anchor" in evidence_text.lower()


def test_go_docs_include_module_and_runtime_guidance(tmp_path):
    repo = tmp_path / "go-docs"
    repo.mkdir()
    (repo / "README.md").write_text("# Go Docs\n", encoding="utf-8")
    (repo / "go.mod").write_text("module example.com/go-docs\n\ngo 1.22\n", encoding="utf-8")
    (repo / "cmd").mkdir()
    (repo / "cmd" / "server").mkdir(parents=True)
    (repo / "cmd" / "server" / "main.go").write_text("package main\nfunc main(){}\n", encoding="utf-8")
    (repo / "internal").mkdir()
    (repo / "internal" / "service.go").write_text("package internal\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "server_test.go").write_text("package tests\n", encoding="utf-8")

    analysis = analyze_repository(repo)
    docs = compose_docset(analysis, build_default_docset_plan(analysis))
    stack = next(doc for doc in docs if doc.doc_id == "stack-and-entrypoints")
    bridge = next(doc for doc in docs if doc.doc_id == "bridge-topics")

    stack_text = "\n".join(item for section in stack.sections for item in section.body)
    bridge_text = "\n".join(item for section in bridge.sections for item in section.body)

    assert "cmd/server/main.go" in stack_text
    assert "go.mod" in stack_text.lower()
    assert "internal/" in bridge_text.lower() or "go module" in bridge_text.lower()


def test_rust_docs_include_crate_and_test_guidance(tmp_path):
    repo = tmp_path / "rust-docs"
    repo.mkdir()
    (repo / "README.md").write_text("# Rust Docs\n", encoding="utf-8")
    (repo / "Cargo.toml").write_text("[package]\nname = \"rust-docs\"\nversion = \"0.1.0\"\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "main.rs").write_text("fn main() {}\n", encoding="utf-8")
    (repo / "src" / "lib.rs").write_text("pub fn run() {}\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "smoke_test.rs").write_text("#[test]\nfn smoke() {}\n", encoding="utf-8")

    analysis = analyze_repository(repo)
    docs = compose_docset(analysis, build_default_docset_plan(analysis))
    code_path = next(doc for doc in docs if doc.doc_id == "code-reading-path")
    dev_guide = next(doc for doc in docs if doc.doc_id == "development-guide")

    code_text = "\n".join(item for section in code_path.sections for item in section.body)
    dev_text = "\n".join(item for section in dev_guide.sections for item in section.body)

    assert "Cargo.toml" in code_text
    assert "src/main.rs" in code_text or "src/lib.rs" in code_text
    assert "crate" in dev_text.lower() or "module" in dev_text.lower()


def test_java_docs_include_build_and_source_set_guidance(tmp_path):
    repo = tmp_path / "java-docs"
    repo.mkdir()
    (repo / "README.md").write_text("# Java Docs\n", encoding="utf-8")
    (repo / "build.gradle").write_text("plugins { id 'java' }\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "main").mkdir()
    (repo / "src" / "main" / "java").mkdir(parents=True)
    (repo / "src" / "main" / "java" / "App.java").write_text("class App { public static void main(String[] args) {} }\n", encoding="utf-8")
    (repo / "src" / "test").mkdir()
    (repo / "src" / "test" / "java").mkdir(parents=True)
    (repo / "src" / "test" / "java" / "AppTest.java").write_text("class AppTest {}\n", encoding="utf-8")

    analysis = analyze_repository(repo)
    docs = compose_docset(analysis, build_default_docset_plan(analysis))
    overview = next(doc for doc in docs if doc.doc_id == "overview")
    dev_guide = next(doc for doc in docs if doc.doc_id == "development-guide")

    overview_text = "\n".join(item for section in overview.sections for item in section.body)
    dev_text = "\n".join(item for section in dev_guide.sections for item in section.body)

    assert "java" in overview_text.lower()
    assert "build.gradle" in overview_text
    assert "src/main/java" in dev_text or "src/test/java" in dev_text
