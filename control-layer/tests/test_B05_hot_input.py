"""B05 · hot-input S2 CORRECTION + S3 NEW_TASK."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inputblock.store import InputStore
from loops.correction_set import apply_correction
from runtime.durable import DurableRuntime


def test_s2_correction_same_mission():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td))
        store = InputStore()
        m = rt.create_mission("API v1")
        rt.checkpoint(m.mission_id, phase="ejecutar", cursor={"step": 4})
        r = apply_correction(
            runtime=rt,
            mission_id=m.mission_id,
            content="CORRECTION: usar /v2 no /v1",
            store=store,
        )
        assert r.same_mission is True
        assert r.rejected_new_task is False
        assert r.applied_signals >= 1
        st = rt.load(m.mission_id)
        assert st is not None
        assert st.mission_id == m.mission_id  # GOAL_LOCK
        assert st.cursor.get("last_signal_kind") in ("CORRECTION", "UPDATE")


def test_s3_new_task_does_not_mix():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td))
        m_a = rt.create_mission("mission A")
        rt.checkpoint(m_a.mission_id, phase="plan")
        r = apply_correction(
            runtime=rt,
            mission_id=m_a.mission_id,
            content="NEW_TASK: construir otro sistema",
        )
        assert r.rejected_new_task is True
        assert r.applied_signals == 0
        st = rt.load(m_a.mission_id)
        assert st is not None
        assert len(st.signals) == 0  # no encoló en A
        # B se crea aparte
        m_b = rt.create_mission("mission B desde NEW_TASK")
        assert m_b.mission_id != m_a.mission_id


def test_update_same_mission():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td))
        m = rt.create_mission("g")
        rt.checkpoint(m.mission_id, phase="plan")
        r = apply_correction(
            runtime=rt,
            mission_id=m.mission_id,
            content="UPDATE: añadir paso de tests",
        )
        assert r.same_mission is True
        assert r.rejected_new_task is False


if __name__ == "__main__":
    test_s2_correction_same_mission()
    test_s3_new_task_does_not_mix()
    test_update_same_mission()
    print("B05 OK")
