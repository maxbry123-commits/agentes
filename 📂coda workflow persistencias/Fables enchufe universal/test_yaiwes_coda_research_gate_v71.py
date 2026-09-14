from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import yaiwes_coda_research_gate_v71 as gate


class TestResearchGateV71(unittest.TestCase):
    def test_missing_research_connection_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "web.research is required"):
                gate.build_research_broker()

    def test_remote_plain_http_is_rejected(self):
        with self.assertRaises(ValueError):
            gate.ApiResearchAdapter("http://example.com/research")

    def test_configured_mcp_registers_research_capability(self):
        env = {
            "YAIWES_RESEARCH_MCP_URL": "https://research.example.test/mcp",
            "YAIWES_RESEARCH_MCP_TOOL": "search",
        }
        with patch.dict(os.environ, env, clear=True):
            broker = gate.build_research_broker()
            self.assertTrue(broker.has("web.research"))

    def test_canonical_entrypoint_requires_24_executed_research_cycles(self):
        fake_report = {
            "research_cycles": 24,
            "evidence": [{"research_status": "EXECUTED"} for _ in range(24)],
            "status": "CLOSED_24_CODA",
        }
        fake_broker = gate.bus.ToolBroker()
        fake_broker.register(
            gate.bus.ToolDescriptor(
                capability="web.research",
                name="fake",
                source="unit-test",
                description="benign research",
                risk="benign",
                executable=True,
            ),
            lambda payload: payload,
        )
        with patch.object(gate, "build_research_broker", return_value=fake_broker), patch.object(
            gate.bus, "run_coda_chain", return_value=fake_report
        ) as run:
            report = gate.run_coda_chain("/tmp/state", "task-1", {"objective": "test"})
            self.assertTrue(report["research_fail_closed"])
            run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
