"""Tests cimiento aislamiento + classifier + version + cache."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from memory.api import build_memory_stack, default_context
from memory.classifier import MemoryClass, classify_memory
from memory.guard import MemoryAccessDenied
from memory.integridad import check_local_integrity
from memory.schemas.context import MemoryNamespace
from memory.versioning import CacheKey, VersionManager


def test_isolation_namespaces():
    a = default_context(project_id="A", agent_id="backend", scope="private")
    b = default_context(project_id="B", agent_id="backend", scope="private")
    assert MemoryNamespace.from_context(a).value != MemoryNamespace.from_context(b).value


def test_write_denied_without_perm():
    with tempfile.TemporaryDirectory() as td:
        rt = build_memory_stack(state_dir=td)
        ctx = default_context(project_id="A", permissions=("read",))
        try:
            rt.capture(ctx, "dato", skip_classifier=True)
            raise AssertionError("expected deny")
        except MemoryAccessDenied:
            pass


def test_classifier_discard_noise():
    r = classify_memory("ok")
    assert r.klass == MemoryClass.DISCARD
    assert r.store is False


def test_version_bump_invalidates_cache_key_concept():
    with tempfile.TemporaryDirectory() as td:
        vm = VersionManager(Path(td) / "v.json")
        ctx = default_context(project_id="P")
        c1 = vm.attach(ctx)
        k1 = CacheKey.build(c1, kind="recall", query="arch")
        vm.bump("P")
        c2 = vm.attach(ctx)
        k2 = CacheKey.build(c2, kind="recall", query="arch")
        assert k1.value != k2.value


def test_capture_recall_integrity():
    with tempfile.TemporaryDirectory() as td:
        rt = build_memory_stack(state_dir=td)
        ctx = default_context(project_id="JARVIS", agent_id="backend")
        rt.capture(
            ctx,
            "decidimos arquitectura hexagonal",
            meta={"name": "arch", "tags": ["JARVIS"], "register_doc": True},
        )
        hits = rt.recall(ctx, "hexagonal")
        assert hits
        rep = check_local_integrity(Path(td) / "memory_local")
        assert rep.ok


if __name__ == "__main__":
    test_isolation_namespaces()
    test_write_denied_without_perm()
    test_classifier_discard_noise()
    test_version_bump_invalidates_cache_key_concept()
    test_capture_recall_integrity()
    print("MC04-MC08 OK")
