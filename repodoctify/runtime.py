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
from .models import DocumentSpec, DocsetPlan, RepositoryProfile, SectionNode
from .planning import build_default_docset_plan
from .targeting import TargetRepoDecision, resolve_target_repo
from .workspace import ensure_external_workspace, find_latest_workspace, write_workspace_metadata


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


def resolve_repo_decision(
    current_dir: str | Path,
    requested_repo: str | Path | None = None,
    strict_conflict_check: bool = False,
) -> TargetRepoDecision:
    return resolve_target_repo(
        current_dir=current_dir,
        requested_repo=requested_repo,
        strict_conflict_check=strict_conflict_check,
    )


def run_repodoctify(
    repo_path: str | Path,
    command: str | None = None,
    workspace_root: str | Path | None = None,
    public_locator: str | None = None,
    installed_tools: set[str] | None = None,
    run_id: str | None = None,
    reuse_latest: bool = False,
    current_dir: str | Path | None = None,
    strict_conflict_check: bool = False,
) -> RepoDoctifyRunResult:
    resolved_command = command or COMMAND_RENDER_MD
    if resolved_command not in SUPPORTED_COMMANDS:
        raise ValueError(f"Unsupported RepoDoctify command: {resolved_command}")

    decision = resolve_repo_decision(
        current_dir=current_dir or Path.cwd(),
        requested_repo=repo_path,
        strict_conflict_check=strict_conflict_check,
    )
    if decision.should_ask:
        raise ValueError(decision.question)

    repo = decision.repo_path
    workspace = _resolve_workspace(
        repo,
        workspace_root=workspace_root,
        run_id=run_id,
        reuse_latest=reuse_latest,
    )
    analysis = None
    plan = None
    docs = None
    ir_path = workspace / "ir" / "docset-ir.json"

    written_files: list[Path] = []
    write_workspace_metadata(workspace, repo)
    plan_path = workspace / "plan" / "docset-plan.json"
    if plan_path.exists():
        written_files.append(plan_path)

    if resolved_command == COMMAND_PLAN:
        analysis = analyze_repository(repo, public_locator=public_locator)
        plan = build_default_docset_plan(analysis)
        _write_plan(plan_path, analysis.profile, plan)
        if plan_path not in written_files:
            written_files.append(plan_path)
        return RepoDoctifyRunResult(
            command=resolved_command,
            workspace=workspace,
            plan_path=plan_path,
            ir_path=None,
            written_files=written_files,
        )

    profile: RepositoryProfile
    if reuse_latest and plan_path.exists() and ir_path.exists():
        profile, plan, docs = _load_ir_bundle(ir_path)
    else:
        analysis = analyze_repository(repo, public_locator=public_locator)
        plan = build_default_docset_plan(analysis)
        docs = compose_docset(analysis, plan)
        profile = analysis.profile
        _write_plan(plan_path, profile, plan)
        _write_json(
            ir_path,
            {
                "repository_profile": asdict(profile),
                "docset_plan": asdict(plan),
                "documents": [asdict(doc) for doc in docs],
            },
        )
    if plan_path not in written_files:
        written_files.append(plan_path)
    if ir_path not in written_files:
        written_files.append(ir_path)

    if resolved_command == COMMAND_RENDER_MD:
        render_result = render_markdown_docset(profile, docs)
        written_files.extend(_write_files(workspace / "md", render_result.files))
        return RepoDoctifyRunResult(
            command=resolved_command,
            workspace=workspace,
            plan_path=plan_path,
            ir_path=ir_path,
            written_files=written_files,
        )

    if resolved_command == COMMAND_HTML:
        render_result = render_html_docset(profile, docs)
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
    _write_json(manifest_path, build_docset_manifest(profile, docs))
    handoff_payload = build_feishu_handoff_payload(profile, docs, manifest_path=manifest_path)
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


def _write_plan(path: Path, profile: RepositoryProfile, plan: DocsetPlan) -> None:
    _write_json(
        path,
        {
            "repo_label": profile.repo_label,
            "documents": plan.documents,
            "document_titles": plan.document_titles,
            "document_roles": plan.document_roles,
            "reading_routes": plan.reading_routes,
            "readme_aggregation_strategy": plan.readme_aggregation_strategy,
        },
    )


def _resolve_workspace(
    repo_path: Path,
    workspace_root: str | Path | None,
    run_id: str | None,
    reuse_latest: bool,
) -> Path:
    if reuse_latest:
        existing = find_latest_workspace(repo_path, workspace_root=workspace_root)
        if existing is not None:
            return existing
    return ensure_external_workspace(repo_path, workspace_root=workspace_root, run_id=run_id)


def _load_ir_bundle(ir_path: Path) -> tuple[RepositoryProfile, DocsetPlan, list[DocumentSpec]]:
    payload = json.loads(ir_path.read_text(encoding="utf-8"))
    profile = RepositoryProfile(**payload["repository_profile"])
    plan = DocsetPlan(**payload["docset_plan"])
    documents = [_document_from_dict(item) for item in payload["documents"]]
    return profile, plan, documents


def _document_from_dict(payload: dict) -> DocumentSpec:
    sections = [SectionNode(**section) for section in payload.get("sections", [])]
    data = dict(payload)
    data["sections"] = sections
    return DocumentSpec(**data)
