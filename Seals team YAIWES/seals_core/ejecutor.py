"""
ejecutor.py - El router 90/10 real. Este archivo NUNCA llama a un LLM
directamente. Solo decide, via if/elif, cual funcion determinista o
cual funcion de LLM debe correr, siguiendo dag_schema.yaml.
Actualizado: mission_id por tarea + Tenacity para reintentos con backoff.
"""
import json
import uuid
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential

from instalador_deterministico import instalar_componente
from consultor_experto import consultar_experto_cerebras
from verificador import verificar_con_claude

RAIZ = Path(__file__).parent


def ejecutar_tarea(tarea: dict) -> dict:
    """
    tarea = {"tipo": ..., "nombre": ..., "url": ..., "descripcion": ...}
    Devuelve {"status": "PASS"|"GAP", "mission_id": ..., "evidencia": {...}}
    """
    mission_id = tarea.get("mission_id") or str(uuid.uuid4())
    tarea = {**tarea, "mission_id": mission_id}

    if tarea["tipo"] == "instalar_paquete":
        ok = instalar_componente(tarea["nombre"], tarea["url"], RAIZ)
        if ok:
            return {"status": "PASS", "mission_id": mission_id, "evidencia": {"path": str(RAIZ / tarea["nombre"])}}
        return investigar_comunidad(tarea)

    elif tarea["tipo"] == "evaluar_componente":
        respuesta = consultar_experto_cerebras(
            contexto=tarea, pregunta=f"Este componente encaja con YAIWES? {tarea}"
        )
        return {"status": "PASS", "mission_id": mission_id, "evidencia": {"respuesta": respuesta}}

    elif tarea["tipo"] == "diseno_arquitectura":
        veredicto = verificar_con_claude(tarea)
        return {"status": veredicto["status"], "mission_id": mission_id, "evidencia": veredicto}

    elif tarea["tipo"] == "verificar_existencia":
        existe = (RAIZ / tarea["nombre"]).exists()
        return {"status": "PASS", "mission_id": mission_id, "evidencia": {"existe": existe}}

    return investigar_comunidad(tarea)


@retry(stop=stop_after_attempt(20), wait=wait_exponential(multiplier=1, min=2, max=60), reraise=False)
def _intento_resolver_gap(tarea: dict, intento_actual: list) -> str:
    """Un solo intento, envuelto por Tenacity para backoff exponencial real
    entre reintentos (2s, 4s, 8s... hasta 60s), en vez de un for ciego."""
    intento_actual[0] += 1
    respuesta = consultar_experto_cerebras(
        contexto=tarea,
        pregunta=f"Intento {intento_actual[0]}/20: como resolver este GAP? {tarea}",
    )
    if "RESUELTO" not in respuesta.upper():
        raise ValueError("aun no resuelto, Tenacity reintenta con backoff")
    return respuesta


def investigar_comunidad(tarea: dict) -> dict:
    """Regla dura: nunca detenerse, nunca escalar sin intentar 20 formas.
    Ahora con backoff exponencial real (Tenacity) entre intentos."""
    mission_id = tarea.get("mission_id") or str(uuid.uuid4())
    intento_actual = [0]
    try:
        respuesta = _intento_resolver_gap(tarea, intento_actual)
        return {"status": "PASS", "mission_id": mission_id, "evidencia": {"intento": intento_actual[0], "respuesta": respuesta}}
    except Exception:
        return {"status": "GAP", "mission_id": mission_id, "evidencia": {"intentos": intento_actual[0], "nota": "registrado, no bloquea siguiente tarea"}}


def loop_principal(cola_tareas: list) -> None:
    """No stop, no escala. Termina una, sigue con la otra."""
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
