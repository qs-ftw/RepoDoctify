from __future__ import annotations

from .models import DocsetPlan, DocumentSpec, RepositoryProfile
from .utils import slugify


def build_docset_manifest(profile: RepositoryProfile, docs: list[DocumentSpec]) -> dict:
    return {
        "repo_label": profile.repo_label,
        "source_path": profile.source_path,
        "public_locator": profile.public_locator,
        "documents": [
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "role": doc.role,
                "file_name": f"{slugify(doc.doc_id)}.md",
            }
            for doc in docs
        ],
    }


def build_docset_manifest_from_plan(profile: RepositoryProfile, plan: DocsetPlan) -> dict:
    return {
        "repo_label": profile.repo_label,
        "source_path": profile.source_path,
        "public_locator": profile.public_locator,
        "documents": [
            {
                "doc_id": doc_id,
                "title": plan.document_titles[doc_id],
                "role": plan.document_roles[doc_id],
                "file_name": f"{slugify(doc_id)}.md",
            }
            for doc_id in plan.documents
        ],
    }
