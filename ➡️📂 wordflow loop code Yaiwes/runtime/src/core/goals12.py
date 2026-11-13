"""Deterministic input/output GOALS12 gates for Wordflow code tasks."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence, Tuple

GOALS12 = (
    "INPUT_LITERAL_CAPTURED",
    "PROVENANCE_VERIFIED",
    "TASK_CONTRACT_VALID",
    "DEPENDENCIES_MAPPED",
    "PLACEMENT_APPROVED",
    "REUSE_RESEARCH_COMPLETE",
    "SAFETY_GATE_PASS",
    "SANDBOX_GATE_PASS",
    "INDEPENDENT_REVIEW_PASS",
    "EVIDENCE_COMPLETE",
    "STATE_PERSISTED",
    "OUTPUT_ACCEPTANCE_PASS",
)

# Literal Director-approved goals from DIRECTOR-CODE-GRAPH-METHODS.md.  Keep
# GOALS12 above for compatibility with the first code-graph control batch.
INPUT_GOALS12 = (
    "identificar_objetivo",
    "congelar_input_y_hash",
    "enumerar_alcance",
    "resolver_repo_rama_ruta_version",
    "capturar_restricciones",
    "capturar_autorizacion",
    "inventariar_dependencias",
    "inventariar_fuentes",
    "definir_evidencia_admisible",
    "definir_pre_post_condiciones",
    "fijar_formato_y_destino_salida",
    "compilar_cada_paso_como_nodo",
)

OUTPUT_GOALS12 = (
    "ejecutar_exacto_el_contrato",
    "preservar_trazabilidad_literal",
    "producir_artefactos_validos",
    "demostrar_pruebas_reproducibles",
    "cruzar_fuentes",
    "resolver_contradicciones",
    "cerrar_sin_supuestos",
    "registrar_url_version_sha_run_id",
    "mantener_ledger_encadenado",
    "reparar_y_reverificar_gap",
    "cumplir_control_de_salida",
    "cerrar_solo_con_12_12_verified_closed_zero_gaps",
)

ASK_CONSILIO12 = (
    "QUE_AFIRMO",
    "QUE_EVIDENCIA_LO_DEMUESTRA",
    "QUE_PODRIA_DEMOSTRAR_QUE_ESTOY_EQUIVOCADO",
    "ESTOY_MIRANDO_LA_FUENTE_CORRECTA",
    "LA_RUTA_VERSION_COINCIDE",
    "EXISTE_REALMENTE",
    "HAY_OTRA_EXPLICACION",
    "QUE_DEPENDENCIA_FALTA",
    "PUEDO_REPRODUCIRLO",
    "EL_RESULTADO_CONTRADICE_ALGO",
    "QUE_GAP_PERMANECE",
    "QUE_EVIDENCIA_PERMITE_CERRAR",
)

REQUIRED_SIMULATIONS = ("NORMAL", "LIMIT", "ADVERSARIAL")


@dataclass(frozen=True)
class Goals12Result:
    passed: bool
    missing: Tuple[str, ...]
    status: str


@dataclass(frozen=True)
class Goals12RunResult:
    passed: bool
    missing: Tuple[str, ...]
    status: str
    evidence_sha256: str
    execution_authorized: bool = False


def evaluate_goals12(
    evidence: Mapping[str, bool],
    *,
    council_checks: int,
    simulations: int,
    refutations: int,
    cross_check: bool,
) -> Goals12Result:
    missing = [goal for goal in GOALS12 if evidence.get(goal) is not True]
    if council_checks < 12:
        missing.append("COUNCIL12_INCOMPLETE")
    if simulations < 3:
        missing.append("SIMULATIONS_LT_3")
    if refutations < 3:
        missing.append("REFUTATIONS_LT_3")
    if cross_check is not True:
        missing.append("GLOBAL_CROSS_CHECK_MISSING")
    return Goals12Result(
        not missing,
        tuple(missing),
        "PASS" if not missing else "GAP",
    )


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_goal_evidence(
    section: object, required: Sequence[str], prefix: str, missing: list[str]
) -> None:
    if not isinstance(section, Mapping):
        missing.append(f"{prefix}_EVIDENCE_INVALID")
        return
    for goal in required:
        item = section.get(goal)
        if not isinstance(item, Mapping) or item.get("passed") is not True:
            missing.append(f"{prefix}_GOAL_MISSING:{goal}")
            continue
        refs = item.get("evidence_refs")
        if not isinstance(refs, (list, tuple)) or not refs or not all(
            isinstance(ref, str) and ref.strip() for ref in refs
        ):
            missing.append(f"{prefix}_EVIDENCE_MISSING:{goal}")


def _validate_named_checks(
    checks: object,
    required_names: Sequence[str],
    prefix: str,
    missing: list[str],
    *,
    result_key: str = "passed",
) -> None:
    if not isinstance(checks, (list, tuple)):
        missing.append(f"{prefix}_INVALID")
        return
    indexed = {
        item.get("name"): item
        for item in checks
        if isinstance(item, Mapping) and isinstance(item.get("name"), str)
    }
    for name in required_names:
        item = indexed.get(name)
        if item is None or item.get(result_key) is not True:
            missing.append(f"{prefix}_MISSING_OR_FAILED:{name}")
            continue
        refs = item.get("evidence_refs")
        if not isinstance(refs, (list, tuple)) or not refs:
            missing.append(f"{prefix}_EVIDENCE_MISSING:{name}")


def evaluate_goals12_run(run: Mapping[str, Any]) -> Goals12RunResult:
    """Validate one complete, evidence-bound GOALS12 run.

    The result is advisory and never grants execution or deployment authority.
    Invalid/missing evidence fails closed and is included in the canonical hash.
    """

    missing: list[str] = []
    if run.get("schema") != "yaiwes.goals12/v1":
        missing.append("SCHEMA_INVALID")
    if not isinstance(run.get("node_id"), str) or not run["node_id"].strip():
        missing.append("NODE_ID_MISSING")

    _validate_goal_evidence(run.get("input_goals"), INPUT_GOALS12, "INPUT", missing)
    _validate_goal_evidence(run.get("output_goals"), OUTPUT_GOALS12, "OUTPUT", missing)
    _validate_named_checks(run.get("council"), ASK_CONSILIO12, "COUNCIL12", missing)
    _validate_named_checks(
        run.get("simulations"), REQUIRED_SIMULATIONS, "SIMULATION", missing
    )

    refutations = run.get("refutations")
    if not isinstance(refutations, (list, tuple)) or len(refutations) < 3:
        missing.append("REFUTATIONS_LT_3")
    else:
        for index, item in enumerate(refutations[:3], start=1):
            if not isinstance(item, Mapping) or item.get("survived") is not True:
                missing.append(f"REFUTATION_FAILED:{index}")
            elif not item.get("evidence_refs"):
                missing.append(f"REFUTATION_EVIDENCE_MISSING:{index}")

    cross_checks = run.get("cross_checks")
    if not isinstance(cross_checks, (list, tuple)) or not cross_checks:
        missing.append("GLOBAL_CROSS_CHECK_MISSING")
    else:
        for index, item in enumerate(cross_checks, start=1):
            if not isinstance(item, Mapping) or item.get("passed") is not True:
                missing.append(f"CROSS_CHECK_FAILED:{index}")
            elif not item.get("evidence_refs"):
                missing.append(f"CROSS_CHECK_EVIDENCE_MISSING:{index}")

    evidence_sha256 = _canonical_sha256(run)
    return Goals12RunResult(
        passed=not missing,
        missing=tuple(missing),
        status="VERIFIED_CLOSED" if not missing else "GAP",
        evidence_sha256=evidence_sha256,
        execution_authorized=False,
    )
