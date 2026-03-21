from __future__ import annotations

from .analysis import RepositoryAnalysis
from .models import DocumentSpec, DocsetPlan, SectionNode


def compose_docset(analysis: RepositoryAnalysis, plan: DocsetPlan) -> list[DocumentSpec]:
    docs = {
        "homepage": _compose_homepage(analysis),
        "overview": _compose_overview(analysis),
        "code-reading-path": _compose_code_reading_path(analysis),
        "module-map": _compose_module_map(analysis),
        "evidence-guide": _compose_evidence_guide(analysis),
        "development-guide": _compose_development_guide(analysis),
    }
    ordered_docs = [docs[doc_id] for doc_id in plan.documents]
    _attach_next_reads(ordered_docs)
    return ordered_docs


def _compose_homepage(analysis: RepositoryAnalysis) -> DocumentSpec:
    sections = [
        SectionNode(
            kind="paragraph",
            title="Why This Docset Exists",
            body=[
                f"This docset helps a first-time reader build a working mental model for `{analysis.profile.repo_label}`.",
                "It is organized by learning obstacles instead of raw directory order.",
            ],
        ),
        SectionNode(
            kind="numbered_list",
            title="Recommended Reading Routes",
            body=[
                "30-minute orientation: overview -> code-reading-path -> module-map",
                "First-day maintenance: overview -> module-map -> development-guide",
                "Problem localization: overview -> evidence-guide -> module-map",
            ],
        ),
        SectionNode(
            kind="summary",
            title="Source Authority",
            body=analysis.profile.source_authority_notes,
        ),
    ]
    return DocumentSpec(
        doc_id="homepage",
        title="Homepage",
        role="homepage",
        question_answered="Where should a new reader start, and which route fits their goal?",
        target_reader="A developer opening the repository for the first time.",
        sections=sections,
    )


def _compose_overview(analysis: RepositoryAnalysis) -> DocumentSpec:
    sections = [
        SectionNode(
            kind="paragraph",
            title="Repository Identity",
            body=[
                f"Repository label: `{analysis.profile.repo_label}`.",
                f"Primary audience: {analysis.profile.primary_audience or 'Not specified'}.",
                (
                    f"Public locator: {analysis.profile.public_locator}."
                    if analysis.profile.public_locator
                    else "Public locator is not provided yet, so local structure remains the main locator."
                ),
            ],
        ),
        SectionNode(
            kind="numbered_list",
            title="Top-Level Directories",
            body=_numbered_directory_lines(analysis.top_level_directories),
        ),
        SectionNode(
            kind="numbered_list",
            title="Top-Level Files",
            body=_numbered_file_lines(analysis.top_level_files),
        ),
    ]
    return DocumentSpec(
        doc_id="overview",
        title="Overview",
        role="overview",
        question_answered="What kind of repository is this, and what are its main surfaces?",
        target_reader="A reader who needs the repository's shape before diving into details.",
        sections=sections,
    )


def _compose_code_reading_path(analysis: RepositoryAnalysis) -> DocumentSpec:
    reading_order: list[str] = []
    if analysis.readme_files:
        reading_order.extend(
            f"Start with `{name}` to capture the repository contract." for name in analysis.readme_files
        )
    reading_order.extend(
        f"Read `{name}` next to understand the primary implementation surface."
        for name in analysis.source_entries
    )
    reading_order.extend(
        f"Use `{name}` to verify intended behavior and edge cases."
        for name in analysis.test_entries
    )
    reading_order.extend(
        f"Check `{name}` to understand runtime and packaging assumptions."
        for name in analysis.config_files
    )
    if not reading_order:
        reading_order.append("Start from the top-level tree because no strong entrypoint signal was detected.")

    sections = [
        SectionNode(
            kind="numbered_list",
            title="Start With These Files",
            body=reading_order,
        ),
        SectionNode(
            kind="paragraph",
            title="How To Read The Main Chain",
            body=[
                "Follow the human-facing entrypoint first, then the main source directory, then tests, then config.",
                "That order keeps the conceptual contract ahead of implementation details.",
            ],
        ),
    ]
    return DocumentSpec(
        doc_id="code-reading-path",
        title="Code Reading Path",
        role="main_chain",
        question_answered="Which files should a new maintainer read first, and in what order?",
        target_reader="A developer trying to build a correct reading sequence quickly.",
        sections=sections,
    )


