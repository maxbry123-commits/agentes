"""
ejecutor.py - FIX P0-01, P0-02, P0-03, P0-04, P0-09, P0-11 (auditoria 5x).
P0-01: cada tarea valida su ruta contra dag_schema.yaml FRESCO (dag_engine.py).
P0-09 NUEVO: loop_principal ahora SI reencola lo que devuelve el watchdog
(antes se ignoraba el retorno de watchdog_check()).
P0-11 NUEVO: idempotencia real via idempotencia.py - mismo command_id +
mismo payload = REPLAY; mismo command_id + payload distinto = CONFLICT.
"""
import json
import uuid
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential

import dag_engine
from idempotencia import REGISTRO_GLOBAL
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
    command_id = tarea.get("command_id", mission_id)

    # P0-11 FIX: chequeo de idempotencia ANTES de tocar cualquier side effect.
    accion, resultado_previo = REGISTRO_GLOBAL.verificar(command_id, tarea)
    if accion == "REPLAY":
        return {**resultado_previo, "idempotencia": "REPLAY_RESULTADO_PREVIO"}
    if accion == "IDEMPOTENCY_CONFLICT":
        return {"status": "GAP", "mission_id": mission_id, "evidencia": {"motivo": "IDEMPOTENCY_CONFLICT_MISMO_ID_DISTINTO_PAYLOAD"}}

    # P0-01 FIX: validar contra el DAG cargado fresco ANTES de ejecutar.
    dag_ok, dag_info = dag_engine.validar_ruta_de_tipo(tarea["tipo"])
    if not dag_ok:
        resultado = {"status": "GAP", "mission_id": mission_id, "evidencia": {"motivo": "DAG_NO_DECLARA_ESTA_RUTA", "detalle": dag_info}}
        REGISTRO_GLOBAL.registrar_resultado(command_id, tarea, resultado)
        return resultado
    nodo_dag = dag_info

    if tarea["tipo"] == "instalar_paquete":
        ok = instalar_componente(tarea["nombre"], tarea["url"], RAIZ)
        if ok:
            resultado = {"status": "PASS", "mission_id": mission_id, "nodo_dag": nodo_dag, "evidencia": {"path": str(RAIZ / tarea["nombre"])}}
        else:
            resultado = investigar_comunidad(tarea)
        REGISTRO_GLOBAL.registrar_resultado(command_id, tarea, resultado)
        return resultado

    elif tarea["tipo"] == "evaluar_componente":
        respuesta = consultar_experto_cerebras(contexto=tarea, pregunta=f"Este componente encaja con YAIWES? {tarea}")
        if _es_error_de_provider(respuesta):
            resultado = {"status": "GAP", "mission_id": mission_id, "nodo_dag": nodo_dag, "evidencia": {"tipo_error": "PROVIDER_ERROR_OR_AUTH_ERROR", "respuesta": respuesta}}
        else:
            resultado = {"status": "PASS", "mission_id": mission_id, "nodo_dag": nodo_dag, "evidencia": {"respuesta": respuesta}}
        REGISTRO_GLOBAL.registrar_resultado(command_id, tarea, resultado)
        return resultado

    elif tarea["tipo"] == "diseno_arquitectura":
        veredicto = verificar_con_claude(tarea)
        resultado = {"status": veredicto["status"], "mission_id": mission_id, "nodo_dag": nodo_dag, "evidencia": {**veredicto, "tipo_veredicto": "LLM_ADVISORY_OPINION_NO_ES_ORACLE_OBJETIVO"}}
        REGISTRO_GLOBAL.registrar_resultado(command_id, tarea, resultado)
        return resultado

    elif tarea["tipo"] == "verificar_existencia":
        existe = (RAIZ / tarea["nombre"]).exists()
        if not existe:
            resultado = {"status": "GAP", "mission_id": mission_id, "nodo_dag": nodo_dag, "evidencia": {"existe": False, "motivo": "archivo_no_encontrado"}}
        else:
            resultado = {"status": "PASS", "mission_id": mission_id, "nodo_dag": nodo_dag, "evidencia": {"existe": True}}
        REGISTRO_GLOBAL.registrar_resultado(command_id, tarea, resultado)
        return resultado

    resultado = investigar_comunidad(tarea)
    REGISTRO_GLOBAL.registrar_resultado(command_id, tarea, resultado)
    return resultado


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
    # P0-09 FIX: el retorno del watchdog ya NO se ignora, se reencola de verdad.
    activar_watchdog(cola_tareas)
    if cola_tareas:
        loop_principal(cola_tareas)


def registrar_evidencia(tarea: dict, resultado: dict) -> None:
    log = RAIZ / "evidencia_local.jsonl"
    with open(log, "a") as f:
        f.write(json.dumps({"tarea": tarea, "resultado": resultado}) + "\n")


def activar_watchdog(cola_tareas: list) -> None:
    from watchdog import watchdog_check, reencolar_en
    pendientes = watchdog_check()
    reencolar_en(cola_tareas, pendientes)
