from __future__ import annotations

from .analysis import RepositoryAnalysis
from .models import DocsetPlan


DOC_BLUEPRINTS = (
    ("homepage", "Homepage", "homepage"),
    ("overview", "Overview", "overview"),
    ("code-reading-path", "Code Reading Path", "main_chain"),
    ("module-map", "Module Map", "module_map"),
    ("evidence-guide", "Evidence Guide", "boundary_guide"),
    ("development-guide", "Development Guide", "development_guide"),
)


def build_default_docset_plan(analysis: RepositoryAnalysis) -> DocsetPlan:
    documents = [doc_id for doc_id, _, _ in DOC_BLUEPRINTS]
    document_titles = {doc_id: title for doc_id, title, _ in DOC_BLUEPRINTS}
    document_roles = {doc_id: role for doc_id, _, role in DOC_BLUEPRINTS}
    reading_routes = {
        "30-minute orientation": ["homepage", "overview", "code-reading-path"],
        "first-day maintenance": ["homepage", "overview", "module-map", "development-guide"],
        "problem localization": ["overview", "module-map", "evidence-guide"],
        "feature development": ["overview", "code-reading-path", "module-map", "development-guide"],
    }
    if not analysis.test_entries:
        reading_routes["problem localization"] = ["overview", "module-map", "development-guide"]
    return DocsetPlan(
        documents=documents,
        document_titles=document_titles,
        document_roles=document_roles,
        reading_routes=reading_routes,
        readme_aggregation_strategy="homepage_plus_doc_inventory",
    )
