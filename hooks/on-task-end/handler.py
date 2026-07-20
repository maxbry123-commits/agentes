#!/usr/bin/env python3
"""handler.py — on-task-end (spec)"""
import json, sys, uuid, time

def handle(event):
    s = event.get("status", "unknown")
    memory = []
    metrics = []
    kind = "success" if s == "ok" else "failure" if s in ("fail","blocked") else "pattern"
    memory.append({
        "id": f"mem-{uuid.uuid4().hex[:8]}",
        "kind": kind,
        "content": f"task {event.get('task_id')} status={s}",
        "refs": [event.get("agent_id"), event.get("skill_id")],
        "score": 1.0 if s == "ok" else -0.5,
        "created_at": time.time(),
    })
    metrics.append(f"task.duration_s={event.get('duration_s',0)}")
    if event.get("cost_usd"):
        metrics.append(f"task.cost_usd={event['cost_usd']}")
    warns = []
    if s in ("fail","blocked"):
        warns.append(f"task {event.get('task_id')} terminó con status={s}")
    return {"memory_entries_added": memory, "metrics_emitted": metrics, "warnings": warns}

if __name__ == "__main__":
    e = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(handle(e)))
