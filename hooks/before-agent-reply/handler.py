#!/usr/bin/env python3
"""handler.py — before_agent_reply (spec, NO ejecutable)"""
import json, sys

def handle(event):
    text = event.get("reply_text", "")
    user = event.get("user_id", "")
    if user != "maxbry":
        return {"final_text": text, "truncated": False}
    lines = text.splitlines()
    if len(lines) <= 6:
        return {"final_text": text, "truncated": False}
    kept = "\n".join(lines[:6])
    return {
        "final_text": kept + "\n\n[…truncado, decí 'expandir' para todo]",
        "truncated": True,
        "reason": "max-6-lines",
    }

if __name__ == "__main__":
    e = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(handle(e)))
