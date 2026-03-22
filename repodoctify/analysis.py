from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from .models import RepositoryProfile


CONFIG_FILE_NAMES = (
    "pyproject.toml",
    "package.json",
    "tsconfig.json",
    "Cargo.toml",
    "go.mod",
    "Makefile",
    "setup.py",
    "requirements.txt",
)

IGNORED_NAMES = {".git", ".pytest_cache", "__pycache__"}


@dataclass(slots=True)
class RepositoryAnalysis:
    profile: RepositoryProfile
    repo_kind: str = "generic_repo"
    primary_language: str = "unknown"
    top_level_files: list[str] = field(default_factory=list)
    top_level_directories: list[str] = field(default_factory=list)
    readme_files: list[str] = field(default_factory=list)
    entrypoint_candidates: list[str] = field(default_factory=list)
    docs_entries: list[str] = field(default_factory=list)
    source_entries: list[str] = field(default_factory=list)
    test_entries: list[str] = field(default_factory=list)
    source_layout: list[str] = field(default_factory=list)
    test_layout: list[str] = field(default_factory=list)
    docs_layout: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    tooling_signals: dict[str, str] = field(default_factory=dict)
    evidence_strength: dict[str, str] = field(default_factory=dict)
    code_anchor_chains: list[str] = field(default_factory=list)


def analyze_repository(
    repo_path: str | Path,
    public_locator: str | None = None,
    primary_audience: str | None = None,
) -> RepositoryAnalysis:
    repo = Path(repo_path).resolve()
    file_inventory = _collect_file_inventory(repo)
    entries = sorted(
        (entry for entry in repo.iterdir() if entry.name not in IGNORED_NAMES),
        key=lambda entry: (entry.is_file(), entry.name.lower()),
    )

    top_level_files = [entry.name for entry in entries if entry.is_file()]
    top_level_directories = [entry.name for entry in entries if entry.is_dir()]
    readme_files = [name for name in top_level_files if name.lower().startswith("readme")]
    docs_entries = _collect_docs_entries(repo)
    source_entries = _detect_source_entries(repo, top_level_directories, file_inventory)
    test_entries = _detect_test_entries(repo, top_level_directories, file_inventory)
    config_files = [name for name in top_level_files if name in CONFIG_FILE_NAMES]
    primary_language = _detect_primary_language(top_level_files, file_inventory)
    repo_kind = _detect_repo_kind(primary_language, top_level_files, file_inventory)
    source_layout = _detect_source_layout(file_inventory, source_entries)
    test_layout = _detect_test_layout(file_inventory, test_entries)
    docs_layout = docs_entries
    tooling_signals = _detect_tooling_signals(repo, top_level_files, file_inventory, primary_language)
    entrypoint_candidates = _detect_entrypoint_candidates(
        repo,
        top_level_files,
        readme_files,
        file_inventory,
        primary_language,
    )
    evidence_strength = _build_evidence_strength(readme_files, test_entries, docs_entries, config_files)
    code_anchor_chains = _build_code_anchor_chains(
        readme_files=readme_files,
        entrypoint_candidates=entrypoint_candidates,
        source_layout=source_layout,
        test_layout=test_layout,
        config_files=config_files,
        tooling_signals=tooling_signals,
    )

    profile = RepositoryProfile(
        repo_label=repo.name,
        source_path=str(repo),
        public_locator=public_locator,
        primary_audience=primary_audience or "First-time readers and maintainers",
        source_authority_notes=_build_authority_notes(readme_files, test_entries, config_files),
    )
    return RepositoryAnalysis(
        profile=profile,
        repo_kind=repo_kind,
        primary_language=primary_language,
        top_level_files=top_level_files,
        top_level_directories=top_level_directories,
        readme_files=readme_files,
        entrypoint_candidates=entrypoint_candidates,
        docs_entries=docs_entries,
        source_entries=source_entries,
        test_entries=test_entries,
        source_layout=source_layout,
        test_layout=test_layout,
        docs_layout=docs_layout,
        config_files=config_files,
        tooling_signals=tooling_signals,
        evidence_strength=evidence_strength,
        code_anchor_chains=code_anchor_chains,
    )


