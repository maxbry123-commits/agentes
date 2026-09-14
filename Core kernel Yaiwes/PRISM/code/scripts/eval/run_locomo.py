from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Reproducibility guard: PYTHONHASHSEED must be fixed so any residual set-order
# dependence (e.g. future refactors that add new set iterations) cannot leak
# hash-seed randomness into observable results. The primary fix is the
# `sorted(idx.episode_ids)` in mmem/retrieval/path_scorer.py; this assert is
# belt-and-suspenders for future-proofing. See PRISM Day 1 health check.
if os.environ.get("PYTHONHASHSEED") != "0":
    sys.exit(
        "PYTHONHASHSEED must be 0 for reproducible LoCoMo runs.\n"
        "Set it before invoking Python, e.g.:\n"
        "  PowerShell:  $env:PYTHONHASHSEED=0; python -m scripts.eval.run_locomo ...\n"
        "  bash/zsh  :  PYTHONHASHSEED=0 python -m scripts.eval.run_locomo ...\n"
        f"Current value: {os.environ.get('PYTHONHASHSEED')!r}"
    )

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mmem.config import MMemConfig
from mmem.core.edges import EdgeType
from mmem.ingestion.pipeline import IngestionPipeline
from mmem.retrieval.anchor_discovery import discover_anchors
from mmem.retrieval.output_assembler import RetrievalResult, assemble_output
from mmem.retrieval.path_scorer import score_episodes
from mmem.retrieval.query_preprocessor import preprocess_query
from mmem.retrieval.search import bundle_search
from mmem.retrieval.subgraph_extractor import extract_subgraph
from mmem.utils.embedding import EmbeddingModel
from mmem.utils.llm import LLMClient
from scripts.eval.locomo_chunker import chunk_conversation
from scripts.eval.locomo_loader import QAPair, category_name, group_qa_by_conversation, load_locomo
from scripts.eval.metrics import compute_bleu1, compute_f1, normalize_judge_label, tokenize
from scripts.eval.prompts import LLM_JUDGE_PROMPT, QA_GENERATION_PROMPT
from scripts.eval.report import format_report, summarize_results

if TYPE_CHECKING:
    from mmem.retrieval.intent_classifier import IntentClassifier


logger = logging.getLogger("locomo_eval")

DATASET_URLS = [
    "https://raw.githubusercontent.com/snap-research/locomo/main/data/locomo10.json",
]

