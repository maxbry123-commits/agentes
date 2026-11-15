# -*- coding: utf-8 -*-
"""W8 tests — schemas, evidence_bridge, watchdog, supervisor, ficha.v2."""
from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wordflow.engine.evidence_bridge import goals_out_to_evidence_packet  # noqa: E402
from wordflow.engine.main_loop import run_main_12  # noqa: E402
from wordflow.engine.supervisor import (  # noqa: E402
    is_expired,
    make_checkpoint,
    refresh_ttl,
    validate_checkpoint,
)
from wordflow.engine.watchdog import check_watchdog  # noqa: E402

WF = Path(__file__).resolve().parents[1]
LOOP = WF / "store" / "main_12.yaml"
SCHEMAS = WF / "schemas"
FICHA = WF / "ficha.v2.json"


def _raw(**kw):
    b = {
        "schema_version": "1.0",
        "block_id": "IB-W8",
        "source_type": "chat",
        "raw_text": "Implementar control-layer/control/fingerprint.py ≤120 LOC",
        "quality_bar": "never_MVP",
        "goals_hint": ["fingerprint"],
        "priority": "P0",
        "doc_refs": [{"doc_id": "SALIDA4_FP", "section": "§14.2"}],
        "constraints": {"loc_limit": 120, "success_criteria": "tests green"},
    }
    b.update(kw)
    return b


class TestSchemasW1(unittest.TestCase):
    def test_architecture_schema(self):
        p = SCHEMAS / "architecture_output.schema.json"
        self.assertTrue(p.is_file())
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(data["$id"], "wordflow.architecture_output.v1")
        self.assertIn("files", data["required"])
        self.assertIn("evidence_ref", data["required"])

    def test_code_schema(self):
        p = SCHEMAS / "code_output.schema.json"
        self.assertTrue(p.is_file())
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(data["$id"], "wordflow.code_output.v1")
        self.assertEqual(data["properties"]["llm_control"]["const"], "DENY")


class TestEvidenceW2(unittest.TestCase):
    def test_packet_required_keys(self):
        pkt = goals_out_to_evidence_packet(
            block={"block_id": "IB-X", "doc_refs": [{"doc_id": "D1"}]},
            goals_out={"GOUT-01": {"status": "DONE"}},
            tasks=[{"path": "a.py", "status": "PENDING"}],
            loop_status="COMPLETED",
        )
        for k in ("schema_version", "task_id", "claim_status", "repo", "files", "doc_anchors"):
            self.assertIn(k, pkt)
        self.assertEqual(pkt["claim_status"], "PARTIAL")
        self.assertEqual(len(pkt["repo"]["base_commit"]), 40)
        self.assertGreaterEqual(len(pkt["doc_anchors"]), 1)

    def test_main_loop_emits_packet(self):
        state = run_main_12(_raw(), loop_path=LOOP)
        self.assertEqual(state["status"], "COMPLETED")
        pkt = state.get("evidence_packet")
        self.assertIsInstance(pkt, dict)
        self.assertEqual(pkt["schema_version"], "1.0")
        self.assertIn("task_id", pkt)


class TestWatchdogW3(unittest.TestCase):
    def test_ok(self):
        r = check_watchdog(
            step_id="S01", step_name="n", started_at=time.monotonic(), timeout_seconds=60
        )
        self.assertTrue(r["ok"])

    def test_timeout(self):
        r = check_watchdog(
            step_id="S01", step_name="n", started_at=time.monotonic() - 200, timeout_seconds=1
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "TIMEOUT")

    def test_secret_leak(self):
        r = check_watchdog(
            step_id="S05",
            step_name="sentinel",
            started_at=time.monotonic(),
            text_blobs=["token ghp_abcdefghijklmnopqrstuvwxyz0123456789"],
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "SECRET_LEAK")

    def test_stuck(self):
        r = check_watchdog(
            step_id="S05",
            step_name="sentinel",
            started_at=time.monotonic(),
            last_step_id="S05",
            same_step_count=5,
            stuck_threshold=3,
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "STUCK_STEP")


class TestSupervisorW4(unittest.TestCase):
    def test_checkpoint_ttl(self):
        cp = make_checkpoint(
            block_hash="abc",
            step_id="S11",
            step_name="checkpoint",
            steps_ok=10,
            steps_total=12,
            status="RUNNING",
            ttl_seconds=60,
        )
        self.assertFalse(is_expired(cp))
        self.assertEqual(validate_checkpoint(cp)["reason"], "OK")

    def test_expired(self):
        cp = make_checkpoint(
            block_hash="abc",
            step_id="S11",
            step_name="checkpoint",
            steps_ok=1,
            steps_total=1,
            status="RUNNING",
            ttl_seconds=0.001,
        )
        time.sleep(0.01)
        self.assertTrue(is_expired(cp))
        self.assertEqual(validate_checkpoint(cp)["reason"], "EXPIRED")

    def test_refresh(self):
        cp = make_checkpoint(
            block_hash="x",
            step_id="S12",
            step_name="n",
            steps_ok=1,
            steps_total=1,
            status="COMPLETED",
            ttl_seconds=1,
        )
        time.sleep(0.01)
        cp2 = refresh_ttl(cp, ttl_seconds=3600)
        self.assertFalse(is_expired(cp2))

    def test_main_loop_checkpoint(self):
        state = run_main_12(_raw(), loop_path=LOOP)
        cp = state.get("checkpoint")
        self.assertIsInstance(cp, dict)
        self.assertIn("expires_at", cp)
        self.assertEqual(cp.get("status"), "COMPLETED")


class TestFichaW7(unittest.TestCase):
    def test_ficha_abi(self):
        self.assertTrue(FICHA.is_file())
        data = json.loads(FICHA.read_text(encoding="utf-8"))
        self.assertEqual(data["abi_version"], "2.0")
        self.assertEqual(data["llm_control"], "DENY")
        self.assertEqual(data["mount_mode"], "sidecar")
        self.assertEqual(data["artifact_id"], "wordflow.yaiwes.v1")
        self.assertEqual(data["extension_type"], "wordflow_runtime")
        self.assertEqual(data["entry_point"], "extensions.wordflow.engine.entrypoint_v1:run_v1")


if __name__ == "__main__":
    unittest.main()