def _collect_docs_entries(repo: Path) -> list[str]:
    docs_dir = repo / "docs"
    if not docs_dir.exists() or not docs_dir.is_dir():
        return []
    return [
        f"docs/{entry.name}"
        for entry in sorted(docs_dir.iterdir(), key=lambda item: item.name.lower())
        if entry.name not in IGNORED_NAMES
    ]


def _collect_file_inventory(repo: Path, max_depth: int = 4) -> list[str]:
    inventory: list[str] = []
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(repo)
        if any(part in IGNORED_NAMES for part in relative.parts):
            continue
        if len(relative.parts) > max_depth:
            continue
        inventory.append(relative.as_posix())
    return sorted(inventory)


def _detect_source_entries(
    repo: Path,
    top_level_directories: list[str],
    file_inventory: list[str],
) -> list[str]:
    candidates: list[str] = []
    source_like_names = {"src", "lib", "app", "apps", "packages"}
    for name in top_level_directories:
        lower = name.lower()
        if lower in {"tests", "test"} or lower.endswith("_tests"):
            continue
        if name in source_like_names:
            candidates.append(name)
            continue
        path = repo / name
        if path.is_dir() and any(
            child.startswith(f"{name}/") and child.endswith((".py", ".ts", ".tsx", ".js", ".jsx"))
            for child in file_inventory
        ):
            candidates.append(name)
    return sorted(set(candidates))


def _detect_test_entries(
    repo: Path,
    top_level_directories: list[str],
    file_inventory: list[str],
) -> list[str]:
    candidates: list[str] = []
    for name in top_level_directories:
        lower = name.lower()
        if lower in {"tests", "test"} or lower.endswith("_tests"):
            candidates.append(name)
            continue
        path = repo / name
        if path.is_dir() and any(
            child.startswith(f"{name}/")
            and Path(child).name.startswith(("test", "spec"))
            for child in file_inventory
        ):
            candidates.append(name)
    return sorted(set(candidates))


def _detect_primary_language(top_level_files: list[str], file_inventory: list[str]) -> str:
    suffixes = [Path(path).suffix.lower() for path in file_inventory]
    python_count = suffixes.count(".py")
    typescript_count = suffixes.count(".ts") + suffixes.count(".tsx")
    javascript_count = suffixes.count(".js") + suffixes.count(".jsx")

    if "pyproject.toml" in top_level_files or "setup.py" in top_level_files or python_count:
        if python_count >= typescript_count + javascript_count:
            return "python"
    if "tsconfig.json" in top_level_files or typescript_count:
        return "typescript"
    if "package.json" in top_level_files or javascript_count:
        return "javascript"
    return "unknown"


def _detect_repo_kind(primary_language: str, top_level_files: list[str], file_inventory: list[str]) -> str:
    if primary_language == "python":
        if "pyproject.toml" in top_level_files or "setup.py" in top_level_files:
            return "python_package"
        return "python_repo"
    if primary_language == "typescript":
        if "package.json" in top_level_files:
            return "node_typescript"
        return "typescript_repo"
    if primary_language == "javascript":
        if "package.json" in top_level_files:
            return "node_javascript"
        return "javascript_repo"
    if any(path.endswith(".md") for path in file_inventory):
        return "docs_heavy_repo"
    return "generic_repo"


def _detect_source_layout(file_inventory: list[str], source_entries: list[str]) -> list[str]:
    layout: list[str] = []
    for name in source_entries:
        for path in file_inventory:
            if path.startswith(f"{name}/") and path.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
                layout.append(path)
    return layout[:12]


def _detect_test_layout(file_inventory: list[str], test_entries: list[str]) -> list[str]:
    layout: list[str] = []
    for name in test_entries:
        for path in file_inventory:
            if path.startswith(f"{name}/"):
                layout.append(path)
    return layout[:12]


