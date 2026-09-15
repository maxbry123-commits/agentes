"""
watchdog.py - Se activa cuando la cola de tareas queda vacia.
Revisa el inventario oficial + Crazy Wall en busca de trabajo pendiente
(PENDING_STEP1) y lo reencola. Si no hay nada, espera y reintenta.
"""
import json
import time
from pathlib import Path


def watchdog_check(intervalo_segundos: int = 600) -> list[dict]:
    gaps = escanear_inventario_por_pendientes()
    if gaps:
        log(f"Watchdog encontro {len(gaps)} tareas pendientes. Reencolando.")
        return gaps
    log("Watchdog: sin tareas pendientes. Reintenta en 10 minutos.")
    time.sleep(intervalo_segundos)
    return []


def escanear_inventario_por_pendientes() -> list[dict]:
    """
    Placeholder: se conecta al inventario real via el conector GitHub
    (fuera del alcance de este archivo, lo hace el orquestador Claude
    o una llamada a la API de GitHub desde este mismo proceso).
    """
    return []


def log(mensaje: str) -> None:
    ruta = Path(__file__).parent / "watchdog.log"
    with open(ruta, "a") as f:
        f.write(f"{mensaje}\n")
