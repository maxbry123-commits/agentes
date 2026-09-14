from pathlib import Path
import tempfile
import unittest
from yaiwes_persistence_adapter import YaiwesPersistenceAdapter

class PersistenceAdapterTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            state_path = Path(td) / "state.json"
            adapter = YaiwesPersistenceAdapter(state_path)
            state = adapter.claim("T-1")
            self.assertEqual(state.status, "CLAIMED")
            state = adapter.checkpoint_task("T-1", {"step": 2})
            self.assertEqual(state.checkpoint["step"], 2)
            state = adapter.verify("T-1", {"pass": True})
            self.assertEqual(state.status, "VERIFIED")
            state = adapter.release("T-1")
            self.assertEqual(state.status, "RELEASED")

if __name__ == "__main__":
    unittest.main()
