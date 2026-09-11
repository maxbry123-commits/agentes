"""
YAIWES G-018 provenance adaptation.
Original user-upload SHA-256: 759d0d7855d8df106462b966bfc4ee543f24a3e789a27048f253159b58ff8d1a
SDPA v2.0 + FABLES — Ficha Contract v2
Contrato declarativo para componentes enchufables.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

NIVELES = ("n0", "n1", "n2", "n3", "n4")


@dataclass
class DataType:
    family: str
    type: str
    version: int = 1


@dataclass
class IOContract:
    datatype: DataType
    schema_ref: str = ""


@dataclass
class Contrato:
    rol: str
    consume: Optional[IOContract] = None
    expone: Optional[IOContract] = None
    input_map: Dict[str, str] = field(default_factory=dict)
    output_map: Dict[str, str] = field(default_factory=dict)


@dataclass
class Ejecucion:
    kind: Literal["code", "llm", "hybrid"]
    transport: Literal["importlib", "grpc", "http", "mcp", "wasm", "command"]
    runtime_type: Literal["compute", "reasoning", "io"]
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
    tribunal_case_id: str = ""


@dataclass
class Veredicto:
    valido: bool
    errores: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    ficha_normalizada: Optional[Dict[str, Any]] = None


def _ensure_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {k: _ensure_dict(getattr(value, k)) for k in value.__dataclass_fields__}
    if isinstance(value, dict):
        return {k: _ensure_dict(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_ensure_dict(v) for v in value]
    return value


def normalizar_v15(c: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza manifests previos a v2.0 sin inventar campos críticos."""
    out = dict(c)
    out.setdefault("estado", "draft")
    out.setdefault("categoria", "pipeline")
    out.setdefault("etapa", "P")
    out.setdefault("perfiles", {})
    out.setdefault("presupuesto", {})
    out.setdefault("telemetria", {})
    out.setdefault("evidencia", {})
    out.setdefault("failover", {})
    out.setdefault("salud", {})
    out.setdefault("trazas", {})
    out.setdefault("activacion", {})
    out.setdefault("repeticion", {})
    out.setdefault("repite_en", [])
    return out


def validar(c_raw: Dict[str, Any]) -> Veredicto:
    c = normalizar_v15(c_raw)
    errores: List[str] = []
    warnings: List[str] = []

    required = ("artifact_id", "version", "estado", "contrato", "ejecucion", "seguridad", "firma")
    for key in required:
        if key not in c:
            errores.append(f"V01 missing:{key}")

    artifact_id = str(c.get("artifact_id", ""))
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,127}", artifact_id):
        errores.append("V02 artifact_id")

    if c.get("categoria") == "acelerador" and c.get("etapa") != "A":
        errores.append("V03 acelerador_requires_etapa_A")

    version = str(c.get("version", ""))
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errores.append("V04 version_semver")

    estado = c.get("estado")
    if estado not in {"draft", "testing", "active", "deprecated", "revoked"}:
        errores.append("V05 estado")

    ejec = c.get("ejecucion", {})
    if ejec.get("kind") not in {"code", "llm", "hybrid"}:
        errores.append("V06 ejecucion.kind")
    if ejec.get("transport") not in {"importlib", "grpc", "http", "mcp", "wasm", "command"}:
        errores.append("V07 ejecucion.transport")
    if ejec.get("runtime_type") not in {"compute", "reasoning", "io"}:
        errores.append("V08 ejecucion.runtime_type")

    seguridad = c.get("seguridad", {})
    if seguridad.get("sandbox") not in {"container", "process", "none"}:
        errores.append("V09 seguridad.sandbox")
    if estado == "active" and seguridad.get("sandbox") == "none":
        errores.append("V10 active_requires_sandbox")

    firma = c.get("firma", {})
    if estado == "active" and not str(firma.get("gpg_key_id", "")).strip():
        errores.append("V11 active_requires_signature")

    contract_hash = str(c.get("contract_hash", ""))
    if contract_hash and not re.fullmatch(r"sha256:[0-9a-f]{64}", contract_hash):
        errores.append("V12 contract_hash")

    profiles = c.get("perfiles", {})
    unknown_levels = sorted(set(profiles) - set(NIVELES))
    if unknown_levels:
        errores.append("V13 unknown_profiles:" + ",".join(unknown_levels))

    for nivel, p in profiles.items():
        for fld in ("iteraciones", "simulaciones", "criticas", "muestras_k"):
            if int(p.get(fld, 0)) < 0:
                errores.append(f"V14 {nivel}.{fld}")

    ficha_normalizada = None if errores else c
    return Veredicto(not errores, errores, warnings, ficha_normalizada)


def ficha_to_dict(ficha: FichaContract) -> Dict[str, Any]:
    """Serializa FichaContract a dict plano."""
    return _ensure_dict(ficha)


def _io_from_dict(value: Optional[Dict[str, Any]]) -> Optional[IOContract]:
    if not value:
        return None
    datatype = value.get("datatype")
    if isinstance(datatype, dict):
        dt = DataType(**datatype)
    elif isinstance(datatype, DataType):
        dt = datatype
    else:
        raise ValueError("datatype required")
    return IOContract(datatype=dt, schema_ref=value.get("schema_ref", ""))


def dict_to_ficha(d: Dict[str, Any]) -> FichaContract:
    """Deserializa dict a FichaContract (con defaults)."""
    d = normalizar_v15(d)
    veredicto = validar(d)
    if not veredicto.valido:
        raise ValueError("invalid FichaContract: " + ";".join(veredicto.errores))
    return FichaContract(
        artifact_id=d["artifact_id"],
        version=d["version"],
        estado=d["estado"],
        contrato=Contrato(
            rol=d["contrato"]["rol"],
            consume=_io_from_dict(d["contrato"].get("consume")),
            expone=_io_from_dict(d["contrato"].get("expone")),
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
            gpg_key_id=d["firma"].get("gpg_key_id", "PENDIENTE"),
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
        tribunal_case_id=d.get("tribunal_case_id", ""),
    )


def _run_tests() -> None:
    valid = {
        "artifact_id": "sdpa.plugins.test",
        "version": "1.0.0",
        "estado": "active",
        "contract_hash": "sha256:" + "a" * 64,
        "tribunal_case_id": "CASE-001",
        "contrato": {
            "rol": "transform",
            "consume": {"datatype": {"family": "text", "type": "string", "version": 1}},
            "expone": {"datatype": {"family": "text", "type": "string", "version": 1}},
        },
        "ejecucion": {
            "kind": "code",
            "transport": "importlib",
            "runtime_type": "compute",
            "idempotente": True,
        },
        "seguridad": {"sandbox": "process", "limites": {"timeout_ms": 5000}},
        "firma": {"gpg_key_id": "ABC123"},
        "categoria": "pipeline",
        "etapa": "P",
    }
    verdict = validar(valid)
    assert verdict.valido, verdict.errores
    ficha = dict_to_ficha(valid)
    assert ficha.artifact_id == "sdpa.plugins.test"
    bad = dict(valid)
    bad["categoria"] = "acelerador"
    assert "V03 acelerador_requires_etapa_A" in validar(bad).errores
    print("[FichaContractV2] All tests passed.")


if __name__ == "__main__":
    _run_tests()
