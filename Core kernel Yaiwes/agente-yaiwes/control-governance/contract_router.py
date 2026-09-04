# -*- coding: utf-8 -*-
"""ContractRouter — D7. Load SALIDA4 13 operation types. 0% LLM.

Source of truth: control-layer/rules/routing.yaml (B0 DONE).
Does not rewrite 85 contract bodies — only selects contract IDs by op type.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

# Fallback if yaml missing / file absent (must stay = 13 keys)
DEFAULT_ROUTING: dict[str, list[str]] = {
    "READ_LOCAL": ["C03", "C04", "C28", "C41"],
    "WRITE_LOCAL": ["C03", "C04", "C27", "C29", "C35", "C45", "C48"],
    "NETWORK_CALL": ["C33", "C36", "C37", "C38", "C40", "C41", "C42"],
    "LLM_CALL": ["C02", "C03", "C28", "C33", "C36", "C40", "C41", "C43", "C44", "C49", "C73"],
    "MOUNT_EXTENSION": ["C51", "C52", "C53", "C54", "C55", "C82", "C83", "C84", "C85"],
    "CODE_EXEC": ["C03", "C27", "C29", "C35", "C45", "C48", "C33"],
    "FILE_DELETE": ["C03", "C04", "C27", "C29", "C45", "C48"],
    "GIT_OP": ["C33", "C36", "C40", "C41", "C45", "C82"],
    "DEPLOY": ["C33", "C36", "C40", "C45", "C48", "C82", "C83", "C85"],
    "RESEARCH": ["C02", "C28", "C33", "C36", "C41", "C73", "C81"],
    "CREDENTIAL_USE": ["C33", "C36", "C40", "C45", "C47", "C48", "C49"],
    "STATE_WRITE": ["C03", "C04", "C27", "C28", "C29"],
    "PARALLEL_BATCH": ["C03", "C28", "C33", "C36", "C41", "C44"],
}

ALWAYS = ["C00"]  # governance


def _load_yaml_routing() -> dict[str, list[str]] | None:
    root = Path(__file__).resolve().parents[3]
    path = root / "control-layer" / "rules" / "routing.yaml"
    if not path.is_file():
        return None
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, list[str]] = {}
    for k, v in data.items():
        if str(k).startswith("#"):
            continue
        if isinstance(v, list):
            out[str(k)] = [str(x) for x in v]
    return out if out else None


class ContractRouter:
    def __init__(self, routing: dict[str, list[str]] | None = None):
        self.routing = routing or _load_yaml_routing() or dict(DEFAULT_ROUTING)

    def operation_types(self) -> list[str]:
        return sorted(self.routing.keys())

    def select(self, operation: str, *,
               include_c00: bool = True) -> dict[str, Any]:
        op = (operation or "").upper()
        if op not in self.routing:
            return {
                "ok": False,
                "reason": "UNKNOWN_OPERATION",
                "operation": op,
                "known": self.operation_types(),
            }
        contracts = list(self.routing[op])
        if include_c00 and "C00" not in contracts:
            contracts = ALWAYS + contracts
        return {
            "ok": True,
            "operation": op,
            "contracts": contracts,
            "n": len(contracts),
            "source": "routing.yaml" if _load_yaml_routing() else "DEFAULT_ROUTING",
        }

    def assert_13(self) -> dict[str, Any]:
        n = len(self.routing)
        return {
            "ok": n == 13,
            "count": n,
            "types": self.operation_types(),
        }
