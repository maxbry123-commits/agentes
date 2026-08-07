"""Tests A10 · same mission rebuild."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inputblock.store import InputStore
from loops.correction_set import apply_correction, rebuild_from_pending_signals
from runtime.durable import DurableRuntime


def test_correction_same_mission():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td) / "state")
        store = InputStore()
        m = rt.create_mission("construir API")
        rt.checkpoint(m.mission_id, phase="plan", cursor={"step": 1})
        r = apply_correction(
            runtime=rt,
            mission_id=m.mission_id,
            content="CORRECTION: el endpoint debe ser /v2",
            store=store,
        )
        assert r.same_mission is True
        assert r.rejected_new_task is False
        assert r.applied_signals >= 1
        assert r.rebuild_hash.startswith("sha256:")
        assert len(store) == 1


def test_new_task_does_not_touch_mission():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td) / "state")
        m = rt.create_mission("g")
        before = rt.load(m.mission_id)
        r = apply_correction(
            runtime=rt,
            mission_id=m.mission_id,
            content="NEW_TASK: otro proyecto",
        )
        assert r.rejected_new_task is True
        after = rt.load(m.mission_id)
        assert before is not None and after is not None
        assert len(after.signals) == len(before.signals)


def test_pending_after_resume():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td) / "state")
        m = rt.create_mission("g")
        rt.checkpoint(m.mission_id, phase="ejecutar")
        from runtime.durable import SignalKind

        rt.enqueue_signal(m.mission_id, SignalKind.UPDATE, {"patch": {"x": 1}})
        # no apply yet — simula señal llegada mientras down
        r = rebuild_from_pending_signals(rt, m.mission_id)
        assert r.applied_signals == 1
        assert r.cursor.get("patch") == {"x": 1}


if __name__ == "__main__":
    test_correction_same_mission()
    test_new_task_does_not_touch_mission()
    test_pending_after_resume()
    print("A10 tests OK")
