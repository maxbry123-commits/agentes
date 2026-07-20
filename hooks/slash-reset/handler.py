#!/usr/bin/env python3
"""handler.py — /reset (spec)"""
import json, sys

def handle(event):
    return {
        "session_id": event["session_id"],
        "cleared_keys": ["history", "scratchpad", "loaded_skills", "working_memory"],
        "message_to_user": "Contexto borrado. Empezamos de cero en esta sesión.",
    }

if __name__ == "__main__":
    e = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(handle(e)))
