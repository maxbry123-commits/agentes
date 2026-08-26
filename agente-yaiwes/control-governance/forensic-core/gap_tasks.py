from __future__ import annotations

import uuid

_QUEUE: list[dict] = []


def _uid(prefix: str = "task") -> str:
    try:
        from .models import uid
        return uid(prefix)
    except Exception:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"


class GapTaskCompiler:
    """GAP → TaskSpec. Auditor never writes code; only emits tasks."""

    def compile(self, report, workspace_id: str):
        from .models import TaskSpec

        tasks = []
        for gap in report.gaps:
            tasks.append(
                TaskSpec(
                    task_id=_uid("task"),
                    gap_id=gap.gap_id,
                    objective=gap.recommendation or f"Resolve: {gap.requirement}",
                    target="repository",
                    acceptance=(
                        "gap no longer reported as MISSING/PARTIAL",
                        "validator passes",
                        "evidence packet generated",
                    ),
                    workspace_id=workspace_id,
                )
            )
        return tasks


def enqueue_gap(gap: dict) -> str:
    """T29: enqueue one gap as a fake code_path task. No infinite autofix."""
    if not isinstance(gap, dict):
        raise TypeError("gap must be dict")
    task_id = str(gap.get("task_id") or _uid("task"))
    _QUEUE.append({"task_id": task_id, "gap": gap, "status": "queued", "mode": "fake"})
    return task_id


def queued_gaps() -> list[dict]:
    return list(_QUEUE)


def accept_fake(task_id: str) -> dict:
    for row in _QUEUE:
        if row["task_id"] == task_id:
            row["status"] = "accepted_fake"
            return {"ok": True, "task_id": task_id, "mode": "fake"}
    return {"ok": False, "task_id": task_id, "error": "not_found"}


if __name__ == "__main__":
    tid = enqueue_gap({"gap_id": "G1", "requirement": "x"})
    assert tid
    assert len(queued_gaps()) == 1
    assert accept_fake(tid)["ok"] is True
    print("ok", tid)
