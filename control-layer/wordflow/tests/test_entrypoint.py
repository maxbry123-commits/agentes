"""Tests A14 · Wordflow entrypoint."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow.entrypoint import WordflowApp


def test_run_mission_read_ok():
    with tempfile.TemporaryDirectory() as td:
        app = WordflowApp(Path(td))
        r = app.run_mission("leer readme", op_type="READ_LOCAL")
        assert r.blocked is False
        assert r.mission_id
        assert r.output.get("mode") == "wordflow"


def test_run_mission_secret_blocks():
    with tempfile.TemporaryDirectory() as td:
        app = WordflowApp(Path(td))
        r = app.run_mission(
            "escribir secret",
            op_type="WRITE_LOCAL",
            payload={"content": "api_key=sk-live-xxx"},
        )
        assert r.blocked is True
        assert r.sheriff_state in ("RED", "BLACK", "YELLOW", "ORANGE")


if __name__ == "__main__":
    test_run_mission_read_ok()
    test_run_mission_secret_blocks()
    print("A14 tests OK")
