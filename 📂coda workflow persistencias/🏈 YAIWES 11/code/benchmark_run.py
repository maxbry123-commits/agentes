#!/usr/bin/env python3
"""基准测试入口 — 批量运行 CTF 用例并输出报告。

用法:
    python benchmark_run.py                                   # 运行全部用例
    python benchmark_run.py --filter sqli                     # 只运行 ID/名称含 "sqli" 的用例
    python benchmark_run.py --parallel --workers 4            # 4 个并行 Worker
    python benchmark_run.py --report ./benchmark_results.json # 保存 JSON 报告
    python benchmark_run.py --list                            # 仅列出用例，不运行
"""

import argparse
import logging
import sys
import os

# 确保项目根在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from benchmark.case import discover_cases


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("benchmark_run.log", encoding="utf-8"),
        ],
    )
    # 降低依赖库的日志噪音
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def main():
    parser = argparse.ArgumentParser(
        description="CTF Agent 基准测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--filter", "-f", default=None,
                        help="按 ID 或名称筛选用例（不区分大小写）")
    parser.add_argument("--parallel", "-p", action="store_true",
                        help="并行执行用例")
    parser.add_argument("--workers", "-w", type=int, default=2,
                        help="并行 Worker 数（默认 2）")
    parser.add_argument("--timeout", "-t", type=int, default=600,
                        help="单个用例超时秒数（默认 600）")
    parser.add_argument("--report", "-r", default=None,
                        help="JSON 报告输出路径")
    parser.add_argument("--list", "-l", action="store_true",
                        help="仅列出可用用例，不执行")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger("benchmark")

    # 加载配置
    config = Config.load_config()

    # 列出用例
    cases = discover_cases()
    if not cases:
        logger.warning("未发现任何用例 (benchmark/cases/ 目录为空)")
        print("\n  请将 CTF 题目 YAML 文件放入 benchmark/cases/ 目录")
        print("  参考格式: benchmark/cases/example_basic.yaml\n")
        return

    if args.list:
        print(f"\n  可用用例 ({len(cases)} 个):\n")
        for c in cases:
            print(f"  {c.id:<24s} {c.name:<32s} {c.category:<10s} {c.difficulty:<8s}")
        print()
        return

    # 运行基准测试（延迟导入，避免 chromadb 等依赖干扰 --list）
    from benchmark.runner import BenchmarkRunner
    runner = BenchmarkRunner(
        config=config,
        parallel=args.parallel,
        max_workers=args.workers,
        default_timeout=args.timeout,
    )
    results = runner.run_all(case_filter=args.filter)

    # 输出报告
    print("\n")
    print(runner.report_text())

    if args.report:
        runner.report_json(path=args.report)

    # 退出码
    passed = sum(1 for r in results if r.solved)
    total = len(results)
    sys.exit(0 if total > 0 and passed == total else 1)


if __name__ == "__main__":
    main()
