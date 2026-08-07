"""B04 · resume tras kill · sim S1 (proceso muere, otro retoma)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.durable import DurableRuntime, MissionStatus


def test_resume_after_process_death():
    with tempfile.TemporaryDirectory() as td:
        # proceso A
        rt_a = DurableRuntime(Path(td))
        m = rt_a.create_mission("misión larga 4h")
        rt_a.checkpoint(m.mission_id, phase="ejecutar", cursor={"step": 7, "file": "a.py"})
        rt_a.checkpoint(m.mission_id, phase="validar", cursor={"step": 8, "tests": 3})
        mid = m.mission_id
        token_before = rt_a.load(mid).run_token  # type: ignore

        # kill proceso A (solo dejamos de usar rt_a)
        del rt_a

        # proceso B (nueva instancia, mismo state_dir)
        rt_b = DurableRuntime(Path(td))
        resumed = rt_b.resume(mid)
        assert resumed.status == MissionStatus.RUNNING
        assert resumed.phase == "validar"
        assert resumed.cursor.get("step") == 8
        assert resumed.cursor.get("tests") == 3
        assert len(resumed.checkpoints) == 2
        assert resumed.run_token != token_before  # nuevo lease


def test_resume_completed_stays_completed():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td))
        m = rt.create_mission("done")
        rt.checkpoint(m.mission_id, phase="fin")
        rt.complete(m.mission_id, ok=True)
        r = DurableRuntime(Path(td)).resume(m.mission_id)
        assert r.status == MissionStatus.COMPLETED


def test_resume_cancelled_stays_cancelled():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td))
        m = rt.create_mission("cx")
        from runtime.durable import SignalKind

        rt.enqueue_signal(m.mission_id, SignalKind.CANCEL, {})
        rt.apply_next_signal(m.mission_id)
        r = DurableRuntime(Path(td)).resume(m.mission_id)
        assert r.status == MissionStatus.CANCELLED


if __name__ == "__main__":
    test_resume_after_process_death()
    test_resume_completed_stays_completed()
    test_resume_cancelled_stays_cancelled()
    print("B04 OK")
