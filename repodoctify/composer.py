from __future__ import annotations

from .analysis import RepositoryAnalysis
from .models import CodeAnchorChain, DocumentSpec, DocsetPlan, SectionNode


def compose_docset(analysis: RepositoryAnalysis, plan: DocsetPlan) -> list[DocumentSpec]:
    docs = {
        "homepage": _compose_homepage(analysis),
        "overview": _compose_overview(analysis),
        "code-reading-path": _compose_code_reading_path(analysis),
        "stack-and-entrypoints": _compose_stack_and_entrypoints(analysis),
        "bridge-topics": _compose_bridge_topics(analysis),
        "module-map": _compose_module_map(analysis),
        "evidence-guide": _compose_evidence_guide(analysis),
        "development-guide": _compose_development_guide(analysis),
    }
    ordered_docs = [docs[doc_id] for doc_id in plan.documents]
    _attach_next_reads(ordered_docs)
    return ordered_docs


def _compose_homepage(analysis: RepositoryAnalysis) -> DocumentSpec:
    repo_summary = (
        f"`{analysis.profile.repo_label}` looks like a {analysis.repo_kind} with `{analysis.primary_language}` as the main language."
        if analysis.primary_language != "unknown"
        else f"`{analysis.profile.repo_label}` currently looks like a mixed or generic repository."
    )
    sections = [
        SectionNode(
            kind="paragraph",
            title="Why This Docset Exists",
            body=[
                f"This docset helps a first-time reader build a working mental model for `{analysis.profile.repo_label}`.",
                "It is organized by learning obstacles instead of raw directory order.",
                repo_summary,
            ],
        ),
        SectionNode(
            kind="numbered_list",
            title="Recommended Reading Routes",
            body=_homepage_routes(analysis),
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
    tech_stack_lines = _tech_stack_lines(analysis)
    sections = [
        SectionNode(
            kind="paragraph",
            title="Repository Identity",
            body=[
                f"Repository label: `{analysis.profile.repo_label}`.",
                f"Primary language: {analysis.primary_language}.",
                f"Repository kind: {analysis.repo_kind}.",
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
        SectionNode(
            kind="numbered_list",
            title="Tech Stack Signals",
            body=tech_stack_lines,
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
            f"Start with `{name}` to capture the repository contract and the human-facing why behind the code."
            for name in analysis.readme_files
        )
    reading_order.extend(
        f"Read `{name}` next to understand the primary implementation surface and where the real entrypoint hands control to source code."
        for name in analysis.entrypoint_candidates
        if name not in analysis.readme_files and name not in analysis.config_files
    )
    reading_order.extend(
        f"Use `{name}` to verify intended behavior, edge cases, and what change would count as a regression."
        for name in analysis.test_layout[:3]
    )
    reading_order.extend(
        f"Check `{name}` to understand runtime, packaging, and environment assumptions before you change behavior."
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
            kind="numbered_list",
            title="Follow These Chains",
            body=analysis.code_anchor_chains
            or ["Follow the strongest entrypoint, then its nearest test, because no higher-confidence call chain was detected."],
        ),
        SectionNode(
            kind="paragraph",
            title="How To Read The Main Chain",
            body=[
                "Follow the human-facing entrypoint first, then the main source directory, then tests, then config.",
                "That order keeps the conceptual contract ahead of implementation details.",
                "In practice, read files that explain why the repository exists before files that explain how each helper works.",
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


def _compose_stack_and_entrypoints(analysis: RepositoryAnalysis) -> DocumentSpec:
    sections = [
        SectionNode(
            kind="numbered_list",
            title="Primary Entrypoints",
            body=[
                f"`{path}` is a likely entrypoint or early reading anchor."
                for path in analysis.entrypoint_candidates[:6]
            ]
            or ["No strong entrypoint candidates were detected yet."],
        ),
        SectionNode(
            kind="numbered_list",
            title="Tooling And Runtime Signals",
            body=_tooling_lines(analysis),
        ),
    ]
    return DocumentSpec(
        doc_id="stack-and-entrypoints",
        title="Stack And Entrypoints",
        role="stack",
        question_answered="Which runtime and tooling signals define how this repository starts and builds?",
        target_reader="A reader who wants the fastest route to the practical startup surface.",
        sections=sections,
    )


def _compose_bridge_topics(analysis: RepositoryAnalysis) -> DocumentSpec:
    sections = [
        SectionNode(
            kind="numbered_list",
            title="Likely Bridge Topics",
            body=_bridge_topic_lines(analysis),
        ),
        SectionNode(
            kind="paragraph",
            title="Why These Topics Matter",
            body=[
                "These topics usually cut across directories or ownership boundaries.",
                "They often connect workspace layout, package scripts, source entrypoints, and test evidence rather than living in a single file.",
                _bridge_anchor_summary(analysis),
                "If the generated docset later grows deeper, these are strong candidates for standalone deep-dive docs.",
            ],
        ),
    ]
    return DocumentSpec(
        doc_id="bridge-topics",
        title="Bridge Topics",
        role="bridge",
        question_answered="Which cross-cutting concepts are likely to block first-time reading if left implicit?",
        target_reader="A maintainer who needs to identify hidden learning obstacles early.",
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
    evidence_lines.extend(f"`{name}` is a test evidence source." for name in analysis.test_layout[:4])
    evidence_lines.extend(f"`{name}` is a config evidence source." for name in analysis.config_files)
    evidence_lines.extend(f"`{name}` is a supplemental docs source." for name in analysis.docs_entries)
    evidence_lines.extend(
        f"`{key}` evidence is currently `{value}`."
        for key, value in analysis.evidence_strength.items()
        if value != "weak"
    )
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
                _evidence_anchor_summary(analysis),
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
                "If multiple entrypoint candidates exist, start with the most human-facing entrypoint before reading helper modules.",
                "Before editing code, decide which entrypoint, ownership surface, and tests should move together with the change.",
            ],
        ),
        SectionNode(
            kind="numbered_list",
            title="Change Chains To Follow",
            body=_development_anchor_lines(analysis)
            or ["Use the main entrypoint, its nearest implementation file, and the closest test as the first change boundary."],
        ),
        SectionNode(
            kind="paragraph",
            title="Change Risk Signals",
            body=[
                *_language_specific_change_risk_lines(analysis),
                (
                    f"Changes touching `{', '.join(analysis.source_entries)}` and `{', '.join(analysis.test_entries)}` together "
                    "are likely cross-boundary edits."
                    if analysis.source_entries and analysis.test_entries
                    else "Cross-directory changes usually signal higher coordination cost."
                ),
                "If you cannot explain which doc in this set should change alongside code, the code change probably needs more analysis first.",
                "A safe first implementation usually starts at the smallest ownership surface that can satisfy the change without widening the boundary.",
                "For debugging, start from the failing entrypoint or test anchor before widening the search into helpers.",
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
    for name in analysis.source_layout[:4]:
        lines.append(f"`{name}` is a concrete source file worth reading early.")
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


def _homepage_routes(analysis: RepositoryAnalysis) -> list[str]:
    routes = [
        "30-minute orientation: overview -> code-reading-path -> module-map",
        "First-day maintenance: overview -> module-map -> development-guide",
    ]
    if analysis.evidence_strength.get("tests") == "strong":
        routes.append("Problem localization: overview -> evidence-guide -> module-map")
    if analysis.primary_language in {"python", "typescript", "javascript", "go", "rust", "java"}:
        routes.append("Runtime familiarization: overview -> stack-and-entrypoints -> code-reading-path")
    return routes


def _tooling_lines(analysis: RepositoryAnalysis) -> list[str]:
    lines = [
        f"`{key}` suggests `{value}`."
        for key, value in sorted(analysis.tooling_signals.items())
    ]
    if not lines:
        lines.append("No strong tooling signals were detected yet.")
    return lines


def _tech_stack_lines(analysis: RepositoryAnalysis) -> list[str]:
    lines = [f"The main implementation language is `{analysis.primary_language}`."]
    lines.extend(_tooling_lines(analysis))
    return lines


def _bridge_topic_lines(analysis: RepositoryAnalysis) -> list[str]:
    topics: list[str] = []
    if analysis.tooling_signals.get("workspace_layout") == "monorepo":
        topics.append("Workspace boundaries and package ownership will matter across `apps/` and `packages/`.")
    if analysis.primary_language == "python":
        topics.append("Packaging and runtime entrypoints likely flow through `pyproject.toml`, CLI modules, and `src/`.")
    if analysis.primary_language in {"typescript", "javascript"}:
        topics.append("Build scripts, package scripts, and source entrypoints likely split responsibilities.")
    if analysis.primary_language == "go":
        topics.append("Go module boundaries likely flow through `go.mod`, `cmd/` entrypoints, and `internal/` ownership surfaces.")
    if analysis.primary_language == "rust":
        topics.append("Rust crate behavior likely splits between `Cargo.toml`, `src/main.rs`, `src/lib.rs`, and integration tests.")
    if analysis.primary_language == "java":
        topics.append("Java build and ownership boundaries likely split across Gradle or Maven config, `src/main/java`, and `src/test/java`.")
    if analysis.evidence_strength.get("tests") == "strong":
        topics.append("Tests are strong evidence and should be read when README and source disagree.")
    if analysis.docs_entries:
        topics.append("Written docs may explain architecture choices that are not obvious from entrypoint files alone.")
    if not topics:
        topics.append("Configuration and directory ownership are the two most likely bridge topics in this repository.")
    return topics


def _development_anchor_lines(analysis: RepositoryAnalysis) -> list[str]:
    lines: list[str] = []
    for chain in analysis.code_anchor_details[:3]:
        lines.append(_development_line_for_chain(chain))
    return lines


def _development_line_for_chain(chain: CodeAnchorChain) -> str:
    if chain.chain_kind == "workspace_shared":
        return (
            f"If the change touches shared logic, start from `{chain.implementation_anchor or chain.entry_anchor}`, "
            f"then confirm the change boundary with `{chain.test_anchor or chain.entry_anchor}`."
        )
    if chain.chain_kind == "workspace_app":
        return (
            f"If the bug shows up at app startup, debug from `{chain.entry_anchor}` first, then verify with "
            f"`{chain.test_anchor or chain.entry_anchor}` before widening the change boundary."
        )
    if chain.implementation_anchor and chain.test_anchor:
        return (
            f"For behavior changes, use `{chain.entry_anchor}` -> `{chain.implementation_anchor}` -> `{chain.test_anchor}` "
            "as the primary change boundary."
        )
    if chain.test_anchor:
        return (
            f"For debugging, start from `{chain.entry_anchor}` and confirm the behavior with `{chain.test_anchor}` "
            "before editing adjacent modules."
        )
    return f"Use `{chain.entry_anchor}` as the first anchor before widening the change boundary."


def _bridge_anchor_summary(analysis: RepositoryAnalysis) -> str:
    if any(chain.chain_kind == "workspace_shared" for chain in analysis.code_anchor_details):
        return "In workspace repos, the app entrypoint and shared package path should be treated as separate ownership surfaces."
    if analysis.primary_language == "go":
        return "In Go repos, `cmd/` entrypoints and `internal/` packages often define the first real ownership boundary."
    if analysis.primary_language == "rust":
        return "In Rust repos, the first useful bridge is usually between crate entrypoints, library modules, and regression tests."
    if analysis.primary_language == "java":
        return "In Java repos, source sets and build config usually matter more than single-file entrypoints."
    return "The strongest bridge topics usually sit between the main entrypoint, its implementation handoff, and the nearest test."


def _evidence_anchor_summary(analysis: RepositoryAnalysis) -> str:
    if analysis.code_anchor_details:
        return "When code anchors exist, treat the linked test anchor or regression anchor as the highest-priority evidence surface."
    return "When no code anchors are available, use tests and config files as the best available evidence surfaces."


def _language_specific_change_risk_lines(analysis: RepositoryAnalysis) -> list[str]:
    if analysis.primary_language == "go":
        return [
            "In Go repos, prefer changes that stay inside one `cmd/` entrypoint or one `internal/` package before widening the boundary."
        ]
    if analysis.primary_language == "rust":
        return [
            "In Rust repos, decide early whether the change belongs at the crate entrypoint, inside `src/lib.rs`, or in a narrower module."
        ]
    if analysis.primary_language == "java":
        return [
            "In Java repos, start by choosing the smallest source set boundary, usually `src/main/java` for behavior and `src/test/java` for regression proof."
        ]
    return []
