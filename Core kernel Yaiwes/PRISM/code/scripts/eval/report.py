from __future__ import annotations

from statistics import mean
from typing import Any

from scripts.eval.locomo_loader import CATEGORY_NAMES, category_name
from scripts.eval.metrics import compute_judge_score


def summarize_results(
    results: list[dict[str, Any]],
    ingestion_stats: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    evaluated = [r for r in results if not r.get("error")]

    overall = {
        "count": len(evaluated),
        "judge_score": compute_judge_score(evaluated),
        "bleu1": _avg(evaluated, "bleu1"),
        "f1": _avg(evaluated, "f1"),
        "avg_query_latency_sec": _avg(evaluated, "retrieval_latency_sec"),
        "avg_context_tokens_est": _avg(evaluated, "context_tokens_est"),
    }

    per_category: list[dict[str, Any]] = []
    for cat_id in sorted(CATEGORY_NAMES.keys()):
        bucket = [r for r in evaluated if int(r.get("category", 0)) == cat_id]
        if not bucket:
            continue
        per_category.append(
            {
                "category_id": cat_id,
                "category_name": category_name(cat_id),
                "count": len(bucket),
                "judge_score": compute_judge_score(bucket),
                "bleu1": _avg(bucket, "bleu1"),
                "f1": _avg(bucket, "f1"),
            }
        )

    ingestion = _summarize_ingestion(ingestion_stats or [])
    return {"overall": overall, "per_category": per_category, "ingestion": ingestion}


def format_report(summary: dict[str, Any], ablation: str) -> str:
    overall = summary.get("overall", {})
    ingestion = summary.get("ingestion", {})
    rows = summary.get("per_category", [])

    lines: list[str] = []
    lines.append("=" * 58)
    lines.append(f"LoCoMo Evaluation Report - M-Mem ({ablation})")
    lines.append("=" * 58)
    lines.append("")
    lines.append("Overall:")
    lines.append(f"  LLM Judge Score: {overall.get('judge_score', 0.0):.4f}")
    lines.append(f"  BLEU-1:          {overall.get('bleu1', 0.0):.4f}")
    lines.append(f"  F1:              {overall.get('f1', 0.0):.4f}")
    lines.append(f"  #QA:             {int(overall.get('count', 0))}")
    lines.append("")
    lines.append("Per Category:")
    lines.append("  Category        Count   Judge    BLEU-1   F1")
    for row in rows:
        lines.append(
            f"  {row['category_name']:<14} "
            f"{int(row['count']):<7} "
            f"{row['judge_score']:.4f}   "
            f"{row['bleu1']:.4f}   "
            f"{row['f1']:.4f}"
        )
    lines.append("")
    lines.append("Ingestion Stats:")
    lines.append(f"  Conversations:  {int(ingestion.get('conversation_count', 0))}")
    lines.append(f"  Total chunks:   {int(ingestion.get('total_chunks', 0))}")
    lines.append(f"  Total episodes: {int(ingestion.get('total_episodes', 0))}")
    lines.append(f"  Avg ingest/chk: {ingestion.get('avg_ingest_sec_per_chunk', 0.0):.3f}s")
    lines.append("")
    lines.append("Retrieval Stats:")
    lines.append(f"  Avg query latency: {overall.get('avg_query_latency_sec', 0.0):.3f}s")
    lines.append(f"  Avg context tokens: {overall.get('avg_context_tokens_est', 0.1):.1f}")
    lines.append("=" * 58)
    return "\n".join(lines)


def _avg(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(r.get(key, 0.0)) for r in rows if r.get(key) is not None]
    if not values:
        return 0.0
    return mean(values)


def _summarize_ingestion(stats: list[dict[str, Any]]) -> dict[str, Any]:
    if not stats:
        return {
            "conversation_count": 0,
            "total_chunks": 0,
            "total_episodes": 0,
            "avg_ingest_sec_per_chunk": 0.0,
        }

    total_chunks = sum(int(s.get("chunk_count", 0)) for s in stats)
    total_episodes = sum(int(s.get("episode_count", 0)) for s in stats)
    chunk_times: list[float] = []
    for s in stats:
        value = s.get("ingest_sec_per_chunk")
        if value is not None:
            chunk_times.append(float(value))
    avg_chunk_time = mean(chunk_times) if chunk_times else 0.0

    return {
        "conversation_count": len(stats),
        "total_chunks": total_chunks,
        "total_episodes": total_episodes,
        "avg_ingest_sec_per_chunk": avg_chunk_time,
    }

