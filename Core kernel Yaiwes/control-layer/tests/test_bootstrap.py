"""Tests A17 · bootstrap pipeline."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bootstrap import run_control_pipeline
from runtime.durable import DurableRuntime


def test_pipeline_read_ok():
    r = run_control_pipeline(op_type="READ_LOCAL", payload={"path": "x"}, mount_mode="dual")
    assert r.ok is True
    assert r.blocked is False


def test_pipeline_secret_blocks_with_durable():
    with tempfile.TemporaryDirectory() as td:
        rt = DurableRuntime(Path(td))
        r = run_control_pipeline(
            op_type="WRITE_LOCAL",
            payload={"content": "api_key=sk-x"},
            goal="write secret",
            runtime=rt,
            mount_mode="wordflow",
        )
        assert r.blocked is True
        assert r.mission_id
        st = rt.load(r.mission_id)
        assert st is not None
        assert len(st.checkpoints) >= 1


if __name__ == "__main__":
    test_pipeline_read_ok()
    test_pipeline_secret_blocks_with_durable()
    print("A17 tests OK")
