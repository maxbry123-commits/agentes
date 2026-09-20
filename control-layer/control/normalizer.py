"""Normalizer — entrada a estructura estándar.
SOURCE: SALIDA_4 · CAPA DE CONTROL A1
"""
from __future__ import annotations
from typing import Any


def normalize(raw: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(raw, str):
        return {"text": raw, "action": "unknown", "data_sensitivity": "internal"}
    out = dict(raw)
    out.setdefault("text", "")
    out.setdefault("action", "unknown")
    out.setdefault("data_sensitivity", "internal")
    return out
