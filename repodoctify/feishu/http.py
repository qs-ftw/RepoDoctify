from __future__ import annotations

import json
import urllib.request


def json_request(
    url: str,
    bearer_token: str,
    *,
    method: str = "GET",
    data: dict | None = None,
    timeout: int = 60,
) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        },
        method=method,
        data=(json.dumps(data).encode("utf-8") if data is not None else None),
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode())
    if payload.get("code") != 0:
        raise RuntimeError(f"Feishu request failed: {payload}")
    return payload


def get_json(url: str, bearer_token: str, *, timeout: int = 30) -> dict:
    return json_request(url, bearer_token, timeout=timeout)


def post_json(url: str, data: dict, bearer_token: str, *, timeout: int = 30) -> dict:
    return json_request(url, bearer_token, method="POST", data=data, timeout=timeout)


def patch_json(url: str, data: dict, bearer_token: str, *, timeout: int = 30) -> dict:
    return json_request(url, bearer_token, method="PATCH", data=data, timeout=timeout)


def delete_json(url: str, data: dict, bearer_token: str, *, timeout: int = 30) -> dict:
    return json_request(url, bearer_token, method="DELETE", data=data, timeout=timeout)
