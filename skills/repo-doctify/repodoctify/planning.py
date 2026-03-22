from __future__ import annotations

from .analysis import RepositoryAnalysis
from .models import DocsetPlan


DOC_BLUEPRINTS = (
    ("homepage", "学习首页", "homepage"),
    ("overview", "这个仓库到底在做什么", "overview"),
    ("code-reading-path", "第一次读仓应该先抓哪条主链", "main_chain"),
    ("stack-and-entrypoints", "入口、运行方式和技术栈怎么看", "stack"),
    ("bridge-topics", "哪些桥接机制最容易把人读晕", "bridge"),
    ("module-map", "核心目录和模块分别负责什么", "module_map"),
    ("evidence-guide", "判断行为和支持边界该看哪些证据", "boundary_guide"),
    ("development-guide", "第一次上手改功能该怎么下手", "development_guide"),
)


def build_default_docset_plan(analysis: RepositoryAnalysis) -> DocsetPlan:
    selected_ids = _select_document_ids(analysis)
    documents = [doc_id for doc_id, _, _ in DOC_BLUEPRINTS if doc_id in selected_ids]
    document_titles = {doc_id: title for doc_id, title, _ in DOC_BLUEPRINTS if doc_id in selected_ids}
    document_roles = {doc_id: role for doc_id, _, role in DOC_BLUEPRINTS if doc_id in selected_ids}
    reading_routes = {
        "30 分钟建立主心智模型": _filter_existing(
            documents,
            ["homepage", "overview", "code-reading-path", "stack-and-entrypoints"],
        ),
        "准备开始维护或接手": _filter_existing(
            documents,
            ["homepage", "overview", "module-map", "development-guide"],
        ),
        "开始排查问题和判断边界": _filter_existing(
            documents,
            ["overview", "module-map", "evidence-guide", "bridge-topics"],
        ),
        "准备新增功能或扩规则": _filter_existing(
            documents,
            ["overview", "code-reading-path", "module-map", "development-guide"],
        ),
    }
    if not analysis.test_entries:
        reading_routes["开始排查问题和判断边界"] = _filter_existing(
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
    if analysis.primary_language in {"python", "typescript", "javascript", "go", "rust", "java"}:
        selected.add("stack-and-entrypoints")
    if analysis.primary_language in {"go", "rust", "java"}:
        selected.add("bridge-topics")
    if analysis.primary_language == "python" and (
        complexity_score >= 6 or analysis.test_entries or analysis.docs_entries or len(analysis.entrypoint_candidates) >= 3
    ):
        selected.add("bridge-topics")
    if complexity_score >= 8:
        selected.add("bridge-topics")
    return selected


def _filter_existing(documents: list[str], candidates: list[str]) -> list[str]:
    available = set(documents)
    return [doc_id for doc_id in candidates if doc_id in available]
