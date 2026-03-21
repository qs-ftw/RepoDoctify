from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RepositoryProfile:
    repo_label: str
    source_path: str
    public_locator: str | None = None
    primary_audience: str | None = None
    source_authority_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SectionNode:
    kind: str
    title: str = ""
    body: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DocumentSpec:
    doc_id: str
    title: str
    role: str
    question_answered: str = ""
    target_reader: str = ""
    sections: list[SectionNode] = field(default_factory=list)
    next_reads: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CrossLinkMap:
    homepage_links: list[str] = field(default_factory=list)
    next_read_links: dict[str, list[str]] = field(default_factory=dict)
    reading_route_links: dict[str, list[str]] = field(default_factory=dict)
    aggregate_readme_links: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DocsetPlan:
    documents: list[str] = field(default_factory=list)
    document_titles: dict[str, str] = field(default_factory=dict)
    document_roles: dict[str, str] = field(default_factory=dict)
    reading_routes: dict[str, list[str]] = field(default_factory=dict)
    readme_aggregation_strategy: str = "homepage_plus_doc_inventory"
