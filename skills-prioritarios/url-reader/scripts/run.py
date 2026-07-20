#!/usr/bin/env python3
"""run.py — url-reader"""
import json, sys, os, urllib.request, re

def main():
    p = json.loads(sys.stdin.read() or "{}")
    url = p["url"]
    max_chars = p.get("max_chars", 50000)
    timeout = p.get("timeout_s", 20)
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mavis-Reader/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            html = r.read().decode("utf-8", errors="replace")
            status = r.status
            final = r.geturl()
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)})); sys.exit(1)
    text = re.sub(r"<script.*?</script>", "", html, flags=re.S|re.I)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.S|re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    truncated = len(text) > max_chars
    text = text[:max_chars]
    print(json.dumps({
        "ok": True,
        "status_code": status,
        "final_url": final,
        "markdown": text,
        "length": len(text),
        "truncated": truncated,
    }))

if __name__ == "__main__":
    main()
