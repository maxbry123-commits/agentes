"""Resolve the orchestrator's args from a (rl_traces, model_repo) pair.

Given just a training-trace dataset and the trained-model repo, the
orchestrator can fill the remaining inputs by querying the Supabase
metadata DB and inspecting the model repo on the HuggingFace Hub:

  --post-rl-eval     ← sandbox_jobs(model_id = <model>).hf_traces_link
  --post-rl-eval-ts  ← models.training_end (post-RL checkpoint mtime)
  --baseline-eval    ← sandbox_jobs(model_id = base_model_id).hf_traces_link
  --baseline-eval-ts ← <base_model>.training_end (the base model's own
                       finish time — the actual checkpoint the RL forked
                       from). Falls back to <base_model>.creation_time,
                       then to <model>.training_start, then null.
  --training-log-dir ← <model_repo>/training_logs/* if present
                      (downloaded to a local snapshot dir on demand)

The Supabase calls reuse ``database.unified_db`` so we inherit its auth
+ retry handling. HF lookups use the standard ``huggingface_hub`` client.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class Resolved:
    """Result of an autofill resolve. Any field may be ``None`` if not found."""

    post_rl_eval: Optional[str] = None
    post_rl_eval_ts: Optional[str] = None  # ISO 8601
    baseline_eval: Optional[str] = None
    baseline_eval_ts: Optional[str] = None  # ISO 8601
    training_log_dir: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Optional[str]]:
        return {
            "post_rl_eval": self.post_rl_eval,
            "post_rl_eval_ts": self.post_rl_eval_ts,
            "baseline_eval": self.baseline_eval,
            "baseline_eval_ts": self.baseline_eval_ts,
            "training_log_dir": self.training_log_dir,
        }


def parse_hf_url(value: str) -> str:
    """Normalize a HuggingFace URL or bare repo id to ``owner/name``.

    Accepts:
      - ``https://huggingface.co/owner/name``
      - ``https://huggingface.co/datasets/owner/name``
      - ``https://huggingface.co/owner/name/tree/main/...``
      - ``owner/name``
    """
    value = (value or "").strip()
    if not value:
        raise ValueError("empty HF reference")
    if not value.startswith("http"):
        # Assume bare "owner/name" — strip leading "datasets/" if present.
        if value.startswith("datasets/"):
            value = value[len("datasets/") :]
        return value
    parsed = urlparse(value)
    parts = [p for p in parsed.path.split("/") if p]
    # Drop a leading "datasets" segment.
    if parts and parts[0] == "datasets":
        parts = parts[1:]
    # Keep just the owner/name pair (drop /tree/main/... etc.).
    if len(parts) < 2:
        raise ValueError(f"could not parse owner/name from HF URL {value!r}")
    return f"{parts[0]}/{parts[1]}"


# ---------------------------------------------------------------------------
# Supabase queries
# ---------------------------------------------------------------------------


def _supabase_client(use_admin: bool = False):
    """Return a Supabase client via the existing unified_db helper."""
    from database.unified_db.utils import get_supabase_client

    return get_supabase_client(use_admin=use_admin)


def _model_by_name(client, name: str) -> Optional[Dict[str, Any]]:
    """Look up a model row by ``name`` (the HF repo id). Returns None if missing."""
    resp = client.table("models").select("*").eq("name", name).limit(1).execute()
    return resp.data[0] if resp.data else None


def _model_by_id(client, model_id: str) -> Optional[Dict[str, Any]]:
    """Look up a model row by primary-key ``id``. Returns None if missing."""
    resp = client.table("models").select("*").eq("id", model_id).limit(1).execute()
    return resp.data[0] if resp.data else None


# Fallback chain for extracting a primary numeric score from the ``metrics``
# JSONB column. ``metrics`` is a list of ``{"name": str, "value": float}``
# entries on this schema; we walk the keys in this order, first hit wins.
DEFAULT_SCORE_KEYS: tuple = (
    "accuracy",
    "mean_reward",
    "Mean",
    "MeanDropEI",
    "reward",
    "score",
    "pass_rate",
)


def _score_of_job(job: Dict[str, Any], key: Optional[str] = None) -> Optional[float]:
    """Extract a numeric score from a sandbox_job's ``metrics`` column.

    Supports both shapes seen in the wild:
      - list of ``{"name", "value"}`` dicts (the current schema)
      - bare ``{key: value}`` dict (older rows / future migrations)

    When ``key`` is None, walks :data:`DEFAULT_SCORE_KEYS` and returns the
    first match. Returns None if no numeric value is found.
    """
    metrics = job.get("metrics")
    if metrics is None:
        return None
    candidates = [key] if key else list(DEFAULT_SCORE_KEYS)
    if isinstance(metrics, list):
        index = {m.get("name"): m.get("value") for m in metrics if isinstance(m, dict)}
        for k in candidates:
            v = index.get(k)
            if isinstance(v, (int, float)):
                return float(v)
    elif isinstance(metrics, dict):
        for k in candidates:
            v = metrics.get(k)
            if isinstance(v, (int, float)):
                return float(v)
    return None


def _recency_key(job: Dict[str, Any]) -> tuple:
    """Sort key implementing "most-recent eval wins".

    The authoritative "when evaluated" field is ``ended_at`` (the job's
    completion time), falling back to ``started_at`` then ``created_at``.
    ``created_at`` is registration/backfill time and can DISAGREE with the
    true eval order (a batch re-register stamps a *newer* ``created_at`` on an
    *older* eval), so it is only a last-resort tiebreak.

    A missing timestamp sorts as OLDEST, never newest: the empty string
    precedes any ISO-8601 value, and callers sort DESCENDING, so a
    null-``ended_at`` row falls to the end instead of masquerading as "latest".
    (ISO-8601 UTC strings compare correctly lexicographically.)
    """
    return (
        job.get("ended_at") or "",
        job.get("started_at") or "",
        job.get("created_at") or "",
    )


def _eval_jobs_for_model(client, model_id: str) -> List[Dict[str, Any]]:
    """Return ALL sandbox_jobs for ``model_id`` that have an hf_traces_link,
    sorted MOST-RECENT-FIRST by :func:`_recency_key`.

    Callers dedup a benchmark's multiple evals by taking the FIRST element
    for that benchmark. The sort is done in Python (not via DB ``.order``)
    because PostgREST's ``desc`` default is NULLS FIRST, which would float a
    null-``ended_at`` row above a genuinely newer completed eval;
    :func:`_recency_key` maps null → oldest to prevent that.
    """
    resp = (
        client.table("sandbox_jobs")
        .select(
            "id,hf_traces_link,benchmark_id,started_at,ended_at,created_at,job_status,metrics"
        )
        .eq("model_id", model_id)
        .execute()
    )
    jobs = [r for r in (resp.data or []) if r.get("hf_traces_link")]
    jobs.sort(key=_recency_key, reverse=True)
    return jobs


def _benchmark_name_to_id(client, name_or_id: str) -> Optional[str]:
    """Accept either a benchmark UUID or a benchmark name; return the UUID."""
    if "-" in name_or_id and len(name_or_id) == 36:
        return name_or_id  # already a UUID
    resp = (
        client.table("benchmarks")
        .select("id")
        .eq("name", name_or_id)
        .limit(1)
        .execute()
    )
    return resp.data[0]["id"] if resp.data else None


def _pick_eval_pair(
    post_jobs: List[Dict[str, Any]],
    baseline_jobs: List[Dict[str, Any]],
    *,
    selection: str = "largest-delta",
    score_key: Optional[str] = None,
    benchmark: Optional[str] = None,
) -> Dict[str, Any]:
    """Pick a (post_job, baseline_job, delta_info) triple from the candidate lists.

    Selection strategies:
      - ``"largest-delta"``: rank pairs by ``post_score - baseline_score``,
        pick the largest (the "most-improved-by-RL" benchmark). Requires
        a benchmark with at least one eval on each side and numeric scores.
      - ``"largest-abs-delta"``: same but ranked by ``|post - baseline|``
        (catches regressions too).
      - ``"latest"``: pick the most recent post-RL job (any benchmark);
        match the baseline to the same benchmark if available, else the
        most recent baseline job overall.
      - ``"benchmark"``: filter both sides to ``benchmark`` (UUID or name)
        and pick the latest from each.

    Returns a dict with keys ``post``, ``baseline``, ``delta``,
    ``selection_strategy``, ``benchmark_id``, plus any explanatory notes
    in ``reason``. ``post`` and/or ``baseline`` may be None if no match.
    """
    by_benchmark: Dict[str, Dict[str, Any]] = {}
    for j in post_jobs:
        bid = j.get("benchmark_id")
        if bid and bid not in by_benchmark:
            by_benchmark[bid] = {"post": j, "baseline": None}
    for j in baseline_jobs:
        bid = j.get("benchmark_id")
        if bid is None:
            continue
        if bid in by_benchmark:
            if by_benchmark[bid]["baseline"] is None:
                by_benchmark[bid]["baseline"] = j
        else:
            by_benchmark[bid] = {"post": None, "baseline": j}

    def _info(pair: Dict[str, Any], reason: str) -> Dict[str, Any]:
        post = pair.get("post")
        base = pair.get("baseline")
        ps = _score_of_job(post, score_key) if post else None
        bs = _score_of_job(base, score_key) if base else None
        delta = (ps - bs) if (ps is not None and bs is not None) else None
        return {
            "post": post,
            "baseline": base,
            "post_score": ps,
            "baseline_score": bs,
            "delta": delta,
            "selection_strategy": selection,
            "benchmark_id": (post or base or {}).get("benchmark_id"),
            "reason": reason,
        }

    if selection == "benchmark":
        if not benchmark:
            return _info(
                {}, "selection=benchmark requires --eval-benchmark; none supplied"
            )
        # Resolve name → id if a client+name was supplied (handled by caller).
        target = benchmark
        pair = by_benchmark.get(target, {"post": None, "baseline": None})
        return _info(pair, f"pinned to benchmark={target}")

    if selection == "latest":
        # Most recent post-RL job (already sorted desc), match baseline by benchmark.
        post = post_jobs[0] if post_jobs else None
        base = None
        if post and post.get("benchmark_id"):
            for j in baseline_jobs:
                if j.get("benchmark_id") == post["benchmark_id"]:
                    base = j
                    break
        if base is None and baseline_jobs:
            base = baseline_jobs[0]
        return _info(
            {"post": post, "baseline": base}, "selection=latest (most recent post-RL)"
        )

    # Default: largest-delta / largest-abs-delta — both need a matched pair.
    pairs_with_delta = []
    for bid, pair in by_benchmark.items():
        ps = _score_of_job(pair["post"], score_key) if pair["post"] else None
        bs = _score_of_job(pair["baseline"], score_key) if pair["baseline"] else None
        if ps is None or bs is None:
            continue
        pairs_with_delta.append((bid, pair, ps - bs))

    if not pairs_with_delta:
        # Fall back to latest if no matched pair has numeric scores.
        return _pick_eval_pair(
            post_jobs,
            baseline_jobs,
            selection="latest",
            score_key=score_key,
            benchmark=benchmark,
        ) | {"selection_strategy": f"{selection}→latest (no matched scored pair)"}

    rank_key = (
        (lambda t: abs(t[2])) if selection == "largest-abs-delta" else (lambda t: t[2])
    )
    bid, pair, delta = max(pairs_with_delta, key=rank_key)
    return _info(
        pair,
        f"selection={selection}: ranked {len(pairs_with_delta)} matched pair(s); "
        f"chose benchmark={bid[:8]} with delta={delta:+.4f}",
    )


def list_evals_for_model(
    rl_traces: str,
    model_repo: str,
    *,
    score_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Enumerate all matched eval pairs without picking one.

    Returns a dict with ``post_only``, ``baseline_only``, and ``matched``
    arrays; each ``matched`` entry has the benchmark id, both job ids,
    both scores (under ``score_key`` or the default chain), and delta.
    Useful for `--list-evals` operator workflow.
    """
    model_name = parse_hf_url(model_repo)
    client = _supabase_client()
    model = _model_by_name(client, model_name)
    if model is None:
        return {"error": f"no model with name={model_name}"}
    post_jobs = _eval_jobs_for_model(client, model["id"])
    base_jobs = (
        _eval_jobs_for_model(client, model["base_model_id"])
        if model.get("base_model_id")
        else []
    )
    by_b: Dict[str, Dict[str, Any]] = {}
    for j in post_jobs:
        bid = j.get("benchmark_id") or ""
        by_b.setdefault(bid, {"post": [], "baseline": []})["post"].append(j)
    for j in base_jobs:
        bid = j.get("benchmark_id") or ""
        by_b.setdefault(bid, {"post": [], "baseline": []})["baseline"].append(j)
    matched, post_only, baseline_only = [], [], []
    for bid, lists in by_b.items():
        post = lists["post"][0] if lists["post"] else None
        base = lists["baseline"][0] if lists["baseline"] else None
        ps = _score_of_job(post, score_key) if post else None
        bs = _score_of_job(base, score_key) if base else None
        row = {
            "benchmark_id": bid,
            "post_job_id": (post or {}).get("id"),
            "baseline_job_id": (base or {}).get("id"),
            "post_score": ps,
            "baseline_score": bs,
            "delta": (ps - bs) if (ps is not None and bs is not None) else None,
            "post_traces": (post or {}).get("hf_traces_link"),
            "baseline_traces": (base or {}).get("hf_traces_link"),
        }
        if post and base:
            matched.append(row)
        elif post:
            post_only.append(row)
        elif base:
            baseline_only.append(row)
    matched.sort(
        key=lambda r: r["delta"] if r["delta"] is not None else -1e9, reverse=True
    )
    return {
        "model_id": model["id"],
        "base_model_id": model.get("base_model_id"),
        "matched": matched,
        "post_only": post_only,
        "baseline_only": baseline_only,
    }


