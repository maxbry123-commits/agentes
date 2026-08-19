"""T33 — protected path patterns → HOLD. No overwrite of historical main."""
from __future__ import annotations

import fnmatch

DEFAULT_PROTECTED = [
    ".github/workflows/**",
    "**/secrets/**",
    "**/*credential*",
    "**/*token*",
    "PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md",
]


def is_protected(path: str, patterns: list[str] | None = None) -> bool:
    pats = patterns or DEFAULT_PROTECTED
    dest = str(path)
    return any(fnmatch.fnmatch(dest, pat) for pat in pats)


def check_protected(paths: list[str], patterns: list[str] | None = None) -> dict:
    blocked = [p for p in paths if is_protected(p, patterns)]
    if blocked:
        return {
            "ok": False,
            "status": "HOLD",
            "reason": "PROTECTED_PATH",
            "blocked": blocked,
        }
    return {"ok": True, "status": "OK", "blocked": []}


if __name__ == "__main__":
    hit = check_protected([".github/workflows/x.yml"])
    assert hit["status"] == "HOLD" and hit["ok"] is False
    miss = check_protected(["extensions/foo.py"])
    assert miss["ok"] is True
    print("ok", hit["status"], miss["status"])
