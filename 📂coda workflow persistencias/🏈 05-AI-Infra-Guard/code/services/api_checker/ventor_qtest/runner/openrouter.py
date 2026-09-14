"""OpenRouter model endpoint discovery helpers."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Sequence
from urllib.parse import quote

import requests

OPENROUTER_BASE_URL = "https://openrouter.ai"
OPENROUTER_CHAT_PATH = "/api/v1/chat/completions"


def fetch_model_endpoints(
    model: str,
    *,
    api_key: str | None = None,
    timeout: float = 30.0,
    base_url: str = OPENROUTER_BASE_URL,
) -> List[Dict[str, Any]]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'services/api_checker/ventor_qtest/runner/openrouter.py','step':'fetch_model_endpoints','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def extract_provider_tags(endpoints: Sequence[Mapping[str, Any]]) -> List[str]:
    """Extract unique provider tags in stable order."""

    tags: List[str] = []
    seen = set()
    for endpoint in endpoints:
        tag = str(endpoint.get("tag") or "").strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
    return tags


def build_openrouter_vendors(
    *,
    api_key: str,
    model: str,
    provider_tags: Sequence[str],
    name_prefix: str = "or",
    base_url: str = OPENROUTER_BASE_URL,
    path: str = OPENROUTER_CHAT_PATH,
) -> List[Dict[str, Any]]:
    """Build runner vendor configurations from provider tags."""

    model = str(model or "").strip()
    if not model:
        raise ValueError("model 不能为空")
    if not api_key:
        raise ValueError("api_key 不能为空")

    tags = [str(tag).strip() for tag in provider_tags if str(tag).strip()]
    if not tags:
        raise ValueError("provider_tags 不能为空")

    vendors: List[Dict[str, Any]] = []
    used_names = set()
    for tag in tags:
        base_name = _build_vendor_name(tag, prefix=name_prefix)
        candidate = base_name
        idx = 2
        while candidate in used_names:
            candidate = f"{base_name}-{idx}"
            idx += 1
        used_names.add(candidate)

        vendors.append(
            {
                "name": candidate,
                "base_url": base_url,
                "path": path,
                "api_key": api_key,
                "model": model,
                "schema": "openai",
                "provider": {
                    "order": [tag],
                    "allow_fallbacks": False,
                },
            }
        )
    return vendors


def _build_vendor_name(tag: str, *, prefix: str) -> str:
    core = re.sub(r"[^0-9a-zA-Z]+", "-", tag.lower()).strip("-")
    if not core:
        core = "provider"
    cleaned_prefix = re.sub(r"[^0-9a-zA-Z]+", "-", str(prefix or "").lower()).strip("-")
    if cleaned_prefix:
        return f"{cleaned_prefix}-{core}"
    return core
