from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from scripts.eval.locomo_loader import CATEGORY_NAMES
from scripts.eval.metrics import normalize_judge_label

SANITY_LLM_CALL_RATE = 0.461


def write_diagnostics_report(
    r5_results_dir: Path,
    a9_summary_path: Path,
    output_path: Path,
    sanity_llm_call_rate: float = SANITY_LLM_CALL_RATE,
) -> str:
    records = _load_records(r5_results_dir)
    r5_summary = _load_json(r5_results_dir / "summary_full.json")
    a9_summary = _load_json(a9_summary_path)
    report = build_diagnostics_report(
        records=records,
        r5_summary=r5_summary,
        a9_summary=a9_summary,
        sanity_llm_call_rate=sanity_llm_call_rate,
        result_source=r5_results_dir,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return report


def build_diagnostics_report(
    records: list[dict[str, Any]],
    r5_summary: dict[str, Any],
    a9_summary: dict[str, Any],
    sanity_llm_call_rate: float = SANITY_LLM_CALL_RATE,
    result_source: Path | None = None,
) -> str:
    clean_records = [r for r in records if not r.get("error")]
    total_records = len(clean_records)
    classifier_counts = Counter(str(r.get("classifier_used", "missing")) for r in clean_records)
    llm_count = classifier_counts.get("llm", 0)
    llm_rate = llm_count / total_records if total_records else 0.0
    delta_pp = (llm_rate - sanity_llm_call_rate) * 100.0

    lines: list[str] = []
    lines.append("# R5-1 Gated Full Diagnostics")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(f"- Records: {total_records}")
    source = result_source if result_source is not None else Path("scripts/eval/results/R5-1")
    lines.append(f"- Result source: `{_display_path(source)}`")
    lines.append(f"- Sanity LLM-call baseline: {_pct(sanity_llm_call_rate)}")
    lines.append("")
    lines.append("## Classifier Used Distribution")
    lines.append("")
    lines.append("| classifier_used | count | share |")
    lines.append("|---|---:|---:|")
    for name, count in _ordered_counts(classifier_counts):
        lines.append(f"| {name} | {count} | {_pct(count / total_records if total_records else 0.0)} |")
    lines.append("")
    lines.append("## LLM Call Rate")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("|---|---:|")
    lines.append(f"| R5-1 full LLM classifier calls | {llm_count} / {total_records} |")
    lines.append(f"| R5-1 full LLM-call rate | {_pct(llm_rate)} |")
    lines.append(f"| Sanity baseline | {_pct(sanity_llm_call_rate)} |")
    lines.append(f"| Delta vs sanity | {delta_pp:+.2f} pp |")
    lines.append("")
    lines.append("## Accuracy Heatmap")
    lines.append("")
    lines.extend(_format_heatmap(clean_records))
    lines.append("")
    lines.append("## Latency By Classifier")
    lines.append("")
    lines.extend(_format_latency_table(clean_records))
    lines.append("")
    lines.append("## Per-Category Accuracy: R5-1 vs A9 Full")
    lines.append("")
    lines.extend(_format_category_comparison(r5_summary, a9_summary))
    lines.append("")
    return "\n".join(lines)


def _load_records(results_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(results_dir.glob("conv-*.json")):
        payload = _load_json(path)
        for record in payload.get("results", []):
            if isinstance(record, dict):
                records.append(record)
    return records


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _ordered_counts(counts: Counter[str]) -> list[tuple[str, int]]:
    preferred = ["keyword_gated", "prototype", "llm", "none", "fallback", "keyword", "error", "missing"]
    rows: list[tuple[str, int]] = [(name, counts[name]) for name in preferred if counts.get(name)]
    seen = {name for name, _ in rows}
    rows.extend((name, count) for name, count in sorted(counts.items()) if name not in seen)
    return rows


def _format_heatmap(records: list[dict[str, Any]]) -> list[str]:
    categories = _category_names(records)
    classifiers = _classifier_names(records)
    lines = ["| category | " + " | ".join(classifiers) + " |"]
    lines.append("|---|" + "|".join("---:" for _ in classifiers) + "|")
    for category in categories:
        row = [category]
        for classifier in classifiers:
            bucket = [
                r
                for r in records
                if str(r.get("category_name", "unknown")) == category
                and str(r.get("classifier_used", "missing")) == classifier
            ]
            row.append(_accuracy_cell(bucket))
        lines.append("| " + " | ".join(row) + " |")
    return lines


def _format_latency_table(records: list[dict[str, Any]]) -> list[str]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        buckets[str(record.get("classifier_used", "missing"))].append(record)

    lines = ["| classifier_used | count | avg retrieval sec | avg total sec |"]
    lines.append("|---|---:|---:|---:|")
    for name, _ in _ordered_counts(Counter({k: len(v) for k, v in buckets.items()})):
        bucket = buckets[name]
        lines.append(
            f"| {name} | {len(bucket)} | "
            f"{_avg(bucket, 'retrieval_latency_sec'):.3f} | "
            f"{_avg(bucket, 'total_latency_sec'):.3f} |"
        )
    return lines


def _format_category_comparison(r5_summary: dict[str, Any], a9_summary: dict[str, Any]) -> list[str]:
    r5_rows = _summary_categories(r5_summary)
    a9_rows = _summary_categories(a9_summary)
    seen = set(r5_rows) | set(a9_rows)
    preferred = [CATEGORY_NAMES[i] for i in (1, 2, 3, 4)]
    categories = [name for name in preferred if name in seen]
    categories.extend(sorted(seen - set(categories)))
    lines = ["| category | R5-1 acc | A9-full acc | delta | R5-1 n | A9 n |"]
    lines.append("|---|---:|---:|---:|---:|---:|")
    for category in categories:
        r5 = r5_rows.get(category, {})
        a9 = a9_rows.get(category, {})
        r5_acc = float(r5.get("judge_score", 0.0))
        a9_acc = float(a9.get("judge_score", 0.0))
        lines.append(
            f"| {category} | {_pct(r5_acc)} | {_pct(a9_acc)} | "
            f"{(r5_acc - a9_acc) * 100.0:+.2f} pp | "
            f"{int(r5.get('count', 0))} | {int(a9.get('count', 0))} |"
        )
    return lines


def _summary_categories(summary_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    summary = summary_payload.get("summary", {})
    rows = summary.get("per_category", [])
    return {
        str(row.get("category_name", "unknown")): row
        for row in rows
        if isinstance(row, dict)
    }


def _category_names(records: list[dict[str, Any]]) -> list[str]:
    order = [CATEGORY_NAMES[i] for i in (1, 2, 3, 4)]
    seen = {str(r.get("category_name", "unknown")) for r in records}
    rows = [name for name in order if name in seen]
    rows.extend(sorted(seen - set(rows)))
    return rows


def _classifier_names(records: list[dict[str, Any]]) -> list[str]:
    counts = Counter(str(r.get("classifier_used", "missing")) for r in records)
    return [name for name, _ in _ordered_counts(counts)]


def _accuracy_cell(bucket: list[dict[str, Any]]) -> str:
    judged = [
        r for r in bucket
        if normalize_judge_label(str(r.get("judge_label", ""))) in {"CORRECT", "WRONG"}
    ]
    if not judged:
        return "-"
    correct = sum(
        1
        for r in judged
        if normalize_judge_label(str(r.get("judge_label", ""))) == "CORRECT"
    )
    return f"{_pct(correct / len(judged))} (n={len(judged)})"


def _avg(records: list[dict[str, Any]], key: str) -> float:
    values = [float(r[key]) for r in records if r.get(key) is not None]
    return mean(values) if values else 0.0


def _pct(value: float) -> str:
    return f"{value * 100.0:.2f}%"


def _display_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build R5-1 gated full diagnostics.")
    parser.add_argument("--r5-results-dir", type=Path, default=Path("scripts/eval/results/R5-1"))
    parser.add_argument("--a9-summary-path", type=Path, default=Path("scripts/eval/results/A9/summary_full.json"))
    parser.add_argument("--output-path", type=Path, default=Path("scripts/eval/reports/r5-1_gated_full_diagnostics.md"))
    parser.add_argument("--sanity-llm-call-rate", type=float, default=SANITY_LLM_CALL_RATE)
    args = parser.parse_args()
    write_diagnostics_report(
        r5_results_dir=args.r5_results_dir,
        a9_summary_path=args.a9_summary_path,
        output_path=args.output_path,
        sanity_llm_call_rate=args.sanity_llm_call_rate,
    )
    print(f"Saved diagnostics report: {args.output_path}")


if __name__ == "__main__":
    main()
