"""VG-01 tests — MockIntelligenceGateway deterministic."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.gateway.intelligence import (
    MockIntelligenceGateway,
    make_request,
)


class TestMockGateway(unittest.TestCase):
    def setUp(self):
        self.gw = MockIntelligenceGateway(fixed_text="OK_MOCK")

    def test_llm_complete_mock(self):
        req = make_request("TASK-1", "llm.complete", {"messages": [{"role": "user", "content": "hi"}]})
        res = self.gw.execute(req)
        self.assertEqual(res.status, "MOCK")
        self.assertEqual(res.output.get("text"), "OK_MOCK")
        self.assertEqual(res.provider, "mock")
        self.assertIsNotNone(res.evidence_hash)

    def test_memory_recall_empty(self):
        req = make_request("TASK-2", "memory.recall", {"query": "x"})
        res = self.gw.execute(req)
        self.assertEqual(res.status, "MOCK")
        self.assertEqual(res.output.get("items"), [])

    def test_memory_capture(self):
        req = make_request("TASK-3", "memory.capture", {"event": {"k": 1}})
        res = self.gw.execute(req)
        self.assertTrue(res.output.get("stored"))

    def test_unknown_capability_deny(self):
        req = make_request("TASK-4", "foo.bar", {})
        res = self.gw.execute(req)
        self.assertEqual(res.status, "DENY")

    def test_router_body_shape(self):
        req = make_request("TASK-5", "llm.complete", {"messages": []})
        body = req.to_router_body()
        for key in ("request_id", "task_id", "trace_id", "operation", "policy", "input"):
            self.assertIn(key, body)
        self.assertEqual(body["operation"], "llm.complete")

    def test_calls_recorded(self):
        self.gw.execute(make_request("T", "llm.complete", {}))
        self.assertEqual(len(self.gw.calls), 1)


if __name__ == "__main__":
    unittest.main()
