# -*- coding: utf-8 -*-
"""control/fingerprint.py — Fingerprint Engine 0% LLM.
Fuente: SALIDA 4 §14.2 · CAPA_CONTROL_1 A2
Huella determinista: 7 booleanos + action. Sin LLM.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Union


@dataclass(frozen=True)
class Fingerprint:
    """Huella de operación. Mismo input → mismo fingerprint (L15)."""

    action: str
    writes: bool
    network: bool
    external: bool
    credentials: bool
    irreversible: bool
    parallel: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def hash(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True).encode("utf-8")
        return "sha256:" + hashlib.sha256(raw).hexdigest()


# Patrones deterministas (orden fijo → reproducibilidad)
_ACTION_PATTERNS = (
    ("delete", re.compile(r"\b(delete|remove|rm|unlink|drop)\b", re.I)),
    ("install", re.compile(r"\b(install|pip\s+install|npm\s+i|apt\s+install|clone)\b", re.I)),
    ("mount", re.compile(r"\b(mount|load_extension|register_extension)\b", re.I)),
    ("exec", re.compile(r"\b(exec|execute|run|subprocess|shell)\b", re.I)),
    ("write", re.compile(r"\b(write|save|create|update|commit|push|put)\b", re.I)),
    ("network", re.compile(r"\b(http|https|fetch|request|api|download|curl)\b", re.I)),
    ("read", re.compile(r"\b(read|get|list|show|cat|load)\b", re.I)),
)

_NETWORK = re.compile(r"(https?://|ftp://|\bapi\b|\bendpoint\b|\burl\b)", re.I)
_SECRET = re.compile(
    r"\b(token|secret|password|api[_-]?key|credential|bearer|authorization)\b", re.I
)
_EXTERNAL = re.compile(r"\b(github|huggingface|docker\.io|npmjs|pypi|external|remote)\b", re.I)
_IRREVERSIBLE = re.compile(
    r"\b(delete|drop|purge|destroy|force|rm\s+-rf|wipe|revoke)\b", re.I
)
_PARALLEL = re.compile(r"\b(parallel|concurrent|async|batch|fan-?out)\b", re.I)
_WRITE = re.compile(
    r"\b(write|install|create|update|commit|push|save|put|mount|register)\b", re.I
)


def _as_text(data: Union[str, Dict[str, Any], None]) -> str:
    if data is None:
        return ""
    if isinstance(data, dict):
        return json.dumps(data, sort_keys=True, default=str)
    return str(data)


def _detect_action(text: str) -> str:
    for name, pat in _ACTION_PATTERNS:
        if pat.search(text):
            return name
    return "unknown"


def build_fingerprint(input_data: Union[str, Dict[str, Any], None]) -> Fingerprint:
    """Construye Fingerprint desde input crudo. 0% LLM. Determinista."""
    text = _as_text(input_data)
    lower = text.lower()
    return Fingerprint(
        action=_detect_action(lower),
        writes=bool(_WRITE.search(lower)),
        network=bool(_NETWORK.search(lower)),
        external=bool(_EXTERNAL.search(lower)),
        credentials=bool(_SECRET.search(lower)),
        irreversible=bool(_IRREVERSIBLE.search(lower)),
        parallel=bool(_PARALLEL.search(lower)),
    )


def fingerprint_from_dict(d: Dict[str, Any]) -> Fingerprint:
    """Rehidrata Fingerprint desde dict (tests / state)."""
    return Fingerprint(
        action=str(d.get("action", "unknown")),
        writes=bool(d.get("writes", False)),
        network=bool(d.get("network", False)),
        external=bool(d.get("external", False)),
        credentials=bool(d.get("credentials", False)),
        irreversible=bool(d.get("irreversible", False)),
        parallel=bool(d.get("parallel", False)),
    )
