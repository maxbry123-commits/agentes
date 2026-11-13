"""Tests A09 · durable resume + signals."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.durable import DurableRuntime, MissionStatus, SignalKind


def test_checkpoint_and_resume():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td))
        m = rt.create_mission("goal demo")
        rt.checkpoint(m.mission_id, phase="ejecutar", cursor={"step": 3})
        # simula caída: nueva instancia
        rt2 = DurableRuntime(Path(td))
        resumed = rt2.resume(m.mission_id)
        assert resumed.status == MissionStatus.RUNNING
        assert resumed.phase == "ejecutar"
        assert resumed.cursor.get("step") == 3
        assert len(resumed.checkpoints) == 1


def test_signal_fifo_correction():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td))
        m = rt.create_mission("g")
        rt.checkpoint(m.mission_id, phase="plan")
        rt.enqueue_signal(m.mission_id, SignalKind.UPDATE, {"patch": {"n": 1}})
        rt.enqueue_signal(m.mission_id, SignalKind.CORRECTION, {"patch": {"n": 2}})
        s1 = rt.apply_next_signal(m.mission_id)
        assert s1 is not None and s1.kind == SignalKind.UPDATE
        s2 = rt.apply_next_signal(m.mission_id)
        assert s2 is not None and s2.kind == SignalKind.CORRECTION
        st = rt.load(m.mission_id)
        assert st is not None
        assert st.cursor.get("patch") == {"n": 2}


def test_new_task_rejected_on_mission():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td))
        m = rt.create_mission("g")
        try:
            rt.enqueue_signal(m.mission_id, SignalKind.NEW_TASK, {})
            assert False, "should raise"
        except ValueError as e:
            assert "NEW_TASK" in str(e)


if __name__ == "__main__":
    test_checkpoint_and_resume()
    test_signal_fifo_correction()
    test_new_task_rejected_on_mission()
    print("A09 tests OK")
