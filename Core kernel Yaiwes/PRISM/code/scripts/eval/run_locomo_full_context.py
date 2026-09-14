from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mmem.config import MMemConfig
from mmem.utils.llm import LLMClient
from scripts.eval.locomo_loader import (
    LoCoMoConversation,
    QAPair,
    category_name,
    group_qa_by_conversation,
    load_locomo,
)
from scripts.eval.metrics import compute_bleu1, compute_f1, normalize_judge_label, tokenize
from scripts.eval.prompts import LLM_JUDGE_PROMPT, QA_GENERATION_PROMPT
from scripts.eval.report import format_report, summarize_results


logger = logging.getLogger("locomo_full_context")


def main() -> None:
    args = _parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    config = MMemConfig()
    llm_client = LLMClient(config=config.llm)

    conversations, qa_pairs = load_locomo(args.data_path)
    qa_by_conv = group_qa_by_conversation(qa_pairs)
    selected = _select_conversations(
        conversations=conversations,
        mode=args.mode,
        conv_id=args.conv_id,
        max_conversations=args.max_conversations,
    )

    baseline_name = args.baseline_name
    results_root = Path(args.results_dir) / baseline_name
    results_root.mkdir(parents=True, exist_ok=True)

    qa_limit = args.qa_limit
    if qa_limit is None and args.mode == "sanity":
        qa_limit = 200

    all_results: list[dict[str, Any]] = []
    context_stats: list[dict[str, Any]] = []

    for conv in selected:
        logger.info("Conversation %s: assembling full context", conv.sample_id)
        context_text = _format_full_context(conv)
        context_meta = {
            "checkpoint_dir": "",
            "loaded_from_checkpoint": False,
            "chunk_count": 1,
            "episode_count": 0,
            "ingest_total_sec": 0.0,
            "ingest_sec_per_chunk": 0.0,
            "retrieval_unit": "full_conversation",
            "context_chars": len(context_text),
            "context_tokens_est": len(tokenize(context_text)),
        }
        context_stats.append(context_meta)

        conv_qas = qa_by_conv.get(conv.sample_id, [])
        if not conv_qas:
            logger.warning("Conversation %s has no QA pairs, skipping", conv.sample_id)
            continue

        result_path = results_root / f"{conv.sample_id}.json"
        payload = _load_results_payload(
            result_path=result_path,
            conversation_id=conv.sample_id,
            baseline_name=baseline_name,
            mode=args.mode,
            context_meta=context_meta,
            config={
                "retrieval": "full_conversation_context",
                "answer_model": config.llm.qa_model,
                "judge_model": config.llm.judge_model,
            },
        )
        done_uids = {str(item.get("qa_uid", "")) for item in payload.get("results", [])}

        evaluated_count = 0
        for qa in conv_qas:
            if not args.include_adversarial and qa.category == 5:
                continue
            if qa_limit is not None and evaluated_count >= qa_limit:
                break

            qa_uid = _qa_uid(qa)
            if qa_uid in done_uids:
                evaluated_count += 1
                continue

            logger.info(
                "Evaluating %s QA#%d (%s)",
                conv.sample_id,
                qa.qa_index,
                category_name(qa.category),
            )
            record = _evaluate_one_qa(
                qa=qa,
                context_text=context_text,
                llm_client=llm_client,
                config=config,
            )
            if args.fail_on_error and record.get("judge_label") == "ERROR":
                raise RuntimeError(
                    f"QA evaluation failed for {conv.sample_id}#{qa.qa_index}: {record.get('error')}"
                )
            payload["results"].append(record)
            payload["updated_at"] = _utc_now()
            _write_json(result_path, payload)

            done_uids.add(qa_uid)
            evaluated_count += 1

        payload["context"] = context_meta
        payload["updated_at"] = _utc_now()
        _write_json(result_path, payload)
        all_results.extend(payload.get("results", []))

    summary = summarize_results(all_results, ingestion_stats=context_stats)
    report_text = format_report(summary, ablation=baseline_name)
    print(report_text)

    summary_payload = {
        "baseline": baseline_name,
        "mode": args.mode,
        "generated_at": _utc_now(),
        "summary": summary,
        "conversations": [c.sample_id for c in selected],
        "config": {
            "retrieval": "full_conversation_context",
            "include_adversarial": args.include_adversarial,
            "answer_model": config.llm.qa_model,
            "judge_model": config.llm.judge_model,
        },
    }
    summary_json_path = results_root / f"summary_{args.mode}.json"
    summary_txt_path = results_root / f"report_{args.mode}.txt"
    _write_json(summary_json_path, summary_payload)
    summary_txt_path.write_text(report_text, encoding="utf-8")

    logger.info("Saved summary JSON: %s", summary_json_path)
    logger.info("Saved report text:  %s", summary_txt_path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LoCoMo Full Context baseline.")
    parser.add_argument("--mode", choices=["sanity", "full"], default="sanity")
    parser.add_argument("--conv-id", type=str, default="0", help="Conversation index or sample_id for sanity mode.")
    parser.add_argument(
        "--data-path",
        type=str,
        default=str(PROJECT_ROOT / "scripts" / "eval" / "data" / "locomo10.json"),
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default=str(PROJECT_ROOT / "scripts" / "eval" / "results_baselines"),
    )
    parser.add_argument("--baseline-name", type=str, default="FullContext")
    parser.add_argument("--qa-limit", type=int, default=None, help="Optional max number of QA per conversation.")
    parser.add_argument("--max-conversations", type=int, default=None, help="Optional limit for full mode.")
    parser.add_argument("--include-adversarial", action="store_true", help="Include category=5 QA.")
    parser.add_argument("--fail-on-error", action="store_true", help="Abort without writing a QA record when evaluation fails.")
    return parser.parse_args()


def _evaluate_one_qa(
    qa: QAPair,
    context_text: str,
    llm_client: LLMClient,
    config: MMemConfig,
) -> dict[str, Any]:
    qa_uid = _qa_uid(qa)
    start_total = time.perf_counter()

    try:
        t0 = time.perf_counter()
        # Full Context has no retrieval model call; this measures context handoff overhead.
        retrieval_context = context_text
        retrieval_latency = time.perf_counter() - t0

        t1 = time.perf_counter()
        generated = llm_client.chat(
            prompt=QA_GENERATION_PROMPT.format(
                context=retrieval_context,
                question=qa.question,
            ),
            model=config.llm.qa_model,
            temperature=0.0,
        ).strip()
        generation_latency = time.perf_counter() - t1

        t2 = time.perf_counter()
        judge_raw = llm_client.chat_json(
            prompt=LLM_JUDGE_PROMPT.format(
                question=qa.question,
                gold_answer=qa.answer,
                generated_answer=generated,
            ),
            model=config.llm.judge_model,
            temperature=0.0,
        )
        judge_latency = time.perf_counter() - t2

        if isinstance(judge_raw, dict):
            judge_reasoning = str(judge_raw.get("reasoning", "")).strip()
            judge_label = normalize_judge_label(str(judge_raw.get("label", "")))
        else:
            judge_reasoning = ""
            judge_label = "UNKNOWN"

        bleu1 = compute_bleu1(qa.answer, generated)
        f1 = compute_f1(qa.answer, generated)
        total_latency = time.perf_counter() - start_total

        return {
            "qa_uid": qa_uid,
            "conversation_id": qa.conversation_id,
            "qa_index": qa.qa_index,
            "category": qa.category,
            "category_name": category_name(qa.category),
            "question": qa.question,
            "gold_answer": qa.answer,
            "generated_answer": generated,
            "evidence": qa.evidence,
            "judge_label": judge_label,
            "judge_reasoning": judge_reasoning,
            "bleu1": bleu1,
            "f1": f1,
            "retrieval_latency_sec": retrieval_latency,
            "generation_latency_sec": generation_latency,
            "judge_latency_sec": judge_latency,
            "total_latency_sec": total_latency,
            "bundles_count": 1,
            "best_bundle_score": None,
            "best_bundle_path": "full_context",
            "context_chars": len(retrieval_context),
            "context_tokens_est": len(tokenize(retrieval_context)),
            "context_preview": retrieval_context[:500],
            "query_type_hints": [],
            "classifier_used": "none",
            "intent_confidences": {},
            "error": None,
            "timestamp": _utc_now(),
        }
    except Exception as exc:
        total_latency = time.perf_counter() - start_total
        logger.exception("QA evaluation failed for conversation=%s index=%d", qa.conversation_id, qa.qa_index)
        return {
            "qa_uid": qa_uid,
            "conversation_id": qa.conversation_id,
            "qa_index": qa.qa_index,
            "category": qa.category,
            "category_name": category_name(qa.category),
            "question": qa.question,
            "gold_answer": qa.answer,
            "generated_answer": "",
            "evidence": qa.evidence,
            "judge_label": "ERROR",
            "judge_reasoning": "",
            "bleu1": 0.0,
            "f1": 0.0,
            "retrieval_latency_sec": 0.0,
            "generation_latency_sec": 0.0,
            "judge_latency_sec": 0.0,
            "total_latency_sec": total_latency,
            "bundles_count": 0,
            "best_bundle_score": None,
            "best_bundle_path": None,
            "context_chars": 0,
            "context_tokens_est": 0,
            "context_preview": "",
            "query_type_hints": [],
            "classifier_used": "none",
            "intent_confidences": {},
            "error": str(exc),
            "timestamp": _utc_now(),
        }


def _format_full_context(conv: LoCoMoConversation) -> str:
    lines: list[str] = []
    lines.append(f"Conversation: {conv.sample_id}")
    if conv.speaker_a or conv.speaker_b:
        lines.append(f"Speakers: {conv.speaker_a}, {conv.speaker_b}".strip())

    for session in conv.sessions:
        if session.date_time:
            lines.append("")
            lines.append(f"[Session {session.session_num} | {session.date_time}]")
        else:
            lines.append("")
            lines.append(f"[Session {session.session_num}]")
        for turn in session.turns:
            speaker = turn.speaker or "Speaker"
            lines.append(f"{speaker}: {turn.text}")
    return "\n".join(lines).strip()


def _select_conversations(
    conversations: list[Any],
    mode: str,
    conv_id: str,
    max_conversations: int | None,
) -> list[Any]:
    if not conversations:
        return []

    if mode == "sanity":
        return [_resolve_conversation(conversations, conv_id)]

    if max_conversations is not None and max_conversations > 0:
        return conversations[:max_conversations]
    return conversations


def _resolve_conversation(conversations: list[Any], conv_id: str) -> Any:
    if conv_id.isdigit():
        idx = int(conv_id)
        if idx < 0 or idx >= len(conversations):
            raise IndexError(f"conv-id index out of range: {conv_id}")
        return conversations[idx]

    for conv in conversations:
        if getattr(conv, "sample_id", "") == conv_id:
            return conv
    raise ValueError(f"Conversation id not found: {conv_id}")


def _load_results_payload(
    result_path: Path,
    conversation_id: str,
    baseline_name: str,
    mode: str,
    context_meta: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if result_path.exists():
        payload = json.loads(result_path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, dict):
            same_run_identity = (
                payload.get("conversation_id") == conversation_id
                and payload.get("baseline") == baseline_name
                and payload.get("mode") == mode
            )
            if same_run_identity:
                payload.setdefault("results", [])
                payload["context"] = context_meta
                payload["config"] = config
                return payload
            logger.info(
                "Starting fresh result payload for %s (%s/%s); existing payload was %s/%s",
                conversation_id,
                baseline_name,
                mode,
                payload.get("baseline"),
                payload.get("mode"),
            )

    return {
        "conversation_id": conversation_id,
        "baseline": baseline_name,
        "mode": mode,
        "context": context_meta,
        "config": config,
        "results": [],
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
    }


def _qa_uid(qa: QAPair) -> str:
    raw = "|".join(
        [
            qa.conversation_id,
            str(qa.qa_index),
            str(qa.category),
            qa.question,
            qa.answer,
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
