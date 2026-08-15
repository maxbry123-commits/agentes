"""VF-03 — forensic_audit EvidencePacket."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.forensic_api import forensic_audit
from wordflow_kernel.repo_truth import LocalRepoTruth


class TestVF03(unittest.TestCase):
    def test_packet_with_tasks(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, "x.py").write_text("def ok():\n    pass\n", encoding="utf-8")
            pkt = forensic_audit(
                target=td,
                requirements=[
                    {"requirement": "ok fn", "marker": "ok"},
                    {"requirement": "missing", "marker": "zzz_missing"},
                ],
                claims=[{"claim_id": "c1", "text": "ok", "marker": "ok"}],
                mission_id="M1",
                workspace_id="W1",
                repo=LocalRepoTruth(td),
            )
            self.assertTrue(pkt.packet_id.startswith("ep_"))
            self.assertEqual(pkt.mission_id, "M1")
            self.assertTrue(pkt.content_hash)
            self.assertEqual(len(pkt.recommended_tasks), 1)
            self.assertEqual(pkt.crosscheck.get("counts", {}).get("IMPLEMENTED"), 1)


if __name__ == "__main__":
    unittest.main()
