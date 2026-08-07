"""API de memoria nativa del Wordflow · Local siempre · Tencent opcional."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from memory.providers.local_provider import LocalProvider
from memory.providers.tencent.adapter import TencentAdapter
from memory.router import MemoryRouter
from memory.schemas.context import MemoryContext


def build_memory_stack(
    *,
    state_dir: str | Path,
    enable_tencent: bool = False,
    tencent_url: str = "http://127.0.0.1:8420",
    tencent_api_key: str = "",
) -> MemoryRouter:
    local = LocalProvider(Path(state_dir) / "memory_local")
    secondary = None
    if enable_tencent:
        secondary = TencentAdapter(tencent_url, api_key=tencent_api_key)
    return MemoryRouter(local, secondary=secondary)


def default_context(
    *,
    project_id: str = "default",
    agent_id: str = "default",
    session_id: str = "",
    task_id: str = "",
    scope: str = "project",
) -> MemoryContext:
    return MemoryContext(
        project_id=project_id,
        agent_id=agent_id,
        session_id=session_id,
        task_id=task_id,
        memory_scope=scope,
    )
