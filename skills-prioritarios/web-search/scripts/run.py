#!/usr/bin/env python3
"""run.py — web-search"""
import json, sys, os, urllib.request, urllib.parse

def serper(q, n):
    key = os.environ.get("SERPER_API_KEY")
    if not key: return None
    body = json.dumps({"q": q, "n": n}).encode()
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=body,
        headers={"X-API-KEY": key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)
    return [
        {"title": o.get("title",""), "url": o.get("link",""), "snippet": o.get("snippet","")}
        for o in (data.get("organic") or [])[:n]
    ]

def ddg(q, n):
    return []

def main():
    p = json.loads(sys.stdin.read() or "{}")
    q = p["q"]
    n = p.get("n", 10)
    provider = p.get("provider", "auto")
    results, used = [], None
    if provider in ("auto","serper"):
        try:
            r = serper(q, n)
            if r is not None: results, used = r, "serper"
        except Exception as e:
            if provider == "serper":
                print(json.dumps({"ok": False, "error": str(e)})); sys.exit(1)
    if not results and provider in ("auto","ddg"):
        results, used = ddg(q, n), "ddg"
    if not results and provider in ("auto","bing"):
        used = "bing"
    print(json.dumps({"ok": True, "provider_used": used, "results": results, "count": len(results)}))

if __name__ == "__main__":
    main()
