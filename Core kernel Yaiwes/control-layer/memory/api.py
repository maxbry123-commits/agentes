"""API memoria nativa · Local siempre · Tencent opcional · Guard/Version."""
from __future__ import annotations

from pathlib import Path

from memory.guard import MemoryGuard
from memory.policy import MemoryPolicy
from memory.providers.local_provider import LocalProvider
from memory.providers.tencent.adapter import TencentAdapter
from memory.router import MemoryRouter
from memory.schemas.context import MemoryContext
from memory.versioning import VersionManager


def build_memory_stack(
    *,
    state_dir: str | Path,
    enable_tencent: bool = False,
    tencent_url: str = "http://127.0.0.1:8420",
    tencent_api_key: str = "",
    allow_global_write: bool = False,
) -> MemoryRouter:
    root = Path(state_dir)
    local = LocalProvider(root / "memory_local")
    secondary = None
    if enable_tencent:
        secondary = TencentAdapter(tencent_url, api_key=tencent_api_key)
    guard = MemoryGuard(MemoryPolicy(allow_global_write=allow_global_write))
    versions = VersionManager(root / "memory_versions.json")
    return MemoryRouter(local, secondary=secondary, guard=guard, versions=versions)


def default_context(
    *,
    project_id: str = "default",
    agent_id: str = "default",
    session_id: str = "",
    task_id: str = "",
    scope: str = "project",
    permissions: tuple[str, ...] = ("read", "write"),
) -> MemoryContext:
    return MemoryContext(
        project_id=project_id,
        agent_id=agent_id,
        session_id=session_id,
        task_id=task_id,
        memory_scope=scope,
        permissions=permissions,
    )
