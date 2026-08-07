"""Verificar despliegue — genera evidence.json.
SOURCE: CAPA DE CONTROL 1 · sin evidence.json no está desplegado.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import hashlib
import json
from datetime import datetime, timezone


@dataclass
class Evidence:
    ok: bool
    timestamp: str
    files_count: int
    local_hashes: dict[str, str]
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verificar(root: str | Path, mapped: list[dict[str, str]]) -> Evidence:
    root_p = Path(root)
    hashes: dict[str, str] = {}
    for item in mapped:
        src = root_p / item["src"]
        if src.exists() and src.is_file():
            hashes[item["src"]] = _sha256(src)

    ok = len(hashes) == len(mapped) and len(mapped) > 0
    return Evidence(
        ok=ok,
        timestamp=datetime.now(timezone.utc).isoformat(),
        files_count=len(hashes),
        local_hashes=hashes,
        notes="local verification only; remote compare is runtime step",
    )


def write_evidence(evidence: Evidence, out: str | Path = "evidence.json") -> None:
    Path(out).write_text(json.dumps(evidence.to_dict(), indent=2), encoding="utf-8")
