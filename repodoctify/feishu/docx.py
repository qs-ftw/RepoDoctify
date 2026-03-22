from __future__ import annotations

import urllib.parse
import uuid

from .http import delete_json, get_json, post_json


def fetch_tenant_access_token(app_id: str, app_secret: str) -> str:
    payload = post_json(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        {"app_id": app_id, "app_secret": app_secret},
        bearer_token=None,
    )
    return payload["tenant_access_token"]


def fetch_document_blocks(document_id: str, bearer_token: str) -> list[dict]:
    items: list[dict] = []
    page_token = ""
    while True:
        query = {"page_size": 500, "document_revision_id": -1}
        if page_token:
            query["page_token"] = page_token
        url = (
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks?"
            f"{urllib.parse.urlencode(query)}"
        )
        payload = get_json(url, bearer_token)
        data = payload["data"]
        items.extend(data["items"])
        if not data.get("has_more"):
            return items
        page_token = data["page_token"]


def create_document_child_block(
    document_id: str,
    parent_id: str,
    child: dict,
    index: int,
    bearer_token: str,
) -> dict:
    client_token = str(uuid.uuid4())
    query = urllib.parse.urlencode({"document_revision_id": -1, "client_token": client_token})
    url = (
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/"
        f"{parent_id}/children?{query}"
    )
    return post_json(url, {"children": [child], "index": index}, bearer_token)


def delete_document_child_range(
    document_id: str,
    parent_id: str,
    start_index: int,
    end_index: int,
    bearer_token: str,
) -> dict:
    client_token = str(uuid.uuid4())
    query = urllib.parse.urlencode({"document_revision_id": -1, "client_token": client_token})
    url = (
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/"
        f"{parent_id}/children/batch_delete?{query}"
    )
    return delete_json(url, {"start_index": start_index, "end_index": end_index}, bearer_token)
