"""Fingerprint Engine · 7 booleanos · 0% LLM · determinista.

Misma entrada estructurada → mismo fingerprint (hash estable).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

# Señales mínimas (alineadas con risk_matrix.yaml)
_CREDENTIAL_RE = re.compile(
    r"(api[_-]?key|secret|password|token|private[_-]?key|aws_access|BEGIN (RSA|OPENSSH))",
    re.I,
)
_NETWORK_RE = re.compile(r"https?://|ftp://", re.I)
_EXEC_RE = re.compile(r"subprocess|os\.system|shell\s*=\s*True|\beval\s*\(|\bexec\s*\(", re.I)


@dataclass(frozen=True)
class Fingerprint:
    """7 booleanos + tipo de operación + hash estable."""

    is_read: bool
    is_write: bool
    is_delete: bool
    is_exec: bool
    is_network: bool
    is_secret: bool
    is_external: bool
    op_type: str
    fingerprint_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _norm_op(raw: str | None) -> str:
    if not raw:
        return "READ_LOCAL"
    return str(raw).strip().upper()


def _payload_text(payload: Mapping[str, Any] | None) -> str:
    if not payload:
        return ""
    try:
        return json.dumps(payload, sort_keys=True, default=str)
    except TypeError:
        return str(payload)


def build_fingerprint(
    *,
    op_type: str | None = None,
    path: str | None = None,
    payload: Mapping[str, Any] | None = None,
    flags: Mapping[str, bool] | None = None,
) -> Fingerprint:
    """Construye fingerprint determinista.

    flags opcionales permiten al caller declarar hechos ya conocidos
    (p.ej. is_network=True). Si no, se infiere de op_type + payload + path.
    """
    op = _norm_op(op_type)
    text = _payload_text(payload) + " " + (path or "")
    flags = dict(flags or {})

    is_read = flags.get("is_read", op.startswith("READ") or "READ" in op)
    is_write = flags.get("is_write", "WRITE" in op or "CREATE" in op or "UPDATE" in op)
    is_delete = flags.get("is_delete", "DELETE" in op or "REMOVE" in op)
    is_exec = flags.get("is_exec", "EXEC" in op or "COMMAND" in op or bool(_EXEC_RE.search(text)))
    is_network = flags.get(
        "is_network",
        "NETWORK" in op or "EXTERNAL" in op or "API" in op or bool(_NETWORK_RE.search(text)),
    )
    is_secret = flags.get("is_secret", bool(_CREDENTIAL_RE.search(text)))
    is_external = flags.get("is_external", is_network or "CROSS_SYSTEM" in op or "EXTERNAL" in op)

    # Elevación: write + secret → sigue siendo write pero secret=true
    canonical = {
        "is_read": bool(is_read),
        "is_write": bool(is_write),
        "is_delete": bool(is_delete),
        "is_exec": bool(is_exec),
        "is_network": bool(is_network),
        "is_secret": bool(is_secret),
        "is_external": bool(is_external),
        "op_type": op,
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    return Fingerprint(
        is_read=canonical["is_read"],
        is_write=canonical["is_write"],
        is_delete=canonical["is_delete"],
        is_exec=canonical["is_exec"],
        is_network=canonical["is_network"],
        is_secret=canonical["is_secret"],
        is_external=canonical["is_external"],
        op_type=op,
        fingerprint_hash=f"sha256:{h}",
    )
