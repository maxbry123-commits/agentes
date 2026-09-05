"""VALIDATOR v2.0 — SOURCE: ENCHUFE UNIVERSAL v2.0
22 invariantes v1.5 + 14 nuevas v2.0.
Compatibilidad: acepta fichas v1.5 (aplica defaults).
"""
from __future__ import annotations
import re
from dataclasses import dataclass

RE_ARTIFACT = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
RE_HASH = re.compile(r"^sha256:[a-f0-9]{64}$")
RE_VER = re.compile(r"^\d+\.\d+\.\d+$")
NIVELES = tuple(f"n{i}" for i in range(6))

DEFAULTS_V2 = {
    "categoria": "pipeline",
    "etapa": "P",
    "perfiles": {n: {"habilitada": True, "iteraciones": 1} for n in NIVELES},
    "repeticion": {"max": 1, "condicion": "nunca"},
    "repite_en": [],
    "activacion": {},
    "presupuesto": {},
    "telemetria": {"metricas": ["tiempo", "errores", "reintentos"], "span_otel": True},
    "evidencia": {"produce": [], "destino": "runtime/evidence/"},
    "failover": {"sustituible_por": []},
    "salud": {"metodo": "ping", "heartbeat_interval_s": 30},
}


@dataclass(frozen=True)
class Veredicto:
    valido: bool
    errores: tuple[str, ...] = ()
    ficha_normalizada: dict | None = None


def normalizar_v15(c: dict) -> dict:
    out = dict(c)
    for k, v in DEFAULTS_V2.items():
        out.setdefault(k, v)
    out.setdefault("firma", {"gpg_key_id": "PENDIENTE", "revocation_ref": "contracts/revocation_list.json"})
    return out


def validar(c: dict) -> Veredicto:
    c = normalizar_v15(c)
    e: list[str] = []
    add = e.append

    # Núcleo v1.5
    if not RE_ARTIFACT.match(c.get("artifact_id", "")):
        add("I01_artifact_id")
    if not RE_VER.match(c.get("version", "")):
        add("I02_version_semver")
    est = c.get("estado")
    if est not in {"draft", "testing", "active", "deprecated", "revoked"}:
        add("I03_estado")
    if est == "active" and not RE_HASH.match(c.get("contract_hash", "")):
        add("I04_active_requiere_hash")

    rol = c.get("contrato", {}).get("rol")
    con = c.get("contrato", {}).get("consume")
    exp = c.get("contrato", {}).get("expone")
    if rol == "source" and con is not None:
        add("I05_source_no_consume")
    if rol == "sink" and exp is not None:
        add("I06_sink_no_expone")
    if rol == "transform" and (con is None or exp is None):
        add("I07_transform_ambos")

    ej = c.get("ejecucion", {})
    if ej.get("kind") not in {"code", "llm", "db", "api", "tool", "agent"}:
        add("I08_kind")
    if ej.get("runtime_type") not in {"compute", "hybrid", "llm", "agent"}:
        add("I09_runtime_type")
    ratio = ej.get("llm_ratio", 0.0)
    if ej.get("runtime_type") == "compute" and ratio > 0.10:
        add("I10_compute_ratio_max_010")

    seg = c.get("seguridad", {})
    lim = seg.get("limites", {})
    if not (isinstance(lim.get("timeout_ms"), int) and lim["timeout_ms"] > 0):
        add("I11_timeout")
    if lim.get("deadline_ms", lim.get("timeout_ms", 1)) < lim.get("timeout_ms", 1):
        add("I12_deadline_ge_timeout")
    if seg.get("sandbox") == "none" and seg.get("permisos"):
        add("I13_none_sin_permisos")

    # Nuevas v2.0
    if c["categoria"] not in {"pipeline", "transversal", "acelerador"}:
        add("V01_categoria")
    if c["etapa"] not in {"E", "P", "S", "T", "A"}:
        add("V02_etapa")
    if c["categoria"] == "acelerador" and c["etapa"] != "A":
        add("V03_acelerador_etapa_A")
    if c["categoria"] == "transversal" and c["etapa"] != "T":
        add("V04_transversal_etapa_T")

    for n, p in c["perfiles"].items():
        if n not in NIVELES:
            add(f"V05_perfil_invalido:{n}")
        if p.get("iteraciones", 1) < 1:
            add(f"V06_iteraciones:{n}")

    rep = c["repeticion"]
    if rep.get("max", 1) < 1:
        add("V07_repeticion_max")
    if rep.get("condicion") not in {"nunca", "si_falla_verificacion", "si_memoria_cambia", "siempre_por_nivel"}:
        add("V08_repeticion_condicion")
    if rep.get("max", 1) > 1 and not ej.get("idempotente", False):
        add("V09_repetible_debe_ser_idempotente")

    validos = {"INPUT", "CONTEXT_LOADER", "EXEC_STATE", "ARTIFACT_ENGINE", "MEMORY", "MASTER_JSON", "CONTEXT_MANAGER"}
    for punto in c["repite_en"]:
        if punto not in validos:
            add(f"V10_repite_en:{punto}")

    for n, b in c["presupuesto"].items():
        if n not in NIVELES:
            add(f"V11_presupuesto_nivel:{n}")
        if b.get("max_ms", 1) <= 0 or b.get("max_tokens", 1) <= 0:
            add(f"V12_presupuesto_positivo:{n}")

    if est == "active" and c["firma"]["gpg_key_id"] in ("", "PENDIENTE"):
        add("V13_active_requiere_gpg")

    if ej.get("kind") == "agent":
        if "max_steps" not in ej or "allowed_actions" not in ej:
            add("V14_agent_requiere_max_steps_y_whitelist")

    return Veredicto(valido=not e, errores=tuple(e), ficha_normalizada=c if not e else None)


def compatibles(a: dict, b: dict) -> bool:
    ea = (a.get("contrato", {}).get("expone") or {}).get("datatype", {})
    cb = (b.get("contrato", {}).get("consume") or {}).get("datatype", {})
    return bool(ea) and ea == cb
