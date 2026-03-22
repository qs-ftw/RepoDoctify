from __future__ import annotations

import json
from dataclasses import dataclass

from .manifest import build_docset_manifest
from .models import DocumentSpec, RepositoryProfile, SectionNode
from .utils import slugify


@dataclass(slots=True)
class MarkdownRenderResult:
    files: dict[str, str]
    manifest: dict


def _render_section_markdown(section: SectionNode) -> str:
    lines: list[str] = []
    if section.title:
        lines.append(f"## {section.title}")
        lines.append("")

    if section.kind == "paragraph":
        lines.extend(section.body)
        lines.append("")
        return "\n".join(lines).rstrip()

    if section.kind == "numbered_list":
        for index, item in enumerate(section.body, start=1):
            lines.append(f"{index}. {item}")
        lines.append("")
        return "\n".join(lines).rstrip()

    if section.kind == "comparison_table":
        headers = section.metadata.get("headers", [])
        rows = section.metadata.get("rows", [])
        if headers:
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for row in rows:
                lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
            lines.append("")
        return "\n".join(lines).rstrip()

    if section.kind == "code_anchor":
        lang = section.metadata.get("language", "text")
        lines.append(f"```{lang}")
        lines.extend(section.body)
        lines.append("```")
        lines.append("")
        return "\n".join(lines).rstrip()

    if section.kind == "mermaid":
        lines.append("```mermaid")
        lines.extend(section.body)
        lines.append("```")
        lines.append("")
        return "\n".join(lines).rstrip()

    if section.kind in {"callout", "summary"}:
        lines.extend([f"> {line}" for line in section.body])
        lines.append("")
        return "\n".join(lines).rstrip()

    lines.extend(section.body)
    lines.append("")
    return "\n".join(lines).rstrip()


def _render_document_markdown(document: DocumentSpec) -> str:
    parts = [f"# {document.title}", ""]
    if document.question_answered:
        parts.extend([document.question_answered, ""])
    for section in document.sections:
        rendered = _render_section_markdown(section)
        if rendered:
            parts.extend([rendered, ""])
    if document.next_reads:
        parts.extend(["## Next Read", ""])
        for index, item in enumerate(document.next_reads, start=1):
            parts.append(f"{index}. {item}")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"
def _render_readme(profile: RepositoryProfile, docs: list[DocumentSpec]) -> str:
    lines = [f"# {profile.repo_label}", "", "## Document Inventory", ""]
    for doc in docs:
        lines.append(f"- [{doc.title}]({slugify(doc.doc_id)}.md) ({doc.role})")
    lines.append("")
    return "\n".join(lines)


def render_markdown_docset(
    profile: RepositoryProfile,
    docs: list[DocumentSpec],
) -> MarkdownRenderResult:
    files: dict[str, str] = {}
    for document in docs:
        files[f"{slugify(document.doc_id)}.md"] = _render_document_markdown(document)
    manifest = build_docset_manifest(profile, docs)
    files["README.md"] = _render_readme(profile, docs)
    files["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    return MarkdownRenderResult(files=files, manifest=manifest)
