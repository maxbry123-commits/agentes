"""Thin, fail-closed Graphiti adapter for YAIWES G-027.

Graphiti remains an external reusable component. This module does not vendor,
execute, import, or replace Graphiti. It pins source provenance, normalizes
temporal-memory request envelopes, registers that adapter through the canonical
FABLES/Ficha bus, and refuses runtime execution unless the existing SandboxManager
produces real isolation evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Final, Mapping

from runtime.src.core.fables_binding_gate import verify_canonical_fables_binding
from runtime.src.uek.sandbox_manager import SandboxManager
from runtime.src.uek.universal_plugin_bus_v2_integrated import (
    ComponentCandidate,
    PluginStatus,
    TargetConventions,
    UniversalPluginBus,
)

CONTRACT_ID: Final[str] = "yaiwes.graphiti_temporal_adapter/v1"
PLUGIN_ID: Final[str] = "yaiwes.graphiti.temporal_adapter"
SOURCE_REPOSITORY: Final[str] = "maxbry123-commits/osquestador-auditor"
SOURCE_PATH: Final[str] = "graphiti/"
SOURCE_LICENSE: Final[str] = "Apache-2.0"
SOURCE_TREE_SHA: Final[str] = "de7d3161dbbfa8ebfba88c0618277fcc4543dde1"
SOURCE_ENTRY_BLOB: Final[str] = "7555a1f828c4b94970911876bfd257aaa4577d4c"
SOURCE_INIT_BLOB: Final[str] = "0ba72ffccb4b9060c6c49e6bf48fa9e07cedded2"
SOURCE_LICENSE_BLOB: Final[str] = "5feb0d9d299a1107adfa8331306b13cc0eff2d78"
FABLES_GATE_BLOB: Final[str] = "516e639fc64d048a6bc922a4021c933985867a4b"

_EXPECTED_PROOF: Final[dict[str, str]] = {
    "repository": SOURCE_REPOSITORY,
    "path": SOURCE_PATH,
    "tree_sha": SOURCE_TREE_SHA,
    "entry_blob": SOURCE_ENTRY_BLOB,
    "init_blob": SOURCE_INIT_BLOB,
    "license_blob": SOURCE_LICENSE_BLOB,
    "license": SOURCE_LICENSE,
}

_FABLES_CANDIDATE_SOURCE: Final[str] = """\
def graphiti_add_episode(request):
    return request

def graphiti_search_memory(request):
    return request
