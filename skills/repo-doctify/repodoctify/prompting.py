from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from .analysis import RepositoryAnalysis
from .manifest import build_docset_manifest_from_plan
from .models import DocsetPlan


COMMAND_PLAN = "规划输出框架"
COMMAND_RENDER_MD = "以 md 形式输出全部内容"
COMMAND_HTML = "以 html 形式输出全部内容"
COMMAND_FEISHU = "以飞书形式输出全部内容"


@dataclass(slots=True)
class PromptBundle:
    packet: dict
    files: dict[str, str]


def build_prompt_bundle(
    *,
    analysis: RepositoryAnalysis,
    plan: DocsetPlan,
    command: str,
    workspace: Path,
) -> PromptBundle:
    mode_slug = _mode_slug(command)
    manifest = build_docset_manifest_from_plan(analysis.profile, plan)
    output_root = _output_root(workspace, command)
    write_targets = _build_write_targets(plan, command, output_root)
    document_prompts = _build_document_prompts(analysis, plan, command)
    packet = {
        "product": "RepoDoctify",
        "mode": mode_slug,
        "workspace": str(workspace),
        "output_root": str(output_root),
        "execution_controls": {
            "one_shot_required": command == COMMAND_RENDER_MD,
            "must_complete_all_targets_in_single_run": command == COMMAND_RENDER_MD,
            "max_additional_reads_after_budget_exhausted": 0 if command == COMMAND_RENDER_MD else 2,
            "preferred_write_mechanism": (
                "single_multi_file_apply_patch" if command == COMMAND_RENDER_MD else "per_target_file_write"
            ),
            "preferred_verification_mode": (
                "single_bulk_file_existence_check" if command == COMMAND_RENDER_MD else "per_target_check"
            ),
        },
        "reading_budget": _build_reading_budget(analysis),
        "language_policy": "follow_user_language_default_to_chinese_for_current_debug_round",
        "inputs": {
            "repository_analysis": "ir/repository-analysis.json",
            "docset_plan": "plan/docset-plan.json",
            "manifest": "artifacts/manifest.json",
            "output_contract": f"prompt/{mode_slug}-output-contract.json",
            "write_targets": "prompt/write-targets.json",
            "document_prompts": "prompt/document-prompts.json",
        },
        "references": _reference_paths(command),
        "expected_outputs": _expected_outputs(plan, command),
        "non_goals": [
            "Do not let Python helper code synthesize document prose.",
            "Do not invent repository behavior that is not grounded in actual files.",
            "Do not turn ordered reading advice into tables unless horizontal comparison is the point.",
        ],
        "authoring_rules": [
            "Generate content from repository evidence and the plan, not from canned text snippets.",
            "When a document mentions another generated document, add a real hyperlink in the target format.",
            "Use concrete file paths, entrypoints, tests, configs, and call chains instead of abstract filler statements.",
            "If evidence is weak or missing, say that explicitly and point the reader to the closest source of truth.",
        ],
        "manifest": manifest,
    }
    files = {
        "packet.json": json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
        "authoring-brief.md": _build_authoring_brief(packet, analysis, plan, command),
        "write-targets.json": json.dumps(write_targets, ensure_ascii=False, indent=2) + "\n",
        "document-prompts.json": json.dumps(document_prompts, ensure_ascii=False, indent=2) + "\n",
        f"{mode_slug}-output-contract.json": json.dumps(
            _build_output_contract(plan, command),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    }
    return PromptBundle(packet=packet, files=files)


def _mode_slug(command: str) -> str:
    if command == COMMAND_PLAN:
        return "plan"
    if command == COMMAND_HTML:
        return "html"
    if command == COMMAND_FEISHU:
        return "feishu"
    return "md"


def _reference_paths(command: str) -> list[str]:
    shared = [
        "references/repo-docset-framework.md",
        "references/docset-ir.md",
    ]
    if command == COMMAND_HTML:
        return shared + [
            "references/markdown-rendering-rules.md",
            "references/html-rendering-rules.md",
        ]
    if command == COMMAND_FEISHU:
        return shared + [
            "references/markdown-rendering-rules.md",
            "references/feishu-rendering-handoff.md",
            "references/feishu-runtime-model.md",
        ]
    if command == COMMAND_PLAN:
        return shared
    return shared + ["references/markdown-rendering-rules.md"]


def _expected_outputs(plan: DocsetPlan, command: str) -> list[str]:
    if command == COMMAND_PLAN:
        return ["plan/docset-plan.json"]
    if command == COMMAND_HTML:
        return ["html/index.html"] + [f"html/{doc_id}.html" for doc_id in plan.documents]
    if command == COMMAND_FEISHU:
        return [f"feishu:{doc_id}" for doc_id in plan.documents]
    return ["md/README.md", "md/manifest.json"] + [f"md/{doc_id}.md" for doc_id in plan.documents]


def _output_root(workspace: Path, command: str) -> Path:
    if command == COMMAND_HTML:
        return workspace / "output" / "html"
    if command == COMMAND_FEISHU:
        return workspace / "output" / "feishu"
    if command == COMMAND_PLAN:
        return workspace / "output" / "plan"
    return workspace / "output" / "md"


def _build_write_targets(plan: DocsetPlan, command: str, output_root: Path) -> dict:
    mode_slug = _mode_slug(command)
    if command == COMMAND_PLAN:
        return {
            "mode": mode_slug,
            "output_root": str(output_root),
            "targets": [],
        }
    targets: list[dict[str, str]] = []
    if command == COMMAND_RENDER_MD:
        targets.append({"kind": "manifest", "path": str(output_root / "manifest.json")})
        for doc_id in plan.documents:
            targets.append({"kind": "document", "doc_id": doc_id, "path": str(output_root / f"{doc_id}.md")})
        targets.append({"kind": "aggregate_readme", "path": str(output_root / "README.md")})
    elif command == COMMAND_HTML:
        targets.append({"kind": "index", "path": str(output_root / "index.html")})
        for doc_id in plan.documents:
            targets.append({"kind": "document", "doc_id": doc_id, "path": str(output_root / f"{doc_id}.html")})
    else:
        for doc_id in plan.documents:
            targets.append({"kind": "feishu_document", "doc_id": doc_id, "path": f"feishu:{doc_id}"})
    verification = {
        "per_target_rule": "After writing one target, confirm it exists before moving on.",
    }
    if command == COMMAND_RENDER_MD:
        file_paths = [target["path"] for target in targets]
        verification["preferred_pattern"] = "single_multi_file_apply_patch_then_bulk_check"
        verification["bulk_exists_command"] = " && ".join(f"test -f '{path}'" for path in file_paths)
        verification["expected_target_count"] = len(file_paths)
    return {
        "mode": mode_slug,
        "output_root": str(output_root),
        "targets": targets,
        "verification": verification,
    }


def _build_reading_budget(analysis: RepositoryAnalysis) -> dict:
    flat_repo = not analysis.top_level_directories and len(analysis.top_level_files) <= 24
    priority_paths: list[str] = []
    for path in analysis.readme_files:
        if path not in priority_paths:
            priority_paths.append(path)
    for path in analysis.entrypoint_candidates[:4]:
        if path not in priority_paths:
            priority_paths.append(path)
    for path in analysis.source_layout[:4]:
        if path not in priority_paths:
            priority_paths.append(path)
    for path in analysis.config_files[:2]:
        if path not in priority_paths:
            priority_paths.append(path)
    if not priority_paths:
        priority_paths.extend(_fallback_priority_paths(analysis))
    return {
        "repo_shape": "flat_repo" if flat_repo else "layered_repo",
        "max_additional_file_reads": 6 if flat_repo else 10,
        "priority_paths": priority_paths,
        "rules": [
            "Start from priority_paths before exploring anything else.",
            "Do not glob-read every source file.",
            "If the repository is flat, stop after the key chain is clear instead of sampling every module.",
        ],
    }


def _fallback_priority_paths(analysis: RepositoryAnalysis) -> list[str]:
    preferred_names_by_language = {
        "python": [
            "engine.py",
            "gpt.py",
            "dataloader.py",
            "dataset.py",
            "tokenizer.py",
            "checkpoint_manager.py",
            "common.py",
            "execution.py",
            "core_eval.py",
        ],
        "typescript": ["src/index.ts", "src/main.ts", "package.json", "tsconfig.json"],
        "javascript": ["src/index.js", "src/main.js", "package.json"],
        "go": ["main.go", "cmd/server/main.go", "go.mod"],
        "rust": ["src/main.rs", "src/lib.rs", "Cargo.toml"],
        "java": ["src/main/java/App.java", "pom.xml", "build.gradle"],
    }
    available = set(analysis.top_level_files) | set(analysis.source_layout) | set(analysis.entrypoint_candidates)
    fallback: list[str] = []
    for candidate in preferred_names_by_language.get(analysis.primary_language, []):
        if candidate in available and candidate not in fallback:
            fallback.append(candidate)
    for candidate in analysis.top_level_files[:6]:
        if candidate.endswith((".py", ".ts", ".js", ".go", ".rs", ".java")) and candidate not in fallback:
            fallback.append(candidate)
    return fallback[:6]


def _build_output_contract(plan: DocsetPlan, command: str) -> dict:
    mode_slug = _mode_slug(command)
    return {
        "mode": mode_slug,
        "documents": [
            {
                "doc_id": doc_id,
                "title": plan.document_titles[doc_id],
                "role": plan.document_roles[doc_id],
            }
            for doc_id in plan.documents
        ],
        "rules": [
            "Every output document must align with the declared doc_id and title.",
            "Use repository-relative paths when naming code anchors.",
            "Keep claims traceable to actual repository evidence.",
            "Cross-document mentions must be hyperlinkable in the output format.",
        ],
    }


def _doc_diagram(doc_id: str) -> dict | None:
    """Return diagram spec if this doc type requires a diagram, else None."""
    specs: dict[str, dict] = {
        "homepage": {
            "type": "mindmap",
            "after_section": "推荐阅读路线",
            "content": "All doc types in this docset as a reading route mindmap",
        },
        "module-map": {
            "type": "classDiagram",
            "after_section": "模块协作关系",
            "content": "Key modules, their responsibilities, and collaboration arrows",
        },
        "code-reading-path": {
            "type": "flowchart",
            "after_section": "主链概览",
            "content": "Primary code reading chain from entry to output",
        },
    }
    return specs.get(doc_id)


def _build_document_prompts(analysis: RepositoryAnalysis, plan: DocsetPlan, command: str) -> dict:
    return {
        "mode": _mode_slug(command),
        "documents": [
            {
                "doc_id": doc_id,
                "title": plan.document_titles[doc_id],
                "role": plan.document_roles[doc_id],
                "question_answered": _doc_question(doc_id),
                "required_sections": _doc_required_sections(doc_id),
                "evidence_paths": _doc_evidence_paths(doc_id, analysis),
                "must_include_paths": _doc_evidence_paths(doc_id, analysis)[:4],
                "seed_points": _doc_seed_points(doc_id, analysis),
                "cross_links": _doc_cross_links(doc_id, plan),
                "diagram": _doc_diagram(doc_id),
            }
            for doc_id in plan.documents
        ],
    }


def _doc_question(doc_id: str) -> str:
    return {
        "homepage": "这个仓库值不值得继续读，以及应该按什么顺序读。",
        "overview": "这个仓库到底解决什么问题、核心对象是什么、边界在哪里。",
        "code-reading-path": "第一次读仓最应该抓住哪几条主链，调用关系怎么串起来。",
        "stack-and-entrypoints": "这个仓库从哪里被调用、怎么运行、关键技术栈是什么。",
        "module-map": "顶层模块分别负责什么，互相如何配合。",
        "development-guide": "第一次接手改功能时应该从哪几个文件切入，怎么降低改坏风险。",
    }.get(doc_id, "这篇文档要回答的核心问题。")


def _doc_required_sections(doc_id: str) -> list[str]:
    defaults = {
        "homepage": ["仓库定位", "推荐阅读路线", "当前缺失项", "文档索引"],
        "overview": ["仓库目标", "关键事实", "核心对象", "边界与不确定性"],
        "code-reading-path": ["主链概览", "主链一", "主链二", "最先看哪些文件"],
        "stack-and-entrypoints": ["最接近真实入口的装配点", "运行边界", "分词与数据入口", "技术栈判断"],
        "module-map": ["模块总览", "逐模块职责", "模块协作关系"],
        "development-guide": ["改动前先确认什么", "按变更类型切入", "高风险点", "最小验证路径"],
    }
    return defaults.get(doc_id, ["核心内容"])


def _doc_evidence_paths(doc_id: str, analysis: RepositoryAnalysis) -> list[str]:
    preferred = {
        "homepage": ["engine.py", "gpt.py", "dataloader.py", "dataset.py", "tokenizer.py", "checkpoint_manager.py"],
        "overview": ["gpt.py", "engine.py", "dataloader.py", "dataset.py"],
        "code-reading-path": ["checkpoint_manager.py", "engine.py", "gpt.py", "dataloader.py", "tokenizer.py"],
        "stack-and-entrypoints": ["checkpoint_manager.py", "tokenizer.py", "common.py", "engine.py"],
        "module-map": ["engine.py", "gpt.py", "dataloader.py", "dataset.py", "tokenizer.py", "checkpoint_manager.py"],
        "development-guide": ["gpt.py", "dataloader.py", "dataset.py", "tokenizer.py", "checkpoint_manager.py", "engine.py"],
    }.get(doc_id, [])
    available = set(analysis.top_level_files) | set(analysis.entrypoint_candidates) | set(analysis.source_layout)
    paths = [path for path in preferred if path in available]
    if not paths:
        paths = list(analysis.top_level_files[:6])
    return paths[:6]


def _doc_cross_links(doc_id: str, plan: DocsetPlan) -> list[str]:
    preferred = {
        "homepage": ["overview", "code-reading-path", "stack-and-entrypoints", "module-map", "development-guide"],
        "overview": ["code-reading-path", "module-map", "stack-and-entrypoints"],
        "code-reading-path": ["overview", "stack-and-entrypoints", "module-map"],
        "stack-and-entrypoints": ["overview", "code-reading-path", "development-guide"],
        "module-map": ["overview", "development-guide"],
        "development-guide": ["module-map", "code-reading-path", "overview"],
        "bridge-topics": ["module-map", "code-reading-path", "evidence-guide"],
        "evidence-guide": ["module-map", "stack-and-entrypoints", "bridge-topics"],
    }.get(doc_id, [])
    available = set(plan.documents)
    return [item for item in preferred if item in available]


def _doc_seed_points(doc_id: str, analysis: RepositoryAnalysis) -> list[str]:
    primary = {
        "homepage": [
            f"说明 `{analysis.profile.repo_label}` 更像训练/推理内核而不是完整应用。",
            "明确指出仓库缺少 README、tests、显式 CLI 或配置入口时，新人应如何调整阅读策略。",
            "把阅读路线压成 30 分钟主心智模型和接手维护两条路径。",
        ],
        "overview": [
            "先定义仓库目标，再说明仓库边界和缺失项。",
            "把核心对象收敛到模型、数据装载、分词器、checkpoint、推理引擎。",
        ],
        "code-reading-path": [
            "至少串出一条从 checkpoint 到生成 token 的推理链。",
            "至少串出一条从 parquet 数据到训练 batch 的数据链。",
        ],
        "stack-and-entrypoints": [
            "强调这里没有显式 CLI，最接近入口的是装配函数和可被外部导入的模块。",
            "指出关键技术栈来自 PyTorch、parquet、分词器实现和高性能注意力路径。",
        ],
        "module-map": [
            "逐个解释顶层关键文件，而不是只列目录。",
            "把模块之间的协作关系说清楚。",
        ],
        "development-guide": [
            "按改模型、改数据、改分词、改 checkpoint、改推理五类给切入点。",
            "强调当前仓缺测试时的最低验证策略。",
        ],
        "bridge-topics": [
            "列出跨越多个模块的关键机制：依赖注入、插件系统、中间件/拦截器链、反射/动态派发。",
            "对每个桥接机制，说明它在哪里被注册、在哪里被调用、为什么必须用这种方式而不是直接调用。",
            "指出新人最容易在这里产生误解的两个点。",
        ],
        "evidence-guide": [
            "说明如何通过测试文件、benchmark、assertion、日志、类型注解推断真实行为边界。",
            "指出哪些文件既是规格说明又是验收标准。",
            "说明如何区分文档声称的边界和实际运行时行为。",
        ],
    }.get(doc_id, [])
    return primary


def _build_authoring_brief(
    packet: dict,
    analysis: RepositoryAnalysis,
    plan: DocsetPlan,
    command: str,
) -> str:
    mode_slug = _mode_slug(command)
    lines = [
        "# RepoDoctify Prompt Bundle",
        "",
        "## Task",
        f"- Target mode: `{mode_slug}`",
        f"- Repository: `{analysis.profile.repo_label}`",
        f"- Source path: `{analysis.profile.source_path}`",
        "- Generate the docset content yourself from the repository evidence and plan.",
        "- The Python runtime is only allowed to prepare analysis, plan, manifest, and prompt files.",
        "",
        "## Required Inputs",
        "- `ir/repository-analysis.json`",
        "- `plan/docset-plan.json`",
        "- `artifacts/manifest.json`",
        f"- `prompt/{mode_slug}-output-contract.json`",
        "- `prompt/write-targets.json`",
        "- `prompt/document-prompts.json`",
        "",
        "## Repo Snapshot",
        f"- Primary language: `{analysis.primary_language}`",
        f"- Repo kind: `{analysis.repo_kind}`",
        f"- Top-level directories: {', '.join(analysis.top_level_directories) or '(none)'}",
        f"- Top-level files: {', '.join(analysis.top_level_files) or '(none)'}",
        f"- Entrypoint candidates: {', '.join(analysis.entrypoint_candidates[:8]) or '(none)'}",
        f"- Source anchors: {', '.join(analysis.source_layout[:8]) or '(none)'}",
        f"- Test anchors: {', '.join(analysis.test_layout[:8]) or '(none)'}",
        f"- Config files: {', '.join(analysis.config_files) or '(none)'}",
        "",
        "## Planned Documents",
    ]
    for doc_id in plan.documents:
        lines.append(
            f"- `{doc_id}`: {plan.document_titles[doc_id]} ({plan.document_roles[doc_id]})"
        )
    lines.extend(
        [
            "",
            "## Generation Constraints",
            "- Do not emit generic filler such as 'connect the external entry and real implementation' unless you explain the actual files involved.",
            "- Prefer concrete call paths, file paths, and configuration switches over abstract summaries.",
            "- For '先看哪些文件' or other ordered reading sections, use numbered lists instead of tables unless comparison is genuinely horizontal.",
            "- Mention uncertainty explicitly when the repository does not provide enough evidence.",
            "- When generating Markdown or HTML, preserve Mermaid blocks when they meaningfully clarify the structure.",
            "- Actively add diagrams and tables where they genuinely clarify structure. See `references/rendering-rules.md` for the decision table and design rules (diagrams: mindmap / sequenceDiagram / erDiagram / classDiagram / flowchart; tables for comparison, lookup, and index). For flowchart chains of 5+ steps, use `flowchart TD` (top-down) instead of `flowchart LR` — long LR chains render nodes too small to read. Every diagram and table must be accompanied by 1-3 sentences of explanation — never leave one naked.",
            "- Write the output files one at a time in the order listed by `prompt/write-targets.json`.",
            "- Before writing each document, read its single current document task from `prompt/document-prompts.json` and answer only that document's question. If the document has a `diagram` field, add the required Mermaid diagram immediately after the `after_section` heading before continuing.",
            "- Do not keep exploring once the evidence is sufficient for the planned documents; switch to writing.",
            "- Do not stop after writing only homepage. For Markdown mode, you must complete all targets in a single run.",
            "- After writing each file, verify that it exists before moving to the next target.",
            "- Do not glob-read every source file. Follow `reading_budget.priority_paths` first and stay within the budget unless a hard gap remains.",
        ]
    )
    if command == COMMAND_RENDER_MD:
        lines.extend(
            [
                "- Load `references/markdown-rendering-rules.md` for Markdown-specific rendering rules.",
                "- For Markdown mode, prefer a single multi-file `apply_patch` that creates every missing `.md` target and `README.md` in one pass.",
                "- After the multi-file write, run one bulk existence check using the command declared in `prompt/write-targets.json`.",
                "- Do not pause for commentary after `homepage.md`; continue until every declared Markdown target exists.",
            ]
        )
    if command == COMMAND_HTML:
        lines.extend(
            [
                "- Load `references/html-rendering-rules.md` for HTML-specific rendering rules.",
            ]
        )
    if command == COMMAND_FEISHU:
        lines.extend(
            [
                "- Follow the Feishu handoff references for tables, Mermaid, and update strategy.",
                "- Treat `lark-mcp` as the connectivity layer only; RepoDoctify owns the content and publish plan.",
            ]
        )
    return "\n".join(lines) + "\n"
