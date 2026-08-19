"""T17 — run_knowledge_index(instance_id). No embeddings. Empty is OK."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .instance_store import InstanceStore, PersistentRegistry

_INDEX_EXTS = {".md", ".json", ".txt", ".yaml", ".yml"}


def run_knowledge_index(
    instance_id: str = "v1",
    *,
    store: Optional[InstanceStore] = None,
    registry: Optional[PersistentRegistry] = None,
) -> dict[str, Any]:
    if not instance_id or "/" in instance_id or ".." in instance_id:
        return {"ok": False, "indexed": 0, "error": "invalid instance_id"}

    used = store or (registry.store if registry is not None else InstanceStore())
    root = used.dir_for(instance_id)
    kdir = root / "knowledge"
    kdir.mkdir(parents=True, exist_ok=True)

    entries: list[str] = []
    for path in sorted(kdir.rglob("*")):
        if path.is_file() and path.suffix.lower() in _INDEX_EXTS:
            entries.append(path.relative_to(kdir).as_posix())

    return {
        "ok": True,
        "indexed": len(entries),
        "files": entries,
        "instance_id": instance_id,
        "root": str(kdir),
    }


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        store = InstanceStore(root=Path(tmp))
        empty = run_knowledge_index("v1", store=store)
        assert empty["ok"] is True
        assert empty["indexed"] == 0
        k = Path(empty["root"])
        (k / "note.md").write_text("# n\n", encoding="utf-8")
        one = run_knowledge_index("v1", store=store)
        assert one["indexed"] == 1
        other = run_knowledge_index("v2", store=store)
        assert other["indexed"] == 0
        print("ok", empty["indexed"], one["indexed"], other["indexed"])
