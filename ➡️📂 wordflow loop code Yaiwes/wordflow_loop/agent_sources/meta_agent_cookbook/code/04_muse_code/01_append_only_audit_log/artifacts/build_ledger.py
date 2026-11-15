#!/usr/bin/env python3
"""Build a color-coded audit ledger from a `muse export` document.

Usage:
    muse export --session <id> --out trajectory.json
    python3 build_ledger.py trajectory.json          # prints a colored ledger
    python3 build_ledger.py trajectory.json --plain   # no color (for piping)

One row per journaled action, in log order. Each row shows the sequence
number, elapsed time, the lane (model call / tool run / edit / approval), and
the authorization stamp the harness recorded BEFORE the effect ran. The
authorization comes from `side_effect_intent.policy_decision` and, for anything
that needed review, the `decision_applied.decision_source`.
"""
import json
import sys

LANES = {
    "model":    ("\033[38;2;108;158;255m", "model call"),
    "tool":     ("\033[38;2;86;182;128m",  "tool run"),
    "edit":     ("\033[38;2;196;140;255m", "edit"),
    "approval": ("\033[38;2;240;180;70m",  "approval"),
}
RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[38;2;120;120;130m"


def rows_from_export(doc):
    base = None
    for ev in doc["events"]:
        if ev["kind"] != "record":
            continue
        env = ev["envelope"]
        e = env.get("payload", {}).get("event", {})
        seq, kind, ts = env.get("sequence"), e.get("kind"), env.get("recorded_at")
        if base is None and ts:
            base = ts
        rel = f"+{(ts - base) / 1e6:6.1f}s" if ts and base else ""
        if kind == "side_effect_intent":
            op, pd = e.get("operation", ""), e.get("policy_decision", "")
            if op.startswith("model"):
                yield seq, rel, "model", f"provider=meta  auth={pd}"
            elif op == "tool:edit_file":
                yield seq, rel, "edit", f"edit_file  auth={pd}"
            elif op.startswith("tool"):
                yield seq, rel, "tool", f"{op.split(':', 1)[1]:11s}auth={pd}"
        elif kind == "requested":
            subj = e.get("approval_subject", {})
            yield seq, rel, "approval", f"REQUESTED  {e.get('tool_name')}: {subj.get('raw_command', '')}"
        elif kind == "decision_applied":
            ds = e.get("decision_source", {})
            yield seq, rel, "approval", f"{e.get('decision').upper()}  by {ds.get('kind')}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    plain = "--plain" in sys.argv
    doc = json.load(open(args[0]))
    sid = doc["sessions"][0]["session_id"] if doc.get("sessions") else "?"
    ended = "clean" if not doc["session_terminated_abnormally"] else "NO ORDERLY END"
    print(f"audit ledger  {sid}  ({len(doc['events'])} events, termination: {ended})")
    for seq, rel, lane, detail in rows_from_export(doc):
        color, label = LANES[lane]
        if plain:
            print(f"{seq:>4}  {rel:>8}  {label:<10} {detail}")
        else:
            hi = lane == "approval" or "llm_judge" in detail
            print(f"  {seq:>4}  {DIM}{rel:>8}{RESET}  {color}\u2588 {BOLD if hi else ''}"
                  f"{label:<10}{RESET} {color}{detail}{RESET}")


if __name__ == "__main__":
    main()
