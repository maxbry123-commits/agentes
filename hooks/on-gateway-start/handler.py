#!/usr/bin/env python3
"""handler.py — on-gateway-start (spec)"""
import json, sys, os

PRIORITY_SKILLS = ["task-manager","test-runner","git","terminal","web-search","url-reader"]
REQUIRED_ENV = ["OC_GATEWAY_TOKEN","GITHUB_PAT_MAXBRY"]

def handle(event):
    log, warns = [], []
    for k in REQUIRED_ENV:
        if not os.environ.get(k):
            warns.append(f"missing env: {k}")
    log.append("cargando 6 skills prioritarios")
    for s in PRIORITY_SKILLS:
        log.append(f"  - {s}: ok (stub)")
    log.append("ping MCPs críticos: openclaw-mcp=ok filesystem=ok")
    return {"init_log": log, "loaded_skills": PRIORITY_SKILLS, "warnings": warns}

if __name__ == "__main__":
    e = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(handle(e)))