def _detect_tooling_signals(
    repo: Path,
    top_level_files: list[str],
    file_inventory: list[str],
    primary_language: str,
) -> dict[str, str]:
    signals: dict[str, str] = {}
    if "package.json" in top_level_files:
        signals["package_manager"] = "npm-compatible"
        try:
            payload = json.loads((repo / "package.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        if payload.get("workspaces"):
            signals["workspace_layout"] = "monorepo"
        if "build" in payload.get("scripts", {}):
            signals["build_script"] = "present"
    if "pyproject.toml" in top_level_files:
        signals["build_system"] = "pyproject"
    elif "setup.py" in top_level_files:
        signals["build_system"] = "setup.py"
    if "tsconfig.json" in top_level_files:
        signals["typescript_config"] = "present"
    if primary_language != "unknown":
        signals["runtime"] = primary_language
    if any(path.endswith(".test.ts") or path.endswith(".spec.ts") for path in file_inventory):
        signals["test_style"] = "spec-style"
    return signals


def _detect_entrypoint_candidates(
    repo: Path,
    top_level_files: list[str],
    readme_files: list[str],
    file_inventory: list[str],
    primary_language: str,
) -> list[str]:
    candidates: list[str] = []
    candidates.extend(readme_files)
    if "package.json" in top_level_files:
        candidates.append("package.json")
    if "pyproject.toml" in top_level_files:
        candidates.append("pyproject.toml")

    preferred_names = {
        "python": ("main.py", "cli.py", "__main__.py", "app.py"),
        "typescript": ("index.ts", "main.ts", "app.ts", "cli.ts"),
        "javascript": ("index.js", "main.js", "app.js", "cli.js"),
    }.get(primary_language, ("main.py", "index.ts", "index.js", "app.py"))

    for name in preferred_names:
        for path in file_inventory:
            if path.endswith(name):
                candidates.append(path)
    for path in file_inventory:
        if path.startswith(("src/", "apps/", "packages/")) and path.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
            candidates.append(path)

    ordered: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = candidate.replace(str(repo) + "/", "")
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered[:10]


def _build_evidence_strength(
    readme_files: list[str],
    test_entries: list[str],
    docs_entries: list[str],
    config_files: list[str],
) -> dict[str, str]:
    return {
        "readme": "strong" if readme_files else "weak",
        "tests": "strong" if test_entries else "weak",
        "docs": "medium" if docs_entries else "weak",
        "config": "strong" if config_files else "weak",
    }


def _build_authority_notes(
    readme_files: list[str],
    test_entries: list[str],
    config_files: list[str],
) -> list[str]:
    notes: list[str] = []
    if readme_files:
        notes.append("README files provide the first repository-level contract.")
    if test_entries:
        notes.append("Test directories provide executable evidence for behavior and boundaries.")
    if config_files:
        notes.append("Top-level config files reveal runtime, build, and packaging assumptions.")
    if not notes:
        notes.append("Repository structure is the primary source of truth because top-level docs are sparse.")
    return notes


def _build_code_anchor_chains(
    readme_files: list[str],
    entrypoint_candidates: list[str],
    source_layout: list[str],
    test_layout: list[str],
    config_files: list[str],
    tooling_signals: dict[str, str],
) -> list[str]:
    chains: list[str] = []
    if readme_files and entrypoint_candidates:
        chains.append(
            f"Follow `{readme_files[0]}` -> `{entrypoint_candidates[0]}` first to map the human-facing contract to the real entrypoint."
        )

    source_anchor = _choose_source_anchor(entrypoint_candidates, source_layout)
    test_anchor = test_layout[0] if test_layout else None
    config_anchor = config_files[0] if config_files else None

    if source_anchor is not None and test_anchor is not None:
        chains.append(
            f"Follow `{source_anchor}` -> `{test_anchor}` to confirm the primary behavior path and its regression anchor."
        )
    elif source_anchor is not None:
        chains.append(
            f"Follow `{source_anchor}` as the main implementation anchor before widening into helper modules."
        )

    if tooling_signals.get("workspace_layout") == "monorepo":
        workspace_source = next(
            (path for path in source_layout if path.startswith(("apps/", "packages/"))),
            None,
        )
        if workspace_source is not None:
            chains.append(
                f"Follow `package.json` -> `{workspace_source}` to understand how workspace scripts hand control to package-level source entrypoints."
            )

    if source_anchor is not None and config_anchor is not None:
        chains.append(
            f"Use `{config_anchor}` after `{source_anchor}` when you need the runtime or packaging boundary for a change."
        )
    return chains[:4]


def _choose_source_anchor(entrypoint_candidates: list[str], source_layout: list[str]) -> str | None:
    for candidate in entrypoint_candidates:
        if candidate.startswith(("src/", "apps/", "packages/")):
            return candidate
    if source_layout:
        return source_layout[0]
    return None
