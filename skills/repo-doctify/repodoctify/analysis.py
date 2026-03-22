from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from .models import CodeAnchorChain, RepositoryProfile


CONFIG_FILE_NAMES = (
    "pyproject.toml",
    "package.json",
    "tsconfig.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
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
    code_anchor_details: list[CodeAnchorChain] = field(default_factory=list)
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
    code_anchor_details = _build_code_anchor_details(
        readme_files=readme_files,
        entrypoint_candidates=entrypoint_candidates,
        source_layout=source_layout,
        test_layout=test_layout,
        config_files=config_files,
        tooling_signals=tooling_signals,
        primary_language=primary_language,
    )
    code_anchor_chains = [_render_code_anchor_chain(chain) for chain in code_anchor_details]

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
        code_anchor_details=code_anchor_details,
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
        if path.is_dir() and any(child.startswith(f"{name}/") and child.endswith(_SOURCE_FILE_SUFFIXES) for child in file_inventory):
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
        if name == "src" and any(child.startswith("src/test/") for child in file_inventory):
            candidates.append("src/test")
            continue
        path = repo / name
        if path.is_dir() and any(
            child.startswith(f"{name}/")
            and (
                Path(child).name.startswith(("test", "spec"))
                or child.endswith(("Test.java", "_test.go"))
            )
            for child in file_inventory
        ):
            candidates.append(name)
    return sorted(set(candidates))


def _detect_primary_language(top_level_files: list[str], file_inventory: list[str]) -> str:
    suffixes = [Path(path).suffix.lower() for path in file_inventory]
    python_count = suffixes.count(".py")
    typescript_count = suffixes.count(".ts") + suffixes.count(".tsx")
    javascript_count = suffixes.count(".js") + suffixes.count(".jsx")
    go_count = suffixes.count(".go")
    rust_count = suffixes.count(".rs")
    java_count = suffixes.count(".java")

    if "pyproject.toml" in top_level_files or "setup.py" in top_level_files or python_count:
        if python_count >= typescript_count + javascript_count:
            return "python"
    if "tsconfig.json" in top_level_files or typescript_count:
        return "typescript"
    if "package.json" in top_level_files or javascript_count:
        return "javascript"
    if "go.mod" in top_level_files or go_count:
        return "go"
    if "Cargo.toml" in top_level_files or rust_count:
        return "rust"
    if "pom.xml" in top_level_files or "build.gradle" in top_level_files or "build.gradle.kts" in top_level_files or java_count:
        return "java"
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
    if primary_language == "go":
        return "go_module" if "go.mod" in top_level_files else "go_repo"
    if primary_language == "rust":
        return "rust_crate" if "Cargo.toml" in top_level_files else "rust_repo"
    if primary_language == "java":
        return "java_repo"
    if any(path.endswith(".md") for path in file_inventory):
        return "docs_heavy_repo"
    return "generic_repo"


def _detect_source_layout(file_inventory: list[str], source_entries: list[str]) -> list[str]:
    layout: list[str] = []
    for name in source_entries:
        for path in file_inventory:
            if path.startswith(f"{name}/") and path.endswith(_SOURCE_FILE_SUFFIXES):
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
    if "go.mod" in top_level_files:
        signals["build_system"] = "go.mod"
    if "Cargo.toml" in top_level_files:
        signals["build_system"] = "cargo"
    if "pom.xml" in top_level_files:
        signals["build_system"] = "maven"
    if "build.gradle" in top_level_files or "build.gradle.kts" in top_level_files:
        signals["build_system"] = "gradle"
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
        "go": ("cmd/server/main.go", "cmd/main.go", "main.go"),
        "rust": ("src/main.rs", "src/lib.rs"),
        "java": ("src/main/java/App.java", "src/main/java/Main.java"),
    }.get(primary_language, ("main.py", "index.ts", "index.js", "app.py", "main.go", "src/main.rs"))

    for name in preferred_names:
        for path in file_inventory:
            if path.endswith(name):
                candidates.append(path)
    for path in file_inventory:
        if path.startswith(("src/", "apps/", "packages/", "cmd/", "internal/")) and path.endswith(_SOURCE_FILE_SUFFIXES):
            candidates.append(path)
    if "go.mod" in top_level_files:
        candidates.append("go.mod")
    if "Cargo.toml" in top_level_files:
        candidates.append("Cargo.toml")
    if "pom.xml" in top_level_files:
        candidates.append("pom.xml")
    if "build.gradle" in top_level_files:
        candidates.append("build.gradle")
    if "build.gradle.kts" in top_level_files:
        candidates.append("build.gradle.kts")

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


