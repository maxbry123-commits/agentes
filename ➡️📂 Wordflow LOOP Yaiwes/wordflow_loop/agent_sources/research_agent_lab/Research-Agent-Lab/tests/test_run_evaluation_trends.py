from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from tools.run_evaluation_trends import summarize_run_evaluations


def _write_eval(root: Path, run_id: str, status: str, score: int, warnings: list[str], blocking: list[str]) -> None:
    folder = root / run_id / "artifacts" / "run_evaluations"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "eval.json").write_text(json.dumps({
        "status": status,
        "score": score,
        "warnings": warnings,
        "blocking_issues": blocking,
        "summary": [f"status={status}", f"score={score}"],
    }), encoding="utf-8")


class RunEvaluationTrendTest(TestCase):
    def test_summarizes_status_counts_and_scores(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_eval(root, "20260618_000001_a1b2c3", "pass", 100, [], [])
            _write_eval(root, "20260618_000002_d4e5f6", "needs_review", 90, ["warn one"], [])
            _write_eval(root, "20260618_000003_g7h8i9", "block", 65, [], ["block one"])

            summary = summarize_run_evaluations(root, limit=10)

            self.assertEqual(summary["run_count"], 3)
            self.assertEqual(summary["status_counts"]["pass"], 1)
            self.assertEqual(summary["status_counts"]["needs_review"], 1)
            self.assertEqual(summary["status_counts"]["block"], 1)
            self.assertEqual(summary["average_score"], 85.0)
            self.assertEqual(summary["latest_status"], "block")

    def test_handles_empty_runs_directory(self):
        with TemporaryDirectory() as tmp:
            summary = summarize_run_evaluations(Path(tmp), limit=5)

            self.assertEqual(summary["run_count"], 0)
            self.assertEqual(summary["status_counts"], {})
            self.assertEqual(summary["average_score"], 0.0)


if __name__ == "__main__":
    main()
