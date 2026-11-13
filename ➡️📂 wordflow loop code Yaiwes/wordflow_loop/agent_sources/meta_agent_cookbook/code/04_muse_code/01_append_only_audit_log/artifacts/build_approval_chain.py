#!/usr/bin/env python3
"""Renders the approval evidence chain from a Muse Code export.

Finds the first approval in the export and prints the records that carry it,
from the request through to the moment the effect starts. Every line is read
back out of the export, so the diagram cannot drift from the run it documents.

Usage:
    python3 build_approval_chain.py trajectory.json
    python3 build_approval_chain.py trajectory.json --plain
"""

import json
import sys

DIM = "\x1b[38;2;130;130;130m"
WHITE = "\x1b[38;2;235;235;235m"
AMBER = "\x1b[38;2;235;170;60m"
GREEN = "\x1b[38;2;110;200;140m"
CYAN = "\x1b[38;2;110;190;220m"
BOLD = "\x1b[1m"
OFF = "\x1b[0m"

plain = "--plain" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
path = args[0] if args else "trajectory.json"


def c(color, text):
    return text if plain else f"{color}{text}{OFF}"


def b(text):
    return text if plain else BOLD + text


def short(value, width=12):
    value = str(value)
    return value if len(value) <= width else value[: width - 1] + "…"


with open(path) as f:
    doc = json.load(f)

records = []
for event in doc.get("events", []):
    envelope = event.get("envelope") or {}
    sequence = envelope.get("sequence")
    if sequence is None:
        continue
    payload = envelope.get("payload") or {}
    inner = payload.get("event") or payload.get("record") or {}
    records.append((sequence, envelope.get("payload_type"), inner, payload))

start = next(
    (
        r
        for r in records
        if r[2].get("kind") == "requested" and "approval_subject" in r[2]
    ),
    None,
)
if start is None:
    sys.exit("no approval found in this export (the run may have used --yolo)")

window = [r for r in records if start[0] <= r[0]]
end = next((r[0] for r in window if r[1] == "tool_batch.effect.started"), window[-1][0])
window = [r for r in window if r[0] <= end]

subject = start[2]["approval_subject"]
command = subject.get("raw_command", "")
pending = start[2].get("pending_action_id", "")
choices = " ".join(
    f"[{ch.get('label')}]" for ch in start[2].get("available_choices", [])
)

print(
    c(CYAN, b('"what did the agent do, and who allowed it?"'))
    + c(DIM, "  —  one approval, from the export")
)
print(
    c(
        DIM,
        f"jq '.events[] | select(.envelope.sequence>={start[0]} "
        f"and .envelope.sequence<={end})' {path}",
    )
)
print()

# Amber up to the decision, green once the verdict is recorded.
DECIDED = "decision_applied"
seen_decision = False
for sequence, payload_type, inner, payload in window:
    kind = inner.get("kind") if payload_type == "runtime.session" else payload_type
    if kind is None:
        kind = payload_type
    detail = []
    if kind == "requested":
        head = "approval.review"
        detail.append(f"bash wants: {command}")
        detail.append(f"choices: {choices}")
    elif kind == "approval_wait.effect.started":
        head = "the run BLOCKS here"
        detail.append(f"pending_action_id {short(pending, 13)}")
        detail.append("the tool has not run, execution is suspended on the approval")
    elif kind == "stage_requirement_resolved":
        head = "choice bound"
        detail.append(
            f"decision={inner.get('decision')}  policy_result={inner.get('policy_result')}"
        )
        detail.append(f"resolution: {(inner.get('resolution') or {}).get('kind')}")
    elif kind == "decision_applied":
        head = "WHO ALLOWED IT"
        source = inner.get("decision_source") or {}
        detail.append(f"decision={str(inner.get('decision')).upper()}")
        detail.append(
            "decision_source: {{ kind: {}, prompt_version: {}, context_digest: {} }}".format(
                source.get("kind"),
                source.get("prompt_version"),
                short(source.get("context_digest"), 22),
            )
        )
    elif kind == "approval_wait.effect.terminal":
        head = "unblocked"
        detail.append(f"outcome: {(inner.get('outcome') or {}).get('kind')}")
        detail.append("same pending_action_id, the wait is discharged")
    elif kind == "side_effect_intent":
        head = "INTENT (pre-run stamp)"
        detail.append(f"operation: {inner.get('operation')}")
        detail.append(
            f"policy_decision: {inner.get('policy_decision')}   "
            "← authorization recorded BEFORE the effect starts"
        )
    elif kind == "tool_batch.effect.started":
        head = "the effect finally runs"
    else:
        continue

    color = GREEN if seen_decision else AMBER
    if kind == DECIDED:
        seen_decision = True
        color = GREEN
    print(
        f"{c(DIM, str(sequence).rjust(4))} {c(color, '▌')}"
        f"{c(WHITE, b(kind.ljust(30)))} {c(DIM, head)}"
    )
    for line in detail:
        print(f"     {c(DIM, '│')}   {c(DIM, line)}")

print()
print(
    c(DIM, "Threading key: ")
    + c(WHITE, f"pending_action_id {pending}")
    + c(DIM, " links every record above.")
)
print(
    c(
        DIM,
        "Read top to bottom: request → block → decide → record the "
        "authorizer → unblock → stamp intent → run.",
    )
)
