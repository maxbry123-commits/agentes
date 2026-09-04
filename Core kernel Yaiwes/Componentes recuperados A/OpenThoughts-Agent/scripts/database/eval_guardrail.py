#!/usr/bin/env python3
"""Authoritative eval-guardrail counts + a PASS/FAIL gate wrapper.

This is the ONE place the OT-Agent side reproduces the leaderboard's per-eval
guardrail computation. It is a faithful port of the canonical TypeScript:

    OT-Agent-Leaderboard  server/storage.ts:416-449
    (github.com/richardzhuang0412/OT-Agent-Leaderboard)

which is what produces the leaderboard's **"Errors: k"** badge (isHighErrors) and
the **incomplete** flag. Do NOT hand-roll this logic anywhere else (a skill's inline
gate, an ad-hoc script) — import from here so it can never drift from the leaderboard.
If the canonical storage.ts changes (BENIGN set, threshold, fields), re-sync it here.

Two layers (see the module's two public functions):
  * guardrail_counts()  -- AUTHORITATIVE counts; mirrors storage.ts exactly.
  * passes_gate()       -- OUR use-case: turn the counts into a PASS/FAIL keep-vs-
                           de-register decision against a threshold (the leaderboard
                           shows a raw count; we need a boolean gate).

The two functions are PURE (pass a stats dict + planned n_trials). SUPABASE_URL /
SUPABASE_SERVICE_ROLE_KEY are only needed for the CLI (fetches a job by id).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any, Optional, Tuple

# --- Canonical BENIGN set: EXACT mirror of storage.ts:422-426. Keep in sync. ---
# (NB: the leaderboard benign-izes `SummarizationTimeout`, NOT `SummarizationError` —
#  an earlier hand-rolled copy had that wrong.)
BENIGN_ERRORS = frozenset(
    {
        "AgentTimeoutError",
        "ContextLengthExceededError",
        "SummarizationTimeout",
        "SummarizationTimeoutError",
        "BadRequestError",
        "NonZeroAgentExitCodeError",
        "VerifierRuntimeError",
    }
)

# The leaderboard's isHighErrors boundary (storage.ts:449 `invalidErrorCount > 10`).
CANONICAL_HIGH_ERRORS_THRESHOLD = 10


@dataclass
class GuardrailCounts:
    invalid_error_count: (
        int  # Σ len(exception_stats[type]) over NON-benign, array-shaped types
    )
    is_high_errors: bool  # invalid_error_count > 10  (the "Errors: k" badge condition)
    is_incomplete: bool  # attempted (stats.n_trials) < planned (job.n_trials)
    attempted_n_trials: Optional[int]
    planned_n_trials: Optional[int]


def _coerce_stats(stats: Any) -> Optional[dict]:
    """storage.ts: `if (typeof stats === 'string') stats = JSON.parse(...)` (undefined on failure);
    non-string is used as-is."""
    if isinstance(stats, str):
        try:
            return json.loads(stats)
        except Exception:
            return None
    return stats if isinstance(stats, dict) else None


def guardrail_counts(stats: Any, planned_n_trials: Optional[int]) -> GuardrailCounts:
    """AUTHORITATIVE per-eval guardrail counts. Faithful port of storage.ts:416-449.

    stats            = the `sandbox_jobs.stats` JSON (dict or JSON string).
    planned_n_trials = `sandbox_jobs.n_trials` (the PLANNED trial count).
    """
    stats = _coerce_stats(stats)

    invalid_error_count = 0
    evals = (stats or {}).get("evals") or {}
    if isinstance(evals, dict):
        for eval_data in evals.values():
            exception_stats = (eval_data or {}).get("exception_stats") or {}
            if not isinstance(exception_stats, dict):
                continue
            for error_type, trials in exception_stats.items():
                # storage.ts: `if (Array.isArray(trials) && !BENIGN.has(type)) count += trials.length`
                # Only ARRAY-shaped exception_stats are counted; an integer-shaped value is ignored,
                # exactly as the canonical code does.
                if isinstance(trials, list) and error_type not in BENIGN_ERRORS:
                    invalid_error_count += len(trials)

    attempted = (stats or {}).get("n_trials")
    attempted = attempted if isinstance(attempted, int) else None
    is_incomplete = (
        attempted is not None
        and planned_n_trials is not None
        and attempted < planned_n_trials
    ) or (attempted is None and planned_n_trials is not None and planned_n_trials > 0)
    return GuardrailCounts(
        invalid_error_count=invalid_error_count,
        is_high_errors=invalid_error_count > CANONICAL_HIGH_ERRORS_THRESHOLD,
        is_incomplete=is_incomplete,
        attempted_n_trials=attempted,
        planned_n_trials=planned_n_trials,
    )


def passes_gate(
    stats: Any,
    planned_n_trials: Optional[int],
    *,
    max_invalid_errors: int = CANONICAL_HIGH_ERRORS_THRESHOLD,
    require_complete: bool = True,
    min_complete_frac: Optional[float] = None,
) -> Tuple[bool, str]:
    """OUR use-case: a PASS/FAIL keep-vs-de-register decision built on the AUTHORITATIVE
    counts (the leaderboard shows the raw count; a purge/harvest needs a boolean).

    PASS iff  invalid_error_count <= max_invalid_errors  AND  <completeness ok>.

    - max_invalid_errors defaults to 10, reproducing the leaderboard's own isHighErrors
      boundary (`> 10`). To gate on a FRACTION instead (the campaign's "non-benign <= 10%"),
      pass max_invalid_errors=round(0.10 * planned_n_trials).
    - Completeness: pass **min_complete_frac** (e.g. 0.90 for the campaign's "valid-complete
      >= 90%") to gate on attempted/planned >= that fraction; otherwise, if require_complete,
      use the canonical strict `is_incomplete` (attempted < planned).

    Returns (passed, reason_string).
    """
    c = guardrail_counts(stats, planned_n_trials)
    reasons = []
    if c.invalid_error_count > max_invalid_errors:
        reasons.append(
            f"high-errors ({c.invalid_error_count} non-benign > {max_invalid_errors})"
        )
    if min_complete_frac is not None:
        frac = (
            (c.attempted_n_trials or 0) / planned_n_trials if planned_n_trials else 0.0
        )
        if frac < min_complete_frac:
            reasons.append(
                f"incomplete ({c.attempted_n_trials}/{c.planned_n_trials} = {frac:.1%} < {min_complete_frac:.0%})"
            )
    elif require_complete and c.is_incomplete:
        reasons.append(
            f"incomplete ({c.attempted_n_trials}/{c.planned_n_trials} trials)"
        )
    passed = not reasons
    return passed, ("PASS" if passed else "FAIL: " + "; ".join(reasons))


# --------------------------------------------------------------------------- CLI
def _get_client():
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print(
            "Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set",
            file=sys.stderr,
        )
        sys.exit(1)
    return create_client(url, key)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Print the canonical eval-guardrail counts + PASS/FAIL for a sandbox_jobs row."
    )
    ap.add_argument("--job-id", required=True, help="sandbox_jobs.id to evaluate")
    ap.add_argument(
        "--max-invalid-errors",
        type=int,
        default=CANONICAL_HIGH_ERRORS_THRESHOLD,
        help="gate threshold on non-benign error count (default 10 = leaderboard isHighErrors)",
    )
    ap.add_argument(
        "--no-require-complete", action="store_true", help="do NOT fail on incomplete"
    )
    ap.add_argument("--json", action="store_true", help="emit JSON")
    a = ap.parse_args(argv)

    c = _get_client()
    rows = (
        c.table("sandbox_jobs")
        .select("id,stats,n_trials,model_id,benchmark_id,username")
        .eq("id", a.job_id)
        .execute()
        .data
    )
    if not rows:
        print(f"no sandbox_jobs row with id={a.job_id}", file=sys.stderr)
        sys.exit(1)
    job = rows[0]
    counts = guardrail_counts(job.get("stats"), job.get("n_trials"))
    passed, reason = passes_gate(
        job.get("stats"),
        job.get("n_trials"),
        max_invalid_errors=a.max_invalid_errors,
        require_complete=not a.no_require_complete,
    )
    if a.json:
        print(
            json.dumps({**asdict(counts), "passed": passed, "reason": reason}, indent=2)
        )
    else:
        print(f"job {a.job_id} (user={job.get('username')})")
        print(
            f"  invalid_error_count = {counts.invalid_error_count}  (Errors:k badge = {counts.is_high_errors})"
        )
        print(
            f"  incomplete          = {counts.is_incomplete}  ({counts.attempted_n_trials}/{counts.planned_n_trials} trials)"
        )
        print(f"  GATE                = {reason}")


if __name__ == "__main__":
    main()
