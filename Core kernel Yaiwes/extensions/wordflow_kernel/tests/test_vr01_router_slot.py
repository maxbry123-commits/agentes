"""VR-01 — Router slot contracts."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.router_slot import RouterUniversalAdapter, RouteRequest


class TestVR01(unittest.TestCase):
    def test_deny_without_url(self):
        ad = RouterUniversalAdapter(base_url="")
        self.assertFalse(ad.available())
        res = ad.route(RouteRequest("t", "tr", "llm.complete", {}))
        self.assertEqual(res.status, "DENY")


if __name__ == "__main__":
    unittest.main()
