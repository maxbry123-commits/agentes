"""
watchdog.py - Se activa cuando la cola de tareas queda vacia.
Escanea el inventario oficial (GitHub API real, via GITHUB_TOKEN de
entorno) en busca de nodos PENDING_STEP1 y los reencola.
Codigo real, no placeholder.
"""
import os
import json
import time
import base64
from pathlib import Path

import requests

REPO = "maxbry123-commits/agentes"
INVENTARIO_PATH = "Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.json"


def watchdog_check(intervalo_segundos: int = 600) -> list[dict]:
    pendientes = escanear_inventario_por_pendientes()
    if pendientes:
        log(f"Watchdog encontro {len(pendientes)} tareas pendientes. Reencolando.")
        return pendientes
    log("Watchdog: sin tareas pendientes. Reintenta en 10 minutos.")
    time.sleep(intervalo_segundos)
    return []


def escanear_inventario_por_pendientes() -> list[dict]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log("GAP: GITHUB_TOKEN no configurado como variable de entorno")
        return []

    url = f"https://api.github.com/repos/{REPO}/contents/{INVENTARIO_PATH}"
    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
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
        if isinstance(c, dict) and c.get("crazy_wall_status") == "PENDING_STEP1"
    ]
    return pendientes


def log(mensaje: str) -> None:
    ruta = Path(__file__).parent / "watchdog.log"
    with open(ruta, "a") as f:
        f.write(f"{mensaje}\n")
