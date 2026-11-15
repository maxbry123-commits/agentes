"""Control local de idempotencia y ventana horaria para Comand Center.

No contiene credenciales ni realiza llamadas de red. El archivo de estado se
crea en tiempo de ejecución junto a este módulo y no forma parte del código
fuente versionado.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

STATE_PATH = Path(__file__).with_name(".control_disparos.json")


def _estado_vacio() -> dict[str, Any]:
    return {"shas_procesados": [], "disparos": []}


def cargar_estado(state_path: Path = STATE_PATH) -> dict[str, Any]:
    """Carga el estado; ante archivo inexistente devuelve un estado vacío."""
    if not state_path.exists():
        return _estado_vacio()
    data = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("ESTADO_IDEMPOTENCIA_INVALIDO")
    data.setdefault("shas_procesados", [])
    data.setdefault("disparos", [])
    return data


def guardar_estado(estado: dict[str, Any], state_path: Path = STATE_PATH) -> None:
    """Guarda el estado con reemplazo atómico."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_name(state_path.name + ".tmp")
    tmp.write_text(json.dumps(estado, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, state_path)


def _normalizar_sha(commit_sha: str) -> str:
    sha = commit_sha.strip()
    if not sha:
        raise ValueError("COMMIT_SHA_VACIO")
    return sha


def sha_ya_procesado(commit_sha: str, state_path: Path = STATE_PATH) -> bool:
    """Devuelve True si el SHA ya cerró un ciclo de disparo."""
    sha = _normalizar_sha(commit_sha)
    estado = cargar_estado(state_path)
    return sha in estado["shas_procesados"]


def registrar_sha_procesado(commit_sha: str, state_path: Path = STATE_PATH) -> None:
    """Marca un SHA como procesado sin duplicarlo."""
    sha = _normalizar_sha(commit_sha)
    estado = cargar_estado(state_path)
    if sha not in estado["shas_procesados"]:
        estado["shas_procesados"].append(sha)
        guardar_estado(estado, state_path)


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def contar_disparos_ultima_hora(
    state_path: Path = STATE_PATH,
    ahora: datetime | None = None,
) -> int:
    """Cuenta disparos registrados dentro de la ventana móvil de una hora."""
    now = (ahora or datetime.now(timezone.utc)).astimezone(timezone.utc)
    limite = now - timedelta(hours=1)
    estado = cargar_estado(state_path)
    return sum(
        1
        for fila in estado["disparos"]
        if isinstance(fila, dict)
        and isinstance(fila.get("timestamp"), str)
        and _parse_timestamp(fila["timestamp"]) >= limite
    )


def registrar_disparo(
    commit_sha: str,
    component_id: str,
    state_path: Path = STATE_PATH,
    ahora: datetime | None = None,
) -> None:
    """Registra un intento de disparo antes de invocar el ejecutor existente."""
    sha = _normalizar_sha(commit_sha)
    component = str(component_id).strip()
    if not component:
        raise ValueError("COMPONENT_ID_VACIO")
    now = (ahora or datetime.now(timezone.utc)).astimezone(timezone.utc)
    limite = now - timedelta(hours=1)
    estado = cargar_estado(state_path)
    recientes = []
    for fila in estado["disparos"]:
        if not isinstance(fila, dict) or not isinstance(fila.get("timestamp"), str):
            continue
        if _parse_timestamp(fila["timestamp"]) >= limite:
            recientes.append(fila)
    recientes.append(
        {
            "commit_sha": sha,
            "component_id": component,
            "timestamp": now.isoformat(),
        }
    )
    estado["disparos"] = recientes
    guardar_estado(estado, state_path)
