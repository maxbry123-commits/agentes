#!/usr/bin/env python3
"""handler.py — before_tool_call (spec, NO ejecutable)"""
import re, json, sys

PII_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[CARD]"),
    (re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[PHONE]"),
]

DESTRUCTIVE_BASH = [r"\brm\s+-rf\s+/", r"\bmkfs\b", r"\bdd\s+if=", r":\(\)\s*\{"]
DESTRUCTIVE_RE = re.compile("|".join(DESTRUCTIVE_BASH))

def redact_pii(obj):
    if isinstance(obj, str):
        for pat, repl in PII_PATTERNS:
            obj = pat.sub(repl, obj)
        return obj
    if isinstance(obj, dict):
        return {k: redact_pii(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_pii(x) for x in obj]
    return obj

def handle(event):
    out = {"allow": True, "mutated_args": redact_pii(event.get("tool_args", {}))}
    if event.get("tool_id") == "bash" and DESTRUCTIVE_RE.search(str(out["mutated_args"])):
        return {"allow": False, "reason": "pol.destructive-bash"}
    return out

if __name__ == "__main__":
    e = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(handle(e)))
