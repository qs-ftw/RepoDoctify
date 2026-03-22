#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Callable

import lark_mcp_user_token_wrapper as wrapper


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 3000
SUCCESS_BODY = "authorization succeeded, you can close this page now\n"


Logger = Callable[[str], None]


@dataclass(frozen=True)
class LocalAuthServer:
    server: HTTPServer
    authorize_url: str
    public_base_url: str
    localhost_authorize_url: str


def normalize_public_base_url(public_base_url: str | None, port: int) -> str:
    if public_base_url:
        return public_base_url.rstrip("/")
    if port == 0:
        raise ValueError("public_base_url is required when port=0")
    return f"http://localhost:{port}"


def build_handler(
    *,
    store: wrapper.TokenStore,
    credentials: wrapper.AppCredentials,
    authorize_url: str,
    public_base_url: str,
    logger: Logger,
) -> type[BaseHTTPRequestHandler]:
    class LocalhostAuthHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            logger(f"[localhost-auth] {fmt % args}")

        def do_GET(self) -> None:  # noqa: N802
            if self.path.startswith("/authorize"):
                self.send_response(302)
                self.send_header("Location", authorize_url)
                self.end_headers()
                logger("[localhost-auth] redirected /authorize to upstream authorize URL")
                return

            if self.path.startswith("/callback"):
                callback_url = f"{public_base_url}{self.path}"
                try:
                    parsed = wrapper.parse_callback_url(callback_url)
                    wrapper.exchange_code_for_tokens(
                        store=store,
                        credentials=credentials,
                        code=parsed["code"],
                        state=parsed.get("state"),
                    )
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(SUCCESS_BODY.encode("utf-8"))
                    logger("[localhost-auth] authorization succeeded and token stored")
                except Exception as error:
                    body = f"authorization failed: {error}\n"
                    self.send_response(500)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(body.encode("utf-8"))
                    logger(f"[localhost-auth] authorization failed: {error}")
                return

            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"not found\n")

    return LocalhostAuthHandler


def build_server(
    *,
    store: wrapper.TokenStore,
    credentials: wrapper.AppCredentials,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    public_base_url: str | None = None,
    redirect_uri: str | None = None,
    scopes: list[str] | None = None,
    logger: Logger = print,
) -> LocalAuthServer:
    effective_public_base_url = normalize_public_base_url(public_base_url, port)
    effective_redirect_uri = redirect_uri or f"{effective_public_base_url}/callback"
    authorize_url = wrapper.build_authorize_url(
        store=store,
        credentials=credentials,
        redirect_uri=effective_redirect_uri,
        scopes=scopes or list(wrapper.DEFAULT_SCOPES),
    )
    handler = build_handler(
        store=store,
        credentials=credentials,
        authorize_url=authorize_url,
        public_base_url=effective_public_base_url,
        logger=logger,
    )
    server = HTTPServer((host, port), handler)
    return LocalAuthServer(
        server=server,
        authorize_url=authorize_url,
        public_base_url=effective_public_base_url,
        localhost_authorize_url=f"{effective_public_base_url}/authorize",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a localhost OAuth helper that persists Feishu user_access_token for lark-mcp."
    )
    parser.add_argument("--app-id", help="Feishu app id")
    parser.add_argument("--app-secret", help="Feishu app secret")
    parser.add_argument("--domain", default=None, help="Feishu domain")
    parser.add_argument(
        "--config-path",
        default=str(wrapper.DEFAULT_CONFIG_PATH),
        help="Codex config path used to infer app credentials",
    )
    parser.add_argument(
        "--store-path",
        default=str(wrapper.DEFAULT_STORE_PATH),
        help="Path to the local user-token JSON store",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="Host interface to bind locally",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Local TCP port to bind",
    )
    parser.add_argument(
        "--public-base-url",
        default=None,
        help="User-facing base URL; defaults to http://localhost:<port>",
    )
    parser.add_argument(
        "--redirect-uri",
        default=None,
        help="Explicit redirect URI; defaults to <public-base-url>/callback",
    )
    parser.add_argument(
        "--scope",
        nargs="+",
        default=None,
        help="OAuth scopes, defaults to offline_access plus docx read/write",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = wrapper.TokenStore(Path(args.store_path))
    credentials = wrapper.resolve_app_credentials(args)
    auth_server = build_server(
        store=store,
        credentials=credentials,
        host=args.host,
        port=args.port,
        public_base_url=args.public_base_url,
        redirect_uri=args.redirect_uri,
        scopes=args.scope,
    )
    print(f"LOCALHOST_AUTH_URL={auth_server.localhost_authorize_url}", flush=True)
    print(f"UPSTREAM_AUTHORIZE_URL={auth_server.authorize_url}", flush=True)
    print(f"TOKEN_STORE={Path(args.store_path).expanduser()}", flush=True)
    print(
        f"[localhost-auth] listening on {auth_server.public_base_url}",
        flush=True,
    )
    try:
        auth_server.server.serve_forever()
    except KeyboardInterrupt:
        print("[localhost-auth] stopped", flush=True)
    finally:
        auth_server.server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
