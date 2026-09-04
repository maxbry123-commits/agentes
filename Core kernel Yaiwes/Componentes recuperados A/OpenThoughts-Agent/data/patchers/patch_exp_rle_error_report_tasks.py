#!/usr/bin/env python3
"""
exp_rle_error_report v2 patcher.

Background
----------
DCAgent/exp_rle_error_report is a prompt-engineering treatment of the same
upstream 5,000-task pool used by exp_rle_detailed / exp_rle_heavy_padding /
exp_flat25_speed_bonus / exp_flat25_pseudocode / exp_flat25_stackoverflow
(those are covered by ``patch_exp_rle_detailed_tasks.py`` and
``patch_rle_flat25_tasks.py``).

QC observation (2026-05-14):
  Smoke test reports 200/200 infra-ok but only 2/200 solved (1%). Hand
  inspection of 10/10 traces shows the same disease as exp_rle_detailed:
  the synthesized ``tests/test_solution.py`` imports random third-party
  packages that are neither pre-installed in the daytona sandbox image
  nor mentioned in the task description. Examples observed in the QC dir:

    * task 0026 (Smart in-memory SDK):  test imports ``cmd2``
    * task 0053 (distributed_asgi):     test imports ``traveling_salesperson``
    * task 0058 (salesman.orders sig):  test imports ``get_pr_info``
    * task 0094 (PennyLane CUDA):       test imports ``aiocron``
    * task 0159 (Sphinx project):       test imports ``celery``
    * task 0204 (gs_quant datetime):    test imports ``soocii_pubsub_lib``
    * task 0217 (Patch class API):      test imports ``illud``
    * task 0244 (Ansible ceph role):    test imports csv/pandas-style names

  In every observed failure the agent's task description has zero overlap
  with the test imports, so no amount of agent skill can solve the task.
  The verifier correctly reports reward=0 (the tests don't even import),
  so this is not a "rubber-stamp" leak — it's a wholesale task/test
  mismatch in the upstream pool.

Container image (``environment/Dockerfile``) is just ``python3 + pytest``.
The runtime hook (``tests/test.sh``) pip-installs a fixed whitelist
(requests numpy pandas scipy scikit-learn torch tensorflow keras httpx
aiohttp ddtrace django flask fastapi matplotlib seaborn pillow pydantic
pytest-mock requests-mock faker pyyaml pytz cryptography bcrypt
hypothesis).

Fix
---
Reuse the rle_flat25 evaluator unchanged: drop any task whose
``tests/test_solution.py`` (a) doesn't compile or (b) imports a
top-level module that is neither stdlib, in the container whitelist,
nor mentioned literally in ``instruction.md``. Tasks are dropped (not
mutated) — the upstream 5,000-task pool is large enough that the
survivors remain a healthy dataset.

Idempotency: this patcher only removes task directories; re-running on a
already-filtered tree is a no-op (nothing left to drop).

Usage
-----
  python data/patchers/patch_exp_rle_error_report_tasks.py --root <tasks_dir>
  python data/patchers/patch_exp_rle_error_report_tasks.py --root <tasks_dir> --dry-run
  python data/patchers/patch_exp_rle_error_report_tasks.py --root <tasks_dir> --limit 200
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

# Reuse the shared evaluator from the rle_flat25 patcher.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from patch_rle_flat25_tasks import evaluate_task  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--root",
        required=True,
        type=Path,
        help="Directory containing extracted task folders.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report counts; do not delete dropped task folders.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only inspect the first N tasks (debug).",
    )
    p.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Write per-task verdict JSON to this file.",
    )
    p.add_argument(
        "--show-bad", type=int, default=20, help="Print the first N bad-import samples."
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    root: Path = args.root
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    task_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    print(
        f"[patch_exp_rle_error_report] inspecting {len(task_dirs)} tasks under {root}"
    )

    syntax_dropped = 0
    no_test_dropped = 0
    import_dropped = 0
    kept = 0

    bad_import_samples: list[tuple[str, list[str]]] = []
    verdicts: dict[str, dict] = {}

    for td in task_dirs:
        v = evaluate_task(td)
        verdicts[td.name] = v
        if v["kept"]:
            kept += 1
            continue
        reason = v["reason"]
        if reason == "no_test_file":
            no_test_dropped += 1
        elif (
            reason.startswith("syntax_error")
            or reason.startswith("ast_syntax")
            or reason.startswith("compile_error")
        ):
            syntax_dropped += 1
        elif reason == "missing_import":
            import_dropped += 1
            if len(bad_import_samples) < args.show_bad:
                bad_import_samples.append((td.name, v["bad_imports"]))

    total = len(task_dirs)

    print()
    print(f"[patch_exp_rle_error_report] total:          {total}")
    print(f"[patch_exp_rle_error_report] no test file:   {no_test_dropped}")
    print(f"[patch_exp_rle_error_report] syntax errors:  {syntax_dropped}")
    print(f"[patch_exp_rle_error_report] import dropped: {import_dropped}")
    print(f"[patch_exp_rle_error_report] kept:           {kept}")

    if bad_import_samples:
        print()
        print(
            f"[patch_exp_rle_error_report] sample bad-import drops (first {len(bad_import_samples)}):"
        )
        for tid, bad in bad_import_samples:
            print(f"  {tid}: {bad}")

    if args.report_json:
        args.report_json.write_text(json.dumps(verdicts, indent=2))
        print(
            f"[patch_exp_rle_error_report] wrote per-task verdicts: {args.report_json}"
        )

    if args.dry_run:
        print("[patch_exp_rle_error_report] dry-run: not deleting dropped tasks.")
        return

    removed = 0
    for tid, v in verdicts.items():
        if v["kept"]:
            continue
        target = root / tid
        if target.exists():
            shutil.rmtree(target)
            removed += 1
    print(f"[patch_exp_rle_error_report] removed {removed} dropped task directories.")


if __name__ == "__main__":
    main()
