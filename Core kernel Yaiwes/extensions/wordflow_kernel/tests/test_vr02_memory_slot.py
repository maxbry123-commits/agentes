"""VR-02 — Memory slot offline local."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.memory import PersistentMemory
from wordflow_kernel.memory_slot import MemoryOrchestratorAdapter, MemoryRequest
from wordflow_kernel.router_slot import RouterUniversalAdapter


class TestVR02(unittest.TestCase):
    def test_local_store_search(self):
        with tempfile.TemporaryDirectory() as td:
            mem = PersistentMemory(td)
            ad = MemoryOrchestratorAdapter(router=RouterUniversalAdapter(base_url=""), local=mem)
            r1 = ad.execute(
                MemoryRequest("t", "tr", "store", item={"k": "hello"}, scope="W")
            )
            self.assertEqual(r1.status, "OK")
            r2 = ad.execute(MemoryRequest("t", "tr", "search", query="hello", scope="W"))
            self.assertEqual(r2.status, "OK")
            self.assertTrue(len(r2.candidates) >= 1)

    def test_deny_without_backend(self):
        ad = MemoryOrchestratorAdapter(router=RouterUniversalAdapter(base_url=""), local=None)
        r = ad.execute(MemoryRequest("t", "tr", "search", query="x"))
        self.assertEqual(r.status, "DENY")


if __name__ == "__main__":
    unittest.main()
