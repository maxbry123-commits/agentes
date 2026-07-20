#!/usr/bin/env python3
"""run.py — task-manager

Spec funcional, NO ejecutable todavía (requiere openclaw runtime).
Lee input JSON de stdin, ejecuta action, escribe output JSON a stdout.
"""
import json, sys, os, time, uuid

TODOS_PATH = os.environ.get(
    "TASK_MANAGER_PATH",
    os.path.expanduser("~/.openclaw/state/todos.json"),
)

def load():
    if not os.path.exists(TODOS_PATH):
        return []
    with open(TODOS_PATH) as f:
        return json.load(f)

def save(items):
    os.makedirs(os.path.dirname(TODOS_PATH), exist_ok=True)
    with open(TODOS_PATH, "w") as f:
        json.dump(items, f, indent=2)

def main():
    payload = json.loads(sys.stdin.read() or "{}")
    action = payload.get("action")
    items = load()

    if action == "add":
        item = {
            "id": payload.get("id") or f"t-{uuid.uuid4().hex[:6]}",
            "title": payload["title"],
            "owner": payload.get("owner", "M3"),
            "status": "pending",
            "created_at": time.time(),
        }
        items.append(item)
        save(items)
        print(json.dumps({"ok": True, "item": item}))
    elif action == "list":
        out = [i for i in items if not payload.get("status") or i["status"] == payload["status"]]
        print(json.dumps({"ok": True, "items": out, "count": len(out)}))
    elif action == "done":
        for i in items:
            if i["id"] == payload["id"]:
                i["status"] = "done"
        save(items)
        print(json.dumps({"ok": True}))
    elif action == "blocked":
        for i in items:
            if i["id"] == payload["id"]:
                i["status"] = "blocked"
        save(items)
        print(json.dumps({"ok": True}))
    elif action == "show":
        item = next((i for i in items if i["id"] == payload["id"]), None)
        print(json.dumps({"ok": item is not None, "item": item}))
    else:
        print(json.dumps({"ok": False, "error": f"unknown action: {action}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
