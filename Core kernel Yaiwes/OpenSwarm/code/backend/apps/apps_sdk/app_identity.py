"""Per-app minted tokens: the ENG-215 v2 hardening. The runtime mints a random token per app
workspace at spawn and the grant gate resolves identity FROM the token, so an app backend can no
longer claim another app's id by writing a different OPENSWARM_OUTPUT_ID style self-report.
Webview apps keep the stronger Origin-port binding; this covers the process lane."""

import json
import os
import secrets
import threading
from typing import Dict, Optional

from typeguard import typechecked

from backend.apps.settings.store import DATA_DIR

APP_TOKENS_FILE = os.path.join(DATA_DIR, "app_tokens.json")

p_lock = threading.Lock()


@typechecked
def p_read_tokens() -> Dict[str, str]:
    try:
        with open(APP_TOKENS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {str(k): str(v) for k, v in raw.items()}
    except Exception:
        return {}


@typechecked
def p_write_tokens(tokens: Dict[str, str]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = APP_TOKENS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)
    os.replace(tmp, APP_TOKENS_FILE)


@typechecked
def mint_app_token(output_id: str) -> str:
    """One stable token per app workspace: re-minting on every spawn would orphan a still-running
    instance's env copy, so an existing token is reused. Persisted so a backend restart doesn't
    strand the tokens live app processes already hold."""
    with p_lock:
        tokens = p_read_tokens()
        for token, oid in tokens.items():
            if oid == output_id:
                return token
        token = secrets.token_urlsafe(24)
        tokens[token] = output_id
        p_write_tokens(tokens)
        return token


@typechecked
def resolve_app_token(token: str) -> Optional[str]:
    if not token:
        return None
    with p_lock:
        return p_read_tokens().get(token)


@typechecked
def revoke_app_token(output_id: str) -> None:
    with p_lock:
        tokens = p_read_tokens()
        kept = {t: oid for t, oid in tokens.items() if oid != output_id}
        if len(kept) != len(tokens):
            p_write_tokens(kept)