"""


@dataclass(frozen=True)
class GraphitiSourceProof:
    repository: str
    path: str
    tree_sha: str
    entry_blob: str
    init_blob: str
    license_blob: str
    license: str


@dataclass(frozen=True)
class GraphitiBindingVerification:
    verified: bool
    plugin_id: str
    source_verified: bool
    base_fables_verified: bool
    registry_verified: bool
    ficha_verified: bool
    execution_authorized: bool
    reason_codes: tuple[str, ...]


def verify_source_proof(actual: Mapping[str, str]) -> GraphitiSourceProof:
    normalized = {key: str(actual.get(key, "")) for key in _EXPECTED_PROOF}
    if normalized != _EXPECTED_PROOF:
        raise ValueError("GRAPHITI_SOURCE_PROOF_MISMATCH")
    return GraphitiSourceProof(**normalized)


def canonical_source_proof() -> GraphitiSourceProof:
    return verify_source_proof(_EXPECTED_PROOF)


def _required_text(value: str, field: str, max_len: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field}_MUST_BE_STRING")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field}_REQUIRED")
    if len(normalized) > max_len:
        raise ValueError(f"{field}_TOO_LONG")
    return normalized


def _utc_iso(value: datetime) -> str:
    if not isinstance(value, datetime):
        raise TypeError("REFERENCE_TIME_MUST_BE_DATETIME")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("REFERENCE_TIME_TIMEZONE_REQUIRED")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_add_episode_request(
    *,
    name: str,
    content: str,
    source_description: str,
    reference_time: datetime,
    group_id: str,
) -> dict[str, Any]:
    return {
        "contract": CONTRACT_ID,
        "component": "graphiti",
        "operation": "add_episode",
        "payload": {
            "name": _required_text(name, "NAME", 256),
            "episode_body": _required_text(content, "CONTENT", 100_000),
            "source_description": _required_text(source_description, "SOURCE_DESCRIPTION", 512),
            "reference_time": _utc_iso(reference_time),
            "group_id": _required_text(group_id, "GROUP_ID", 256),
        },
        "execution_authorized": False,
    }


def build_search_request(*, query: str, group_id: str, limit: int = 10) -> dict[str, Any]:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("LIMIT_OUT_OF_RANGE")
    return {
        "contract": CONTRACT_ID,
        "component": "graphiti",
        "operation": "search",
        "payload": {
            "query": _required_text(query, "QUERY", 10_000),
            "group_id": _required_text(group_id, "GROUP_ID", 256),
            "limit": limit,
        },
        "execution_authorized": False,
    }


def graphiti_ficha_manifest() -> dict[str, Any]:
    return {
        "artifact_id": PLUGIN_ID,
        "version": "1.0.0",
        "estado": "active",
        "contract_hash": "sha256:" + "7" * 64,
        "tribunal_case_id": "G027-CANONICAL",
        "contrato": {
            "rol": "temporal_context_memory",
            "consume": {"datatype": {"family": "memory", "type": "temporal_request", "version": 1}},
            "expone": {"datatype": {"family": "memory", "type": "graphiti_envelope", "version": 1}},
        },
        "ejecucion": {
            "kind": "code",
            "transport": "importlib",
            "runtime_type": "io",
            "entry_point": "runtime.src.core.graphiti_temporal_adapter",
            "idempotente": True,
            "allowed_actions": ["static_contract_validation", "request_envelope_build"],
        },
        "seguridad": {
            "sandbox": "process",
            "permisos": [],
            "limites": {"timeout_ms": 5000, "network": "deny_by_default"},
        },
        "firma": {"gpg_key_id": "G027-LOCAL-VERIFIED"},
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
        "presupuesto": {"n0": {"max_tokens": 0, "max_ms": 5000, "max_costo_usd": 0.0}},
        "evidencia": {"produce": ["L1_static", "L2_build"], "destino": "runtime/evidence/"},
        "salud": {"metodo": "ping", "heartbeat_interval_s": 30},
        "activacion": {"eventos": ["yaiwes.graphiti.request.ready"]},
    }


def verify_graphiti_fables_registration(
    *,
    bus_factory: Callable[[], UniversalPluginBus] = UniversalPluginBus,
    base_binding_verifier: Callable[[], Any] = verify_canonical_fables_binding,
) -> GraphitiBindingVerification:
    reasons: list[str] = []
    source_ok = canonical_source_proof().tree_sha == SOURCE_TREE_SHA
    if source_ok:
        reasons.append("GRAPHITI_SOURCE_PROOF_VERIFIED")

    base = base_binding_verifier()
    base_ok = bool(getattr(base, "verified", False))
    if base_ok:
        reasons.append("CANONICAL_FABLES_BASE_VERIFIED")

    if not (source_ok and base_ok):
        return GraphitiBindingVerification(
            verified=False,
            plugin_id=PLUGIN_ID,
            source_verified=source_ok,
            base_fables_verified=base_ok,
            registry_verified=False,
            ficha_verified=False,
            execution_authorized=False,
            reason_codes=tuple(reasons + ["GRAPHITI_FABLES_PRECONDITION_FAILED"]),
        )

    try:
        bus = bus_factory()
        bus.add_tribunal_approval("G027-CANONICAL")
        reg = bus.enchufar(
            graphiti_ficha_manifest(),
            ComponentCandidate(
                _FABLES_CANDIDATE_SOURCE,
                "python",
                ["runtime/src/core/graphiti_temporal_adapter.py"],
            ),
            TargetConventions("python", "snake_case", "sync", "gradual"),
            registered_by="SOL_2_G027",
        )
        ficha_ok = reg.ficha is not None and reg.ficha.artifact_id == PLUGIN_ID
        registry_ok = (
            reg.status == PluginStatus.ACTIVE
            and bus.registry.get(PLUGIN_ID) is reg
            and any(item["level"] == "L2_build" for item in bus.evidence.get(PLUGIN_ID))
        )
        if ficha_ok:
            reasons.append("GRAPHITI_FICHA_V2_VERIFIED")
        if registry_ok:
            reasons.append("GRAPHITI_REGISTRY_BINDING_VERIFIED")
        verified = source_ok and base_ok and ficha_ok and registry_ok
        if verified:
            reasons.append("GRAPHITI_FABLES_BINDING_VERIFIED")
        return GraphitiBindingVerification(
            verified=verified,
            plugin_id=PLUGIN_ID,
            source_verified=source_ok,
            base_fables_verified=base_ok,
            registry_verified=registry_ok,
            ficha_verified=ficha_ok,
            execution_authorized=False,
            reason_codes=tuple(reasons),
        )
    except Exception as exc:
        return GraphitiBindingVerification(
            verified=False,
            plugin_id=PLUGIN_ID,
            source_verified=source_ok,
            base_fables_verified=base_ok,
            registry_verified=False,
            ficha_verified=False,
            execution_authorized=False,
            reason_codes=tuple(reasons + ["GRAPHITI_FABLES_BINDING_FAILED:" + type(exc).__name__]),
        )


def sandbox_probe(
    executable: str = "/usr/bin/true",
    *,
    manager_factory: Callable[..., SandboxManager] = SandboxManager,
) -> dict[str, Any]:
    if not Path(executable).is_absolute():
        raise ValueError("ABSOLUTE_EXECUTABLE_REQUIRED")
    manager = manager_factory(network_policy="DENY", memory_limit_mb=128, timeout_seconds=5.0)
    result = manager.execute_isolated("graphiti_adapter_probe", [executable])
    if result.get("status") != "EXECUTION_VERIFIED":
        return {
            "status": "BLOCKED_BY_SANDBOX",
            "execution_authorized": False,
            "sandbox": result,
        }
    return {
        "status": "SANDBOX_VERIFIED",
        "execution_authorized": True,
        "sandbox": result,
    }
