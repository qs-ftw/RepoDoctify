#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_DOMAIN = "https://open.feishu.cn"
DEFAULT_REDIRECT_URI = "http://localhost:3000/callback"
DEFAULT_SCOPES = ["offline_access", "docx:document", "docx:document:readonly"]
DEFAULT_CONFIG_PATH = Path.home() / ".codex" / "config.toml"
DEFAULT_STORE_PATH = Path.home() / ".local" / "state" / "lark-mcp-user-token.json"
REFRESH_SKEW_SECONDS = 300


@dataclass(frozen=True)
class AppCredentials:
    app_id: str
    app_secret: str
    domain: str = DEFAULT_DOMAIN


class TokenStore:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temp_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.chmod(temp_path, 0o600)
        temp_path.replace(self.path)
        os.chmod(self.path, 0o600)


def load_app_credentials_from_codex_config(config_path: str | Path) -> AppCredentials:
    data = tomllib.loads(Path(config_path).expanduser().read_text(encoding="utf-8"))
    lark_section = data["mcp_servers"]["lark-mcp"]
    args = lark_section.get("args") or []

    app_id = None
    app_secret = None
    domain = DEFAULT_DOMAIN
    index = 0
    while index < len(args):
        item = args[index]
        next_item = args[index + 1] if index + 1 < len(args) else None
        if item in {"-a", "--app-id"} and next_item:
            app_id = next_item
            index += 2
            continue
        if item in {"-s", "--app-secret"} and next_item:
            app_secret = next_item
            index += 2
            continue
        if item in {"-d", "--domain"} and next_item:
            domain = next_item
            index += 2
            continue
        index += 1

    if not app_id or not app_secret:
        raise RuntimeError(
            f"could not find lark-mcp app credentials in {Path(config_path).expanduser()}"
        )
    return AppCredentials(app_id=app_id, app_secret=app_secret, domain=domain)


def resolve_app_credentials(args: argparse.Namespace) -> AppCredentials:
    if args.app_id and args.app_secret:
        return AppCredentials(
            app_id=args.app_id,
            app_secret=args.app_secret,
            domain=args.domain or DEFAULT_DOMAIN,
        )
    return load_app_credentials_from_codex_config(args.config_path)


def parse_callback_url(callback_url: str) -> dict[str, str]:
    parsed = urllib.parse.urlparse(callback_url)
    params = urllib.parse.parse_qs(parsed.query)
    code = params.get("code", [None])[0]
    if not code:
        raise ValueError("callback URL does not contain a code parameter")
    result = {"code": code}
    state = params.get("state", [None])[0]
    if state:
        result["state"] = state
    return result


def build_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("utf-8")).digest()
    ).rstrip(b"=").decode("utf-8")
    return verifier, challenge


def post_oauth_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OAuth request failed: {error.code} {body}") from error
    try:
        data = json.loads(body)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"OAuth response was not JSON: {body}") from error
    if "access_token" not in data and "error" in data:
        raise RuntimeError(
            f"OAuth request failed: {data['error']} {data.get('error_description', '')}".strip()
        )
    return data


def build_authorize_url(
    store: TokenStore,
    credentials: AppCredentials,
    redirect_uri: str = DEFAULT_REDIRECT_URI,
    scopes: list[str] | None = None,
    state: str | None = None,
    now: int | None = None,
) -> str:
    verifier, challenge = build_pkce_pair()
    auth_state = state or secrets.token_urlsafe(24)
    scope_list = scopes or list(DEFAULT_SCOPES)
    persisted = store.load()
    persisted.update(
        {
            "app_id": credentials.app_id,
            "pending_code_verifier": verifier,
            "pending_state": auth_state,
            "pending_redirect_uri": redirect_uri,
            "pending_scope": " ".join(scope_list),
            "updated_at": int(now if now is not None else time.time()),
        }
    )
    store.save(persisted)
    query = urllib.parse.urlencode(
        {
            "client_id": credentials.app_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "scope": " ".join(scope_list),
            "state": auth_state,
        }
    )
    return f"{credentials.domain.rstrip('/')}/open-apis/authen/v1/authorize?{query}"


