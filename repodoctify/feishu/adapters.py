from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FeishuProbeAdapter:
    def probe_targets(self, plan: dict) -> dict:
        documents: list[dict] = []
        for document in plan.get("documents", []):
            if document.get("publish_mode") == "create_new":
                documents.append(
                    {
                        "doc_id": document["doc_id"],
                        "target_document_id": document.get("target_document_id"),
                        "status": "not_needed",
                    }
                )
                continue
            if document.get("target_document_id"):
                documents.append(
                    {
                        "doc_id": document["doc_id"],
                        "target_document_id": document.get("target_document_id"),
                        "status": "lookup_not_attempted",
                    }
                )
                continue
            documents.append(
                {
                    "doc_id": document["doc_id"],
                    "target_document_id": document.get("target_document_id"),
                    "status": "lookup_required",
                }
            )
        return {"documents": documents}
