"""Tests MC · LocalProvider + namespace + router."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from memory.api import build_memory_stack, default_context
from memory.schemas.context import MemoryNamespace


def test_namespace_isolation():
    a = default_context(project_id="JARVIS", agent_id="backend", scope="private")
    b = default_context(project_id="OTHER", agent_id="backend", scope="private")
    na = MemoryNamespace.from_context(a)
    nb = MemoryNamespace.from_context(b)
    assert na.value != nb.value
    assert "JARVIS" in na.value and "backend" in na.value


def test_local_capture_recall():
    with tempfile.TemporaryDirectory() as td:
        rt = build_memory_stack(state_dir=td, enable_tencent=False)
        ctx = default_context(project_id="P1", agent_id="coder")
        rt.capture(ctx, "arquitectura hexagonal backend", type="doc", meta={"name": "arch", "tags": ["P1", "arch"], "register_doc": True})
        hits = rt.recall(ctx, "hexagonal arquitectura", top_n=5)
        assert hits
        assert rt.health()["primary"]["status"] == "ok"


def test_tencent_health_degraded_without_server():
    from memory.providers.tencent.adapter import TencentAdapter

    ad = TencentAdapter("http://127.0.0.1:59999")
    h = ad.health()
    assert h["status"] == "degraded"


if __name__ == "__main__":
    test_namespace_isolation()
    test_local_capture_recall()
    test_tencent_health_degraded_without_server()
    print("memory_plane OK")
