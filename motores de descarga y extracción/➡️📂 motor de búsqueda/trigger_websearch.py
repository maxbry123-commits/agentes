#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, pathlib, subprocess, sys

SCHEMA = "yaiwes.websearch.trigger.v2"
ENGINE_PATH = pathlib.Path(__file__).resolve().parent / "websearch_engine.py"
DEFAULT_PROVIDERS = "ddgs,brave,tavily,serper,firecrawl"

def main():
    p = argparse.ArgumentParser(description="Trigger local on-demand para Yaiwes web search")
    p.add_argument("query")
    p.add_argument("--providers", default=os.getenv("PROVIDERS", DEFAULT_PROVIDERS))
    p.add_argument("--limit", type=int, default=int(os.getenv("MAX_RESULTS_PER_PROVIDER", "8")))
    p.add_argument("--output-root", default=os.getenv("WEBSEARCH_OUTPUT_ROOT", "./websearch-results"))
    p.add_argument("--run-id", default=os.getenv("RUN_ID", ""))
    a = p.parse_args()
    q = a.query.strip()
    if not q:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "QUERY required"}))
    if not ENGINE_PATH.is_file():
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "ENGINE_PATH_GAP", "detail": str(ENGINE_PATH)}))
    env = dict(os.environ)
    env.update({"QUERY": q, "PROVIDERS": a.providers,
                "MAX_RESULTS_PER_PROVIDER": str(max(1, min(a.limit, 20))),
                "WEBSEARCH_OUTPUT_ROOT": a.output_root})
    if a.run_id: env["RUN_ID"] = a.run_id
    proc = subprocess.run([sys.executable, str(ENGINE_PATH), q], env=env, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    payload = None
    for line in reversed([x.strip() for x in proc.stdout.splitlines() if x.strip()]):
        try:
            obj = json.loads(line)
            if isinstance(obj, dict): payload = obj; break
        except json.JSONDecodeError: pass
    if proc.returncode != 0 or payload is None:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "ENGINE_NO_JSON_OUTPUT",
                                     "detail": (proc.stdout or "")[-2000:]}, ensure_ascii=False))
    print(json.dumps({"schema": SCHEMA, "state": "LOCAL_RUN", "engine_verdict": payload.get("verdict"),
                      "result": payload}, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__": main()
