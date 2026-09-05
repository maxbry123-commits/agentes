"""Verificar v2 — evidence.json (Witness) · 0% LLM
SOURCE: DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2 PASO 5
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class Evidence:
    ok: bool
    timestamp: str
    files_count: int
    local_hashes: dict[str, str]
    repos: dict[str, Any]
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head(repo: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return r.stdout.strip()
    except Exception:
        return None


def verificar(root: str | Path, mapped: list[dict[str, str]]) -> Evidence:
    root_p = Path(root)
    hashes: dict[str, str] = {}
    for item in mapped:
        src = root_p / item["src"]
        if src.exists() and src.is_file():
            hashes[item["src"]] = _sha256(src)
    ok = len(hashes) == len(mapped) and len(mapped) > 0
    return Evidence(
        ok=ok,
        timestamp=datetime.now(timezone.utc).isoformat(),
        files_count=len(hashes),
        local_hashes=hashes,
        repos={},
        notes="local verification; remote ls-remote optional later",
    )


def verificar_repos_listos(repos_dir: Path, plan: dict) -> Evidence:
    repos_plan = plan.get("repos") or {}
    if not repos_plan and plan.get("mapped"):
        for m in plan["mapped"]:
            repos_plan.setdefault(m.get("dest", "default"), []).append(m["src"])
    detail: dict[str, Any] = {}
    all_ok = True
    total = 0
    for name, files in repos_plan.items():
        rp = repos_dir / name
        exists = rp.is_dir()
        n = sum(1 for p in rp.rglob("*") if p.is_file() and ".git" not in p.parts) if exists else 0
        head = _git_head(rp) if exists else None
        entry_ok = exists and (len(files) == 0 or n >= 1)
        if not entry_ok:
            all_ok = False
        detail[name] = {"ok": entry_ok, "files_expected": len(files), "files_local": n, "hash_local": head}
        total += n
    return Evidence(
        ok=all_ok,
        timestamp=datetime.now(timezone.utc).isoformat(),
        files_count=total,
        local_hashes={},
        repos=detail,
        notes="repos_listos check",
    )


def write_evidence(evidence: Evidence, out: str | Path = "evidence.json") -> None:
    Path(out).write_text(json.dumps(evidence.to_dict(), indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root_or_repos", type=Path, nargs="?", default=Path("."))
    ap.add_argument("--plan", type=Path, default=Path("plan.json"))
    ap.add_argument("--out", type=Path, default=Path("evidence.json"))
    ap.add_argument("--mode", choices=["mapped", "repos"], default="repos")
    args = ap.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8")) if args.plan.is_file() else {}
    if args.mode == "mapped":
        ev = verificar(args.root_or_repos, plan.get("mapped") or [])
    else:
        ev = verificar_repos_listos(args.root_or_repos, plan)
    write_evidence(ev, args.out)
    print(f"wrote {args.out} ok={ev.ok}")
    return 0 if ev.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
