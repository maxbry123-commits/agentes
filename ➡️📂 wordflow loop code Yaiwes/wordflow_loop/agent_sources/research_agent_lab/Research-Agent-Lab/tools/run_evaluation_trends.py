from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def summarize_run_evaluations(runs_root: Path | str, *, limit: int = 20) -> dict[str, Any]:
    root = Path(runs_root)
    run_dirs = sorted(
        [path for path in root.glob("20*_*") if path.is_dir()],
        key=lambda path: path.stat().st_mtime,
    )[-limit:]
    reports: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        eval_dir = run_dir / "artifacts" / "run_evaluations"
        eval_files = sorted(eval_dir.glob("*.json")) if eval_dir.exists() else []
        if not eval_files:
            continue
        try:
            report = json.loads(eval_files[-1].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        report["_run_id"] = run_dir.name
        reports.append(report)

    scores = [int(r.get("score", 0) or 0) for r in reports]
    statuses = Counter(str(r.get("status", "unknown")) for r in reports)
    warning_counter: Counter[str] = Counter()
    blocking_counter: Counter[str] = Counter()
    for report in reports:
        warning_counter.update(str(item) for item in report.get("warnings", []) or [])
        blocking_counter.update(str(item) for item in report.get("blocking_issues", []) or [])

    latest = reports[-1] if reports else {}
    average = round(sum(scores) / len(scores), 2) if scores else 0.0
    return {
        "run_count": len(reports),
        "latest_run_id": latest.get("_run_id", ""),
        "latest_status": latest.get("status", ""),
        "latest_score": latest.get("score", 0),
        "average_score": average,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "status_counts": dict(statuses),
        "top_warnings": warning_counter.most_common(5),
        "top_blocking_issues": blocking_counter.most_common(5),
    }


def format_run_evaluation_summary(summary: dict[str, Any]) -> str:
    lines = [
        f"run_count={summary['run_count']}",
        f"latest={summary['latest_run_id']} status={summary['latest_status']} score={summary['latest_score']}",
        f"average_score={summary['average_score']} min={summary['min_score']} max={summary['max_score']}",
        f"status_counts={summary['status_counts']}",
    ]
    if summary["top_blocking_issues"]:
        lines.append("top_blocking_issues:")
        lines.extend(f"- {text} ({count})" for text, count in summary["top_blocking_issues"])
    if summary["top_warnings"]:
        lines.append("top_warnings:")
        lines.extend(f"- {text} ({count})" for text, count in summary["top_warnings"])
    return "\n".join(lines)
