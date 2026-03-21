from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from .analysis import analyze_repository
from .composer import compose_docset
from .feishu_handoff import build_feishu_handoff_payload, ensure_feishu_dependencies
from .html_renderer import render_html_docset
from .manifest import build_docset_manifest
from .markdown_renderer import render_markdown_docset
from .planning import build_default_docset_plan
from .workspace import ensure_external_workspace


COMMAND_PLAN = "规划输出框架"
COMMAND_RENDER_MD = "以 md 形式输出全部内容"
COMMAND_HTML = "以 html 形式输出全部内容"
COMMAND_FEISHU = "以飞书形式输出全部内容"

SUPPORTED_COMMANDS = {COMMAND_PLAN, COMMAND_RENDER_MD, COMMAND_HTML, COMMAND_FEISHU}


@dataclass(slots=True)
class RepoDoctifyRunResult:
    command: str
    workspace: Path
    plan_path: Path
    ir_path: Path | None
    written_files: list[Path]
    handoff_payload: dict | None = None


def run_repodoctify(
    repo_path: str | Path,
    command: str | None = None,
    workspace_root: str | Path | None = None,
    public_locator: str | None = None,
    installed_tools: set[str] | None = None,
    run_id: str | None = None,
) -> RepoDoctifyRunResult:
    resolved_command = command or COMMAND_RENDER_MD
    if resolved_command not in SUPPORTED_COMMANDS:
        raise ValueError(f"Unsupported RepoDoctify command: {resolved_command}")

    workspace = ensure_external_workspace(repo_path, workspace_root=workspace_root, run_id=run_id)
    analysis = analyze_repository(repo_path, public_locator=public_locator)
    plan = build_default_docset_plan(analysis)

    written_files: list[Path] = []
    plan_path = workspace / "plan" / "docset-plan.json"
    _write_json(
        plan_path,
        {
            "repo_label": analysis.profile.repo_label,
            "documents": plan.documents,
            "document_titles": plan.document_titles,
            "document_roles": plan.document_roles,
            "reading_routes": plan.reading_routes,
            "readme_aggregation_strategy": plan.readme_aggregation_strategy,
        },
    )
    written_files.append(plan_path)

    if resolved_command == COMMAND_PLAN:
        return RepoDoctifyRunResult(
            command=resolved_command,
            workspace=workspace,
            plan_path=plan_path,
            ir_path=None,
            written_files=written_files,
        )

    docs = compose_docset(analysis, plan)
    ir_path = workspace / "ir" / "docset-ir.json"
    _write_json(
        ir_path,
        {
            "repository_profile": asdict(analysis.profile),
            "docset_plan": asdict(plan),
            "documents": [asdict(doc) for doc in docs],
        },
    )
    written_files.append(ir_path)

    if resolved_command == COMMAND_RENDER_MD:
        render_result = render_markdown_docset(analysis.profile, docs)
        written_files.extend(_write_files(workspace / "md", render_result.files))
        return RepoDoctifyRunResult(
            command=resolved_command,
            workspace=workspace,
            plan_path=plan_path,
            ir_path=ir_path,
            written_files=written_files,
        )

    if resolved_command == COMMAND_HTML:
        render_result = render_html_docset(analysis.profile, docs)
        written_files.extend(_write_files(workspace / "html", render_result.files))
        return RepoDoctifyRunResult(
            command=resolved_command,
            workspace=workspace,
            plan_path=plan_path,
            ir_path=ir_path,
            written_files=written_files,
        )

    dependency_result = ensure_feishu_dependencies(installed_tools=installed_tools)
    if not dependency_result.ok:
        raise RuntimeError(dependency_result.message)

    manifest_path = workspace / "publish" / "manifest.json"
    _write_json(manifest_path, build_docset_manifest(analysis.profile, docs))
    handoff_payload = build_feishu_handoff_payload(analysis.profile, docs, manifest_path=manifest_path)
    handoff_path = workspace / "publish" / "feishu-handoff.json"
    _write_json(handoff_path, handoff_payload)
    written_files.extend([manifest_path, handoff_path])
    return RepoDoctifyRunResult(
        command=resolved_command,
        workspace=workspace,
        plan_path=plan_path,
        ir_path=ir_path,
        written_files=written_files,
        handoff_payload=handoff_payload,
    )


def _write_files(root: Path, files: dict[str, str]) -> list[Path]:
    written_files: list[Path] = []
    for relative_name, content in files.items():
        path = root / relative_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written_files.append(path)
    return written_files


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
