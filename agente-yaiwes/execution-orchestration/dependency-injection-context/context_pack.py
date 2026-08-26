"""T16 — run_context_pack(instance_id) isolated file pack + hash.

A and B never share files.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from .bootstrap_multi import bootstrap
from .instance_store import InstanceStore, PersistentRegistry


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pack_dir(store: InstanceStore, instance_id: str) -> Path:
    return store.dir_for(instance_id)


def run_context_pack(
    instance_id: str = "v1",
    *,
    registry: Optional[PersistentRegistry] = None,
    store: Optional[InstanceStore] = None,
) -> dict[str, Any]:
    if not instance_id or "/" in instance_id or ".." in instance_id:
        return {"ok": False, "files": [], "hash": "", "error": "invalid instance_id"}

    if registry is not None:
        inst = bootstrap(instance_id, registry=registry)
        used_store = registry.store
    elif store is not None:
        used_store = store
        inst = None
    else:
        inst = bootstrap(instance_id)
        used_store = get_store_from_default()

    if inst is not None:
        used_store.save(inst)

    root = _pack_dir(used_store, instance_id)
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        files.append({"path": rel, "sha256": _sha256_bytes(data), "size": len(data)})

    digest_src = json.dumps(
        [{"path": f["path"], "sha256": f["sha256"]} for f in files],
        separators=(",", ":"),
        ensure_ascii=True,
    )
    pack_hash = _sha256_bytes(digest_src.encode("utf-8"))
    return {
        "ok": True,
        "files": files,
        "hash": pack_hash,
        "instance_id": instance_id,
        "root": str(root),
    }


def get_store_from_default() -> InstanceStore:
    from .spawn import get_registry

    return get_registry().store


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        store = InstanceStore(root=Path(tmp))
        reg = PersistentRegistry(store=store)
        a = bootstrap("v1", name="default", registry=reg)
        b = bootstrap("v2", name="second", registry=reg)
        a.state["mark"] = "A"
        b.state["mark"] = "B"
        store.save(a)
        store.save(b)
        pa = run_context_pack("v1", registry=reg)
        pb = run_context_pack("v2", registry=reg)
        assert pa["ok"] and pb["ok"]
        assert pa["hash"] != pb["hash"], (pa["hash"], pb["hash"])
        assert all(not f["path"].startswith("v2") for f in pa["files"])
        assert str(store.root / "v1") in pa["root"]
        assert str(store.root / "v2") in pb["root"]
        print("ok", pa["hash"][:12], pb["hash"][:12], len(pa["files"]), len(pb["files"]))