def token_endpoint(credentials: AppCredentials) -> str:
    return f"{credentials.domain.rstrip('/')}/open-apis/authen/v2/oauth/token"


def apply_token_response(
    current: dict[str, Any], response: dict[str, Any], now: int | None = None
) -> dict[str, Any]:
    issued_at = int(now if now is not None else time.time())
    updated = dict(current)
    updated["access_token"] = response["access_token"]
    updated["token_type"] = response.get("token_type", updated.get("token_type", "Bearer"))
    updated["updated_at"] = issued_at
    expires_in = response.get("expires_in")
    if expires_in is not None:
        updated["expires_at"] = issued_at + int(expires_in)
    refresh_token = response.get("refresh_token")
    if refresh_token:
        updated["refresh_token"] = refresh_token
    refresh_expires_in = response.get("refresh_expires_in")
    if refresh_expires_in is not None:
        updated["refresh_expires_at"] = issued_at + int(refresh_expires_in)
    if response.get("scope"):
        updated["scope"] = response["scope"]
    updated.pop("pending_code_verifier", None)
    updated.pop("pending_state", None)
    updated.pop("pending_redirect_uri", None)
    updated.pop("pending_scope", None)
    return updated


def exchange_code_for_tokens(
    store: TokenStore,
    credentials: AppCredentials,
    code: str,
    state: str | None = None,
    now: int | None = None,
) -> dict[str, Any]:
    current = store.load()
    verifier = current.get("pending_code_verifier")
    redirect_uri = current.get("pending_redirect_uri")
    expected_state = current.get("pending_state")

    if not verifier or not redirect_uri:
        raise RuntimeError("no pending authorization context found; run authorize-url first")
    if expected_state and state and state != expected_state:
        raise RuntimeError("authorization state mismatch")
    if expected_state and not state:
        raise RuntimeError("callback did not contain a state value")

    response = post_oauth_json(
        token_endpoint(credentials),
        {
            "grant_type": "authorization_code",
            "client_id": credentials.app_id,
            "client_secret": credentials.app_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        },
    )
    updated = apply_token_response(current, response, now=now)
    store.save(updated)
    return updated


def should_refresh(
    stored: dict[str, Any], now: int | None = None, skew_seconds: int = REFRESH_SKEW_SECONDS
) -> bool:
    current_time = int(now if now is not None else time.time())
    access_token = stored.get("access_token")
    expires_at = stored.get("expires_at")
    if not access_token:
        return True
    if expires_at is None:
        return False
    return current_time >= int(expires_at) - skew_seconds


def refresh_access_token(
    store: TokenStore,
    credentials: AppCredentials,
    now: int | None = None,
) -> dict[str, Any]:
    current = store.load()
    refresh_token = current.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("no refresh token available; run authorize-url again")

    payload: dict[str, Any] = {
        "grant_type": "refresh_token",
        "client_id": credentials.app_id,
        "client_secret": credentials.app_secret,
        "refresh_token": refresh_token,
    }
    if current.get("scope"):
        payload["scope"] = current["scope"]

    response = post_oauth_json(token_endpoint(credentials), payload)
    updated = apply_token_response(current, response, now=now)
    store.save(updated)
    return updated


def ensure_valid_access_token(
    store: TokenStore,
    credentials: AppCredentials,
    now: int | None = None,
) -> str:
    stored = store.load()
    if not stored:
        raise RuntimeError("no stored user token found; run authorize-url first")
    if should_refresh(stored, now=now):
        stored = refresh_access_token(store, credentials, now=now)
    access_token = stored.get("access_token")
    if not access_token:
        raise RuntimeError("user token store does not contain an access token")
    return access_token


