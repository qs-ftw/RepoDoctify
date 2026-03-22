from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from .analysis import analyze_repository
from .feishu_handoff import (
    FeishuProbeAdapter,
    FeishuExecutionMode,
    build_feishu_publish_plan,
    build_feishu_verification_summary,
    ensure_feishu_dependencies,
    probe_feishu_auth_state,
)
from .manifest import build_docset_manifest_from_plan
from .models import DocsetPlan, RepositoryProfile
from .planning import build_default_docset_plan
from .prompting import build_prompt_bundle
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
    prompt_bundle_path: Path | None
    written_files: list[Path]
    resolved_repo_path: Path
    repo_resolution_reason: str
    feishu_execution_mode: str | None = None
    feishu_auth_state: dict | None = None
    feishu_publish_plan: dict | None = None
    feishu_probe_summary: dict | None = None


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
    feishu_target_doc_ids: dict[str, str] | None = None
    feishu_probe_adapter: object | None = None


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
    ir_path = workspace / "ir" / "repository-analysis.json"
    prompt_bundle_path: Path | None = None

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
            prompt_bundle_path=None,
            written_files=written_files,
            resolved_repo_path=repo,
            repo_resolution_reason=decision.reason,
        )

    if request.reuse_latest and plan_path.exists() and ir_path.exists():
        analysis, plan = _load_analysis_bundle(ir_path, plan_path)
    else:
        analysis = analyze_repository(repo, public_locator=request.public_locator)
        plan = build_default_docset_plan(analysis)
        _write_plan(plan_path, analysis.profile, plan)
        _write_json(ir_path, asdict(analysis))
    if plan_path not in written_files:
        written_files.append(plan_path)
    if ir_path not in written_files:
        written_files.append(ir_path)

    prompt_bundle_path = workspace / "prompt" / "packet.json"
    prompt_bundle = build_prompt_bundle(
        analysis=analysis,
        plan=plan,
        command=resolved_command,
        workspace=workspace,
    )
    manifest_path = workspace / "artifacts" / "manifest.json"
    _write_json(manifest_path, build_docset_manifest_from_plan(analysis.profile, plan))
    written_files.extend(_write_files(workspace / "prompt", prompt_bundle.files))
    written_files.append(manifest_path)
    if prompt_bundle_path not in written_files:
        written_files.append(prompt_bundle_path)

    if resolved_command == COMMAND_RENDER_MD or resolved_command == COMMAND_HTML:
        return RepoDoctifyRunResult(
            command=resolved_command,
            workspace=workspace,
            plan_path=plan_path,
            ir_path=ir_path,
            prompt_bundle_path=prompt_bundle_path,
            written_files=written_files,
            resolved_repo_path=repo,
            repo_resolution_reason=decision.reason,
        )

    dependency_result = ensure_feishu_dependencies(installed_tools=request.installed_tools)
    if not dependency_result.ok:
        raise RuntimeError(dependency_result.message)

    feishu_mode = request.feishu_mode or FeishuExecutionMode.PLAN_ONLY.value
    publish_manifest_path = workspace / "publish" / "manifest.json"
    _write_json(publish_manifest_path, build_docset_manifest_from_plan(analysis.profile, plan))
    doc_specs = _plan_documents(plan)
    probe_summary = None
    initial_plan = build_feishu_publish_plan(
        analysis.profile,
        doc_specs,
        manifest_path=publish_manifest_path,
        execution_mode=FeishuExecutionMode(feishu_mode),
        requested_target_doc_ids=request.feishu_target_doc_ids,
    )
    if feishu_mode == FeishuExecutionMode.EXECUTE.value:
        adapter = request.feishu_probe_adapter or FeishuProbeAdapter()
        probe_summary = adapter.probe_targets(initial_plan)
    publish_plan = build_feishu_publish_plan(
        analysis.profile,
        doc_specs,
        manifest_path=publish_manifest_path,
        execution_mode=FeishuExecutionMode(feishu_mode),
        requested_target_doc_ids=request.feishu_target_doc_ids,
        probe_results=probe_summary,
    )
    auth_state = probe_feishu_auth_state(
        installed_tools=request.installed_tools,
        require_user_access_token=feishu_mode == FeishuExecutionMode.EXECUTE.value,
        user_token_present=feishu_mode != FeishuExecutionMode.PLAN_ONLY.value,
        user_token_validated=feishu_mode == FeishuExecutionMode.EXECUTE.value,
        target_doc_probe_attempted=bool(request.feishu_target_doc_ids),
        unresolved_target_documents=bool(publish_plan.get("execute_blockers")),
    )
    publish_plan_path = workspace / "publish" / "feishu-publish-plan.json"
    verification_path = workspace / "publish" / "verification-summary.json"
    auth_state_path = workspace / "publish" / "auth-state.json"
    probe_summary_path = workspace / "publish" / "target-probe-summary.json"
    _write_json(publish_plan_path, publish_plan)
    _write_json(verification_path, build_feishu_verification_summary(publish_plan))
    _write_json(auth_state_path, auth_state.as_dict())
    if probe_summary is not None:
        _write_json(probe_summary_path, probe_summary)
        written_files.append(probe_summary_path)
    written_files.extend([publish_manifest_path, publish_plan_path, verification_path, auth_state_path])
    return RepoDoctifyRunResult(
        command=resolved_command,
        workspace=workspace,
        plan_path=plan_path,
        ir_path=ir_path,
        prompt_bundle_path=prompt_bundle_path,
        written_files=written_files,
        resolved_repo_path=repo,
        repo_resolution_reason=decision.reason,
        feishu_execution_mode=feishu_mode,
        feishu_auth_state=auth_state.as_dict(),
        feishu_publish_plan=publish_plan,
        feishu_probe_summary=probe_summary,
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


def _load_analysis_bundle(ir_path: Path, plan_path: Path):
    from .analysis import RepositoryAnalysis
    from .models import CodeAnchorChain

    analysis_payload = json.loads(ir_path.read_text(encoding="utf-8"))
    plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
    profile = RepositoryProfile(
        repo_label=analysis_payload["profile"]["repo_label"],
        source_path=analysis_payload["profile"]["source_path"],
        public_locator=analysis_payload["profile"].get("public_locator"),
        primary_audience=analysis_payload["profile"].get("primary_audience"),
        source_authority_notes=list(analysis_payload["profile"].get("source_authority_notes", [])),
    )
    code_anchor_details = [CodeAnchorChain(**item) for item in analysis_payload.get("code_anchor_details", [])]
    analysis = RepositoryAnalysis(
        profile=profile,
        repo_kind=analysis_payload.get("repo_kind", "generic_repo"),
        primary_language=analysis_payload.get("primary_language", "unknown"),
        top_level_files=list(analysis_payload.get("top_level_files", [])),
        top_level_directories=list(analysis_payload.get("top_level_directories", [])),
        readme_files=list(analysis_payload.get("readme_files", [])),
        entrypoint_candidates=list(analysis_payload.get("entrypoint_candidates", [])),
        docs_entries=list(analysis_payload.get("docs_entries", [])),
        source_entries=list(analysis_payload.get("source_entries", [])),
        test_entries=list(analysis_payload.get("test_entries", [])),
        source_layout=list(analysis_payload.get("source_layout", [])),
        test_layout=list(analysis_payload.get("test_layout", [])),
        docs_layout=list(analysis_payload.get("docs_layout", [])),
        config_files=list(analysis_payload.get("config_files", [])),
        tooling_signals=dict(analysis_payload.get("tooling_signals", {})),
        evidence_strength=dict(analysis_payload.get("evidence_strength", {})),
        code_anchor_details=code_anchor_details,
        code_anchor_chains=list(analysis_payload.get("code_anchor_chains", [])),
        readme_summary_lines=list(analysis_payload.get("readme_summary_lines", [])),
    )
    plan = DocsetPlan(
        documents=list(plan_payload.get("documents", [])),
        document_titles=dict(plan_payload.get("document_titles", {})),
        document_roles=dict(plan_payload.get("document_roles", {})),
        reading_routes=dict(plan_payload.get("reading_routes", {})),
        readme_aggregation_strategy=plan_payload.get(
            "readme_aggregation_strategy",
            "homepage_plus_doc_inventory",
        ),
    )
    return analysis, plan


def _plan_documents(plan: DocsetPlan):
    from .models import DocumentSpec

    return [
        DocumentSpec(
            doc_id=doc_id,
            title=plan.document_titles[doc_id],
            role=plan.document_roles[doc_id],
        )
        for doc_id in plan.documents
    ]
