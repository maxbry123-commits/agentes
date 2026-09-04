"""Sentinela / Router de schemas · activa contratos y procesos · 0% LLM.

No solo valida: **enciende** el subconjunto de C01-C85 que aplica a la
operación y expone el plan de procesos (sheriff, evidence, durable, etc.).

Dual: usable desde Wordflow entrypoint y desde extension ABI.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from .compiler import ContractSet, compile_contract_set
from .fingerprint import Fingerprint, build_fingerprint
from .threat import ThreatResult, analyze_threat

# Mapa contrato → procesos que activa (declarativo, no código de negocio)
PROCESS_MAP: dict[str, tuple[str, ...]] = {
    "C00": ("engine_boot_gate",),
    "C02": ("pre_exec_check",),
    "C03": ("isolation_scope",),
    "C04": ("acl_check",),
    "C27": ("state_write",),
    "C28": ("timeout_budget",),
    "C29": ("saga_or_step",),
    "C33": ("timeout_watch",),
    "C34": ("timeout_hard",),
    "C35": ("rollback",),
    "C36": ("retry_policy",),
    "C41": ("rate_limit",),
    "C43": ("token_budget",),
    "C45": ("secret_scan",),
    "C47": ("credential_gate",),
    "C48": ("audit_trail",),
    "C49": ("evidence_emit",),
    "C51": ("capability_resolve",),
    "C52": ("provenance",),
    "C53": ("test_gate",),
    "C54": ("trust_score",),
    "C55": ("promotion_shadow",),
    "C73": ("llm_boundary",),
    "C74": ("secret_llm_block",),
    "C82": ("extension_mount",),
    "C83": ("extension_health",),
    "C84": ("extension_capabilities",),
    "C85": ("extension_execute",),
}

# Severidad default por prefijo de contrato (hasta YAML fino por Cxx)
SEVERITY_HINT: dict[str, str] = {
    "C00": "alta",
    "C47": "alta",
    "C48": "alta",
    "C49": "alta",
    "C45": "alta",
    "C74": "alta",
    "C34": "alta",
    "C35": "alta",
    "C82": "alta",
    "C83": "alta",
    "C84": "alta",
    "C85": "alta",
}


@dataclass(frozen=True)
class ActivatedSchema:
    contract_id: str
    processes: tuple[str, ...]
    severity: str


@dataclass(frozen=True)
class SentinelaDecision:
    """Salida del router: qué schemas están activos y qué procesos correr."""

    op_type: str
    suggested_op_type: str
    fingerprint_hash: str
    set_hash: str
    risk_score: int
    band: str
    elevated: bool
    active_contracts: tuple[str, ...]
    activated: tuple[ActivatedSchema, ...]
    process_plan: tuple[str, ...]  # orden de ejecución de procesos
    sheriff_required: bool
    block_execution: bool  # quarantine + secret sin limpia
    mode_hint: str  # wordflow | extension | dual

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["activated"] = [asdict(a) for a in self.activated]
        return d


def _severity_for(cid: str) -> str:
    return SEVERITY_HINT.get(cid, "media" if cid.startswith("C0") or cid.startswith("C1") else "baja")


def _process_plan(contracts: Sequence[str]) -> tuple[str, ...]:
    seen: list[str] = []
    for cid in contracts:
        for p in PROCESS_MAP.get(cid, ()):
            if p not in seen:
                seen.append(p)
    # orden fijo de fases de control
    preferred = [
        "engine_boot_gate",
        "pre_exec_check",
        "isolation_scope",
        "acl_check",
        "secret_scan",
        "credential_gate",
        "timeout_budget",
        "token_budget",
        "rate_limit",
        "capability_resolve",
        "extension_mount",
        "extension_health",
        "extension_capabilities",
        "saga_or_step",
        "state_write",
        "timeout_watch",
        "retry_policy",
        "llm_boundary",
        "secret_llm_block",
        "extension_execute",
        "audit_trail",
        "evidence_emit",
        "provenance",
        "test_gate",
        "trust_score",
        "promotion_shadow",
        "timeout_hard",
        "rollback",
    ]
    ordered = [p for p in preferred if p in seen]
    # cualquier proceso no listado al final
    for p in seen:
        if p not in ordered:
            ordered.append(p)
    return tuple(ordered)


def route(
    *,
    op_type: str,
    path: str | None = None,
    payload: Mapping[str, Any] | None = None,
    flags: Mapping[str, bool] | None = None,
    mount_mode: str = "dual",
    strict_reverse: bool = True,
) -> SentinelaDecision:
    """Activa schemas y construye process_plan.

    mount_mode: wordflow | extension | dual
    """
    cs: ContractSet = compile_contract_set(
        op_type=op_type,
        path=path,
        payload=payload,
        flags=flags,
        strict_reverse=strict_reverse,
    )

    activated = tuple(
        ActivatedSchema(
            contract_id=cid,
            processes=PROCESS_MAP.get(cid, ()),
            severity=_severity_for(cid),
        )
        for cid in cs.contracts
    )
    plan = _process_plan(cs.contracts)

    sheriff_required = cs.band in ("sheriff_check", "quarantine") or cs.elevated
    block = cs.band == "quarantine" and (
        "credential_gate" in plan or cs.suggested_op_type == "CREDENTIAL_ACCESS"
    )

    mode = mount_mode if mount_mode in ("wordflow", "extension", "dual") else "dual"

    return SentinelaDecision(
        op_type=cs.op_type,
        suggested_op_type=cs.suggested_op_type,
        fingerprint_hash=cs.fingerprint_hash,
        set_hash=cs.set_hash,
        risk_score=cs.risk_score,
        band=cs.band,
        elevated=cs.elevated,
        active_contracts=cs.contracts,
        activated=activated,
        process_plan=plan,
        sheriff_required=sheriff_required,
        block_execution=block,
        mode_hint=mode,
    )


def route_from_contract_set(
    cs: ContractSet,
    *,
    mount_mode: str = "dual",
) -> SentinelaDecision:
    """Reusa un ContractSet ya compilado (evita doble compile)."""
    activated = tuple(
        ActivatedSchema(
            contract_id=cid,
            processes=PROCESS_MAP.get(cid, ()),
            severity=_severity_for(cid),
        )
        for cid in cs.contracts
    )
    plan = _process_plan(cs.contracts)
    sheriff_required = cs.band in ("sheriff_check", "quarantine") or cs.elevated
    block = cs.band == "quarantine" and (
        "credential_gate" in plan or cs.suggested_op_type == "CREDENTIAL_ACCESS"
    )
    mode = mount_mode if mount_mode in ("wordflow", "extension", "dual") else "dual"
    return SentinelaDecision(
        op_type=cs.op_type,
        suggested_op_type=cs.suggested_op_type,
        fingerprint_hash=cs.fingerprint_hash,
        set_hash=cs.set_hash,
        risk_score=cs.risk_score,
        band=cs.band,
        elevated=cs.elevated,
        active_contracts=cs.contracts,
        activated=activated,
        process_plan=plan,
        sheriff_required=sheriff_required,
        block_execution=block,
        mode_hint=mode,
    )
