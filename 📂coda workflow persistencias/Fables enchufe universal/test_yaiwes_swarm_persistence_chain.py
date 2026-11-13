from pathlib import Path
import tempfile
import unittest
from yaiwes_swarm_persistence_chain import run_chain

class SwarmChainTests(unittest.TestCase):
    def test_end_to_end_24_links(self):
        coda_root = Path(__file__).resolve().parents[1]
        registry = coda_root / "🏈 cancha deportiva de fútbol" / "YAIWES-SWARM-NAVY-SEALS-REGISTRY.json"
        with tempfile.TemporaryDirectory() as td:
            result = run_chain(registry, td, "TASK-E2E-001", {"goal": "persistence-test"})
            self.assertEqual(result["links_completed"], 24)
            self.assertEqual(result["evidence"][0]["order"], 1)
            self.assertEqual(result["evidence"][-1]["order"], 24)
            self.assertTrue(all(x["status"] == "RELEASED" for x in result["evidence"]))

if __name__ == "__main__":
    unittest.main()
