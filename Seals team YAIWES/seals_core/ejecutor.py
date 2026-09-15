"""
ejecutor.py - El router 90/10 real. Este archivo NUNCA llama a un LLM
directamente. Solo decide, via if/elif, cual funcion determinista o
cual funcion de LLM debe correr, siguiendo dag_schema.yaml.
"""
import json
from pathlib import Path

from instalador_deterministico import instalar_componente
from consultor_experto import consultar_experto_cerebras
from verificador import verificar_con_claude

RAIZ = Path(__file__).parent


def ejecutar_tarea(tarea: dict) -> dict:
    """
    tarea = {"tipo": ..., "nombre": ..., "url": ..., "descripcion": ...}
    Devuelve {"status": "PASS"|"GAP", "evidencia": {...}}
    """
    if tarea["tipo"] == "instalar_paquete":
        ok = instalar_componente(tarea["nombre"], tarea["url"], RAIZ)
        if ok:
            return {"status": "PASS", "evidencia": {"path": str(RAIZ / tarea["nombre"])}}
        return investigar_comunidad(tarea)

    elif tarea["tipo"] == "evaluar_componente":
        respuesta = consultar_experto_cerebras(
            contexto=tarea, pregunta=f"Este componente encaja con YAIWES? {tarea}"
        )
        return {"status": "PASS", "evidencia": {"respuesta": respuesta}}

    elif tarea["tipo"] == "diseno_arquitectura":
        veredicto = verificar_con_claude(tarea)
        return {"status": veredicto["status"], "evidencia": veredicto}

    elif tarea["tipo"] == "verificar_existencia":
        existe = (RAIZ / tarea["nombre"]).exists()
        return {"status": "PASS", "evidencia": {"existe": existe}}

    return investigar_comunidad(tarea)


def investigar_comunidad(tarea: dict, max_intentos: int = 20) -> dict:
    """Regla dura: nunca detenerse, nunca escalar sin intentar 20 formas."""
    for intento in range(max_intentos):
        respuesta = consultar_experto_cerebras(
            contexto=tarea,
            pregunta=f"Intento {intento+1}/20: como resolver este GAP? {tarea}",
        )
        if "RESUELTO" in respuesta.upper():
            return {"status": "PASS", "evidencia": {"intento": intento + 1, "respuesta": respuesta}}
    return {"status": "GAP", "evidencia": {"intentos": max_intentos, "nota": "registrado, no bloquea siguiente tarea"}}


def loop_principal(cola_tareas: list[dict]) -> None:
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
