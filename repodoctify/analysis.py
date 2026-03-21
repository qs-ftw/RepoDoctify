from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .models import RepositoryProfile


CONFIG_FILE_NAMES = (
    "pyproject.toml",
    "package.json",
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
    top_level_files: list[str] = field(default_factory=list)
    top_level_directories: list[str] = field(default_factory=list)
    readme_files: list[str] = field(default_factory=list)
    docs_entries: list[str] = field(default_factory=list)
    source_entries: list[str] = field(default_factory=list)
    test_entries: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)


def analyze_repository(
    repo_path: str | Path,
    public_locator: str | None = None,
    primary_audience: str | None = None,
) -> RepositoryAnalysis:
    repo = Path(repo_path).resolve()
    entries = sorted(
        (entry for entry in repo.iterdir() if entry.name not in IGNORED_NAMES),
        key=lambda entry: (entry.is_file(), entry.name.lower()),
    )

    top_level_files = [entry.name for entry in entries if entry.is_file()]
    top_level_directories = [entry.name for entry in entries if entry.is_dir()]
    readme_files = [name for name in top_level_files if name.lower().startswith("readme")]
    docs_entries = _collect_docs_entries(repo)
    source_entries = _detect_source_entries(repo, top_level_directories)
    test_entries = _detect_test_entries(repo, top_level_directories)
    config_files = [name for name in top_level_files if name in CONFIG_FILE_NAMES]

    profile = RepositoryProfile(
        repo_label=repo.name,
        source_path=str(repo),
        public_locator=public_locator,
        primary_audience=primary_audience or "First-time readers and maintainers",
        source_authority_notes=_build_authority_notes(readme_files, test_entries, config_files),
    )
    return RepositoryAnalysis(
        profile=profile,
        top_level_files=top_level_files,
        top_level_directories=top_level_directories,
        readme_files=readme_files,
        docs_entries=docs_entries,
        source_entries=source_entries,
        test_entries=test_entries,
        config_files=config_files,
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


def _detect_source_entries(repo: Path, top_level_directories: list[str]) -> list[str]:
    candidates: list[str] = []
    for name in top_level_directories:
        if name in {"src", "lib", "app"}:
            candidates.append(name)
            continue
        path = repo / name
        if path.is_dir() and any(child.suffix == ".py" for child in path.iterdir() if child.is_file()):
            candidates.append(name)
    return candidates


def _detect_test_entries(repo: Path, top_level_directories: list[str]) -> list[str]:
    candidates: list[str] = []
    for name in top_level_directories:
        lower = name.lower()
        if lower in {"tests", "test"} or lower.endswith("_tests"):
            candidates.append(name)
            continue
        path = repo / name
        if path.is_dir() and any(child.name.startswith("test") for child in path.iterdir()):
            candidates.append(name)
    return candidates


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