ABLATION_CONFIGS: dict[str, dict[str, Any]] = {
    "A1": {
        "name": "Full System",
        "retrieval": {
            "enable_reranking": True,
            "rerank_top_n": 5,
        },
        "runtime": {},
    },
    "A2": {
        # DEPRECATED — composite ablation (A9 − N1 − N3): enable_reranking defaults
        # to False in MMemConfig, so this config is NOT a clean -N1 ablation.
        # Use A2_clean for PRISM paper Table 3.
        "name": "DEPRECATED — composite (A9 − N1 − N3). Use A2_clean for paper Table 3.",
        "retrieval": {"enable_relation_paths": False},
        "runtime": {},
    },
    # ── PRISM paper E2: subtractive ablation of Novelty #1 (relation paths) ──
    # Explicit rerank flags mirror A9 exactly; only enable_relation_paths is flipped.
    # Run with --checkpoint-ablation A9.
    "A2_clean": {
        "name": "PRISM Table 3: A9 − N1 (no relation paths)",
        "retrieval": {
            "enable_reranking": True,        # explicit — do not remove
            "rerank_top_n": 5,               # explicit — do not remove
            "enable_relation_paths": False,  # this is −N1
        },
        "runtime": {},
    },
    "A4": {
        "name": "No Causal Edges",
        "retrieval": {},
        "runtime": {"skip_causal_edges": True},
    },
    "A5": {
        "name": "No Temporal Edges",
        "retrieval": {},
        "runtime": {"skip_temporal_edges": True},
    },
    "A6": {
        "name": "No Direct Episode Penalty",
        "retrieval": {"enable_direct_episode_penalty": False},
        "runtime": {},
    },
    "A7": {
        "name": "Fixed Edge Cost",
        "retrieval": {"enable_query_sensitive_cost": False},
        "runtime": {"edge_as_fixed_cost": True},
    },
    "A8": {
        "name": "Query Decomposition",
        "retrieval": {"enable_query_decomposition": True},
        "runtime": {},
    },
    "A9": {
        "name": "LLM Re-ranking (Round3 frozen, V1 prompt, top_n=5 — do NOT re-run with Round4+ code)",
        "retrieval": {"enable_reranking": True, "rerank_top_n": 5},
        "runtime": {},
    },
    "A9_answer_gpt55": {
        "name": "A9 with GPT-5.5 answer model and GPT-4o-mini judge",
        "retrieval": {"enable_reranking": True, "rerank_top_n": 5},
        "llm": {"judge_model": "gpt-4o-mini", "max_retries": 6},
        "runtime": {"answer_model": "gpt-5.5"},
    },
    "A10_no_cost_adj": {
        # Clean ablation of Novelty #2 (query-sensitive edge cost).
        # Mirrors the R3-A9 default (rerank V1, top_n=5, KS off) but flips only
        # enable_query_sensitive_cost=False. edge_as_fixed_cost stays False so
        # semantic edge distances remain, unlike A7 which compounds two ablations.
        "name": "Ablation of Novelty #2: disable query-sensitive edge cost (rerank V1, top_n=5, KS off)",
        "retrieval": {
            "enable_reranking": True,
            "rerank_top_n": 5,
            "enable_query_sensitive_cost": False,
        },
        "runtime": {},
    },
    # ── PRISM Day 1 health check ──
    # Config is a bit-identical deep copy of A9 (enable_reranking=True,
    # rerank_top_n=5). Separate name gives it its own results dir so the
    # archived scripts/eval/results/A9/ data stays untouched, and the
    # run is launched with `--checkpoint-ablation A9` so retrieval reads
    # the frozen A9 ingest graph + vector store. Purpose: verify the
    # current retrieval code reproduces A9's retrieval-deterministic
    # fields and judge labels on at least conv-30 and conv-49.
    "A9_healthcheck": {
        "name": "PRISM Day 1 health check: A9 config deep-copied; run with --checkpoint-ablation A9",
        "retrieval": {"enable_reranking": True, "rerank_top_n": 5},
        "runtime": {},
    },
    # ── A9 config without LLM rerank, used for bit-exact reproducibility
    # checks. Run two consecutive times with --checkpoint-ablation A9 and
    # diff: all four Layer 1a fields (bundles_count, context_tokens_est,
    # best_bundle_path, best_bundle_score) MUST be 100% bit-identical.
    # Judge label may still differ within ~5% due to QA-model non-determinism.
    "A9_healthcheck_norerank": {
        "name": "PRISM Day 1 health check: A9 − LLM rerank for bit-exact determinism check",
        "retrieval": {"enable_reranking": False},
        "runtime": {},
    },
    # ── PRISM paper E2: subtractive ablation of Novelty #3 (LLM rerank) ──
    # A9 with enable_reranking=False. Re-uses the A9 full-mode ingest
    # checkpoint via --checkpoint-ablation A9, so no re-ingestion.
    # Note: the existing "A1" config is equivalent to A9 (Full System); this
    # "A1_no_rerank" is the clean "− N3" cell for PRISM's Table 3.
    "A1_no_rerank": {
        "name": "PRISM Table 3: A9 − N3 (LLM re-rank disabled)",
        "retrieval": {
            "enable_reranking": False,
        },
        "runtime": {},
    },
    # ── PRISM paper E3: rerank top_n sweep (for Figure 5) ──
    # All three re-use the A9 ingest checkpoint via --checkpoint-ablation A9.
    # top_n=5 is already covered by the existing A9 full-mode run.
    "A9_top3": {
        "name": "PRISM Figure 5: A9 with rerank_top_n=3",
        "retrieval": {"enable_reranking": True, "rerank_top_n": 3},
        "llm": {"max_retries": 6},
        "runtime": {},
    },
    "A9_top7": {
        "name": "PRISM Figure 5: A9 with rerank_top_n=7",
        "retrieval": {"enable_reranking": True, "rerank_top_n": 7},
        "runtime": {},
    },
    "A9_top10": {
        "name": "PRISM Figure 5: A9 with rerank_top_n=10",
        "retrieval": {"enable_reranking": True, "rerank_top_n": 10},
        "runtime": {},
    },
    "R5-1": {
        # Round 5 Stage 2a: A9 + hybrid intent classifier. Quota (Stage 2b) and
        # tiered discount (Stage 3) are explicitly OFF so R5-1 vs A9 is a
        # clean classifier-only ablation. The only two retrieval-config flips
        # vs A9 are (a) intent_classifier_mode=hybrid and (b) flags held at
        # their A9-equivalent defaults.
        "name": "R5-1: A9 + hybrid intent classifier (no quota, no tiered discount)",
        "retrieval": {
            "enable_reranking": True,
            "rerank_top_n": 5,
            "intent_classifier_mode": "hybrid",
            "enable_intent_quota": False,
            "enable_tiered_discount": False,
        },
        "runtime": {},
    },
    # -- Round 5 Stage 2a variance-envelope runs --
    # Config bit-identical to A9. Separate names give them independent
    # checkpoint and results directories so each run forces a fresh ingestion
    # AND a fresh retrieval eval. Together with the original A9 (4/18 ingest)
    # these form a 4-sample envelope of run-to-run ingestion + retrieval noise.
    "A9-run2": {
        "name": "A9 variance-envelope run 2 (config == A9)",
        "retrieval": {"enable_reranking": True, "rerank_top_n": 5},
        "runtime": {},
    },
    "A9-run3": {
        "name": "A9 variance-envelope run 3 (config == A9)",
        "retrieval": {"enable_reranking": True, "rerank_top_n": 5},
        "runtime": {},
    },
    "A9-run4": {
        "name": "A9 variance-envelope run 4 (config == A9)",
        "retrieval": {"enable_reranking": True, "rerank_top_n": 5},
        "runtime": {},
    },
}