def sanitize_extra_args(extra_args: list[str] | None) -> list[str]:
    if not extra_args:
        return []
    args = list(extra_args)
    if args and args[0] == "--":
        args = args[1:]
    sanitized: list[str] = []
    skip_next = False
    flags_with_values = {
        "--token-mode",
        "-u",
        "--user-access-token",
        "-a",
        "--app-id",
        "-s",
        "--app-secret",
        "-d",
        "--domain",
    }
    for item in args:
        if skip_next:
            skip_next = False
            continue
        if item == "--oauth":
            continue
        if item in flags_with_values:
            skip_next = True
            continue
        sanitized.append(item)
    return sanitized


def build_lark_mcp_command(
    credentials: AppCredentials,
    access_token: str,
    extra_args: list[str] | None = None,
    package: str = "@larksuiteoapi/lark-mcp",
) -> list[str]:
    command = [
        "npx",
        "-y",
        package,
        "mcp",
        "-a",
        credentials.app_id,
        "-s",
        credentials.app_secret,
    ]
    if credentials.domain != DEFAULT_DOMAIN:
        command.extend(["-d", credentials.domain])
    command.extend(sanitize_extra_args(extra_args))
    command.extend(["--token-mode", "user_access_token", "-u", access_token])
    return command


def mask_token(token: str | None) -> str:
    if not token:
        return ""
    if len(token) <= 8:
        return "*" * len(token)
    return f"{token[:4]}{'*' * (len(token) - 8)}{token[-4:]}"


def handle_authorize_url(args: argparse.Namespace) -> int:
    store = TokenStore(args.store_path)
    credentials = resolve_app_credentials(args)
    url = build_authorize_url(
        store=store,
        credentials=credentials,
        redirect_uri=args.redirect_uri,
        scopes=args.scope or list(DEFAULT_SCOPES),
    )
    print("Authorization URL:")
    print(url)
    print()
    print("After approval, copy the full callback URL from the browser address bar and run:")
    print(f"python3 {Path(__file__)} exchange-url --url '<callback-url>'")
    return 0


def handle_exchange_code(args: argparse.Namespace) -> int:
    store = TokenStore(args.store_path)
    credentials = resolve_app_credentials(args)
    updated = exchange_code_for_tokens(
        store=store,
        credentials=credentials,
        code=args.code,
        state=args.state,
    )
    print(json.dumps({"status": "ok", "expires_at": updated.get("expires_at")}, indent=2))
    return 0


def handle_exchange_url(args: argparse.Namespace) -> int:
    parsed = parse_callback_url(args.url)
    store = TokenStore(args.store_path)
    credentials = resolve_app_credentials(args)
    updated = exchange_code_for_tokens(
        store=store,
        credentials=credentials,
        code=parsed["code"],
        state=parsed.get("state"),
    )
    print(json.dumps({"status": "ok", "expires_at": updated.get("expires_at")}, indent=2))
    return 0


def handle_refresh(args: argparse.Namespace) -> int:
    store = TokenStore(args.store_path)
    credentials = resolve_app_credentials(args)
    updated = refresh_access_token(store=store, credentials=credentials)
    print(
        json.dumps(
            {
                "status": "ok",
                "access_token": mask_token(updated.get("access_token")),
                "expires_at": updated.get("expires_at"),
            },
            indent=2,
        )
    )
    return 0


def handle_whoami(args: argparse.Namespace) -> int:
    store = TokenStore(args.store_path)
    data = store.load()
    if not data:
        print("No stored token state found.")
        return 1
    print(
        json.dumps(
            {
                "app_id": data.get("app_id"),
                "access_token": mask_token(data.get("access_token")),
                "refresh_token": mask_token(data.get("refresh_token")),
                "scope": data.get("scope"),
                "expires_at": data.get("expires_at"),
                "refresh_expires_at": data.get("refresh_expires_at"),
                "pending_state": data.get("pending_state"),
            },
            indent=2,
        )
    )
    return 0