# ---------------------------------------------------------------------------
# HuggingFace training-logs lookup
# ---------------------------------------------------------------------------


def _download_training_logs(model_repo: str, dest_dir: Path) -> Optional[Path]:
    """Try to snapshot ``<model_repo>/training_logs/*`` into ``dest_dir``.

    Returns the local dir path if the model repo has a ``training_logs/``
    directory and we successfully pulled it; ``None`` otherwise. Cheap
    listing first via ``list_repo_files`` so we don't trigger a download
    for repos that don't have logs.
    """
    try:
        from huggingface_hub import list_repo_files, snapshot_download
    except ImportError:
        logger.warning("huggingface_hub not installed; can't fetch training_logs/")
        return None
    try:
        files = list_repo_files(repo_id=model_repo, repo_type="model")
    except Exception as exc:
        logger.warning("list_repo_files(%s) failed: %s", model_repo, exc)
        return None
    if not any(f.startswith("training_logs/") for f in files):
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        local = snapshot_download(
            repo_id=model_repo,
            repo_type="model",
            allow_patterns=["training_logs/**"],
            local_dir=str(dest_dir),
        )
    except Exception as exc:
        logger.warning(
            "snapshot_download(%s, training_logs/**) failed: %s", model_repo, exc
        )
        return None
    log_dir = Path(local) / "training_logs"
    return log_dir if log_dir.exists() else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve(
    rl_traces: str,
    model_repo: str,
    *,
    eval_selection: str = "largest-delta",
    eval_benchmark: Optional[str] = None,
    eval_score_key: Optional[str] = None,
    training_log_cache: Optional[Path] = None,
    fetch_training_logs: bool = True,
) -> Resolved:
    """Autofill the post-RL/baseline eval + ts + training_log_dir from supabase + HF.

    Args:
        rl_traces: Training-trace dataset (HF id or URL). Used only to
            populate ``notes`` cross-reference; the resolver doesn't need
            to query it.
        model_repo: Trained-model HF id or URL.
        eval_selection: How to pick which eval-job pair to surface when
            the model has multiple. One of:
              - ``"largest-delta"`` (default) — match post/baseline by
                benchmark_id, score with ``eval_score_key``, pick the
                pair with the largest positive delta (i.e. the
                benchmark RL helped the most on; usually the most
                interesting to inspect).
              - ``"largest-abs-delta"`` — same but rank by ``|delta|``;
                catches regressions too.
              - ``"latest"`` — original behavior: most recent post-RL
                sandbox_job, baseline matched by benchmark.
              - ``"benchmark"`` — pin to ``eval_benchmark`` (UUID or
                ``benchmarks.name``).
        eval_benchmark: Required when ``eval_selection="benchmark"``.
        eval_score_key: Which metrics entry to read for the score-delta
            ranking. Defaults to the first hit among
            :data:`DEFAULT_SCORE_KEYS` (``"accuracy"`` first).
        training_log_cache: Where to drop the snapshotted training_logs/.
        fetch_training_logs: If False, skip the HF snapshot step.
    """
    out = Resolved()
    try:
        model_name = parse_hf_url(model_repo)
    except Exception as exc:
        out.notes.append(f"could not parse model_repo {model_repo!r}: {exc}")
        return out

    try:
        rl_name = parse_hf_url(rl_traces)
        out.notes.append(f"rl_traces normalized to {rl_name}")
    except Exception:
        pass  # rl_traces is informational only here

    # ---- Supabase lookup ----
    try:
        client = _supabase_client()
    except Exception as exc:
        out.notes.append(f"supabase client unavailable: {exc}")
        client = None

    model_row: Optional[Dict[str, Any]] = None
    if client is not None:
        try:
            model_row = _model_by_name(client, model_name)
        except Exception as exc:
            out.notes.append(f"models lookup failed: {exc}")

    if model_row is None:
        out.notes.append(f"no row in models table with name={model_name!r}")
    else:
        out.post_rl_eval_ts = model_row.get("training_end") or out.post_rl_eval_ts
        if not out.post_rl_eval_ts:
            out.notes.append("models.training_end is null; post_rl_eval_ts not set")

        # Collect ALL valid eval-jobs on both sides, then rank by the
        # caller's selection strategy. Default is largest-delta — usually
        # the most interesting benchmark to inspect, since the largest
        # gain is where RL learned the most.
        if client is not None:
            try:
                post_jobs = _eval_jobs_for_model(client, model_row["id"])
            except Exception as exc:
                post_jobs = []
                out.notes.append(f"sandbox_jobs lookup (post-RL) failed: {exc}")

            base_id = model_row.get("base_model_id")
            base_jobs: List[Dict[str, Any]] = []
            base_row: Optional[Dict[str, Any]] = None
            if base_id:
                try:
                    base_jobs = _eval_jobs_for_model(client, base_id)
                except Exception as exc:
                    out.notes.append(f"sandbox_jobs lookup (baseline) failed: {exc}")
                try:
                    base_row = _model_by_id(client, base_id)
                except Exception as exc:
                    out.notes.append(f"base-model lookup failed: {exc}")
            else:
                out.notes.append(
                    "models.base_model_id is null; baseline_eval can't be auto-resolved"
                )

            # baseline_eval_ts: prefer the BASE model's training_end
            # (when the snapshot we forked from finished training), then
            # its creation_time, then fall back to the current model's
            # training_start.
            ts_source = None
            if base_row:
                if base_row.get("training_end"):
                    out.baseline_eval_ts = base_row["training_end"]
                    ts_source = f"base_model[{base_id}].training_end"
                elif base_row.get("creation_time"):
                    out.baseline_eval_ts = base_row["creation_time"]
                    ts_source = f"base_model[{base_id}].creation_time"
            if not out.baseline_eval_ts:
                fallback = model_row.get("training_start")
                if fallback:
                    out.baseline_eval_ts = fallback
                    ts_source = "model.training_start (fallback; no base-model row or all base ts are null)"
            if ts_source:
                out.notes.append(
                    f"baseline_eval_ts ← {ts_source} = {out.baseline_eval_ts}"
                )
            else:
                out.notes.append(
                    "baseline_eval_ts unresolved (no base model and no model.training_start)"
                )

            # Resolve a benchmark name → id if the caller passed a name.
            bench_target = eval_benchmark
            if bench_target and "-" not in bench_target:
                try:
                    resolved_bid = _benchmark_name_to_id(client, bench_target)
                    if resolved_bid is None:
                        out.notes.append(
                            f"benchmark name={bench_target!r} not found in benchmarks table"
                        )
                    bench_target = resolved_bid or bench_target
                except Exception as exc:
                    out.notes.append(f"benchmark name lookup failed: {exc}")

            pick = _pick_eval_pair(
                post_jobs,
                base_jobs,
                selection=eval_selection,
                score_key=eval_score_key,
                benchmark=bench_target,
            )
            out.notes.append(f"eval pair selection: {pick['reason']}")
            post = pick.get("post")
            base = pick.get("baseline")
            if post and post.get("hf_traces_link"):
                out.post_rl_eval = post["hf_traces_link"]
                out.notes.append(
                    f"post_rl_eval ← sandbox_jobs[{post['id']}] "
                    f"(benchmark={(post.get('benchmark_id') or '')[:8]}, "
                    f"status={post.get('job_status')}, "
                    f"score={pick.get('post_score')})"
                )
            else:
                out.notes.append("no post-RL eval traces selected")
            if base and base.get("hf_traces_link"):
                out.baseline_eval = base["hf_traces_link"]
                out.notes.append(
                    f"baseline_eval ← sandbox_jobs[{base['id']}] "
                    f"(benchmark={(base.get('benchmark_id') or '')[:8]}, "
                    f"score={pick.get('baseline_score')})"
                )
            else:
                out.notes.append("no baseline eval traces selected")
            if pick.get("delta") is not None:
                out.notes.append(f"chosen-pair score delta: {pick['delta']:+.4f}")

    # ---- HF training_logs/ snapshot ----
    if fetch_training_logs:
        if training_log_cache is None:
            safe = model_name.replace("/", "__")
            training_log_cache = Path.home() / ".ot-agent" / "training_logs" / safe
        log_dir = _download_training_logs(model_name, training_log_cache)
        if log_dir is not None:
            out.training_log_dir = str(log_dir)
            out.notes.append(
                f"training_log_dir ← snapshotted {model_name}/training_logs/ to {log_dir}"
            )
        else:
            out.notes.append(
                f"no training_logs/ in HF repo {model_name} "
                f"(expected at https://huggingface.co/{model_name}/tree/main/training_logs)"
            )
    else:
        out.notes.append("fetch_training_logs=False; training_log_dir not populated")

    return out
