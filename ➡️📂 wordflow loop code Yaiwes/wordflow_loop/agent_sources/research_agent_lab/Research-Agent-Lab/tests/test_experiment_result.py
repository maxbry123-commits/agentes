from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from schemas.experiment_result import ExperimentResult


class ExperimentResultSchemaTest(TestCase):
    def test_defaults(self):
        r = ExperimentResult(experiment_id="experiment_abc")
        self.assertTrue(r.result_id.startswith("expresult_"))
        self.assertEqual(r.status, "skipped")
        self.assertFalse(r.smoke_passed)
        self.assertFalse(r.eval_passed)
        self.assertEqual(r.metrics, {})
        self.assertEqual(r.log_tail, "")
        self.assertEqual(r.artifact_paths, [])
        self.assertEqual(r.duration_seconds, 0.0)
        self.assertEqual(r.error_message, "")
        self.assertEqual(r.run_command, "")
        self.assertEqual(r.notes, [])

    def test_full_populated(self):
        r = ExperimentResult(
            experiment_id="experiment_abc",
            status="passed",
            smoke_passed=True,
            eval_passed=True,
            metrics={"ADE": 0.35, "FDE": 0.72},
            log_tail="epoch 5: ADE=0.35 FDE=0.72",
            artifact_paths=["results/checkpoints/model_0005.p"],
            duration_seconds=45.2,
            run_command="python main_led_nba.py --cfg led_virat_debug",
            notes=["smoke run ok"],
        )
        self.assertEqual(r.status, "passed")
        self.assertTrue(r.smoke_passed)
        self.assertEqual(r.metrics["ADE"], 0.35)

    def test_json_roundtrip(self):
        r = ExperimentResult(
            experiment_id="experiment_xyz",
            status="failed",
            metrics={"ADE": 0.55},
            error_message="CUDA OOM",
        )
        d = asdict(r)
        json_text = json.dumps(d)
        loaded = json.loads(json_text)
        self.assertEqual(loaded["experiment_id"], "experiment_xyz")
        self.assertEqual(loaded["status"], "failed")
        self.assertEqual(loaded["metrics"]["ADE"], 0.55)

    def test_persist_to_artifact_store(self):
        from core.artifact_store import ArtifactStore

        r = ExperimentResult(
            experiment_id="experiment_test",
            status="passed",
            metrics={"FDE": 1.23},
        )
        with TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp))
            store.save_json("run_test", "experiment_results", r.result_id, r)
            files = store.list_artifacts("run_test", "experiment_results")
            self.assertEqual(len(files), 1)
            self.assertTrue(str(files[0]).endswith(".json"))


if __name__ == "__main__":
    main()
