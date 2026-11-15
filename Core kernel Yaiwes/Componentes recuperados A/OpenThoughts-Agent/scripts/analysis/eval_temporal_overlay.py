#!/usr/bin/env python3
"""Overlay eval-time reward markers on the RL-time temporal axis.

Takes post-training eval trace datasets (one per RL checkpoint) and plots
their summary rewards as points on the same time axis, anchored at the
checkpoint's wall-clock time.

Usage:
    python -m scripts.analysis.eval_temporal_overlay \\
        --rl-traces      penfever/rl-training-traces \\
        --eval-traces    penfever/eval@step-500:2026-05-25T12:00 \\
        --eval-traces    penfever/eval@step-1000:2026-05-26T18:30 \\
        --bin-hours      4 \\
        --output         /path/temporal_overlay.png
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.analysis.utils import (  # noqa: E402
    Trace,
    load_traces,
    mean_reward_per_trial,
)


def _floor_to_bin(dt: datetime, bin_size: timedelta, origin: datetime) -> datetime:
    """Floor *dt* into a bin of size *bin_size* relative to *origin*."""
    delta = dt - origin
    bin_index = int(delta.total_seconds() // bin_size.total_seconds())
    return origin + bin_size * bin_index


def _bin_rl_reward(
    traces: List[Trace], bin_hours: float
) -> Tuple[List[datetime], List[float]]:
    """Bin RL traces by date, return parallel (centers, mean_reward) arrays."""
    dated = [t for t in traces if t.date is not None]
    if not dated:
        return [], []
    origin = min(t.date for t in dated)
    bin_size = timedelta(hours=bin_hours)
    buckets: Dict[datetime, List[float]] = defaultdict(list)
    for t in dated:
        if t.reward is None:
            continue
        b = _floor_to_bin(t.date, bin_size, origin)
        buckets[b].append(t.reward)
    centers = sorted(buckets)
    means = [sum(buckets[c]) / len(buckets[c]) for c in centers]
    # Shift to mid-bin for plotting.
    centers = [c + bin_size / 2 for c in centers]
    return centers, means


_ISO_TS_TAIL_RE = re.compile(
    # Anchored: must reach end of string. Accepts:
    #   2026-05-25T12:00
    #   2026-05-25T12:00:01
    #   2026-05-25T12:00:01.651141
    #   2026-05-25T12:00:01+00:00
    #   2026-05-25T12:00:01.651141+00:00
    r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"
    r"(?::\d{2}(?:\.\d+)?)?"
    r"(?:Z|[+-]\d{2}:?\d{2})?)$"
)


def _parse_eval_spec(spec: str) -> Tuple[str, Optional[datetime], Optional[str]]:
    """Parse ``<source>[@<label>][:<iso-timestamp>]``.

    The trailing ``:<iso-timestamp>`` is recognized via an anchored regex
    that accepts ``HH:MM``, ``HH:MM:SS``, ``HH:MM:SS.us``, and any of those
    with a ``+HH:MM`` / ``Z`` UTC offset. The source / label portion can
    safely contain colons.

    Examples:
      ``penfever/foo``                       → (source, None, None)
      ``penfever/foo@step-500``              → (source, None, "step-500")
      ``penfever/foo:2026-05-25T12:00``      → (source, datetime, None)
      ``penfever/foo@step-500:2026-05-25T12:00:01.651141+00:00`` → all three
    """
    label: Optional[str] = None
    ts: Optional[datetime] = None

    # Strip the timestamp tail (anchored regex; matches at most once).
    match = _ISO_TS_TAIL_RE.search(spec)
    if match:
        ts_str = match.group(1)
        head = spec[: match.start()]
        # The separator before the timestamp must be ':' (this is our
        # spec format). If it's not, treat the whole thing as source.
        if head.endswith(":"):
            head = head[:-1]
            try:
                ts = datetime.fromisoformat(ts_str)
            except (TypeError, ValueError):
                ts = None
                head = spec
        else:
            head = spec
    else:
        head = spec

    if "@" in head:
        source, _, label = head.partition("@")
    else:
        source = head
    return source, ts, label


def _eval_marker(spec: str, max_rows: Optional[int]) -> Dict[str, Any]:
    source, ts, label = _parse_eval_spec(spec)
    traces = load_traces(source, max_rows=max_rows)
    mean_r = mean_reward_per_trial([t.raw for t in traces])
    return {
        "spec": spec,
        "source": source,
        "label": label or source,
        "timestamp": ts,
        "n": len(traces),
        "mean_reward": mean_r,
    }


def _is_baseline_label(label: str) -> bool:
    """Heuristic: detect baseline markers so we can colour/style them differently."""
    return label.lower().startswith("baseline") or "base" in label.lower()


def _plot(
    rl_centers, rl_means, eval_markers, output_path: Path, bin_hours: float
) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "[eval-temporal-overlay] matplotlib unavailable; skipping plot",
            file=sys.stderr,
        )
        return
    fig, ax = plt.subplots(figsize=(12, 5))
    if rl_centers:
        ax.plot(
            rl_centers,
            rl_means,
            "-o",
            label=f"RL-time reward (bin={bin_hours}h)",
            color="#36c",
            markersize=4,
        )

    # Group markers by timestamp so co-located ones can be horizontally
    # jittered (without jitter, overlapping markers hide each other).
    plotted = [
        m
        for m in eval_markers
        if m["timestamp"] is not None and m["mean_reward"] is not None
    ]
    by_ts: Dict[datetime, List[Dict[str, Any]]] = defaultdict(list)
    for m in plotted:
        by_ts[m["timestamp"]].append(m)

    # Jitter strategy: total time span / 80 -> per-step offset; 0 for solo.
    if rl_centers:
        span = max(rl_centers) - min(rl_centers)
    elif plotted:
        ts_list = [m["timestamp"] for m in plotted]
        span = max(ts_list) - min(ts_list) if len(ts_list) > 1 else timedelta(hours=1)
    else:
        span = timedelta(hours=1)
    jitter_step = span / 80 if span.total_seconds() > 0 else timedelta(minutes=15)

    baseline_label_set = False
    postrl_label_set = False
    for ts, group in by_ts.items():
        # Sort within group: baseline first so post-RL renders on top, then
        # apply symmetric horizontal jitter around the timestamp.
        group.sort(key=lambda m: 0 if _is_baseline_label(m["label"]) else 1)
        n = len(group)
        # Compute offsets centered on 0: -((n-1)/2)*step ... +((n-1)/2)*step
        for idx, m in enumerate(group):
            offset_index = idx - (n - 1) / 2
            x_pos = ts + jitter_step * offset_index
            is_baseline = _is_baseline_label(m["label"])
            color = "#666" if is_baseline else "#a30"
            marker = "s" if is_baseline else "D"
            edge = "white"
            legend_label: Optional[str] = None
            if is_baseline and not baseline_label_set:
                legend_label = "baseline eval"
                baseline_label_set = True
            elif not is_baseline and not postrl_label_set:
                legend_label = "post-RL eval"
                postrl_label_set = True
            ax.scatter(
                [x_pos],
                [m["mean_reward"]],
                color=color,
                s=90,
                marker=marker,
                edgecolors=edge,
                linewidths=1.2,
                zorder=5,
                label=legend_label,
            )
            # Annotation: stack labels vertically when co-located.
            ax.annotate(
                m["label"],
                (x_pos, m["mean_reward"]),
                textcoords="offset points",
                xytext=(8, 8 - 14 * idx),
                fontsize=8,
                color="#333",
            )
        # Draw a thin vertical guide so eyeballing back to the timestamp is easy.
        if n > 1:
            ax.axvline(
                x=ts,
                color="#bbb",
                linestyle=":",
                linewidth=0.8,
                zorder=1,
                alpha=0.7,
            )

    ax.set_xlabel("wall-clock time")
    ax.set_ylabel("mean reward per trial")
    ax.set_title("RL-time reward (line) with post-RL eval-checkpoint rewards (markers)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=130)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--rl-traces",
        required=True,
        help="RL-time training trace source (HF/JSONL/dir)",
    )
    parser.add_argument(
        "--eval-traces",
        action="append",
        default=[],
        help=(
            "Eval-time trace source with optional label/timestamp: "
            "'<source>[@<label>][:<iso-timestamp>]'. Repeat for multiple "
            "checkpoints. Timestamp is required to place the marker on the "
            "time axis."
        ),
    )
    parser.add_argument(
        "--bin-hours", type=float, default=4.0, help="Hours per RL-time bin"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="PNG output path (JSON sidecar also written)",
    )
    parser.add_argument(
        "--max-rows", type=int, default=None, help="Cap rows per source (smoke testing)"
    )
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    rl_traces = load_traces(args.rl_traces, max_rows=args.max_rows)
    rl_centers, rl_means = _bin_rl_reward(rl_traces, args.bin_hours)
    eval_markers = [_eval_marker(s, args.max_rows) for s in args.eval_traces]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    _plot(rl_centers, rl_means, eval_markers, args.output, args.bin_hours)
    sidecar = args.output.with_suffix(".json")
    sidecar.write_text(
        json.dumps(
            {
                "rl": {
                    "bin_hours": args.bin_hours,
                    "points": [
                        {"t": c.isoformat(), "mean_reward": m}
                        for c, m in zip(rl_centers, rl_means)
                    ],
                },
                "eval": [
                    {
                        "label": m["label"],
                        "source": m["source"],
                        "timestamp": m["timestamp"].isoformat()
                        if m["timestamp"]
                        else None,
                        "n": m["n"],
                        "mean_reward": m["mean_reward"],
                    }
                    for m in eval_markers
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"[eval-temporal-overlay] wrote {args.output} ({len(rl_centers)} RL bins, {len(eval_markers)} eval markers)"
    )
    return 0


def main() -> None:
    sys.exit(run(parse_args()))


if __name__ == "__main__":
    main()
