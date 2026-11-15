"""ModeExportable: a user-created mode (system prompt + allowed tools). Pulled in
as a dependency when a shared dashboard's agent runs in a custom mode. Built-in
modes (agent/ask/plan/...) ship with every install, so they're never bundled,
they surface as requirements instead. Modes are referenced by slug, so import
reuses an existing same-slug mode rather than clobbering it (keeps the session's
`mode` pointer valid without rewriting it)."""
from __future__ import annotations

from backend.apps.swarm.exportable import DepRef, ExportContext, RemapTable
from backend.apps.swarm.models import EntityType, Requirement

# Machine-relative or install-owned fields that must not ride along.
P_DROP = {"is_builtin", "default_folder"}


class ModeExportable:
    type = EntityType.mode

    def __init__(self, mode_id: str, name: str, data: dict):
        self.local_id = mode_id
        self.name = name
        self.p_data = data

    @classmethod
    def load(cls, local_id: str) -> "ModeExportable | None":
        store = p_store()
        if store is None:
            return None
        m = store.load_mode(local_id)
        if m is None:
            return None
        d = m.model_dump()
        return cls(local_id, d.get("name") or local_id, d)

    def serialize(self, ctx: ExportContext) -> dict:
        return {k: v for k, v in self.p_data.items() if k not in P_DROP}

    def files(self) -> dict[str, bytes]:
        return {}

    def dependencies(self) -> list[DepRef]:
        return []

    def requirements(self) -> list[Requirement]:
        return []

    @classmethod
    def import_(cls, payload: dict, files: dict[str, bytes], remap: RemapTable) -> str:
        store = p_store()
        model = p_model()
        if store is None or model is None:
            from backend.apps.swarm.ziputil import BundleError
            raise BundleError("can't import this mode on this build")
        mid = payload.get("id") or (payload.get("name") or "mode").lower().replace(" ", "-")
        # Reuse a same-slug mode (incl. built-ins) instead of overwriting it; sessions point at modes by this slug.
        if store.load_mode(mid) is not None:
            return mid
        data = {k: v for k, v in payload.items() if k != "is_builtin"}
        data["id"] = mid
        data["is_builtin"] = False
        store._save(model(**data))
        return mid


def p_store():
    try:
        from backend.apps.modes import modes
        return modes
    except Exception:
        return None


def p_model():
    try:
        from backend.apps.modes.models import Mode
        return Mode
    except Exception:
        return None
