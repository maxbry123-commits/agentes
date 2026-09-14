"""Healthcheck endpoint for monitoring and deployment.

Provides a simple HTTP endpoint (GET /health) that returns the
system state in JSON. Can be used by systemd, Docker,
or monitoring tools.

Bible reference: §15.5 (systemd + healthcheck)
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

# Start time
_start_time = time.monotonic()
_start_datetime = datetime.now(UTC)


def health_status(
    *,
    llm_available: bool = False,
    llm_backend: str = "ollama",
    channels_active: list[str] | None = None,
    memory_stats: dict[str, Any] | None = None,
    models_loaded: list[str] | None = None,
    errors: list[str] | None = None,
    queue_stats: dict[str, Any] | None = None,
    # Rueckwaertskompatibilitaet
    ollama_available: bool | None = None,
) -> dict[str, Any]:
    """Creates a health status report.

    Returns:
        Dict mit dem aktuellen Systemzustand:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "uptime_seconds": int,
            "started_at": "2026-02-22T10:00:00Z",
            "llm_backend": "openai",
            "llm_available": true/false,
            "ollama": true/false,  (backward compat)
            "channels": ["cli", "telegram"],
            "memory": {...},
            "models": ["gpt-5.2"],
            "queue": {...},
            "errors": [],
        }
    """
    # Backward compatibility: ollama_available as alias for llm_available
    if ollama_available is not None and not llm_available:
        llm_available = ollama_available

    uptime = int(time.monotonic() - _start_time)
    error_list = list(errors) if errors else []

    # Determine status
    if not llm_available:
        status = "degraded"
        error_list.append(f"LLM-Backend '{llm_backend}' nicht erreichbar")
    elif error_list:
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "uptime_seconds": uptime,
        "started_at": _start_datetime.isoformat(),
        "timestamp": datetime.now(UTC).isoformat(),
        "llm_backend": llm_backend,
        "llm_available": llm_available,
        "ollama": llm_available if llm_backend == "ollama" else False,  # backward compat
        "channels": channels_active or [],
        "memory": memory_stats or {},
        "models": models_loaded or [],
        "queue": queue_stats or {},
        "errors": error_list,
    }
