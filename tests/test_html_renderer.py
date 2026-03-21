from repodoctify.html_renderer import render_html_docset
from repodoctify.models import DocumentSpec, RepositoryProfile, SectionNode


def test_html_renderer_emits_index_and_doc_pages():
    docs = [
        DocumentSpec(
            doc_id="overview",
            title="Overview",
            role="overview",
            sections=[SectionNode(kind="paragraph", title="Intro", body=["hello"])],
        )
    ]
    result = render_html_docset(
        RepositoryProfile(repo_label="demo", source_path="/tmp/demo"),
        docs,
    )
    assert "index.html" in result.files
    assert "overview.html" in result.files
    assert "Overview" in result.files["index.html"]
    assert 'href="overview.html"' in result.files["index.html"]


def test_html_renderer_escapes_content():
    docs = [
        DocumentSpec(
            doc_id="overview",
            title="Overview",
            role="overview",
            sections=[SectionNode(kind="paragraph", title="Intro", body=["<unsafe>"])],
        )
    ]
    result = render_html_docset(
        RepositoryProfile(repo_label="demo", source_path="/tmp/demo"),
        docs,
    )
    assert "&lt;unsafe&gt;" in result.files["overview.html"]

