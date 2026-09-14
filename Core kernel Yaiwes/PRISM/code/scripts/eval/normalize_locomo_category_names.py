"""Normalize LoCoMo category names in existing result artifacts.

Older runs may have correct numeric ``category`` values but stale
``category_name`` strings in per-QA records and summary/report files. This
script rewrites completed LoCoMo result directories using the canonical mapping
from ``scripts.eval.locomo_loader``:

    1=multi_hop, 2=temporal, 3=open_domain, 4=single_hop, 5=adversarial

It is intentionally scoped to LoCoMo-style artifacts. LongMemEval result files
use string buckets and are ignored.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.eval.locomo_loader import CATEGORY_NAMES, category_name
from scripts.eval.report import format_report, summarize_results


def main() -> None:
    args = _parse_args()
    roots = [Path(p) for p in args.roots]
    changed_files: set[Path] = set()
    touched_runs: set[Path] = set()

    for root in roots:
        if not root.exists():
            print(f"SKIP missing root: {root}")
            continue
        for json_path in sorted(root.rglob("*.json")):
            if _should_skip_json(json_path):
                continue
            changed, run_dir = _normalize_json_file(json_path, dry_run=args.dry_run)
            if changed:
                changed_files.add(json_path)
            if run_dir is not None:
                touched_runs.add(run_dir)

    # Recompute summaries/reports for run directories with LoCoMo conv/result files.
    for run_dir in sorted(touched_runs):
        for mode in _modes_present(run_dir):
            summary_path = run_dir / f"summary_{mode}.json"
            if not summary_path.exists():
                continue
            changed = _rewrite_summary_and_report(
                run_dir=run_dir,
                mode=mode,
                dry_run=args.dry_run,
            )
            if changed:
                changed_files.add(summary_path)
                report_path = run_dir / f"report_{mode}.txt"
                if report_path.exists():
                    changed_files.add(report_path)

    action = "Would update" if args.dry_run else "Updated"
    print(f"{action} {len(changed_files)} files.")
    for path in sorted(changed_files):
        print(path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize LoCoMo category names in result artifacts.")
    parser.add_argument(
        "--roots",
        nargs="+",
        default=[
            str(PROJECT_ROOT / "scripts" / "eval" / "results" / "_authoritative"),
            str(PROJECT_ROOT / "scripts" / "eval" / "results_baselines"),
        ],
        help="Root directories to scan recursively.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _should_skip_json(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    if "results_longmemeval" in parts or "results_longmemeval_delta70" in parts:
        return True
    return False


def _normalize_json_file(path: Path, dry_run: bool) -> tuple[bool, Path | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return False, None

    changed = False
    run_dir: Path | None = None

    if isinstance(payload, dict):
        if isinstance(payload.get("results"), list):
            for record in payload["results"]:
                if isinstance(record, dict):
                    changed = _normalize_record(record) or changed
            if _looks_like_locomo_payload(payload):
                run_dir = path.parent
        elif isinstance(payload.get("result"), dict):
            # LongMemEval per-question files also use "result"; normalize only
            # if the contained category is numeric.
            changed = _normalize_record(payload["result"]) or changed
            if changed:
                run_dir = path.parent

        if isinstance(payload.get("summary"), dict) and _normalize_summary(payload["summary"]):
            changed = True
            run_dir = path.parent

    if changed and not dry_run:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed, run_dir


def _looks_like_locomo_payload(payload: dict[str, Any]) -> bool:
    if "conversation_id" in payload:
        return True
    rows = payload.get("results")
    if isinstance(rows, list):
        return any(isinstance(r, dict) and "conversation_id" in r for r in rows)
    return False


def _normalize_record(record: dict[str, Any]) -> bool:
    if "category" not in record:
        return False
    try:
        cat_id = int(record.get("category"))
    except Exception:
        return False
    if cat_id not in CATEGORY_NAMES:
        return False
    expected = category_name(cat_id)
    if record.get("category_name") == expected:
        return False
    record["category_name"] = expected
    return True


def _normalize_summary(summary: dict[str, Any]) -> bool:
    changed = False
    rows = summary.get("per_category")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict) or "category_id" not in row:
                continue
            try:
                cat_id = int(row.get("category_id"))
            except Exception:
                continue
            if cat_id not in CATEGORY_NAMES:
                continue
            expected = category_name(cat_id)
            if row.get("category_name") != expected:
                row["category_name"] = expected
                changed = True
    return changed


def _modes_present(run_dir: Path) -> list[str]:
    modes: list[str] = []
    for path in sorted(run_dir.glob("summary_*.json")):
        stem = path.stem
        if stem.startswith("summary_"):
            modes.append(stem[len("summary_") :])
    return modes


def _rewrite_summary_and_report(run_dir: Path, mode: str, dry_run: bool) -> bool:
    records: list[dict[str, Any]] = []
    ingestion_stats: list[dict[str, Any]] = []
    for path in sorted(run_dir.glob("conv-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            continue
        if payload.get("mode") and payload.get("mode") != mode:
            # Some old sanity/full files share directories. Only use files from
            # the requested mode when the mode is recorded.
            continue
        for record in payload["results"]:
            if isinstance(record, dict):
                _normalize_record(record)
                records.append(record)
        for meta_key in ("ingestion", "index", "context"):
            if isinstance(payload.get(meta_key), dict):
                ingestion_stats.append(payload[meta_key])
                break

    if not records:
        return False

    summary_path = run_dir / f"summary_{mode}.json"
    if not summary_path.exists():
        return False
    try:
        summary_payload = json.loads(summary_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return False

    new_summary = summarize_results(records, ingestion_stats=ingestion_stats)
    summary_payload["summary"] = new_summary
    ablation = str(summary_payload.get("ablation") or summary_payload.get("baseline") or run_dir.name)
    report_text = format_report(new_summary, ablation=ablation)

    new_summary_text = json.dumps(summary_payload, ensure_ascii=False, indent=2)
    old_summary_text = summary_path.read_text(encoding="utf-8-sig")
    report_path = run_dir / f"report_{mode}.txt"
    old_report_text = report_path.read_text(encoding="utf-8-sig") if report_path.exists() else None
    changed = old_summary_text != new_summary_text or (
        old_report_text is not None and old_report_text != report_text
    )

    if changed and not dry_run:
        summary_path.write_text(new_summary_text, encoding="utf-8")
        if report_path.exists():
            report_path.write_text(report_text, encoding="utf-8")
    return changed


if __name__ == "__main__":
    main()