def _build_code_anchor_details(
    readme_files: list[str],
    entrypoint_candidates: list[str],
    source_layout: list[str],
    test_layout: list[str],
    config_files: list[str],
    tooling_signals: dict[str, str],
    primary_language: str,
) -> list[CodeAnchorChain]:
    contract_anchor = readme_files[0] if readme_files else None
    config_anchor = _choose_config_anchor(config_files, primary_language)
    details: list[CodeAnchorChain] = []

    if tooling_signals.get("workspace_layout") == "monorepo":
        app_entry = _first_matching(entrypoint_candidates, prefixes=("apps/",), suffixes=("main.ts", "index.ts", "app.ts", "main.js", "index.js"))
        app_test = _match_related_test(app_entry, test_layout)
        if app_entry is not None:
            details.append(
                CodeAnchorChain(
                    label="App startup path",
                    chain_kind="workspace_app",
                    contract_anchor=contract_anchor,
                    entry_anchor=app_entry,
                    test_anchor=app_test,
                    config_anchor=config_anchor,
                )
            )

        shared_entry = _first_matching(source_layout, prefixes=("packages/",), suffixes=("index.ts", "index.js", "service.ts", "service.js"))
        if shared_entry is not None:
            details.append(
                CodeAnchorChain(
                    label="Shared package path",
                    chain_kind="workspace_shared",
                    contract_anchor=contract_anchor,
                    entry_anchor="package.json" if "package_manager" in tooling_signals else shared_entry,
                    implementation_anchor=shared_entry,
                    test_anchor=_match_related_test(shared_entry, test_layout) or (test_layout[0] if test_layout else None),
                    config_anchor=config_anchor,
                )
            )
        return details[:4]

    entry_anchor = _choose_entry_anchor(entrypoint_candidates, primary_language)
    implementation_anchor = _choose_implementation_anchor(source_layout, entry_anchor, primary_language)
    test_anchor = _match_related_test(implementation_anchor or entry_anchor, test_layout)
    if test_anchor is None and test_layout:
        test_anchor = test_layout[0]
    if entry_anchor is not None:
        details.append(
            CodeAnchorChain(
                label="Primary behavior path",
                chain_kind="primary_behavior",
                contract_anchor=contract_anchor,
                entry_anchor=entry_anchor,
                implementation_anchor=implementation_anchor,
                test_anchor=test_anchor,
                config_anchor=config_anchor,
            )
        )
    return details[:4]


def _render_code_anchor_chain(chain: CodeAnchorChain) -> str:
    segments = [f"`{chain.entry_anchor}`"]
    if chain.implementation_anchor:
        segments.append(f"`{chain.implementation_anchor}`")
    if chain.test_anchor:
        segments.append(f"`{chain.test_anchor}`")
    joined = " -> ".join(segments)

    if chain.contract_anchor:
        return (
            f"Follow this chain for {chain.label.lower()}: `{chain.contract_anchor}` -> {joined}. "
            "Use it to understand the contract, the handoff into implementation, and the regression anchor."
        )
    return (
        f"Follow this chain for {chain.label.lower()}: {joined}. "
        "Use it to understand the entrypoint, the implementation handoff, and the regression anchor."
    )


def _choose_entry_anchor(entrypoint_candidates: list[str], primary_language: str) -> str | None:
    preferred_suffixes = {
        "python": ("cli.py", "__main__.py", "main.py", "app.py"),
        "typescript": ("main.ts", "index.ts", "app.ts", "cli.ts"),
        "javascript": ("main.js", "index.js", "app.js", "cli.js"),
        "go": ("cmd/server/main.go", "cmd/main.go", "main.go"),
        "rust": ("src/main.rs", "src/lib.rs"),
        "java": ("src/main/java/App.java", "src/main/java/Main.java"),
    }.get(primary_language, ("main.py", "main.ts", "main.js", "main.go", "src/main.rs"))
    for suffix in preferred_suffixes:
        for candidate in entrypoint_candidates:
            if candidate.endswith(suffix):
                return candidate
    return _first_matching(entrypoint_candidates, prefixes=("src/", "apps/", "packages/", "cmd/", "internal/"))


def _choose_implementation_anchor(
    source_layout: list[str],
    entry_anchor: str | None,
    primary_language: str,
) -> str | None:
    if not source_layout:
        return None
    preferred_names = {
        "python": ("service.py", "core.py", "runner.py", "pipeline.py"),
        "typescript": ("service.ts", "core.ts", "runner.ts", "index.ts"),
        "javascript": ("service.js", "core.js", "runner.js", "index.js"),
        "go": ("service.go", "app.go", "server.go"),
        "rust": ("lib.rs", "mod.rs"),
        "java": ("Service.java", "App.java"),
    }.get(primary_language, ("service.py", "service.ts", "service.js", "service.go"))
    if entry_anchor is not None:
        entry_parent = str(Path(entry_anchor).parent)
        for name in preferred_names:
            for path in source_layout:
                if path.startswith(entry_parent + "/") and path.endswith(name) and path != entry_anchor:
                    return path
    for name in preferred_names:
        for path in source_layout:
            if path.endswith(name) and path != entry_anchor:
                return path
    return None


def _match_related_test(anchor: str | None, test_layout: list[str]) -> str | None:
    if anchor is None:
        return None
    anchor_name = Path(anchor).stem.replace("__main__", "main")
    trimmed = anchor_name.replace("test_", "")
    for test in test_layout:
        test_name = Path(test).stem
        if trimmed and trimmed in test_name:
            return test
    return None


def _choose_config_anchor(config_files: list[str], primary_language: str) -> str | None:
    preferred = {
        "python": ("pyproject.toml", "setup.py", "requirements.txt"),
        "typescript": ("package.json", "tsconfig.json"),
        "javascript": ("package.json",),
        "go": ("go.mod", "Makefile"),
        "rust": ("Cargo.toml",),
        "java": ("pom.xml", "build.gradle", "build.gradle.kts"),
    }.get(primary_language, tuple(config_files))
    for candidate in preferred:
        if candidate in config_files:
            return candidate
    return config_files[0] if config_files else None


_SOURCE_FILE_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java")


def _first_matching(
    paths: list[str],
    prefixes: tuple[str, ...] = (),
    suffixes: tuple[str, ...] = (),
) -> str | None:
    for path in paths:
        if prefixes and not path.startswith(prefixes):
            continue
        if suffixes and not path.endswith(suffixes):
            continue
        return path
    return None
