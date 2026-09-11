"""Deterministic proof gate for the canonical FABLES/Ficha plugin binding.

This module does not implement a second plugin bus. It verifies the adapted
UniversalPluginBus + FichaContract v2 already living under runtime/src/uek.
Candidate source is inspected statically by that bus and is never executed by
this gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from runtime.src.uek.universal_plugin_bus_v2_integrated import (
    ComponentCandidate,
    PluginStatus,
    TargetConventions,
    UniversalPluginBus,
)

CANONICAL_BINDING_ID = "UNIVERSAL_PLUGIN_BUS"
BUS_SOURCE_UPLOAD_SHA256 = "5e4595a86bfd68a3c1fde70ba614ce7b9ec6ea4d6c867912e836cca33c626fc3"
FICHA_SOURCE_UPLOAD_SHA256 = "759d0d7855d8df106462b966bfc4ee543f24a3e789a27048f253159b58ff8d1a"
CONTRACT_ID = "yaiwes.fables_binding/v1"


@dataclass(frozen=True)
class FablesBindingVerification:
    verified: bool
    binding_id: str
    contract_id: str
    reason_codes: Tuple[str, ...]
    registry_verified: bool
    ficha_verified: bool
    unsafe_candidate_rejected: bool
    execution_authorized: bool = False
    deployment_authorized: bool = False


def _manifest() -> dict:
    return {
        "artifact_id": "yaiwes.fables.binding",
        "version": "2.0.0",
        "estado": "active",
        "contract_hash": "sha256:" + "b" * 64,
        "tribunal_case_id": "G018-CANONICAL",
        "contrato": {
            "rol": "reasoning_binding",
            "consume": {"datatype": {"family": "task", "type": "generation_request", "version": 1}},
            "expone": {"datatype": {"family": "decision", "type": "generation_gate", "version": 1}},
        },
        "ejecucion": {
            "kind": "code",
            "transport": "importlib",
            "runtime_type": "reasoning",
            "idempotente": True,
            "allowed_actions": ["static_contract_validation", "registry_binding"],
        },
        "seguridad": {
            "sandbox": "process",
            "permisos": [],
            "limites": {"timeout_ms": 5000},
        },
        "firma": {"gpg_key_id": "G018-LOCAL-VERIFIED"},
        "categoria": "pipeline",
        "etapa": "P",
        "perfiles": {
            "n0": {
                "habilitada": True,
                "iteraciones": 1,
                "simulaciones": 0,
                "criticas": 0,
                "muestras_k": 1,
            }
        },
        "presupuesto": {
            "n0": {"max_tokens": 0, "max_ms": 5000, "max_costo_usd": 0.0}
        },
        "evidencia": {"produce": ["L1_static", "L2_build"], "destino": "runtime/evidence/"},
        "salud": {"metodo": "ping", "heartbeat_interval_s": 30},
        "activacion": {"eventos": ["yaiwes.fables.binding.verified"]},
    }


def verify_canonical_fables_binding() -> FablesBindingVerification:
    reasons = []
    try:
        bus = UniversalPluginBus()
        bus.add_tribunal_approval("G018-CANONICAL")
        candidate = ComponentCandidate(
            "def fables_binding_probe(value=None): return value",
            "python",
            ["runtime/src/core/fables_binding_gate.py"],
        )
        conventions = TargetConventions("python", "snake_case", "sync", "gradual")
        reg = bus.enchufar(_manifest(), candidate, conventions, registered_by="G018_GATE")

        ficha_ok = reg.ficha is not None and reg.ficha.artifact_id == "yaiwes.fables.binding"
        registry_ok = (
            reg.status == PluginStatus.ACTIVE
            and bus.registry.get("yaiwes.fables.binding") is reg
            and any(e["level"] == "L2_build" for e in bus.evidence.get("yaiwes.fables.binding"))
            and bus.trigger_plugin("yaiwes.fables.binding", "yaiwes.fables.binding.verified", {})
        )

        unsafe = bus.hot_swap.shadow_load(
            "yaiwes.fables.unsafe",
            ComponentCandidate("exec('raise RuntimeError(\"MUST_NOT_RUN\")')", "python"),
            999,
        )
        unsafe_rejected = bus.hot_swap.run_shadow_tests(unsafe) is False

        if ficha_ok:
            reasons.append("FICHA_V2_VERIFIED")
        if registry_ok:
            reasons.append("REGISTRY_BINDING_VERIFIED")
        if unsafe_rejected:
            reasons.append("DYNAMIC_EXECUTION_REJECTED")

        verified = ficha_ok and registry_ok and unsafe_rejected
        if verified:
            reasons.append("CANONICAL_FABLES_BINDING_VERIFIED")
        return FablesBindingVerification(
            verified=verified,
            binding_id=CANONICAL_BINDING_ID,
            contract_id=CONTRACT_ID,
            reason_codes=tuple(reasons),
            registry_verified=registry_ok,
            ficha_verified=ficha_ok,
            unsafe_candidate_rejected=unsafe_rejected,
        )
    except Exception as exc:
        return FablesBindingVerification(
            verified=False,
            binding_id=CANONICAL_BINDING_ID,
            contract_id=CONTRACT_ID,
            reason_codes=("FABLES_BINDING_VERIFY_FAILED:" + type(exc).__name__,),
            registry_verified=False,
            ficha_verified=False,
            unsafe_candidate_rejected=False,
        )
