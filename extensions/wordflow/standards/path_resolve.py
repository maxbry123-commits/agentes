"""S8 — resolución determinista de paths (cwd + WF + repo)."""
from __future__ import annotations
from pathlib import Path
from typing import Optional, List

WF_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]


def resolve_path(p: str, *, must_exist: bool = False) -> Path:
    if not p:
        raise ValueError("empty path")
    raw = Path(p)
    candidates: List[Path] = [raw, Path.cwd() / p, WF_ROOT / p, REPO_ROOT / p]
    if p.startswith("extensions/wordflow/"):
        candidates.append(WF_ROOT / p[len("extensions/wordflow/"):])
    if p.startswith("extensions/"):
        candidates.append(REPO_ROOT / p)
    for c in candidates:
        try:
            r = c.resolve()
        except OSError:
            continue
        if must_exist and not r.exists():
            continue
        if not must_exist:
            # prefer existing; else first writable parent candidate
            if r.exists() or r.parent.exists() or REPO_ROOT.exists():
                return r
        else:
            return r
    # last resort: under WF
    return (WF_ROOT / Path(p).name).resolve()


def resolve_optional(p: Optional[str], *, must_exist: bool = False) -> Optional[Path]:
    if not p:
        return None
    return resolve_path(p, must_exist=must_exist)
