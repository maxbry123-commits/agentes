"""
SDPA v2.0 + FABLES — Ficha Contract v2.0
Responsabilidad: Schema de fichas, validador de 36 invariantes,
                 normalización v1.5→v2.0, compatibilidad de tipos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Set, Tuple


# ──────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────

RE_ARTIFACT = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
RE_HASH = re.compile(r"^sha256:[a-f0-9]{64}$")
RE_VER = re.compile(r"^\d+\.\d+\.\d+$")
NIVELES = tuple(f"n{i}" for i in range(6))
CATEGORIAS = {"pipeline", "transversal", "acelerador"}
ETAPAS = {"E", "P", "S", "T", "A"}
KINDS = {"code", "llm", "db", "api", "tool", "agent"}
RUNTIMES = {"compute", "hybrid", "llm", "agent"}
TRANSPORTS = {"stdio", "importlib", "http", "sdk", "prompt", "mcp"}
ROLES = {"source", "transform", "sink", "service"}
ESTADOS = {"draft", "testing", "active", "deprecated", "revoked"}
REPETICION_COND = {"nunca", "si_falla_verificacion", "si_memoria_cambia", "siempre_por_nivel"}
REPETE_EN_VAL = {"INPUT", "CONTEXT_LOADER", "EXEC_STATE", "ARTIFACT_ENGINE",
                  "MEMORY", "MASTER_JSON", "CONTEXT_MANAGER"}
EVIDENCE_LEVELS = {"L1_static", "L2_build", "L3_runtime", "L4_feature"}
SANDBOXES = {"container", "process", "none"}
SALUD_METODOS = {"ping", "http", "exec", "ninguno"}


# ──────────────────────────────────────────────────────────────
# Data classes del schema v2.0
# ──────────────────────────────────────────────────────────────

@dataclass
class DataType:
    family: str
    type: str
    version: int


@dataclass
class IOContract:
    datatype: DataType
    schema_uri: str = ""


@dataclass
class Contrato:
    rol: Literal["source", "transform", "sink", "service"]
    consume: Optional[IOContract] = None
    expone: Optional[IOContract] = None
    input_map: Dict[str, Any] = field(default_factory=dict)
    output_map: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Ejecucion:
    kind: Literal["code", "llm", "db", "api", "tool", "agent"]
    transport: Literal["stdio", "importlib", "http", "sdk", "prompt", "mcp"]
    runtime_type: Literal["compute", "hybrid", "llm", "agent"]
    entry_point: str = ""
    llm_ratio: float = 0.0
    idempotente: bool = False
    max_steps: int = 0
    allowed_actions: List[str] = field(default_factory=list)


@dataclass
class Perfil:
    habilitada: bool = True
    iteraciones: int = 1
    simulaciones: int = 0
    criticas: int = 0
    muestras_k: int = 1


@dataclass
class Repeticion:
    max: int = 1
    condicion: Literal["nunca", "si_falla_verificacion", "si_memoria_cambia", "siempre_por_nivel"] = "nunca"
    backoff: str = "1000*2^n+rand(0,1000)"


@dataclass
class Activacion:
    eventos: List[str] = field(default_factory=list)
    wake_words: List[str] = field(default_factory=list)
    condicion: str = ""


@dataclass
class PresupuestoNivel:
    max_tokens: int = 0
    max_ms: int = 0
    max_costo_usd: float = 0.0


@dataclass
class Telemetria:
    metricas: List[str] = field(default_factory=lambda: ["tiempo", "errores", "reintentos"])
    span_otel: bool = True


@dataclass
class Evidencia:
    produce: List[str] = field(default_factory=list)
    destino: str = "runtime/evidence/"


@dataclass
class Failover:
    sustituible_por: List[str] = field(default_factory=list)
    compensacion: str = ""


@dataclass
class Seguridad:
    sandbox: Literal["container", "process", "none"]
    permisos: List[str] = field(default_factory=list)
    limites: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Salud:
    metodo: Literal["ping", "http", "exec", "ninguno"] = "ping"
    heartbeat_interval_s: int = 30


@dataclass
class Firma:
    gpg_key_id: str = "PENDIENTE"
    revocation_ref: str = "contracts/revocation_list.json"


@dataclass
class Trazas:
    task_id_requerido: bool = True
    trace_id_requerido: bool = True


@dataclass
class FichaContract:
    """Contrato de ficha v2.0 completo."""
    artifact_id: str
    version: str
    estado: Literal["draft", "testing", "active", "deprecated", "revoked"]
    contrato: Contrato
    ejecucion: Ejecucion
    seguridad: Seguridad
    firma: Firma
    contract_hash: str = ""
    categoria: Literal["pipeline", "transversal", "acelerador"] = "pipeline"
    etapa: Literal["E", "P", "S", "T", "A"] = "P"
    perfiles: Dict[str, Perfil] = field(default_factory=dict)
    repeticion: Repeticion = field(default_factory=Repeticion)
    repite_en: List[str] = field(default_factory=list)
    activacion: Activacion = field(default_factory=Activacion)
    presupuesto: Dict[str, PresupuestoNivel] = field(default_factory=dict)
    telemetria: Telemetria = field(default_factory=Telemetria)
    evidencia: Evidencia = field(default_factory=Evidencia)
    failover: Failover = field(default_factory=Failover)
    salud: Salud = field(default_factory=Salud)
    trazas: Trazas = field(default_factory=Trazas)


# ──────────────────────────────────────────────────────────────
# Defaults v2.0 para normalización v1.5
# ──────────────────────────────────────────────────────────────

DEFAULTS_V2: Dict[str, Any] = {
    "categoria": "pipeline",
    "etapa": "P",
    "perfiles": {n: {"habilitada": True, "iteraciones": 1,
                     "simulaciones": 0, "criticas": 0, "muestras_k": 1}
                 for n in NIVELES},
    "repeticion": {"max": 1, "condicion": "nunca",
                   "backoff": "1000*2^n+rand(0,1000)"},
    "repite_en": [],
    "activacion": {"eventos": [], "wake_words": [], "condicion": ""},
    "presupuesto": {},
    "telemetria": {"metricas": ["tiempo", "errores", "reintentos"],
                   "span_otel": True},
    "evidencia": {"produce": [], "destino": "runtime/evidence/"},
    "failover": {"sustituible_por": [], "compensacion": ""},
    "salud": {"metodo": "ping", "heartbeat_interval_s": 30},
    "trazas": {"task_id_requerido": True, "trace_id_requerido": True},
}


# ──────────────────────────────────────────────────────────────
# Validador v2.0 — 36 invariantes
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Veredicto:
    valido: bool
    errores: Tuple[str, ...] = ()
    ficha_normalizada: Optional[Dict[str, Any]] = None


def _ensure_dict(val: Any) -> Dict[str, Any]:
    """Convierte dataclass a dict si es necesario."""
    if hasattr(val, "__dataclass_fields__"):
        return {k: _ensure_dict(v) if hasattr(v, "__dataclass_fields__") else v
                for k, v in val.__dict__.items()}
    return val  # type: ignore[return-value]


def normalizar_v15(c: Dict[str, Any]) -> Dict[str, Any]:
    """Ficha v1.5 → v2.0 aplicando defaults (aditivo, no destruye)."""
    out = dict(c)
    for k, v in DEFAULTS_V2.items():
        out.setdefault(k, v)
    out.setdefault("firma", {"gpg_key_id": "PENDIENTE",
                             "revocation_ref": "contracts/revocation_list.json"})
    return out


def validar(c_raw: Dict[str, Any]) -> Veredicto:  # noqa: C901
    """Valida una ficha contra las 36 invariantes v2.0."""
    c = normalizar_v15(c_raw)
    e: List[str] = []
    add = e.append

    # ── Invariantes v1.5 (núcleo) ──
    if not RE_ARTIFACT.match(c.get("artifact_id", "")):
        add("I01_artifact_id")
    if not RE_VER.match(c.get("version", "")):
        add("I02_version_semver")
    est = c.get("estado")
    if est not in ESTADOS:
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
    if ej.get("kind") not in KINDS:
        add("I08_kind")
    if ej.get("runtime_type") not in RUNTIMES:
        add("I09_runtime_type")
    ratio = ej.get("llm_ratio", 0.0)
    if ej.get("runtime_type") == "compute" and ratio > 0.10:
        add("I10_compute_ratio_max_010")

    seg = c.get("seguridad", {})
    lim = seg.get("limites", {})
    if not (isinstance(lim.get("timeout_ms"), int) and lim["timeout_ms"] > 0):
        add("I11_timeout")
    to = lim.get("timeout_ms", 1)
    dl = lim.get("deadline_ms", to)
    if dl < to:
        add("I12_deadline_ge_timeout")
    if seg.get("sandbox") == "none" and seg.get("permisos"):
        add("I13_none_sin_permisos")

    # ── Invariantes v2.0 (nuevas) ──
    if c["categoria"] not in CATEGORIAS:
        add("V01_categoria")
    if c["etapa"] not in ETAPAS:
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
    if rep.get("condicion") not in REPETICION_COND:
        add("V08_repeticion_condicion")
    if rep.get("max", 1) > 1 and not ej.get("idempotente", False):
        add("V09_repetible_debe_ser_idempotente")

    for punto in c["repite_en"]:
        if punto not in REPETE_EN_VAL:
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

    return Veredicto(valido=not e, errores=tuple(e),
                     ficha_normalizada=c if not e else None)


def compatibles(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    """a.expone.datatype == b.consume.datatype (autoensamblaje)."""
    ea = (a.get("contrato", {}).get("expone") or {}).get("datatype", {})
    cb = (b.get("contrato", {}).get("consume") or {}).get("datatype", {})
    return bool(ea) and ea == cb


def ficha_to_dict(ficha: FichaContract) -> Dict[str, Any]:
    """Serializa FichaContract a dict plano."""
    return _ensure_dict(ficha)


def dict_to_ficha(d: Dict[str, Any]) -> FichaContract:
    """Deserializa dict a FichaContract (con defaults)."""
    d = normalizar_v15(d)
    return FichaContract(
        artifact_id=d["artifact_id"],
        version=d["version"],
        estado=d["estado"],
        contrato=Contrato(
            rol=d["contrato"]["rol"],
            consume=IOContract(**d["contrato"]["consume"]) if d["contrato"].get("consume") else None,
            expone=IOContract(**d["contrato"]["expone"]) if d["contrato"].get("expone") else None,
            input_map=d["contrato"].get("input_map", {}),
            output_map=d["contrato"].get("output_map", {}),
        ),
        ejecucion=Ejecucion(
            kind=d["ejecucion"]["kind"],
            transport=d["ejecucion"]["transport"],
            runtime_type=d["ejecucion"]["runtime_type"],
            entry_point=d["ejecucion"].get("entry_point", ""),
            llm_ratio=d["ejecucion"].get("llm_ratio", 0.0),
            idempotente=d["ejecucion"].get("idempotente", False),
            max_steps=d["ejecucion"].get("max_steps", 0),
            allowed_actions=d["ejecucion"].get("allowed_actions", []),
        ),
        seguridad=Seguridad(
            sandbox=d["seguridad"]["sandbox"],
            permisos=d["seguridad"].get("permisos", []),
            limites=d["seguridad"].get("limites", {}),
        ),
        firma=Firma(
            gpg_key_id=d["firma"]["gpg_key_id"],
            revocation_ref=d["firma"].get("revocation_ref", "contracts/revocation_list.json"),
        ),
        contract_hash=d.get("contract_hash", ""),
        categoria=d.get("categoria", "pipeline"),
        etapa=d.get("etapa", "P"),
        perfiles={n: Perfil(**p) for n, p in d.get("perfiles", {}).items()},
        repeticion=Repeticion(**d.get("repeticion", {})),
        repite_en=d.get("repite_en", []),
        activacion=Activacion(**d.get("activacion", {})),
        presupuesto={n: PresupuestoNivel(**b) for n, b in d.get("presupuesto", {}).items()},
        telemetria=Telemetria(**d.get("telemetria", {})),
        evidencia=Evidencia(**d.get("evidencia", {})),
        failover=Failover(**d.get("failover", {})),
        salud=Salud(**d.get("salud", {})),
        trazas=Trazas(**d.get("trazas", {})),
    )


# ──────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────

def _run_tests() -> None:
    ficha_minima = {
        "artifact_id": "sdpa.plugins.test",
        "version": "1.0.0",
        "estado": "active",
        "contract_hash": "sha256:" + "a" * 64,
        "contrato": {"rol": "transform", "consume": {"datatype": {"family": "text", "type": "string", "version": 1}}, "expone": {"datatype": {"family": "text", "type": "string", "version": 1}}},
        "ejecucion": {"kind": "code", "transport": "importlib", "runtime_type": "compute", "idempotente": True},
        "seguridad": {"sandbox": "process", "limites": {"timeout_ms": 5000}},
        "firma": {"gpg_key_id": "ABC123DEF"},
    }
    v = validar(ficha_minima)
    assert v.valido, f"Ficha mínima debería ser válida: {v.errores}"

    # Test v1.5 sin campos nuevos
    ficha_v15 = {
        "artifact_id": "sdpa.plugins.legacy",
        "version": "0.5.0",
        "estado": "draft",
        "contrato": {"rol": "source", "expone": {"datatype": {"family": "json", "type": "object", "version": 1}}},
        "ejecucion": {"kind": "llm", "transport": "prompt", "runtime_type": "llm", "llm_ratio": 0.8},
        "seguridad": {"sandbox": "container", "limites": {"timeout_ms": 10000}},
    }
    v2 = validar(ficha_v15)
    assert v2.valido, f"v1.5 debería validar bajo v2.0: {v2.errores}"
    assert v2.ficha_normalizada is not None
    assert v2.ficha_normalizada["categoria"] == "pipeline"

    # Test acelerador fuera de A
    bad = dict(ficha_minima)
    bad["categoria"] = "acelerador"
    bad["etapa"] = "P"
    v3 = validar(bad)
    assert "V03_acelerador_etapa_A" in v3.errores

    # Test repetible sin idempotencia
    bad2 = dict(ficha_minima)
    bad2["repeticion"] = {"max": 3, "condicion": "si_falla_verificacion"}
    bad2["ejecucion"] = {"kind": "code", "transport": "importlib", "runtime_type": "compute", "idempotente": False}
    v4 = validar(bad2)
    assert "V09_repetible_debe_ser_idempotente" in v4.errores

    # Test compatibles
    a = {"contrato": {"expone": {"datatype": {"family": "x", "type": "y", "version": 1}}}}
    b = {"contrato": {"consume": {"datatype": {"family": "x", "type": "y", "version": 1}}}}
    assert compatibles(a, b)

    # Test serialización round-trip
    ficha_obj = dict_to_ficha(ficha_minima)
    d = ficha_to_dict(ficha_obj)
    assert d["artifact_id"] == "sdpa.plugins.test"
    assert d["categoria"] == "pipeline"

    print("[FichaContractV2] All tests passed.")


if __name__ == "__main__":
    _run_tests()
