"""
ejecutor.py - FIX P0-02, P0-03, P0-04 (auditoria 5x). Ver Anexo para detalle.
"""
import json
import uuid
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential

from instalador_deterministico import instalar_componente
from consultor_experto import consultar_experto_cerebras
from verificador import verificar_con_claude

RAIZ = Path(__file__).parent

_PROVIDER_ERROR_PREFIXES = ("ERROR_CEREBRAS", "ERROR:", "ERROR_CLAUDE_SDK")


def _es_error_de_provider(respuesta: str) -> bool:
    return any(str(respuesta).startswith(p) for p in _PROVIDER_ERROR_PREFIXES)


def ejecutar_tarea(tarea: dict) -> dict:
    mission_id = tarea.get("mission_id") or str(uuid.uuid4())
    tarea = {**tarea, "mission_id": mission_id}

    if tarea["tipo"] == "instalar_paquete":
        ok = instalar_componente(tarea["nombre"], tarea["url"], RAIZ)
        if ok:
            return {"status": "PASS", "mission_id": mission_id, "evidencia": {"path": str(RAIZ / tarea["nombre"])}}
        return investigar_comunidad(tarea)

    elif tarea["tipo"] == "evaluar_componente":
        respuesta = consultar_experto_cerebras(contexto=tarea, pregunta=f"Este componente encaja con YAIWES? {tarea}")
        if _es_error_de_provider(respuesta):
            return {"status": "GAP", "mission_id": mission_id, "evidencia": {"tipo_error": "PROVIDER_ERROR_OR_AUTH_ERROR", "respuesta": respuesta}}
        return {"status": "PASS", "mission_id": mission_id, "evidencia": {"respuesta": respuesta}}

    elif tarea["tipo"] == "diseno_arquitectura":
        veredicto = verificar_con_claude(tarea)
        return {"status": veredicto["status"], "mission_id": mission_id, "evidencia": {**veredicto, "tipo_veredicto": "LLM_ADVISORY_OPINION_NO_ES_ORACLE_OBJETIVO"}}

    elif tarea["tipo"] == "verificar_existencia":
        existe = (RAIZ / tarea["nombre"]).exists()
        if not existe:
            return {"status": "GAP", "mission_id": mission_id, "evidencia": {"existe": False, "motivo": "archivo_no_encontrado"}}
        return {"status": "PASS", "mission_id": mission_id, "evidencia": {"existe": True}}

    return investigar_comunidad(tarea)


@retry(stop=stop_after_attempt(20), wait=wait_exponential(multiplier=1, min=2, max=60), reraise=False)
def _intento_resolver_gap(tarea: dict, intento_actual: list) -> str:
    intento_actual[0] += 1
    respuesta = consultar_experto_cerebras(contexto=tarea, pregunta=f"Intento {intento_actual[0]}/20: como resolver este GAP? {tarea}")
    if _es_error_de_provider(respuesta) or "RESUELTO" not in respuesta.upper():
        raise ValueError("aun no resuelto")
    return respuesta


def investigar_comunidad(tarea: dict) -> dict:
    mission_id = tarea.get("mission_id") or str(uuid.uuid4())
    intento_actual = [0]
    try:
        respuesta = _intento_resolver_gap(tarea, intento_actual)
        return {"status": "PASS", "mission_id": mission_id, "evidencia": {"intento": intento_actual[0], "respuesta": respuesta}}
    except Exception:
        return {"status": "GAP", "mission_id": mission_id, "evidencia": {"intentos": intento_actual[0], "nota": "registrado, no bloquea siguiente tarea"}}


def loop_principal(cola_tareas: list) -> None:
    while cola_tareas:
        tarea = cola_tareas.pop(0)
        resultado = ejecutar_tarea(tarea)
        registrar_evidencia(tarea, resultado)
    activar_watchdog()


def registrar_evidencia(tarea: dict, resultado: dict) -> None:
    log = RAIZ / "evidencia_local.jsonl"
    with open(log, "a") as f:
        f.write(json.dumps({"tarea": tarea, "resultado": resultado}) + "\n")


def activar_watchdog() -> None:
    from watchdog import watchdog_check
    watchdog_check()
