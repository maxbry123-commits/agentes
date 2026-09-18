"""
watchdog.py - FIX P0-08, P0-09, P0-10 (auditoria 5x).
P0-08: campo real confirmado = wall_status (no crazy_wall_status).
       Verificado en vivo: 213 componentes PENDING_STEP1 reales.
P0-09: ahora expone reencolar_en(cola) que SI inserta las tareas devueltas.
P0-10: heartbeat real escrito a archivo (base minima de durabilidad -
       Wordflow/host externo puede leer este heartbeat para detectar
       si el worker sigue vivo, en vez de un sleep-once-return ciego).
"""
import json
import os
import time
import base64
from pathlib import Path

import requests

REPO = "maxbry123-commits/agentes"
INVENTARIO_PATH = "Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.json"
CAMPO_STATUS_REAL = "wall_status"  # P0-08 FIX: confirmado leyendo el inventario real


def watchdog_check(intervalo_segundos: int = 600) -> list[dict]:
    escribir_heartbeat("CHECKING")
    pendientes = escanear_inventario_por_pendientes()
    if pendientes:
        log(f"Watchdog encontro {len(pendientes)} tareas pendientes (wall_status={CAMPO_STATUS_REAL}=PENDING_STEP1).")
        escribir_heartbeat("FOUND_WORK", tareas=len(pendientes))
        return pendientes
    log("Watchdog: sin tareas pendientes. Reintenta en 10 minutos.")
    escribir_heartbeat("IDLE")
    time.sleep(intervalo_segundos)
    return []


def reencolar_en(cola_tareas: list, pendientes: list[dict]) -> int:
    """P0-09 FIX: antes, activar_watchdog() ignoraba el retorno de
    watchdog_check(). Ahora se llama explicitamente para insertar las
    tareas encontradas de vuelta en la cola real del ejecutor."""
    tareas_convertidas = [
        {"tipo": "verificar_existencia", "nombre": c.get("name", ""), "componente_origen": c}
        for c in pendientes
        if isinstance(c, dict)
    ]
    cola_tareas.extend(tareas_convertidas)
    log(f"Watchdog reencolo {len(tareas_convertidas)} tareas en la cola real.")
    return len(tareas_convertidas)


def escanear_inventario_por_pendientes() -> list[dict]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log("GAP: GITHUB_TOKEN no configurado como variable de entorno")
        return []

    url = f"https://api.github.com/repos/{REPO}/contents/{INVENTARIO_PATH}"
    try:
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        contenido = base64.b64decode(data["content"]).decode("utf-8")
        inventario = json.loads(contenido)
    except Exception as e:
        log(f"GAP: error leyendo inventario: {e}")
        return []

    componentes = inventario.get("components", inventario if isinstance(inventario, list) else [])
    pendientes = [
        c for c in componentes
        if isinstance(c, dict) and c.get(CAMPO_STATUS_REAL) == "PENDING_STEP1"
    ]
    return pendientes


def escribir_heartbeat(estado: str, **extra) -> None:
    """P0-10 FIX (parcial, base minima): heartbeat real en archivo, para
    que un host externo (Wordflow) pueda detectar heartbeat perdido y
    hacer reclaim - en vez de un sleep-once-return sin rastro."""
    ruta = Path(__file__).parent / "watchdog_heartbeat.json"
    payload = {"estado": estado, "timestamp": time.time(), **extra}
    with open(ruta, "w") as f:
        json.dump(payload, f)


def log(mensaje: str) -> None:
    ruta = Path(__file__).parent / "watchdog.log"
    with open(ruta, "a") as f:
        f.write(f"{mensaje}\n")