def handle_print_env(args: argparse.Namespace) -> int:
    store = TokenStore(args.store_path)
    credentials = resolve_app_credentials(args)
    access_token = ensure_valid_access_token(store=store, credentials=credentials)
    print(f'export LARK_USER_ACCESS_TOKEN="{access_token}"')
    print('export LARK_TOKEN_MODE="user_access_token"')
    return 0


def handle_run_mcp(args: argparse.Namespace) -> int:
    store = TokenStore(args.store_path)
    credentials = resolve_app_credentials(args)
    try:
        access_token = ensure_valid_access_token(store=store, credentials=credentials)
    except Exception as error:  # pragma: no cover - manual path
        authorize_url = build_authorize_url(
            store=store,
            credentials=credentials,
            redirect_uri=args.redirect_uri,
            scopes=list(DEFAULT_SCOPES),
        )
        print(str(error), file=sys.stderr)
        print("Authorize a new user token with:", file=sys.stderr)
        print(authorize_url, file=sys.stderr)
        return 1

    command = build_lark_mcp_command(
        credentials=credentials,
        access_token=access_token,
        extra_args=args.extra_args,
    )
    os.execvp(command[0], command)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage Feishu user tokens for lark-mcp without keyring dependencies."
    )
    parser.add_argument("--app-id", help="Feishu app id")
    parser.add_argument("--app-secret", help="Feishu app secret")
    parser.add_argument("--domain", default=None, help="Feishu domain")
    parser.add_argument(
        "--config-path",
        default=str(DEFAULT_CONFIG_PATH),
        help="Codex config path used to infer app credentials",
    )
    parser.add_argument(
        "--store-path",
        default=str(DEFAULT_STORE_PATH),
        help="Path to the local user-token JSON store",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    authorize_url = subparsers.add_parser(
        "authorize-url",
        help="Generate a Feishu authorization URL and persist pending PKCE state",
    )
    authorize_url.add_argument(
        "--redirect-uri",
        default=DEFAULT_REDIRECT_URI,
        help="Redirect URI already configured in the Feishu app",
    )
    authorize_url.add_argument(
        "--scope",
        nargs="+",
        default=None,
        help="OAuth scopes, defaults to offline_access plus docx read/write",
    )
    authorize_url.set_defaults(handler=handle_authorize_url)

    exchange_code = subparsers.add_parser(
        "exchange-code",
        help="Exchange an authorization code for user tokens",
    )
    exchange_code.add_argument("--code", required=True, help="Authorization code")
    exchange_code.add_argument(
        "--state", default=None, help="Optional state copied from the callback URL"
    )
    exchange_code.set_defaults(handler=handle_exchange_code)

    exchange_url = subparsers.add_parser(
        "exchange-url",
        help="Parse a callback URL and exchange its code for user tokens",
    )
    exchange_url.add_argument("--url", required=True, help="Full callback URL")
    exchange_url.set_defaults(handler=handle_exchange_url)

    refresh = subparsers.add_parser("refresh", help="Refresh the stored access token")
    refresh.set_defaults(handler=handle_refresh)

    whoami = subparsers.add_parser("whoami", help="Show stored token metadata")
    whoami.set_defaults(handler=handle_whoami)

    print_env = subparsers.add_parser(
        "print-env",
        help="Print shell exports for the current user access token",
    )
    print_env.set_defaults(handler=handle_print_env)

    run_mcp = subparsers.add_parser(
        "run-mcp",
        help="Run lark-mcp with an injected user_access_token",
    )
    run_mcp.add_argument(
        "--redirect-uri",
        default=DEFAULT_REDIRECT_URI,
        help="Redirect URI to use if reauthorization becomes necessary",
    )
    run_mcp.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Additional downstream lark-mcp arguments after --",
    )
    run_mcp.set_defaults(handler=handle_run_mcp)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
