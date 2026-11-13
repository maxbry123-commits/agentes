# -*- coding: utf-8 -*-
"""Provenance writer — A-SE-05. No secrets. 0% LLM."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def build_provenance(
    *,
    pin: dict[str, Any],
    fetch_result: dict[str, Any] | None = None,
    install_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rec = {
        "schema_version": "1.0",
        "pin_id": pin.get("pin_id"),
        "pin_hash": pin.get("pin_hash"),
        "source_type": pin.get("source_type"),
        "digest": pin.get("digest"),
        "license": pin.get("license"),
        "locator_uri": (pin.get("locator") or {}).get("uri"),
        "fetch_status": (fetch_result or {}).get("status"),
        "install_status": (install_plan or {}).get("status"),
        "llm_control": pin.get("llm_control") or "DENY",
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    meta = dict(pin.get("meta") or {})
    for k in list(meta.keys()):
        if any(s in k.lower() for s in ("token", "password", "secret", "key")):
            meta[k] = "***REDACTED***"
    rec["meta"] = meta
    body = json.dumps(rec, sort_keys=True, separators=(",", ":"))
    rec["evidence_hash"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return rec
