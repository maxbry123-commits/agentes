"""B09 · sim S8 · signals sobreviven caída larga y se aplican en orden."""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from loops.correction_set import rebuild_from_pending_signals
from runtime.durable import DurableRuntime, MissionStatus, SignalKind


def test_signals_survive_restart_and_apply_fifo():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td))
        m = rt.create_mission("larga")
        rt.checkpoint(m.mission_id, phase="ejecutar", cursor={"step": 1})
        # llegan signals mientras "proceso caído"
        rt.enqueue_signal(m.mission_id, SignalKind.UPDATE, {"patch": {"n": 1}})
        rt.enqueue_signal(m.mission_id, SignalKind.CORRECTION, {"patch": {"n": 2}})
        # simula 24h: no tocamos applied; solo reiniciamos runtime
        del rt
        time.sleep(0.01)

        rt2 = DurableRuntime(Path(td))
        pending = rt2.pending_signals(m.mission_id)
        assert len(pending) == 2
        assert pending[0].kind == SignalKind.UPDATE
        assert pending[1].kind == SignalKind.CORRECTION

        r = rebuild_from_pending_signals(rt2, m.mission_id)
        assert r.applied_signals == 2
        st = rt2.load(m.mission_id)
        assert st is not None
        assert st.cursor.get("patch") == {"n": 2}  # último gana en cursor
        assert st.status == MissionStatus.RUNNING
        assert all(s.applied for s in st.signals)


def test_no_reorder_on_reload():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td))
        m = rt.create_mission("g")
        rt.enqueue_signal(m.mission_id, SignalKind.UPDATE, {"i": 0})
        rt.enqueue_signal(m.mission_id, SignalKind.UPDATE, {"i": 1})
        rt.enqueue_signal(m.mission_id, SignalKind.CORRECTION, {"i": 2})
        ids = [s.signal_id for s in rt.pending_signals(m.mission_id)]
        ids2 = [s.signal_id for s in DurableRuntime(Path(td)).pending_signals(m.mission_id)]
        assert ids == ids2


if __name__ == "__main__":
    test_signals_survive_restart_and_apply_fifo()
    test_no_reorder_on_reload()
    print("B09 OK")
