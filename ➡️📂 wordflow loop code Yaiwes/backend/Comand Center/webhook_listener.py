"""Placeholder del futuro receptor de push events de GitHub.

Claude completará después el servidor HTTP. Este archivo NO abre puertos, NO
registra rutas HTTP y NO procesa peticiones de red.
"""

from __future__ import annotations

from typing import Any


def recibir_push_github_placeholder(payload: dict[str, Any]) -> None:
    """Punto de extensión documentado para el futuro listener HTTP.

    Responsabilidad futura autorizada:
    1. recibir un push event de GitHub;
    2. extraer el commit SHA del evento;
    3. entregar ese SHA a comandante_tactico_seal.ejecutar_ciclo().

    La implementación del servidor HTTP queda deliberadamente pendiente para
    Claude y no forma parte de este cambio.
    """
    del payload
    raise NotImplementedError("PLACEHOLDER_HTTP_PENDIENTE_DE_CLAUDE")