_EMPTY = RetrievalResult(bundles=[], context_text="", debug_info={})


def main() -> None:
    args = _parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    data_path = Path(args.data_path)
    _ensure_dataset(data_path)

    config, runtime_flags = _build_config(args.ablation)
    llm_client = LLMClient(config=config.llm)
    embedder = EmbeddingModel(config=config.embedding)

    # Round 5 Stage 2a: build the IntentClassifier exactly once (per process)
    # and only when the ablation asks for hybrid mode — otherwise A1-A10
    # would pay the prototype-embedding startup cost for nothing.
    intent_classifier = None
    if getattr(config.retrieval, "intent_classifier_mode", "keyword") == "hybrid":
        from mmem.retrieval.intent_classifier import IntentClassifier

        logger.info("Building IntentClassifier (hybrid mode) once for this run")
        intent_classifier = IntentClassifier(
            embedder=embedder,
            llm_client=llm_client,
            high_conf_threshold=config.retrieval.intent_high_conf_threshold,
            margin_threshold=config.retrieval.intent_margin_threshold,
            low_conf_threshold=config.retrieval.intent_low_conf_threshold,
            secondary_margin=config.retrieval.intent_secondary_margin,
        )

    conversations, qa_pairs = load_locomo(data_path)
    qa_by_conv = group_qa_by_conversation(qa_pairs)
    selected = _select_conversations(
        conversations=conversations,
        mode=args.mode,
        conv_id=args.conv_id,
        max_conversations=args.max_conversations,
    )

    results_root = Path(args.results_dir) / args.ablation
    # PRISM E2/E3 retrieval-only re-runs: read ingest checkpoint from a
    # different ablation dir (e.g. --checkpoint-ablation A9 while --ablation
    # A1_no_rerank). Defaults to args.ablation so pre-PRISM flows are
    # bit-identical.
    checkpoint_ablation = args.checkpoint_ablation or args.ablation
    checkpoints_root = Path(args.checkpoints_dir) / checkpoint_ablation
    results_root.mkdir(parents=True, exist_ok=True)
    checkpoints_root.mkdir(parents=True, exist_ok=True)
    if checkpoint_ablation != args.ablation:
        logger.info(
            "Reusing ingest checkpoints from ablation %r for retrieval-only run of %r",
            checkpoint_ablation,
            args.ablation,
        )

    all_results: list[dict[str, Any]] = []
    ingestion_stats: list[dict[str, Any]] = []
    qa_limit = args.qa_limit
    if qa_limit is None and args.mode == "sanity":
        qa_limit = 200

    for conv in selected:
        logger.info("Conversation %s: preparing chunks", conv.sample_id)
        chunks = chunk_conversation(conv, max_chunk_chars=args.max_chunk_chars)
        checkpoint_dir = checkpoints_root / conv.sample_id
        pipeline, ingest_meta = _load_or_build_pipeline(
            checkpoint_dir=checkpoint_dir,
            chunks=chunks,
            config=config,
            embedder=embedder,
            llm_client=llm_client,
            runtime_flags=runtime_flags,
            force_reingest=args.force_reingest,
        )
        ingestion_stats.append(ingest_meta)

        conv_qas = qa_by_conv.get(conv.sample_id, [])
        if not conv_qas:
            logger.warning("Conversation %s has no QA pairs, skipping", conv.sample_id)
            continue

        result_path = results_root / f"{conv.sample_id}.json"
        payload = _load_results_payload(
            result_path=result_path,
            conversation_id=conv.sample_id,
            ablation=args.ablation,
            mode=args.mode,
            ingestion_meta=ingest_meta,
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
                pipeline=pipeline,
                config=config,
                embedder=embedder,
                llm_client=llm_client,
                top_k=args.top_k,
                display_mode=args.display_mode,
                edge_as_fixed_cost=bool(runtime_flags.get("edge_as_fixed_cost")),
                intent_classifier=intent_classifier,
                answer_model=runtime_flags.get("answer_model"),
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

        payload["ingestion"] = ingest_meta
        payload["updated_at"] = _utc_now()
        _write_json(result_path, payload)
        all_results.extend(payload.get("results", []))

    summary = summarize_results(all_results, ingestion_stats=ingestion_stats)
    report_text = format_report(summary, ablation=args.ablation)
    print(report_text)

    summary_payload = {
        "ablation": args.ablation,
        "mode": args.mode,
        "generated_at": _utc_now(),
        "summary": summary,
        "conversations": [c.sample_id for c in selected],
    }
    summary_json_path = results_root / f"summary_{args.mode}.json"
    summary_txt_path = results_root / f"report_{args.mode}.txt"
    _write_json(summary_json_path, summary_payload)
    summary_txt_path.write_text(report_text, encoding="utf-8")

    logger.info("Saved summary JSON: %s", summary_json_path)
    logger.info("Saved report text:  %s", summary_txt_path)

    if args.ablation == "R5-1" and args.mode == "full":
        from scripts.eval.gated_diagnostics import write_diagnostics_report

        diagnostics_path = PROJECT_ROOT / "scripts" / "eval" / "reports" / "r5-1_gated_full_diagnostics.md"
        write_diagnostics_report(
            r5_results_dir=results_root,
            a9_summary_path=Path(args.results_dir) / "A9" / "summary_full.json",
            output_path=diagnostics_path,
        )
        logger.info("Saved R5-1 diagnostics report: %s", diagnostics_path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LoCoMo evaluation on M-Mem.")
    parser.add_argument("--mode", choices=["sanity", "full"], default="sanity")
    parser.add_argument("--conv-id", type=str, default="0", help="Conversation index or sample_id for sanity mode.")
    parser.add_argument("--ablation", choices=sorted(ABLATION_CONFIGS.keys()), default="A1")
    parser.add_argument(
        "--checkpoint-ablation",
        type=str,
        default=None,
        help=(
            "If set, read ingest checkpoints from this ablation directory instead "
            "of --ablation. Enables retrieval-only re-runs "
            "(e.g. --ablation A1_no_rerank --checkpoint-ablation A9)."
        ),
    )
    parser.add_argument("--data-path", type=str, default=str(PROJECT_ROOT / "scripts" / "eval" / "data" / "locomo10.json"))
    parser.add_argument("--results-dir", type=str, default=str(PROJECT_ROOT / "scripts" / "eval" / "results"))
    parser.add_argument("--checkpoints-dir", type=str, default=str(PROJECT_ROOT / "scripts" / "eval" / "checkpoints"))
    parser.add_argument("--max-chunk-chars", type=int, default=1024)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--display-mode", choices=["summary", "detail"], default="detail")
    parser.add_argument("--qa-limit", type=int, default=None, help="Optional max number of QA per conversation.")
    parser.add_argument("--max-conversations", type=int, default=None, help="Optional limit for full mode.")
    parser.add_argument("--include-adversarial", action="store_true", help="Include category=5 QA.")
    parser.add_argument("--force-reingest", action="store_true", help="Ignore existing checkpoints and rebuild graph/index.")
    parser.add_argument("--fail-on-error", action="store_true", help="Abort without writing a QA record when evaluation fails.")
    return parser.parse_args()


def _ensure_dataset(data_path: Path) -> None:
    if data_path.exists():
        return

    data_path.parent.mkdir(parents=True, exist_ok=True)
    last_exc: Exception | None = None
    for url in DATASET_URLS:
        try:
            logger.info("Downloading LoCoMo dataset from %s", url)
            with urllib.request.urlopen(url, timeout=120) as resp:
                content = resp.read()
            data_path.write_bytes(content)
            logger.info("Saved dataset to %s", data_path)
            return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_exc = exc
            logger.warning("Dataset download failed from %s: %s", url, exc)

    raise FileNotFoundError(
        f"Unable to find or download dataset at {data_path}. Last error: {last_exc}"
    )


def _build_config(ablation: str) -> tuple[MMemConfig, dict[str, Any]]:
    if ablation not in ABLATION_CONFIGS:
        raise ValueError(f"Unknown ablation: {ablation}")

    cfg = MMemConfig()

    spec = ABLATION_CONFIGS[ablation]
    for key, value in spec.get("retrieval", {}).items():
        setattr(cfg.retrieval, key, value)
    for key, value in spec.get("llm", {}).items():
        setattr(cfg.llm, key, value)

    runtime_flags = dict(spec.get("runtime", {}))
    if runtime_flags.get("skip_causal_edges"):
        cfg.write.enable_causal_consolidation = False
    if runtime_flags.get("edge_as_fixed_cost"):
        # Approximate "edge without semantic vectors" by using one fixed default cost.
        cfg.retrieval.edge_miss_cost = cfg.retrieval.belongs_to_cost

    return cfg, runtime_flags


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


def _load_or_build_pipeline(
    checkpoint_dir: Path,
    chunks: list[Any],
    config: MMemConfig,
    embedder: EmbeddingModel,
    llm_client: LLMClient,
    runtime_flags: dict[str, Any],
    force_reingest: bool,
) -> tuple[IngestionPipeline, dict[str, Any]]:
    checkpoint_exists = (
        (checkpoint_dir / "graph.json").exists()
        and (checkpoint_dir / "faiss").exists()
        and (checkpoint_dir / "pipeline_state.json").exists()
    )

    ingest_total = 0.0
    ingest_sec_per_chunk = 0.0
    loaded_from_checkpoint = checkpoint_exists and not force_reingest

    if loaded_from_checkpoint:
        logger.info("Loaded checkpoint from %s", checkpoint_dir)
        pipeline = IngestionPipeline.load_checkpoint(
            checkpoint_dir,
            config=config,
            embedder=embedder,
            llm_client=llm_client,
        )
    else:
        logger.info("Building checkpoint at %s", checkpoint_dir)
        pipeline = IngestionPipeline(
            config=config,
            embedder=embedder,
            llm_client=llm_client,
        )
        t0 = time.perf_counter()
        for chunk in chunks:
            pipeline.ingest(chunk.text)
        ingest_total = time.perf_counter() - t0
        ingest_sec_per_chunk = ingest_total / max(len(chunks), 1)
        pipeline.save_checkpoint(checkpoint_dir)

    removed_temporal = 0
    removed_causal = 0
    if runtime_flags.get("skip_temporal_edges"):
        removed_temporal = _remove_edges_by_type(pipeline, EdgeType.TEMPORAL)
    if runtime_flags.get("skip_causal_edges"):
        removed_causal = _remove_edges_by_type(pipeline, EdgeType.CAUSAL)
    if removed_temporal or removed_causal:
        pipeline.save_checkpoint(checkpoint_dir)

    stats = pipeline.stats()
    return pipeline, {
        "checkpoint_dir": str(checkpoint_dir),
        "loaded_from_checkpoint": loaded_from_checkpoint,
        "chunk_count": len(chunks),
        "ingest_total_sec": ingest_total,
        "ingest_sec_per_chunk": ingest_sec_per_chunk,
        "episode_count": int(stats.get("episode_count", 0)),
        "removed_temporal_edges": removed_temporal,
        "removed_causal_edges": removed_causal,
    }


def _remove_edges_by_type(pipeline: IngestionPipeline, edge_type: EdgeType) -> int:
    graph = pipeline.graph
    edge_ids = [edge.id for edge in graph.get_edges_by_type(edge_type)]
    for edge_id in edge_ids:
        graph.remove_edge(edge_id)
    return len(edge_ids)


def _evaluate_one_qa(
    qa: QAPair,
    pipeline: IngestionPipeline,
    config: MMemConfig,
    embedder: EmbeddingModel,
    llm_client: LLMClient,
    top_k: int,
    display_mode: str,
    edge_as_fixed_cost: bool,
    intent_classifier: "IntentClassifier | None" = None,
    answer_model: str | None = None,
) -> dict[str, Any]:
    qa_uid = _qa_uid(qa)
    start_total = time.perf_counter()

    # ── R5-1 (gated routing) telemetry ───────────────────────────────────────
    # Capture the PreprocessedQuery that will be used internally by bundle_search.
    # Because IntentClassifier has an LRU cache keyed on the raw query string,
    # the duplicate classify() call inside bundle_search hits the cache and
    # incurs no extra LLM request.
    try:
        _tele_pre = preprocess_query(
            qa.question, config.retrieval, intent_classifier=intent_classifier
        )
        tele_hints = sorted(_tele_pre.query_type_hints)
        tele_classifier_used = _tele_pre.classifier_used
        tele_confidences = dict(_tele_pre.intent_confidences)
    except Exception:  # pragma: no cover - telemetry must never break eval
        logger.exception("Intent telemetry capture failed for %s#%d", qa.conversation_id, qa.qa_index)
        tele_hints = []
        tele_classifier_used = "error"
        tele_confidences = {}

    try:
        t0 = time.perf_counter()
        retrieval = _bundle_search_with_overrides(
            question=qa.question,
            pipeline=pipeline,
            config=config,
            embedder=embedder,
            llm_client=llm_client,
            top_k=top_k,
            display_mode=display_mode,
            edge_as_fixed_cost=edge_as_fixed_cost,
            intent_classifier=intent_classifier,
        )
        retrieval_latency = time.perf_counter() - t0

        t1 = time.perf_counter()
        generated = llm_client.chat(
            prompt=QA_GENERATION_PROMPT.format(
                context=retrieval.context_text,
                question=qa.question,
            ),
            model=answer_model or config.llm.qa_model,
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
            "bundles_count": len(retrieval.bundles),
            "best_bundle_score": retrieval.bundles[0].score if retrieval.bundles else None,
            "best_bundle_path": retrieval.bundles[0].best_path if retrieval.bundles else None,
            "context_chars": len(retrieval.context_text),
            "context_tokens_est": len(tokenize(retrieval.context_text)),
            "context_preview": retrieval.context_text[:500],
            "query_type_hints": tele_hints,
            "classifier_used": tele_classifier_used,
            "intent_confidences": tele_confidences,
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
            "query_type_hints": tele_hints,
            "classifier_used": tele_classifier_used,
            "intent_confidences": tele_confidences,
            "error": str(exc),
            "timestamp": _utc_now(),
        }


def _bundle_search_with_overrides(
    question: str,
    pipeline: IngestionPipeline,
    config: MMemConfig,
    embedder: EmbeddingModel,
    llm_client: LLMClient,
    top_k: int,
    display_mode: str,
    edge_as_fixed_cost: bool,
    intent_classifier: "IntentClassifier | None" = None,
) -> RetrievalResult:
    if not edge_as_fixed_cost:
        return bundle_search(
            question,
            pipeline.graph,
            pipeline.vector_store,
            embedder,
            config=config,
            top_k=top_k,
            display_mode=display_mode,
            chunk_store=pipeline.chunk_store,
            llm_client=llm_client,
            intent_classifier=intent_classifier,
        )

    cfg = config.retrieval
    preprocessed = preprocess_query(question, cfg, intent_classifier=intent_classifier)
    anchors = discover_anchors(preprocessed, pipeline.vector_store, embedder, cfg)
    if not anchors.node_distances:
        return _EMPTY

    # Phase 1b (optional): also support Query Decomposition in the
    # edge_as_fixed_cost branch so future composite ablations (e.g. A7+A8)
    # work without further plumbing.
    if cfg.enable_query_decomposition:
        from mmem.retrieval.query_decomposer import decompose_query

        sub_queries = decompose_query(question, llm_client, config.llm)
        for sub_q in sub_queries:
            sub_preprocessed = preprocess_query(
                sub_q, cfg, intent_classifier=intent_classifier
            )
            sub_anchors = discover_anchors(sub_preprocessed, pipeline.vector_store, embedder, cfg)
            for nid, dist in sub_anchors.node_distances.items():
                prev = anchors.node_distances.get(nid)
                if prev is None or dist < prev:
                    anchors.node_distances[nid] = dist
            for eid, dist in sub_anchors.edge_distances.items():
                prev = anchors.edge_distances.get(eid)
                if prev is None or dist < prev:
                    anchors.edge_distances[eid] = dist

    # Edge semantic distances are disabled in A7 so relation edges fallback to fixed cost.
    anchors.edge_distances = {}
    subgraph = extract_subgraph(anchors, pipeline.graph, cfg)
    if not subgraph.index.episode_ids:
        return _EMPTY

    bundles = score_episodes(subgraph, anchors, preprocessed, cfg)
    if not bundles:
        return _EMPTY
    return assemble_output(
        bundles=bundles,
        graph=pipeline.graph,
        config=cfg,
        top_k=top_k,
        display_mode=display_mode,
        chunk_store=pipeline.chunk_store,
        llm_client=llm_client,
        llm_config=config.llm,
        query=question,
    )


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


def _load_results_payload(
    result_path: Path,
    conversation_id: str,
    ablation: str,
    mode: str,
    ingestion_meta: dict[str, Any],
) -> dict[str, Any]:
    if result_path.exists():
        payload = json.loads(result_path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, dict):
            same_run_identity = (
                payload.get("conversation_id") == conversation_id
                and payload.get("ablation") == ablation
                and payload.get("mode") == mode
            )
            if same_run_identity:
                payload.setdefault("results", [])
                payload["results"] = [
                    item
                    for item in payload["results"]
                    if not _is_error_record(item)
                ]
                payload["ingestion"] = ingestion_meta
                return payload
            logger.info(
                "Starting fresh result payload for %s (%s/%s); existing payload was %s/%s",
                conversation_id,
                ablation,
                mode,
                payload.get("ablation"),
                payload.get("mode"),
            )

    return {
        "conversation_id": conversation_id,
        "ablation": ablation,
        "mode": mode,
        "ingestion": ingestion_meta,
        "results": [],
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
    }


def _is_error_record(item: Any) -> bool:
    if not isinstance(item, dict):
        return True
    return str(item.get("judge_label", "")).strip().upper() == "ERROR" or bool(item.get("error"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
