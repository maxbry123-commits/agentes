import json
import tempfile
import unittest
from pathlib import Path

from bayesian_agent.benchmarks.realfin import (
    build_realfin_prompt,
    grade_realfin_task,
    setup_realfin_workspace,
)
from experiments.run_benchmarks import build_run_plan


class RealFinBenchmarkTests(unittest.TestCase):
    def test_setup_realfin_workspace_exposes_local_cache_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            data_root = Path(td) / "datasets"
            cache_root = data_root / "realfin_benchmark" / "api_cache"
            (cache_root / "baostock" / "daily_qfq_20230101_20260331").mkdir(parents=True)
            (cache_root / "baostock" / "manifest_daily_qfq_20230101_20260331.json").write_text("{}", encoding="utf-8")
            (cache_root / "baostock" / "manifest_aux_daily_qfq_20230101_20260331.json").write_text("{}", encoding="utf-8")
            (cache_root / "tencent" / "manifest_day_qfq_20240101_20260331.json").parent.mkdir(parents=True)
            (cache_root / "tencent" / "manifest_day_qfq_20240101_20260331.json").write_text("{}", encoding="utf-8")
            task = {
                "id": "task_01",
                "prompt": "请将结果写入 `result.txt`。",
                "reference_ans": "hidden",
                "automated_checks": "hidden",
            }
            workspace = Path(td) / "run"

            manifest = setup_realfin_workspace(task, data_root=data_root, workspace=workspace)

            self.assertTrue((workspace / "task.json").exists())
            self.assertTrue((workspace / "realfin_cache_manifest.json").exists())
            self.assertEqual(manifest["cache_root"], str(cache_root.resolve()))
            self.assertNotIn("reference_ans", json.loads((workspace / "task.json").read_text()))

    def test_realfin_prompt_names_cache_and_avoids_eastmoney(self):
        task = {"id": "task_01", "prompt": "将结果写入 `result.txt`。"}
        prompt = build_realfin_prompt(task, Path("/tmp/workspace"))

        self.assertIn("realfin_cache_manifest.json", prompt)
        self.assertIn("api_cache", prompt)
        self.assertIn("Do not call EastMoney", prompt)
        self.assertIn("push2his.eastmoney.com", prompt)
        self.assertIn("result.txt", prompt)
        self.assertIn("write `300531`, not `sz.300531`", prompt)
        self.assertIn("kline/history", prompt)
        self.assertIn("skip rows with blank OHLCV fields", prompt)
        self.assertIn("loaded history/kline OHLCV data", prompt)

    def test_grade_realfin_task_executes_automated_checks(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            (workspace / "result.txt").write_text("ok", encoding="utf-8")
            task = {
                "automated_checks": (
                    "def grade(transcript, workspace_path):\n"
                    "    from pathlib import Path\n"
                    "    return {'file_created': 1.0 if (Path(workspace_path) / 'result.txt').exists() else 0.0}\n"
                )
            }

            scores, success, error = grade_realfin_task(task, {"transcript": "done"}, workspace)

            self.assertEqual(scores, {"file_created": 1.0})
            self.assertTrue(success)
            self.assertEqual(error, "")

    def test_grade_realfin_task_uses_model_response_log_trace(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            (workspace / "result.txt").write_text("300531", encoding="utf-8")
            (workspace / "model_response_log.txt").write_text("loaded history/kline OHLCV data MACD RSI MA5 均线", encoding="utf-8")
            task = {
                "automated_checks": (
                    "def grade(transcript, workspace_path):\n"
                    "    text = str(transcript).lower()\n"
                    "    return {'trace': 1.0 if 'history' in text and 'macd' in text and 'rsi' in text and 'ma5' in text else 0.0}\n"
                )
            }

            scores, success, error = grade_realfin_task(task, {"transcript": ""}, workspace)

            self.assertEqual(scores, {"trace": 1.0})
            self.assertTrue(success)
            self.assertEqual(error, "")

    def test_realfin_all_mode_plans_baseline_full_and_incremental(self):
        plan = build_run_plan("all", Path("/tmp/realfin"), [])

        self.assertEqual([run.name for run in plan], ["baseline", "bayesian_full", "bayesian_incremental"])
        self.assertEqual(plan[2].baseline_paths, ["/tmp/realfin/baseline/results.json"])


if __name__ == "__main__":
    unittest.main()
