from repodoctify.analysis import analyze_repository
from repodoctify.models import CodeAnchorChain


def test_analyze_python_repo_detects_language_entrypoints_and_evidence(tmp_path):
    repo = tmp_path / "python-demo"
    repo.mkdir()
    (repo / "README.md").write_text("# Python Demo\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='python-demo'\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "python_demo").mkdir()
    (repo / "src" / "python_demo" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "src" / "python_demo" / "cli.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_cli.py").write_text("def test_cli():\n    assert True\n", encoding="utf-8")

    analysis = analyze_repository(repo)

    assert analysis.primary_language == "python"
    assert analysis.repo_kind == "python_package"
    assert "src" in analysis.source_entries
    assert "tests" in analysis.test_entries
    assert "pyproject.toml" in analysis.config_files
    assert any("README.md" in candidate for candidate in analysis.entrypoint_candidates)
    assert any("src/python_demo/cli.py" in candidate for candidate in analysis.entrypoint_candidates)
    assert analysis.evidence_strength["tests"] == "strong"


def test_analyze_ts_repo_detects_workspace_and_stack_signals(tmp_path):
    repo = tmp_path / "ts-demo"
    repo.mkdir()
    (repo / "README.md").write_text("# TS Demo\n", encoding="utf-8")
    (repo / "package.json").write_text('{"name":"ts-demo","scripts":{"build":"tsc"}}', encoding="utf-8")
    (repo / "tsconfig.json").write_text('{"compilerOptions":{"target":"ES2022"}}', encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "index.ts").write_text("export function boot() { return 'ok'; }\n", encoding="utf-8")
    (repo / "apps").mkdir()
    (repo / "apps" / "web").mkdir()
    (repo / "apps" / "web" / "main.ts").write_text("console.log('web');\n", encoding="utf-8")

    analysis = analyze_repository(repo)

    assert analysis.primary_language == "typescript"
    assert analysis.repo_kind == "node_typescript"
    assert "src" in analysis.source_entries
    assert "apps" in analysis.source_entries
    assert "package.json" in analysis.config_files
    assert "tsconfig.json" in analysis.config_files
    assert analysis.tooling_signals["package_manager"] == "npm-compatible"
    assert any(candidate.endswith("src/index.ts") for candidate in analysis.entrypoint_candidates)


def test_analyze_repository_builds_code_anchor_chains_for_python_repo(tmp_path):
    repo = tmp_path / "python-chain-demo"
    repo.mkdir()
    (repo / "README.md").write_text("# Python Chain Demo\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='python-chain-demo'\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "python_chain_demo").mkdir()
    (repo / "src" / "python_chain_demo" / "cli.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    (repo / "src" / "python_chain_demo" / "service.py").write_text("def run():\n    return 'ok'\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_cli.py").write_text("def test_cli():\n    assert True\n", encoding="utf-8")

    analysis = analyze_repository(repo)

    assert analysis.code_anchor_details
    assert isinstance(analysis.code_anchor_details[0], CodeAnchorChain)
    primary_chain = analysis.code_anchor_details[0]
    assert primary_chain.entry_anchor == "src/python_chain_demo/cli.py"
    assert primary_chain.test_anchor == "tests/test_cli.py"
    assert primary_chain.config_anchor == "pyproject.toml"

    chain_text = "\n".join(analysis.code_anchor_chains)
    assert "README.md" in chain_text
    assert "src/python_chain_demo/cli.py" in chain_text
    assert "tests/test_cli.py" in chain_text


def test_analyze_repository_prefers_service_anchor_when_present(tmp_path):
    repo = tmp_path / "python-service-anchor"
    repo.mkdir()
    (repo / "README.md").write_text("# Python Service Anchor\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='python-service-anchor'\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "python_service_anchor").mkdir()
    (repo / "src" / "python_service_anchor" / "cli.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    (repo / "src" / "python_service_anchor" / "service.py").write_text("def run():\n    return 'ok'\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_service.py").write_text("def test_service():\n    assert True\n", encoding="utf-8")

    analysis = analyze_repository(repo)

    assert any(chain.implementation_anchor == "src/python_service_anchor/service.py" for chain in analysis.code_anchor_details)


def test_analyze_repository_distinguishes_workspace_app_and_shared_anchors(tmp_path):
    repo = tmp_path / "workspace-anchor-demo"
    repo.mkdir()
    (repo / "README.md").write_text("# Workspace Anchor Demo\n", encoding="utf-8")
    (repo / "package.json").write_text(
        '{"name":"workspace-anchor-demo","workspaces":["apps/*","packages/*"],"scripts":{"build":"tsc","dev":"vite"}}',
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
    (repo / "tests" / "web.test.ts").write_text("it('web',()=>{})\n", encoding="utf-8")

    analysis = analyze_repository(repo)

    assert any(chain.chain_kind == "workspace_app" for chain in analysis.code_anchor_details)
    assert any(chain.chain_kind == "workspace_shared" for chain in analysis.code_anchor_details)
