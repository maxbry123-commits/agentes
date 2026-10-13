"""Contract Rule Engine — when→add, set puro.
SOURCE: SALIDA_4 · routing.yaml · fingerprint + threat
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from .fingerprint import Fingerprint, build_fingerprint
from .threat import analyze, ThreatResult


def _load_routing(path: str | Path | None = None) -> dict[str, Any]:
    import yaml
    p = Path(path or Path(__file__).resolve().parent.parent / "rules" / "routing.yaml")
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _detect_operation(fp: Fingerprint) -> str:
    if fp.credentials:
        return "CREDENTIAL_ACCESS"
    if fp.irreversible and fp.writes:
        return "DELETE"
    if fp.network and fp.external:
        return "NETWORK_CALL"
    if fp.writes:
        return "WRITE_LOCAL"
    if fp.action in {"exec", "execute", "command"}:
        return "EXEC_COMMAND"
    if fp.action == "llm":
        return "LLM_CALL"
    return "READ_LOCAL"


def select_contracts(
    text: str,
    action: str = "unknown",
    data_sensitivity: str = "internal",
    routing_path: str | Path | None = None,
) -> dict[str, Any]:
    fp = build_fingerprint(text, action)
    threat: ThreatResult = analyze(fp, data_sensitivity)
    routing = _load_routing(routing_path)

    op = _detect_operation(fp)
    base = list(routing.get("operation_contracts", {}).get(op, ["C03", "C28"]))
    mods = routing.get("modifiers", {})

    extra: list[str] = []
    if threat.level == "quarantine" or threat.score >= 8:
        extra += mods.get("risk_high", [])
    if fp.irreversible:
        extra += mods.get("irreversible", [])
    if fp.credentials:
        extra += mods.get("secrets", [])
    if fp.parallel:
        extra += mods.get("parallel", [])
    if fp.external:
        extra += mods.get("cross_system", [])

    contracts = sorted(set(base + extra))
    allowed = threat.level != "quarantine"

    return {
        "operation": op,
        "fingerprint": fp.as_dict(),
        "threat": {"score": threat.score, "level": threat.level},
        "contracts": contracts,
        "allowed": allowed,
    }
