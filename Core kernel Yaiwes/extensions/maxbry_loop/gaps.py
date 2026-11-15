import re
from .models import Task, uid

KEYWORDS = [
    "must",
    "required",
    "requirement",
    "todo",
    "pending",
    "missing",
    "gap",
    "verify",
    "test",
    "acceptance",
    "should",
]


def detect_gaps(goal, state):
    gaps = []
    text = goal.text.lower()
    for line in goal.text.splitlines():
        s = line.strip()
        if re.match(r"^[-*]\s+", s) or re.match(r"^\d+[.)]\s+", s):
            if len(s) > 5:
                gaps.append(("document_requirement", s))
    done_titles = " ".join(t.title.lower() for t in state.tasks.values() if t.status == "done")
    for kw in KEYWORDS:
        if kw in text and kw not in done_titles:
            gaps.append(("keyword_gap", f"Review unresolved requirement related to '{kw}'"))
    for t in state.tasks.values():
        if t.status == "done" and (not t.acceptance or not t.evidence):
            gaps.append(
                ("evidence_gap", f"Task {t.id} is done without complete verification evidence")
            )
    seen = set()
    result = []
    for kind, desc in gaps:
        key = (kind, desc)
        if key not in seen:
            seen.add(key)
            result.append((kind, desc))
    return result


def append_gap_tasks(state, gaps, max_new=10):
    added = []
    existing = {t.description for t in state.tasks.values()}
    for kind, desc in gaps[:max_new]:
        if desc in existing:
            continue
        t = Task(
            id=uid("GAP"),
            title=f"Resolve: {desc[:80]}",
            description=desc,
            priority=80,
            acceptance=["Evidence recorded", "No workflow integrity regression"],
            provenance={
                "kind": kind,
                "source": "gap_detector",
                "iteration": state.iteration,
            },
        )
        state.tasks[t.id] = t
        state.workflow_version += 1
        added.append(t)
        existing.add(desc)
    return added
