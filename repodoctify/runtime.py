from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from .analysis import analyze_repository
from .composer import compose_docset
from .feishu_handoff import (
    FeishuExecutionMode,
    build_feishu_publish_plan,
    build_feishu_verification_summary,
    ensure_feishu_dependencies,
    probe_feishu_auth_state,
)
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
    resolved_repo_path: Path
    repo_resolution_reason: str
    feishu_execution_mode: str | None = None
    feishu_auth_state: dict | None = None
    feishu_publish_plan: dict | None = None


@dataclass(slots=True)
class RepoDoctifyRequest:
    requested_repo: str | Path
    current_dir: str | Path | None = None
    command: str | None = None
    workspace_root: str | Path | None = None
    public_locator: str | None = None
    installed_tools: set[str] | None = None
    run_id: str | None = None
    reuse_latest: bool = False
    strict_conflict_check: bool = False
    reading_goal: str | None = None
    feishu_mode: str | None = None


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
    request = RepoDoctifyRequest(
        requested_repo=repo_path,
        current_dir=current_dir,
        command=command,
        workspace_root=workspace_root,
        public_locator=public_locator,
        installed_tools=installed_tools,
        run_id=run_id,
        reuse_latest=reuse_latest,
        strict_conflict_check=strict_conflict_check,
    )
    return run_repodoctify_request(request)


def run_repodoctify_request(request: RepoDoctifyRequest) -> RepoDoctifyRunResult:
    resolved_command = request.command or COMMAND_RENDER_MD
    if resolved_command not in SUPPORTED_COMMANDS:
        raise ValueError(f"Unsupported RepoDoctify command: {resolved_command}")

    decision = resolve_repo_decision(
        current_dir=request.current_dir or Path.cwd(),
        requested_repo=request.requested_repo,
        strict_conflict_check=request.strict_conflict_check,
    )
    if decision.should_ask:
        raise ValueError(decision.question)

    repo = decision.repo_path
    workspace = _resolve_workspace(
        repo,
        workspace_root=request.workspace_root,
        run_id=request.run_id,
        reuse_latest=request.reuse_latest,
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
        analysis = analyze_repository(repo, public_locator=request.public_locator)
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
            resolved_repo_path=repo,
            repo_resolution_reason=decision.reason,
        )

    profile: RepositoryProfile
    if request.reuse_latest and plan_path.exists() and ir_path.exists():
        profile, plan, docs = _load_ir_bundle(ir_path)
    else:
        analysis = analyze_repository(repo, public_locator=request.public_locator)
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
            resolved_repo_path=repo,
            repo_resolution_reason=decision.reason,
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
            resolved_repo_path=repo,
            repo_resolution_reason=decision.reason,
        )

    dependency_result = ensure_feishu_dependencies(installed_tools=request.installed_tools)
    if not dependency_result.ok:
        raise RuntimeError(dependency_result.message)

    feishu_mode = request.feishu_mode or FeishuExecutionMode.PLAN_ONLY.value
    auth_state = probe_feishu_auth_state(
        installed_tools=request.installed_tools,
        require_user_access_token=feishu_mode == FeishuExecutionMode.EXECUTE.value,
        user_token_present=feishu_mode != FeishuExecutionMode.PLAN_ONLY.value,
        user_token_validated=feishu_mode == FeishuExecutionMode.EXECUTE.value,
    )
    manifest_path = workspace / "publish" / "manifest.json"
    _write_json(manifest_path, build_docset_manifest(profile, docs))
    publish_plan = build_feishu_publish_plan(
        profile,
        docs,
        manifest_path=manifest_path,
        execution_mode=FeishuExecutionMode(feishu_mode),
    )
    publish_plan_path = workspace / "publish" / "feishu-publish-plan.json"
    verification_path = workspace / "publish" / "verification-summary.json"
    auth_state_path = workspace / "publish" / "auth-state.json"
    _write_json(publish_plan_path, publish_plan)
    _write_json(verification_path, build_feishu_verification_summary(publish_plan))
    _write_json(auth_state_path, auth_state.as_dict())
    written_files.extend([manifest_path, publish_plan_path, verification_path, auth_state_path])
    return RepoDoctifyRunResult(
        command=resolved_command,
        workspace=workspace,
        plan_path=plan_path,
        ir_path=ir_path,
        written_files=written_files,
        resolved_repo_path=repo,
        repo_resolution_reason=decision.reason,
        feishu_execution_mode=feishu_mode,
        feishu_auth_state=auth_state.as_dict(),
        feishu_publish_plan=publish_plan,
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
