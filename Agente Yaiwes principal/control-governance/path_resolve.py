"""S8/T3 — resolución determinista de paths (cwd + WF + repo walk)."""
from __future__ import annotations
from pathlib import Path
from typing import Optional, List

WF_ROOT = Path(__file__).resolve().parents[1]


def find_repo_root(start: Optional[Path] = None) -> Path:
    """Walk parents looking for repo markers — no fixed parents[N]."""
    cur = (start or Path(__file__)).resolve()
    if cur.is_file():
        cur = cur.parent
    for p in [cur, *cur.parents]:
        if (p / ".git").exists() or (p / "pyproject.toml").exists() or (p / "extensions" / "wordflow").is_dir():
            return p
        if p.name == "agentes" and (p / "extensions").is_dir():
            return p
    # fallback: WF parent chain
    return WF_ROOT.parent.parent if WF_ROOT.parent.name == "extensions" else WF_ROOT.parent


REPO_ROOT = find_repo_root()


def resolve_path(p: str, *, must_exist: bool = False) -> Path:
    if not p:
        raise ValueError("empty path")
    candidates: List[Path] = [Path(p), Path.cwd() / p, WF_ROOT / p, REPO_ROOT / p]
    if p.startswith("extensions/wordflow/"):
        candidates.append(WF_ROOT / p[len("extensions/wordflow/"):])
    if p.startswith("extensions/"):
        candidates.append(REPO_ROOT / p)
    existing = []
    for c in candidates:
        try:
            r = c.resolve()
        except OSError:
            continue
        if r.exists():
            if must_exist or r.suffix == ".py" or True:
                existing.append(r)
                if must_exist:
                    return r
    if must_exist:
        if existing:
            return existing[0]
        raise FileNotFoundError(p)
    if existing:
        return existing[0]
    # dest may not exist yet — prefer under WF or cwd
    for c in candidates:
        try:
            r = c.resolve()
            if r.parent.exists() or REPO_ROOT.exists():
                return r
        except OSError:
            continue
    return (WF_ROOT / Path(p).name).resolve()


def resolve_optional(p: Optional[str], *, must_exist: bool = False) -> Optional[Path]:
    if not p:
        return None
    return resolve_path(p, must_exist=must_exist)


def default_scan_roots() -> List[Path]:
    """T4: roots alineados path_resolve + copy_first."""
    roots = [WF_ROOT, REPO_ROOT]
    kernel = REPO_ROOT / "extensions" / "wordflow_kernel"
    if kernel.exists():
        roots.append(kernel)
    seen, out = set(), []
    for r in roots:
        s = str(r.resolve()) if r.exists() else str(r)
        if s not in seen:
            seen.add(s)
            out.append(r)
    return out
