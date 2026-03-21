import json

from repodoctify.markdown_renderer import render_markdown_docset
from repodoctify.models import DocumentSpec, RepositoryProfile, SectionNode


def test_ir_models_capture_basic_docset_structure():
    profile = RepositoryProfile(repo_label="demo", source_path="/tmp/demo")
    section = SectionNode(kind="paragraph", title="Intro", body=["hello"])
    doc = DocumentSpec(doc_id="overview", title="Overview", role="overview", sections=[section])
    assert profile.repo_label == "demo"
    assert doc.sections[0].kind == "paragraph"


def test_markdown_renderer_emits_split_docs_and_readme():
    docs = [
        DocumentSpec(
            doc_id="overview",
            title="Overview",
            role="overview",
            sections=[SectionNode(kind="paragraph", title="Intro", body=["hello"])],
        )
    ]
    result = render_markdown_docset(
        RepositoryProfile(repo_label="demo", source_path="/tmp/demo"),
        docs,
    )
    assert "README.md" in result.files
    assert "overview.md" in result.files
    assert "manifest.json" in result.files
    assert "Overview" in result.files["README.md"]
    manifest = json.loads(result.files["manifest.json"])
    assert manifest["documents"][0]["title"] == "Overview"

