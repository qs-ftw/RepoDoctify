from __future__ import annotations

from dataclasses import dataclass
from html import escape

from .models import DocumentSpec, RepositoryProfile, SectionNode
from .utils import slugify


@dataclass(slots=True)
class HtmlRenderResult:
    files: dict[str, str]


def _paragraphs(body: list[str]) -> str:
    return "\n".join(f"<p>{escape(line)}</p>" for line in body)


def _render_section_html(section: SectionNode) -> str:
    chunks: list[str] = []
    if section.title:
        chunks.append(f"<h2>{escape(section.title)}</h2>")

    if section.kind == "paragraph":
        chunks.append(_paragraphs(section.body))
        return "\n".join(chunks)

    if section.kind == "numbered_list":
        items = "".join(f"<li>{escape(item)}</li>" for item in section.body)
        chunks.append(f"<ol>{items}</ol>")
        return "\n".join(chunks)

    if section.kind == "comparison_table":
        headers = section.metadata.get("headers", [])
        rows = section.metadata.get("rows", [])
        if headers:
            thead = "".join(f"<th>{escape(str(header))}</th>" for header in headers)
            tbody = "".join(
                "<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>"
                for row in rows
            )
            chunks.append(f"<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>")
        return "\n".join(chunks)

    if section.kind == "code_anchor":
        lang = escape(str(section.metadata.get("language", "text")))
        code = escape("\n".join(section.body))
        chunks.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
        return "\n".join(chunks)

    if section.kind == "mermaid":
        code = escape("\n".join(section.body))
        chunks.append(f'<pre><code class="language-mermaid">{code}</code></pre>')
        return "\n".join(chunks)

    if section.kind in {"callout", "summary"}:
        chunks.append(f'<aside>{"".join(f"<p>{escape(line)}</p>" for line in section.body)}</aside>')
        return "\n".join(chunks)

    chunks.append(_paragraphs(section.body))
    return "\n".join(chunks)


def _render_document_html(document: DocumentSpec) -> str:
    sections = "\n".join(_render_section_html(section) for section in document.sections)
    question = f"<p>{escape(document.question_answered)}</p>" if document.question_answered else ""
    next_reads = ""
    if document.next_reads:
        items = "".join(f"<li>{escape(item)}</li>" for item in document.next_reads)
        next_reads = f"<section><h2>Next Read</h2><ol>{items}</ol></section>"
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>"
        + escape(document.title)
        + "</title></head><body>"
        + f'<nav><a href="index.html">Home</a></nav>'
        + f"<h1>{escape(document.title)}</h1>"
        + question
        + sections
        + next_reads
        + "</body></html>\n"
    )


def render_html_docset(
    profile: RepositoryProfile,
    docs: list[DocumentSpec],
) -> HtmlRenderResult:
    files: dict[str, str] = {}
    for document in docs:
        files[f"{slugify(document.doc_id)}.html"] = _render_document_html(document)

    links = "".join(
        f'<li><a href="{slugify(doc.doc_id)}.html">{escape(doc.title)}</a> ({escape(doc.role)})</li>'
        for doc in docs
    )
    files["index.html"] = (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>"
        + escape(profile.repo_label)
        + "</title></head><body>"
        + f"<h1>{escape(profile.repo_label)}</h1>"
        + "<h2>Document Inventory</h2>"
        + f"<ul>{links}</ul>"
        + "</body></html>\n"
    )
    return HtmlRenderResult(files=files)
