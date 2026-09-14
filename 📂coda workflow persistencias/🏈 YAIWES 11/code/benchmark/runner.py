"""基准测试运行器 — 批量执行用例、收集指标、输出报告。"""

import json
import logging
import os
import threading
import time
import traceback
from dataclasses import dataclass, field, asdict
from typing import Optional

from config import Config
from agent.workflow import Workflow
from benchmark.case import BenchmarkCase, discover_cases
from benchmark.ui import BenchmarkUI

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """单个用例的执行结果。"""
    case_id: str
    name: str
    category: str
    difficulty: str
    solved: bool
    time_elapsed: float
    steps: int
    result: Optional[str] = None
    error: Optional[str] = None


class BenchmarkRunner:
    """基准测试运行器。"""

    def __init__(self, config: dict = None, cases_dir: str = None,
                 parallel: bool = False, max_workers: int = 2,
                 default_timeout: int = 600):
        self.config = config or Config.load_config()
        self.cases_dir = cases_dir
        self.parallel = parallel
        self.max_workers = max_workers
        self.default_timeout = default_timeout
        self.results: list[BenchmarkResult] = []

    # ── 运行 ────────────────────────────────────────────────────────

    def run_all(self, case_filter: str = None) -> list[BenchmarkResult]:
        """运行所有匹配的用例。"""
        cases = discover_cases(self.cases_dir)
        if case_filter:
            cases = [c for c in cases if case_filter.lower() in c.id.lower()
                     or case_filter.lower() in c.name.lower()]
            logger.info("筛选后剩余 %d 个用例", len(cases))

        if not cases:
            logger.warning("没有找到匹配的用例")
            return []

        self.results.clear()
        logger.info("基准测试开始 — %d 个用例, parallel=%s", len(cases), self.parallel)

        if self.parallel and len(cases) > 1:
            self._run_parallel(cases)
        else:
            for case in cases:
                result = self.run_single(case)
                self.results.append(result)

        self._summarize()
        return self.results

    def run_single(self, case: BenchmarkCase) -> BenchmarkResult:
        """运行单个用例。"""
        logger.info("=" * 60)
        logger.info("开始用例: [%s] %s (%s/%s)", case.id, case.name,
                     case.category, case.difficulty)
        logger.info("=" * 60)

        # 准备附件
        self._setup_attachments(case)

        # 构造非交互 UI
        ui = BenchmarkUI(flag_regex=case.flag_regex)
        stop_event = threading.Event()
        timeout = case.timeout or self.default_timeout

        # 定时器
        timer = threading.Timer(timeout, stop_event.set)
        timer.daemon = True
        timer.start()

        start = time.time()
        error = None
        result_str = None

        try:
            result_str = Workflow(
                config=self.config,
                mode=case.mode,
                ui=ui,
            ).solve(
                case.description,
                auto_mode=True,
                stop_event=stop_event,
            )
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
            logger.error("用例 %s 异常: %s", case.id, traceback.format_exc())
        finally:
            timer.cancel()
            elapsed = time.time() - start

        # 判断是否解决
        solved = case.matches_flag(result_str) if result_str else False

        # 从 checkpoint 读取步数
        steps = self._read_step_count(case.description, case.mode)

        result = BenchmarkResult(
            case_id=case.id,
            name=case.name,
            category=case.category,
            difficulty=case.difficulty,
            solved=solved,
            time_elapsed=round(elapsed, 1),
            steps=steps,
            result=result_str,
            error=error,
        )

        status = "✅" if solved else "❌"
        logger.info("%s [%s] %s — %.1fs, %d 步%s",
                     status, case.id, case.name, elapsed, steps,
                     f" ({error})" if error else "")

        # 清理附件
        self._teardown_attachments(case)

        return result

    def _run_parallel(self, cases: list[BenchmarkCase]):
        """并行执行用例。"""
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            fut_map = {pool.submit(self.run_single, c): c for c in cases}
            for fut in as_completed(fut_map):
                try:
                    result = fut.result()
                    self.results.append(result)
                except Exception as e:
                    case = fut_map[fut]
                    self.results.append(BenchmarkResult(
                        case_id=case.id, name=case.name,
                        category=case.category, difficulty=case.difficulty,
                        solved=False, time_elapsed=0, steps=0,
                        error=f"RunnerError: {e}",
                    ))

    # ── 辅助 ────────────────────────────────────────────────────────

    def _setup_attachments(self, case: BenchmarkCase):
        """将用例的 files 写入 attachments/ 目录。"""
        if not case.files:
            return
        os.makedirs("attachments", exist_ok=True)
        for fname, content in case.files.items():
            fpath = os.path.join("attachments", fname)
            try:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.debug("写入附件: %s", fpath)
            except OSError as e:
                logger.warning("写入附件失败 %s: %s", fname, e)

    @staticmethod
    def _teardown_attachments(case: BenchmarkCase):
        """移除用例写入的附件。"""
        if not case.files:
            return
        for fname in case.files:
            fpath = os.path.join("attachments", fname)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
            except OSError:
                pass

    @staticmethod
    def _read_step_count(problem: str, mode: str) -> int:
        """从最新 checkpoint 中读取步数。"""
        try:
            from agent.checkpoint import CheckpointManager
            data = CheckpointManager.load(problem, mode)
            if data:
                return data.get("meta", {}).get("step_count", 0)
        except Exception:
            pass
        return 0

    # ── 报告 ────────────────────────────────────────────────────────

    def _summarize(self):
        """打印汇总。"""
        if not self.results:
            return

        total = len(self.results)
        solved = sum(1 for r in self.results if r.solved)
        avg_time = sum(r.time_elapsed for r in self.results) / total

        logger.info("=" * 60)
        logger.info("基准测试完成: %d/%d 通过 (%.1f%%), 平均 %.1fs",
                     solved, total, solved / total * 100, avg_time)

    def report_text(self) -> str:
        """生成终端可读的报告文本。"""
        if not self.results:
            return "无结果"

        lines = [
            "=" * 72,
            "  CTF Agent 基准测试报告",
            "=" * 72,
            "",
            f"  总计: {len(self.results)} 个用例",
            f"  通过: {sum(1 for r in self.results if r.solved)}",
            f"  失败: {sum(1 for r in self.results if not r.solved)}",
            "",
            "-" * 72,
            f"  {'ID':<20s} {'类别':<10s} {'难度':<8s} {'状态':<6s} {'耗时':>7s} {'步数':>5s}",
            "-" * 72,
        ]

        for r in self.results:
            status = "✅ PASS" if r.solved else "❌ FAIL"
            err_suffix = f"  {r.error}" if r.error else ""
            lines.append(
                f"  {r.case_id:<20s} {r.category:<10s} {r.difficulty:<8s}"
                f" {status:<6s} {r.time_elapsed:>6.1f}s {r.steps:>4d}{err_suffix}"
            )

        lines.extend([
            "-" * 72,
            "",
            "按类别统计:",
        ])

        by_cat = {}
        for r in self.results:
            by_cat.setdefault(r.category, []).append(r)
        for cat, items in sorted(by_cat.items()):
            n_solved = sum(1 for r in items if r.solved)
            lines.append(f"  {cat}: {n_solved}/{len(items)} ({n_solved/len(items)*100:.0f}%)")

        lines.append("")
        return "\n".join(lines)

    def report_json(self, path: str = None) -> str:
        """生成 JSON 报告。"""
        report = {
            "timestamp": time.time(),
            "summary": {
                "total": len(self.results),
                "solved": sum(1 for r in self.results if r.solved),
                "failed": sum(1 for r in self.results if not r.solved),
                "avg_time": round(
                    sum(r.time_elapsed for r in self.results) / len(self.results), 1
                ) if self.results else 0,
            },
            "results": [asdict(r) for r in self.results],
        }
        text = json.dumps(report, ensure_ascii=False, indent=2)
        if path:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            logger.info("报告已保存: %s", path)
        return text
