from __future__ import annotations

from .analysis import RepositoryAnalysis
from .models import DocsetPlan


DOC_BLUEPRINTS = (
    ("homepage", "Homepage", "homepage"),
    ("overview", "Overview", "overview"),
    ("code-reading-path", "Code Reading Path", "main_chain"),
    ("stack-and-entrypoints", "Stack And Entrypoints", "stack"),
    ("bridge-topics", "Bridge Topics", "bridge"),
    ("module-map", "Module Map", "module_map"),
    ("evidence-guide", "Evidence Guide", "boundary_guide"),
    ("development-guide", "Development Guide", "development_guide"),
)


def build_default_docset_plan(analysis: RepositoryAnalysis) -> DocsetPlan:
    selected_ids = _select_document_ids(analysis)
    documents = [doc_id for doc_id, _, _ in DOC_BLUEPRINTS if doc_id in selected_ids]
    document_titles = {doc_id: title for doc_id, title, _ in DOC_BLUEPRINTS if doc_id in selected_ids}
    document_roles = {doc_id: role for doc_id, _, role in DOC_BLUEPRINTS if doc_id in selected_ids}
    reading_routes = {
        "30-minute orientation": _filter_existing(
            documents,
            ["homepage", "overview", "code-reading-path", "stack-and-entrypoints"],
        ),
        "first-day maintenance": _filter_existing(
            documents,
            ["homepage", "overview", "module-map", "development-guide"],
        ),
        "problem localization": _filter_existing(
            documents,
            ["overview", "module-map", "evidence-guide", "bridge-topics"],
        ),
        "feature development": _filter_existing(
            documents,
            ["overview", "code-reading-path", "module-map", "development-guide"],
        ),
    }
    if not analysis.test_entries:
        reading_routes["problem localization"] = _filter_existing(
            documents,
            ["overview", "module-map", "development-guide"],
        )
    return DocsetPlan(
        documents=documents,
        document_titles=document_titles,
        document_roles=document_roles,
        reading_routes=reading_routes,
        readme_aggregation_strategy="homepage_plus_doc_inventory",
    )


def _select_document_ids(analysis: RepositoryAnalysis) -> set[str]:
    complexity_score = 0
    complexity_score += len(analysis.top_level_directories)
    complexity_score += len(analysis.source_entries)
    complexity_score += len(analysis.test_entries)
    complexity_score += 1 if analysis.docs_entries else 0
    complexity_score += 1 if analysis.tooling_signals.get("workspace_layout") == "monorepo" else 0
    complexity_score += 1 if len(analysis.entrypoint_candidates) >= 4 else 0

    selected = {"homepage", "overview", "code-reading-path", "module-map", "development-guide"}
    if analysis.test_entries or analysis.config_files or analysis.docs_entries:
        selected.add("evidence-guide")
    if analysis.primary_language in {"python", "typescript", "javascript"}:
        selected.add("stack-and-entrypoints")
    if complexity_score >= 8:
        selected.add("bridge-topics")
    return selected


def _filter_existing(documents: list[str], candidates: list[str]) -> list[str]:
    available = set(documents)
    return [doc_id for doc_id in candidates if doc_id in available]
