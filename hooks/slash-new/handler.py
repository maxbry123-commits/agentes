#!/usr/bin/env python3
"""handler.py — /new (spec)"""
import json, sys, uuid

def handle(event):
    new_sid = f"sess-{uuid.uuid4().hex[:10]}"
    return {
        "new_session_id": new_sid,
        "message_to_user": "Sesión nueva creada. Decime qué necesitás.",
        "persist_context": {"old_session_id": event.get("session_id")},
    }

if __name__ == "__main__":
    e = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(handle(e)))
