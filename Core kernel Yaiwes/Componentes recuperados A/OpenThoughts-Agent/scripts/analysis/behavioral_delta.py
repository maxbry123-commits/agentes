#!/usr/bin/env python3
"""Diff behavioral metrics + failure-mode distributions between two trace datasets.

Run with the pre-RL trace dataset (or the SFT-only eval traces) as
``--before`` and the post-RL trace dataset as ``--after``.

The script:
- Loads both trace datasets via the shared :func:`scripts.analysis.utils.load_traces`
  loader (HF id, JSONL, or directory of ``result.json`` all supported).
- Extracts per-trace behavioral features (tool-call frequency, tool-error
  rate, think-token budget, response verbosity, code-block density, self-
  correction frequency, premature-stop rate, tool-call-by-name).
- Aggregates macro-level metrics: reward, turn count, conversation token
  count, error-type distribution, failure-mode distribution (from the
  ``failure_mode_analysis`` column if ``update_hf_failure_modes`` was
  run first).
- Diffs each metric, sorted by magnitude of delta so the most-shifted
  behavior appears at the top of the report.

Usage:
    python -m scripts.analysis.behavioral_delta \\
        --before  penfever/pre-rl-eval-traces \\
        --after   penfever/post-rl-eval-traces \\
        --output  /path/behavioral_delta.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.analysis.utils import (  # noqa: E402
    SCALAR_BEHAVIORAL_FIELDS,
    Trace,
    count_tokens,
    get_tiktoken_encoder,
    group_by_task,
    load_traces,
)


# ---------------------------------------------------------------------------
# Display config: human-readable name + unit hint for each behavioral feature.
# ---------------------------------------------------------------------------

_FEATURE_DISPLAY: Dict[str, Tuple[str, str, str]] = {
    # field name        : (label                       , value-fmt , delta-fmt)
    "tool_calls_total": ("tool calls / trace", ".1f", "+.2f"),
    "tool_errors": ("tool errors / trace", ".1f", "+.2f"),
    "tool_responses": ("tool responses / trace", ".1f", "+.2f"),
    "tool_error_rate": ("tool error rate", ".1%", "+.1f"),  # delta as pp
    "think_blocks": ("think blocks / trace", ".2f", "+.2f"),
    "think_tokens": ("think tokens / trace", ".0f", "+.0f"),
    "think_token_ratio": ("think / assistant ratio", ".1%", "+.1f"),  # delta as pp
    "assistant_msgs": ("assistant msgs / trace", ".1f", "+.2f"),
    "assistant_tokens": ("assistant tokens / trace", ".0f", "+.0f"),
    "mean_assistant_tokens": ("mean tokens / asst msg", ".1f", "+.2f"),
    "code_fence_blocks": ("code fences / trace", ".2f", "+.2f"),
    "self_correction_hits": ("self-correction phrases / trace", ".2f", "+.2f"),
}

# Ratio fields are reported in percentage points rather than raw fraction.
_RATIO_FIELDS = {"tool_error_rate", "think_token_ratio"}


@dataclass
class Summary:
    """Aggregated behavioral metrics for one trace dataset."""

    label: str
    n: int
    mean_reward: Optional[float]
    mean_turns: Optional[float]
    mean_tokens: Optional[float]
    error_dist: Dict[str, int]
    failure_mode_dist: Dict[str, int]
    pass_set: set  # tasks with at least one reward > 0
    fail_set: set  # tasks with no reward > 0 (and at least one trial)
    fm_coverage: float  # fraction of rows with a failure_mode label
    # Per-trace behavioral feature means (None-safe).
    behavioral: Dict[str, Optional[float]] = field(default_factory=dict)
    # Tool-call frequency by tool name (sum across all traces).
    tool_call_by_name: Dict[str, int] = field(default_factory=dict)
    # Premature stop rate (assistant-ended traces / total traces with msgs).
    premature_stop_rate: Optional[float] = None


def _mean(xs: Sequence[Optional[float]]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def summarize(label: str, traces: Sequence[Trace]) -> Summary:
    encoder = get_tiktoken_encoder()
    rewards = [t.reward for t in traces if t.reward is not None]
    turns = [t.turns for t in traces if t.turns > 0]
    tokens = [count_tokens(t.conversation, encoder) for t in traces if t.conversation]
    err = Counter(t.error_type for t in traces if t.error_type)
    fm = Counter(t.failure_mode for t in traces if t.failure_mode)
    fm_coverage = (
        sum(1 for t in traces if t.failure_mode) / len(traces) if traces else 0.0
    )
    pass_set: set = set()
    fail_set: set = set()
    for task, rows in group_by_task(traces).items():
        if any((r.reward or 0.0) > 0 for r in rows):
            pass_set.add(task)
        elif rows:
            fail_set.add(task)

    # Behavioral feature means. For ratio fields we average per-trace ratios
    # (None-skipping) rather than dividing sums.
    behavioral: Dict[str, Optional[float]] = {}
    for field_name in SCALAR_BEHAVIORAL_FIELDS:
        values = [getattr(t.behavioral, field_name) for t in traces]
        behavioral[field_name] = _mean(values)

    # Tool-call distribution by tool name.
    tool_calls: Dict[str, int] = {}
    for t in traces:
        for name, count in t.behavioral.tool_calls_by_name.items():
            tool_calls[name] = tool_calls.get(name, 0) + count

    # Premature-stop rate among traces with at least one message.
    eligible = [t for t in traces if t.behavioral.assistant_msgs > 0]
    if eligible:
        premature_rate = sum(1 for t in eligible if t.behavioral.premature_stop) / len(
            eligible
        )
    else:
        premature_rate = None

    return Summary(
        label=label,
        n=len(traces),
        mean_reward=_mean(rewards),
        mean_turns=_mean(turns),
        mean_tokens=_mean(tokens),
        error_dist=dict(err),
        failure_mode_dist=dict(fm),
        pass_set=pass_set,
        fail_set=fail_set,
        fm_coverage=fm_coverage,
        behavioral=behavioral,
        tool_call_by_name=tool_calls,
        premature_stop_rate=premature_rate,
    )


def _delta_str(
    before: Optional[float], after: Optional[float], pct: bool = False
) -> str:
    if before is None or after is None:
        return "—"
    d = after - before
    if pct:
        return f"{d * 100:+.1f}pp"
    return f"{d:+.2f}"


def _format_value(field_name: str, value: Optional[float]) -> str:
    if value is None:
        return "—"
    fmt = _FEATURE_DISPLAY.get(field_name, ("", ".2f", "+.2f"))[1]
    if field_name in _RATIO_FIELDS:
        return f"{value:{fmt}}"
    return f"{value:{fmt}}"


def _format_delta(
    field_name: str, before: Optional[float], after: Optional[float]
) -> str:
    if before is None or after is None:
        return "—"
    d = after - before
    if field_name in _RATIO_FIELDS:
        return f"{d * 100:+.1f}pp"
    fmt = _FEATURE_DISPLAY.get(field_name, ("", "", "+.2f"))[2]
    return f"{d:{fmt}}"


def _ranked_behavioral_deltas(
    before: Summary, after: Summary
) -> List[Tuple[str, Optional[float], Optional[float], Optional[float], float]]:
    """Return (field, before, after, delta, |normalized_delta|) sorted by |normalized_delta| desc.

    Normalization makes ratios (already in 0..1) and large counts comparable:
    we divide each delta by max(|before|, |after|, eps) — so a doubling of
    something small ranks the same as a doubling of something large.
    """
    rows = []
    for field_name in SCALAR_BEHAVIORAL_FIELDS:
        b = before.behavioral.get(field_name)
        a = after.behavioral.get(field_name)
        if b is None or a is None:
            continue
        delta = a - b
        scale = max(abs(b), abs(a), 1e-9)
        rows.append((field_name, b, a, delta, abs(delta) / scale))
    rows.sort(key=lambda r: r[4], reverse=True)
    return rows


def _rank_dist_delta(before: Dict[str, int], after: Dict[str, int]) -> List[tuple]:
    """Return (key, before_share, after_share, delta_share) sorted by |delta|."""
    bt = sum(before.values()) or 1
    at_ = sum(after.values()) or 1
    keys = set(before) | set(after)
    rows = []
    for k in keys:
        b = before.get(k, 0) / bt
        a = after.get(k, 0) / at_
        rows.append((k, b, a, a - b))
    rows.sort(key=lambda r: abs(r[3]), reverse=True)
    return rows


def write_markdown_report(
    before: Summary, after: Summary, output_path: Path, top_n: int = 15
) -> None:
    lines: List[str] = [
        "# Behavioral Delta Report",
        "",
        f"- **Before**: `{before.label}` ({before.n} rows, failure-mode coverage {before.fm_coverage:.0%})",
        f"- **After**:  `{after.label}` ({after.n} rows, failure-mode coverage {after.fm_coverage:.0%})",
        "",
        "## Macro metrics",
        "",
        "| metric | before | after | delta |",
        "|---|---|---|---|",
        f"| mean reward | {before.mean_reward if before.mean_reward is None else f'{before.mean_reward:.3f}'} | "
        f"{after.mean_reward if after.mean_reward is None else f'{after.mean_reward:.3f}'} | "
        f"{_delta_str(before.mean_reward, after.mean_reward)} |",
        f"| mean turns | {before.mean_turns if before.mean_turns is None else f'{before.mean_turns:.1f}'} | "
        f"{after.mean_turns if after.mean_turns is None else f'{after.mean_turns:.1f}'} | "
        f"{_delta_str(before.mean_turns, after.mean_turns)} |",
        f"| mean tokens (conv) | {before.mean_tokens if before.mean_tokens is None else f'{before.mean_tokens:.0f}'} | "
        f"{after.mean_tokens if after.mean_tokens is None else f'{after.mean_tokens:.0f}'} | "
        f"{_delta_str(before.mean_tokens, after.mean_tokens)} |",
        "",
    ]

    # --- Behavioral features (sorted by magnitude of delta) ----------------
    bdeltas = _ranked_behavioral_deltas(before, after)
    if bdeltas:
        lines += [
            "## Behavioral features (sorted by magnitude of delta)",
            "",
            "Per-trace means. Tool-call / tool-error rows surface whether the "
            "model is calling tools more or less often, and whether those calls "
            "succeed. Think-token rows surface whether reasoning budget shifted. "
            "Self-correction and code-fence rows surface stylistic changes.",
            "",
            "| feature | before | after | delta | |Δ| / scale |",
            "|---|---|---|---|---|",
        ]
        for field_name, b, a, _d, norm in bdeltas:
            label = _FEATURE_DISPLAY.get(field_name, (field_name, "", ""))[0]
            lines.append(
                f"| **{label}** | {_format_value(field_name, b)} | "
                f"{_format_value(field_name, a)} | "
                f"{_format_delta(field_name, b, a)} | {norm:.2f} |"
            )
        lines.append("")

    # --- Premature stop rate (binary; reported separately) -----------------
    if before.premature_stop_rate is not None or after.premature_stop_rate is not None:
        lines += [
            "## Premature stop rate",
            "",
            "Fraction of traces ending on an assistant message (rather than a "
            "tool response). For agentic loops this is a proxy for the model "
            "giving up mid-task or running out of context.",
            "",
            "| metric | before | after | delta |",
            "|---|---|---|---|",
            f"| premature stop rate | "
            f"{before.premature_stop_rate if before.premature_stop_rate is None else f'{before.premature_stop_rate:.1%}'} | "
            f"{after.premature_stop_rate if after.premature_stop_rate is None else f'{after.premature_stop_rate:.1%}'} | "
            f"{_delta_str(before.premature_stop_rate, after.premature_stop_rate, pct=True)} |",
            "",
        ]

    # --- Tool-call distribution by tool name -------------------------------
    tool_delta = _rank_dist_delta(before.tool_call_by_name, after.tool_call_by_name)
    if tool_delta:
        lines += [
            "## Tool-call distribution shifts (by tool name)",
            "",
            "Share of all tool calls in each dataset. Rows where a tool's "
            "share rose are evidence the policy adopted that tool more often "
            "post-RL.",
            "",
            "| tool | before share | after share | delta |",
            "|---|---|---|---|",
        ]
        for key, b, a, d in tool_delta[:top_n]:
            lines.append(f"| `{key}` | {b:.1%} | {a:.1%} | {d * 100:+.1f}pp |")
        lines.append("")

    fm_delta = _rank_dist_delta(before.failure_mode_dist, after.failure_mode_dist)
    if fm_delta:
        lines += [
            "## Failure-mode distribution shifts",
            "",
            "Each row is a failure-mode label produced by the GPT judge "
            "(`update_hf_failure_modes.py`); shares are normalized within "
            "each dataset.",
            "",
            "| mode | before share | after share | delta |",
            "|---|---|---|---|",
        ]
        for key, b, a, d in fm_delta[:top_n]:
            lines.append(f"| `{key}` | {b:.1%} | {a:.1%} | {d * 100:+.1f}pp |")
        lines.append("")
    else:
        lines += [
            "## Failure-mode distribution shifts",
            "",
            "_No failure-mode annotations found on either side. Run "
            "`scripts/analysis/update_hf_failure_modes.py` on both repos first "
            "to populate the `failure_mode_analysis` column._",
            "",
        ]

    err_delta = _rank_dist_delta(before.error_dist, after.error_dist)
    if err_delta:
        lines += [
            "## Error-type distribution shifts",
            "",
            "| error | before share | after share | delta |",
            "|---|---|---|---|",
        ]
        for key, b, a, d in err_delta[:top_n]:
            lines.append(f"| `{key}` | {b:.1%} | {a:.1%} | {d * 100:+.1f}pp |")
        lines.append("")

    # Task-level flips
    common_tasks = (before.pass_set | before.fail_set) & (
        after.pass_set | after.fail_set
    )
    newly_passing = sorted(
        t for t in common_tasks if t in before.fail_set and t in after.pass_set
    )
    newly_failing = sorted(
        t for t in common_tasks if t in before.pass_set and t in after.fail_set
    )
    lines += [
        "## Task-level pass/fail flips",
        "",
        f"- Common tasks across both datasets: **{len(common_tasks)}**",
        f"- Newly passing after RL (was-fail → now-pass): **{len(newly_passing)}**",
        f"- Newly failing after RL (was-pass → now-fail): **{len(newly_failing)}**",
        "",
    ]
    if newly_passing:
        lines.append("### Newly passing tasks")
        lines.append("")
        for t in newly_passing[:top_n]:
            lines.append(f"- `{t}`")
        if len(newly_passing) > top_n:
            lines.append(f"- _...and {len(newly_passing) - top_n} more_")
        lines.append("")
    if newly_failing:
        lines.append("### Newly failing tasks (regressions)")
        lines.append("")
        for t in newly_failing[:top_n]:
            lines.append(f"- `{t}`")
        if len(newly_failing) > top_n:
            lines.append(f"- _...and {len(newly_failing) - top_n} more_")
        lines.append("")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Also drop a JSON sidecar with the raw counts so downstream tooling
    # (e.g., the orchestrator, the LLM-judge step) doesn't need to re-parse
    # the markdown.
    sidecar = output_path.with_suffix(".json")
    sidecar.write_text(
        json.dumps(
            {
                "before": {
                    "label": before.label,
                    "n": before.n,
                    "mean_reward": before.mean_reward,
                    "mean_turns": before.mean_turns,
                    "mean_tokens": before.mean_tokens,
                    "error_dist": before.error_dist,
                    "failure_mode_dist": before.failure_mode_dist,
                    "fm_coverage": before.fm_coverage,
                    "behavioral": before.behavioral,
                    "tool_call_by_name": before.tool_call_by_name,
                    "premature_stop_rate": before.premature_stop_rate,
                },
                "after": {
                    "label": after.label,
                    "n": after.n,
                    "mean_reward": after.mean_reward,
                    "mean_turns": after.mean_turns,
                    "mean_tokens": after.mean_tokens,
                    "error_dist": after.error_dist,
                    "failure_mode_dist": after.failure_mode_dist,
                    "fm_coverage": after.fm_coverage,
                    "behavioral": after.behavioral,
                    "tool_call_by_name": after.tool_call_by_name,
                    "premature_stop_rate": after.premature_stop_rate,
                },
                "behavioral_ranked_deltas": [
                    {
                        "field": field_name,
                        "before": b,
                        "after": a,
                        "delta": d,
                        "normalized_abs_delta": norm,
                    }
                    for field_name, b, a, d, norm in _ranked_behavioral_deltas(
                        before, after
                    )
                ],
                "task_flips": {
                    "newly_passing": newly_passing,
                    "newly_failing": newly_failing,
                    "common_count": len(common_tasks),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--before", required=True, help="Pre-RL trace source (HF id, JSONL, or dir)"
    )
    parser.add_argument(
        "--after", required=True, help="Post-RL trace source (HF id, JSONL, or dir)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Markdown report path (sidecar .json also written)",
    )
    parser.add_argument(
        "--max-rows", type=int, default=None, help="Optional cap for smoke tests"
    )
    parser.add_argument(
        "--top-n", type=int, default=15, help="Top N rows per ranked section"
    )
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    before = load_traces(args.before, max_rows=args.max_rows)
    after = load_traces(args.after, max_rows=args.max_rows)
    if not before or not after:
        print(
            f"[behavioral-delta] empty trace set: before={len(before)} after={len(after)}",
            file=sys.stderr,
        )
        return 2
    s_before = summarize(args.before, before)
    s_after = summarize(args.after, after)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_markdown_report(s_before, s_after, args.output, top_n=args.top_n)
    print(
        f"[behavioral-delta] wrote {args.output} (+ {args.output.with_suffix('.json').name})"
    )
    return 0


def main() -> None:
    sys.exit(run(parse_args()))


if __name__ == "__main__":
    main()
