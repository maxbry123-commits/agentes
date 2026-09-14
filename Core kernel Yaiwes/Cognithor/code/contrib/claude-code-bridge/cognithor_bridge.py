#!/usr/bin/env python3
"""Command-type fallback bridge for Claude Code hooks.

Use this when you cannot use Claude Code's native ``"type": "http"`` hook
(e.g. sandboxed environments that block outbound HTTP from hook scripts).
It reads the hook JSON from stdin, forwards it to the corresponding
Cognithor endpoint, and prints the response to stdout.

Usage in ``~/.claude/settings.json``::

    {
      "hooks": {
        "PreToolUse": [{
          "hooks": [{
            "type": "command",
            "command": "python /abs/path/cognithor_bridge.py pre-tool-use",
            "timeout": 30
          }]
        }]
      }
    }

Exits 0 and prints the JSON Cognithor returned. On connection failure the
script exits 0 with ``{}`` on stdout -- Claude Code treats that as
"allow/continue", so a crashed Cognithor never deadlocks the editor.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

ENDPOINTS = {
    "pre-tool-use": "/api/claude-hooks/pre-tool-use",
    "post-tool-use": "/api/claude-hooks/post-tool-use",
    "stop": "/api/claude-hooks/stop",
    "session-start": "/api/claude-hooks/session-start",
    "session-end": "/api/claude-hooks/session-end",
}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in ENDPOINTS:
        print("usage: cognithor_bridge.py <" + "|".join(ENDPOINTS) + ">", file=sys.stderr)
        return 2

    base = os.environ.get("COGNITHOR_URL", "http://localhost:8741").rstrip("/")
    url = base + ENDPOINTS[argv[1]]

    try:
        payload = sys.stdin.buffer.read()
    except Exception as exc:
        print(f"bridge: failed to read stdin: {exc}", file=sys.stderr)
        sys.stdout.write("{}")
        return 0

    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "cognithor-hook-bridge/1",
        },
    )
    token = os.environ.get("COGNITHOR_HOOK_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            sys.stdout.buffer.write(resp.read())
            return 0
    except urllib.error.HTTPError as exc:
        print(f"bridge: HTTP {exc.code} from {url}: {exc.read()[:200]!r}", file=sys.stderr)
        sys.stdout.write("{}")
        return 0
    except urllib.error.URLError as exc:
        print(f"bridge: cannot reach Cognithor at {url}: {exc.reason}", file=sys.stderr)
        sys.stdout.write("{}")
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"bridge: unexpected error: {exc}", file=sys.stderr)
        sys.stdout.write("{}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
