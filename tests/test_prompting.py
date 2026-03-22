import json

from repodoctify.analysis import analyze_repository
from repodoctify.planning import build_default_docset_plan
from repodoctify.prompting import build_prompt_bundle
from repodoctify.runtime import COMMAND_FEISHU, COMMAND_HTML, COMMAND_RENDER_MD


def _make_repo(tmp_path):
    repo = tmp_path / "prompt-demo"
    repo.mkdir()
    (repo / "README.md").write_text("# Prompt Demo\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='prompt-demo'\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_main():\n    assert True\n", encoding="utf-8")
    return repo


def test_markdown_prompt_bundle_describes_model_authored_generation(tmp_path):
    repo = _make_repo(tmp_path)
    analysis = analyze_repository(repo)
    plan = build_default_docset_plan(analysis)

    bundle = build_prompt_bundle(
        analysis=analysis,
        plan=plan,
        command=COMMAND_RENDER_MD,
        workspace=tmp_path / "workspace",
    )

    packet = json.loads(bundle.files["packet.json"])
    brief = bundle.files["authoring-brief.md"]
    contract = json.loads(bundle.files["md-output-contract.json"])
    targets = json.loads(bundle.files["write-targets.json"])
    doc_prompts = json.loads(bundle.files["document-prompts.json"])

    assert packet["mode"] == "md"
    assert "references/markdown-rendering-rules.md" in packet["references"]
    assert "Do not let Python helper code synthesize document prose." in packet["non_goals"]
    assert packet["output_root"].endswith("/output/md")
    assert packet["execution_controls"]["one_shot_required"] is True
    assert packet["execution_controls"]["must_complete_all_targets_in_single_run"] is True
    assert packet["execution_controls"]["max_additional_reads_after_budget_exhausted"] == 0
    assert packet["execution_controls"]["preferred_write_mechanism"] == "single_multi_file_apply_patch"
    assert packet["execution_controls"]["preferred_verification_mode"] == "single_bulk_file_existence_check"
    assert packet["reading_budget"]["max_additional_file_reads"] <= 10
    assert packet["reading_budget"]["priority_paths"]
    assert "Generate the docset content yourself" in brief
    assert "Write the output files one at a time" in brief
    assert "Do not glob-read every source file" in brief
    assert "Do not stop after writing only homepage" in brief
    assert "single multi-file `apply_patch`" in brief
    assert "bulk existence check" in brief
    assert "src/app.py" in brief
    assert contract["documents"]
    assert contract["documents"][0]["doc_id"] == plan.documents[0]
    assert targets["mode"] == "md"
    assert targets["targets"][0]["path"].endswith("/output/md/manifest.json")
    assert targets["verification"]["preferred_pattern"] == "single_multi_file_apply_patch_then_bulk_check"
    assert "test -f" in targets["verification"]["bulk_exists_command"]
    assert any(item["path"].endswith("/output/md/README.md") for item in targets["targets"])
    assert any(item["path"].endswith("/output/md/homepage.md") for item in targets["targets"])
    assert doc_prompts["mode"] == "md"
    assert any(item["doc_id"] == "homepage" for item in doc_prompts["documents"])
    homepage_prompt = next(item for item in doc_prompts["documents"] if item["doc_id"] == "homepage")
    assert "required_sections" in homepage_prompt
    assert "evidence_paths" in homepage_prompt
    assert "must_include_paths" in homepage_prompt
    assert "seed_points" in homepage_prompt
    assert homepage_prompt["required_sections"]
    assert homepage_prompt["evidence_paths"]
    assert homepage_prompt["must_include_paths"]
    assert homepage_prompt["seed_points"]


def test_html_prompt_bundle_includes_html_rules(tmp_path):
    repo = _make_repo(tmp_path)
    analysis = analyze_repository(repo)
    plan = build_default_docset_plan(analysis)

    bundle = build_prompt_bundle(
        analysis=analysis,
        plan=plan,
        command=COMMAND_HTML,
        workspace=tmp_path / "workspace",
    )

    packet = json.loads(bundle.files["packet.json"])
    assert packet["mode"] == "html"
    assert "references/html-rendering-rules.md" in packet["references"]
    assert "html/index.html" in packet["expected_outputs"]


def test_feishu_prompt_bundle_includes_feishu_handoff_rules(tmp_path):
    repo = _make_repo(tmp_path)
    analysis = analyze_repository(repo)
    plan = build_default_docset_plan(analysis)

    bundle = build_prompt_bundle(
        analysis=analysis,
        plan=plan,
        command=COMMAND_FEISHU,
        workspace=tmp_path / "workspace",
    )

    packet = json.loads(bundle.files["packet.json"])
    brief = bundle.files["authoring-brief.md"]

    assert packet["mode"] == "feishu"
    assert "references/feishu-rendering-handoff.md" in packet["references"]
    assert "Treat `lark-mcp` as the connectivity layer only" in brief


def test_reading_budget_falls_back_to_priority_files_for_flat_python_repo(tmp_path):
    repo = tmp_path / "flat-python-demo"
    repo.mkdir()
    (repo / "engine.py").write_text("def run():\n    return 'ok'\n", encoding="utf-8")
    (repo / "gpt.py").write_text("class GPT:\n    pass\n", encoding="utf-8")
    (repo / "dataset.py").write_text("def load():\n    return []\n", encoding="utf-8")
    (repo / "tokenizer.py").write_text("def get_tokenizer():\n    return None\n", encoding="utf-8")

    analysis = analyze_repository(repo)
    plan = build_default_docset_plan(analysis)
    bundle = build_prompt_bundle(
        analysis=analysis,
        plan=plan,
        command=COMMAND_RENDER_MD,
        workspace=tmp_path / "workspace",
    )

    packet = json.loads(bundle.files["packet.json"])
    assert packet["reading_budget"]["repo_shape"] == "flat_repo"
    assert packet["reading_budget"]["priority_paths"]
    assert "engine.py" in packet["reading_budget"]["priority_paths"]
