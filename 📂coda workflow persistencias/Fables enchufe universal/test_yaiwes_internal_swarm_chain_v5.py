from pathlib import Path
import tempfile, unittest
from yaiwes_internal_swarm_chain_v5 import run_swarm
class V5SwarmTest(unittest.TestCase):
    def test_24_components(self):
        coda = Path(__file__).resolve().parents[1]; registry = coda / "🏈 cancha deportiva de fútbol" / "YAIWES-INTERNAL-SWARM-REGISTRY-V5.json"
        with tempfile.TemporaryDirectory() as td:
            result = run_swarm(registry, td, "V5-E2E-001", {"goal":"task-persistence"}); self.assertEqual(result["components_completed"],24); self.assertTrue(all(x["status"]=="RELEASED" for x in result["evidence"]))
if __name__ == "__main__": unittest.main()
