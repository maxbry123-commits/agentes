from pathlib import Path
import tempfile
import unittest
from yaiwes_internal_swarm_chain_v4 import run_internal_chain

class InternalChainV4Tests(unittest.TestCase):
    def test_24_components_and_cumulative_links_close(self):
        coda = Path(__file__).resolve().parents[1]
        registry = coda / "🏈 cancha deportiva de fútbol" / "YAIWES-INTERNAL-SWARM-REGISTRY-V4.json"
        with tempfile.TemporaryDirectory() as td:
            result = run_internal_chain(registry, td, "TASK-INTERNAL-001", {"goal":"persistence"})
            self.assertEqual(result["components_closed"], 24)
            self.assertGreaterEqual(result["transformed_files_closed"], 299)
            self.assertTrue(all(x["status"] == "RELEASED" for x in result["evidence"]))
            self.assertTrue(all(x["links_closed"] >= 1 for x in result["evidence"]))

if __name__ == "__main__": unittest.main()
