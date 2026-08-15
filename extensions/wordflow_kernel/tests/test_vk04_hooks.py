"""VK-04 tests — memory checkpoint ledger trace."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.memory import PersistentMemory
from wordflow_kernel.checkpoint import CheckpointStore
from wordflow_kernel.ledger import MissionLedger
from wordflow_kernel.trace import TraceStore


class TestVK04(unittest.TestCase):
    def test_memory_store_search(self):
        with tempfile.TemporaryDirectory() as td:
            m = PersistentMemory(td)
            m.store({"k": "hello"}, scope="W1")
            hits = m.search("hello", scope="W1")
            self.assertEqual(len(hits), 1)

    def test_checkpoint_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            cp = CheckpointStore(td)
            saved = cp.save("M1", "PLAN", {"tasks": [1]})
            loaded = cp.load("M1")
            self.assertEqual(loaded["stage"], "PLAN")
            self.assertEqual(saved.state_hash, loaded["state_hash"])

    def test_ledger_chain(self):
        with tempfile.TemporaryDirectory() as td:
            led = MissionLedger(td)
            led.append("M1", {"stage": "A"})
            led.append("M1", {"stage": "B"})
            self.assertTrue(led.verify("M1"))

    def test_trace_parent(self):
        with tempfile.TemporaryDirectory() as td:
            tr = TraceStore(td)
            e1 = tr.emit("M1", "AUDIT", "ENTER", {"input": {"x": 1}})
            e2 = tr.emit("M1", "PLAN", "EXIT", {"input": {}, "output": {"ok": True}})
            self.assertEqual(e2.parent_trace, e1.trace_id)
            self.assertEqual(len(tr.read("M1")), 2)


if __name__ == "__main__":
    unittest.main()
