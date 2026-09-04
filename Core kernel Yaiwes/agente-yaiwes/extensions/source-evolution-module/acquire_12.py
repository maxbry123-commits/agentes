# -*- coding: utf-8 -*-
"""C-14 acquire_12 — plan acquisition of repo/source without network. 0% LLM."""
from __future__ import annotations

import re
from typing import Any

from .resource_gate import POST_WORDFLOW_FETCH_ENABLED

_GITHUB = re.compile(r"(?:https?://github\.com/|git@github\.com:)([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", re.I)
_HF = re.compile(r"(?:https?://huggingface\.co/|hf://)([\w.-]+)/([\w.-]+)/?", re.I)


class AcquireError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def parse_source(ref: str) -> dict[str, Any]:
    ref = (ref or "").strip()
    if not ref:
        raise AcquireError("REF_EMPTY")
    m = _GITHUB.match(ref)
    if m:
        return {"provider": "github", "owner": m.group(1), "name": m.group(2), "ref": ref}
    m = _HF.match(ref)
    if m:
        return {"provider": "hf", "owner": m.group(1), "name": m.group(2), "ref": ref}
    if ref.startswith("local://") or ref.startswith("/"):
        return {"provider": "local", "path": ref.replace("local://", ""), "ref": ref}
    return {"provider": "url", "ref": ref}


def plan_acquire(
    sources: list[str],
    *,
    mode: str = "partial",
    pin: str | None = None,
) -> dict[str, Any]:
    """Build acquisition plan. Never fetches. Remote fetch gated."""
    if not sources:
        raise AcquireError("NO_SOURCES")
    if mode not in ("partial", "full", "index_only"):
        raise AcquireError("BAD_MODE", mode)

    items = []
    for src in sources:
        meta = parse_source(src)
        provider = meta["provider"]
        fetchable = False
        if provider == "local":
            fetchable = True
        elif POST_WORDFLOW_FETCH_ENABLED:
            fetchable = True
        items.append({
            **meta,
            "mode": mode,
            "pin": pin,
            "fetchable": fetchable,
            "action": "PLAN_ONLY" if not fetchable else "READY_TO_FETCH",
        })

    blocked = [i for i in items if i["action"] == "PLAN_ONLY" and i["provider"] != "local"]
    return {
        "ok": True,
        "count": len(items),
        "items": items,
        "remote_blocked": len(blocked),
        "post_wordflow_fetch_enabled": bool(POST_WORDFLOW_FETCH_ENABLED),
        "llm_control": "DENY",
    }


def acquire_12(sources: list[str], **kwargs: Any) -> dict[str, Any]:
    return plan_acquire(sources, **kwargs)
