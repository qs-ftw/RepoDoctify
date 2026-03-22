from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import lark_mcp_user_token_wrapper as wrapper


DEFAULT_CONFIG_PATH = wrapper.DEFAULT_CONFIG_PATH
DEFAULT_STORE_PATH = wrapper.DEFAULT_STORE_PATH
AppCredentials = wrapper.AppCredentials
TokenStore = wrapper.TokenStore


def resolve_app_credentials(args) -> AppCredentials:
    return wrapper.resolve_app_credentials(args)


def ensure_valid_access_token(store: TokenStore, credentials: AppCredentials, now: int | None = None) -> str:
    return wrapper.ensure_valid_access_token(store, credentials, now=now)
