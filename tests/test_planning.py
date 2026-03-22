from repodoctify.analysis import analyze_repository
from repodoctify.planning import build_default_docset_plan


def test_planner_adapts_doc_count_for_small_repo(tmp_path):
    repo = tmp_path / "small-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Small Repo\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "main.py").write_text("def main():\n    return 1\n", encoding="utf-8")

    analysis = analyze_repository(repo)
    plan = build_default_docset_plan(analysis)

    assert 4 <= len(plan.documents) <= 6
    assert "homepage" in plan.documents
    assert "overview" in plan.documents


def test_planner_expands_for_more_complex_repo(tmp_path):
    repo = tmp_path / "complex-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Complex Repo\n", encoding="utf-8")
    (repo / "package.json").write_text('{"name":"complex","workspaces":["apps/*","packages/*"]}', encoding="utf-8")
    (repo / "tsconfig.json").write_text("{}", encoding="utf-8")
    for dirname in ["apps", "packages", "docs", "tests", "scripts", "src"]:
        (repo / dirname).mkdir()
    (repo / "src" / "index.ts").write_text("export const x = 1;\n", encoding="utf-8")
    (repo / "tests" / "index.test.ts").write_text("it('x',()=>{});\n", encoding="utf-8")
    (repo / "docs" / "arch.md").write_text("# Arch\n", encoding="utf-8")

    analysis = analyze_repository(repo)
    plan = build_default_docset_plan(analysis)

    assert len(plan.documents) >= 7
    assert "evidence-guide" in plan.documents
    assert "development-guide" in plan.documents


def test_planner_keeps_doc_roles_and_titles_grounded(tmp_path):
    repo = tmp_path / "python-app"
    repo.mkdir()
    (repo / "README.md").write_text("# Python App\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='python-app'\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def boot():\n    return True\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_boot():\n    assert True\n", encoding="utf-8")

    analysis = analyze_repository(repo)
    plan = build_default_docset_plan(analysis)

    assert plan.document_titles["code-reading-path"] == "第一次读仓应该先抓哪条主链"
    assert plan.document_roles["overview"] == "overview"
    assert "code-reading-path" in plan.reading_routes["30 分钟建立主心智模型"]