def _compose_module_map(analysis: RepositoryAnalysis) -> DocumentSpec:
    sections = [
        SectionNode(
            kind="numbered_list",
            title="Directories Worth Mapping",
            body=_module_lines(analysis),
        ),
        SectionNode(
            kind="paragraph",
            title="How To Use This Map",
            body=[
                "Treat each directory as a responsibility surface, not just a storage location.",
                "If a change spans multiple surfaces here, it probably crosses a boundary worth documenting in the final docset.",
            ],
        ),
    ]
    return DocumentSpec(
        doc_id="module-map",
        title="Module Map",
        role="module_map",
        question_answered="Which top-level modules likely own the main responsibilities?",
        target_reader="A reader who needs to localize ownership before editing code.",
        sections=sections,
    )


def _compose_evidence_guide(analysis: RepositoryAnalysis) -> DocumentSpec:
    evidence_lines: list[str] = []
    evidence_lines.extend(f"`{name}` is a documentation source." for name in analysis.readme_files)
    evidence_lines.extend(f"`{name}` is a test evidence source." for name in analysis.test_entries)
    evidence_lines.extend(f"`{name}` is a config evidence source." for name in analysis.config_files)
    evidence_lines.extend(f"`{name}` is a supplemental docs source." for name in analysis.docs_entries)
    if not evidence_lines:
        evidence_lines.append("Repository layout is currently the main evidence source.")

    sections = [
        SectionNode(
            kind="numbered_list",
            title="Evidence Sources",
            body=evidence_lines,
        ),
        SectionNode(
            kind="paragraph",
            title="How To Validate Assumptions",
            body=[
                "Prefer tests over comments when they disagree.",
                "Prefer top-level configs over ad-hoc script assumptions when runtime behavior is unclear.",
            ],
        ),
    ]
    return DocumentSpec(
        doc_id="evidence-guide",
        title="Evidence Guide",
        role="boundary_guide",
        question_answered="Which artifacts provide the strongest evidence when you are unsure how the repo behaves?",
        target_reader="A maintainer verifying assumptions before debugging or changing behavior.",
        sections=sections,
    )


def _compose_development_guide(analysis: RepositoryAnalysis) -> DocumentSpec:
    sections = [
        SectionNode(
            kind="numbered_list",
            title="Safe First Steps",
            body=[
                "Read the overview and code-reading-path docs before opening deep modules.",
                "Use the module map to choose the smallest ownership surface for your change.",
                "Use tests and configs as the final check before treating an assumption as stable.",
            ],
        ),
        SectionNode(
            kind="paragraph",
            title="Change Risk Signals",
            body=[
                (
                    f"Changes touching `{', '.join(analysis.source_entries)}` and `{', '.join(analysis.test_entries)}` together "
                    "are likely cross-boundary edits."
                    if analysis.source_entries and analysis.test_entries
                    else "Cross-directory changes usually signal higher coordination cost."
                ),
                "If you cannot explain which doc in this set should change alongside code, the code change probably needs more analysis first.",
            ],
        ),
    ]
    return DocumentSpec(
        doc_id="development-guide",
        title="Development Guide",
        role="development_guide",
        question_answered="How should a first-time maintainer start making safe changes?",
        target_reader="A developer preparing to add features or fix bugs.",
        sections=sections,
    )


def _attach_next_reads(documents: list[DocumentSpec]) -> None:
    titles = [document.title for document in documents]
    for index, document in enumerate(documents):
        document.next_reads = titles[index + 1 : index + 3]


def _numbered_directory_lines(directories: list[str]) -> list[str]:
    if not directories:
        return ["No top-level directories were detected."]
    return [f"`{name}` is a top-level directory that deserves triage." for name in directories]


def _numbered_file_lines(files: list[str]) -> list[str]:
    if not files:
        return ["No top-level files were detected."]
    return [f"`{name}` is a top-level file that may define repository behavior." for name in files]


def _module_lines(analysis: RepositoryAnalysis) -> list[str]:
    lines: list[str] = []
    for name in analysis.source_entries:
        lines.append(f"`{name}` looks like the primary source surface.")
    for name in analysis.test_entries:
        lines.append(f"`{name}` anchors executable behavior checks.")
    for name in analysis.docs_entries:
        lines.append(f"`{name}` supplements the learning surface with written documentation.")
    remainder = [
        name
        for name in analysis.top_level_directories
        if name not in set(analysis.source_entries + analysis.test_entries + ["docs"])
    ]
    for name in remainder:
        lines.append(f"`{name}` is an additional top-level directory that may hold tooling or support code.")
    if not lines:
        lines.append("No stable top-level module boundaries were detected yet.")
    return lines
