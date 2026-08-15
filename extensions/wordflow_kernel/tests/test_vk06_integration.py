"""VK-06 — kernel package integration offline."""
import json
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.repo_truth import LocalRepoTruth
from wordflow_kernel.forensic import ForensicEngine
from wordflow_kernel.gap_tasks import GapTaskCompiler
from wordflow_kernel.memory import PersistentMemory
from wordflow_kernel.checkpoint import CheckpointStore
from wordflow_kernel.ledger import MissionLedger
from wordflow_kernel.trace import TraceStore
from wordflow_kernel.workflow import WordflowKernel
from wordflow_kernel.gateway import MockIntelligenceGateway
from wordflow_kernel.engines import EngineRegistry, OpenClawEngine, EngineRequest


class TestVK06(unittest.TestCase):
    def test_ficha_llm_deny(self):
        ficha = Path(__file__).resolve().parents[1] / "ficha.v2.json"
        data = json.loads(ficha.read_text(encoding="utf-8"))
        self.assertEqual(data["llm_control"], "DENY")
        self.assertIn("forensic.audit", data["provides"])

    def test_full_audit_plan_with_hooks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "code.py").write_text("def present():\n    return 1\n", encoding="utf-8")
            state = root / "state"
            repo = LocalRepoTruth(root)
            mem = PersistentMemory(state / "memory")
            cp = CheckpointStore(state / "cp")
            led = MissionLedger(state / "led")
            tr = TraceStore(state / "tr")
            k = WordflowKernel(
                audit_engine=ForensicEngine(repo),
                compiler=GapTaskCompiler(),
                trace=tr,
                ledger=led,
                checkpoints=cp,
                memory=mem,
            )
            report, tasks = k.audit_to_plan(
                "M-VK06",
                "W1",
                "local",
                [
                    {"requirement": "present", "marker": "present"},
                    {"requirement": "missing_fn", "marker": "missing_fn_xyz"},
                ],
            )
            self.assertEqual(report.matches, 1)
            self.assertEqual(len(tasks), 1)
            self.assertTrue(led.verify("M-VK06"))
            self.assertIsNotNone(cp.load("M-VK06"))
            self.assertGreaterEqual(len(tr.read("M-VK06")), 1)

    def test_engine_still_via_gateway(self):
        gw = MockIntelligenceGateway(fixed_text="OK")
        reg = EngineRegistry()
        reg.register(OpenClawEngine())
        res = reg.reason(
            "openclaw",
            EngineRequest("T", "TR", [{"role": "user", "content": "x"}]),
            gw,
        )
        self.assertEqual(res.content, "OK")


if __name__ == "__main__":
    unittest.main()
