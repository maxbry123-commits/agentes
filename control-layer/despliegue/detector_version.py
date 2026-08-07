"""detector_version.py v2 — semver por hash + CHANGELOG · 0% LLM
SOURCE: DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2 PASO 3
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def detect(staging: str | Path, previous: dict[str, str] | None = None) -> dict:
    """API legacy: un directorio plano."""
    stage = Path(staging)
    current: dict[str, str] = {}
    for p in stage.rglob("*"):
        if p.is_file() and ".git" not in p.parts:
            current[str(p.relative_to(stage))] = file_hash(p)
    prev = previous or {}
    added = [k for k in current if k not in prev]
    removed = [k for k in prev if k not in current]
    changed = [k for k in current if k in prev and current[k] != prev[k]]
    if removed:
        bump = "major"
    elif added:
        bump = "minor"
    elif changed:
        bump = "patch"
    else:
        bump = "none"
    return {"bump": bump, "added": added, "removed": removed, "changed": changed, "hashes": current}


def snapshot(repo: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in repo.rglob("*"):
        if not p.is_file() or ".git" in p.parts:
            continue
        if p.name in ("VERSION", "CHANGELOG.md", ".version_prev.json"):
            continue
        out[str(p.relative_to(repo))] = file_hash(p)
    return out


def parse_ver(s: str) -> tuple[int, int, int]:
    parts = (s or "0.1.0").strip().split(".")
    while len(parts) < 3:
        parts.append("0")
    return int(parts[0] or 0), int(parts[1] or 0), int(parts[2] or 0)


def fmt(v: tuple[int, int, int]) -> str:
    return f"{v[0]}.{v[1]}.{v[2]}"


def apply_bump(ver: tuple[int, int, int], kind: str) -> tuple[int, int, int]:
    major, minor, patch = ver
    if kind == "major":
        return major + 1, 0, 0
    if kind == "minor":
        return major, minor + 1, 0
    if kind == "patch":
        return major, minor, patch + 1
    return ver


def process_repo(repo: Path) -> dict:
    curr = snapshot(repo)
    prev_path = repo / ".version_prev.json"
    ver_path = repo / "VERSION"
    prev = json.loads(prev_path.read_text(encoding="utf-8")) if prev_path.is_file() else {}
    d = detect(repo, prev)
    kind = d["bump"]
    notes = []
    if d["removed"]:
        notes.append(f"removed: {d['removed']}")
    if d["added"]:
        notes.append(f"added: {d['added']}")
    if d["changed"]:
        notes.append(f"changed: {d['changed']}")
    if not notes:
        notes.append("no changes")
    old = parse_ver(ver_path.read_text(encoding="utf-8") if ver_path.is_file() else "0.1.0")
    new = apply_bump(old, kind)
    ver_path.write_text(fmt(new) + "\n", encoding="utf-8")
    prev_path.write_text(json.dumps(curr, indent=2), encoding="utf-8")
    cl = repo / "CHANGELOG.md"
    entry = f"## {fmt(new)} ({kind})\n" + "\n".join(f"- {n}" for n in notes) + "\n\n"
    prev_cl = cl.read_text(encoding="utf-8") if cl.is_file() else "# CHANGELOG\n\n"
    cl.write_text(entry + prev_cl, encoding="utf-8")
    return {"repo": repo.name, "version": fmt(new), "kind": kind, "notes": notes}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repos_dir", type=Path, nargs="?", default=Path("repos_listos"))
    args = ap.parse_args()
    if not args.repos_dir.is_dir():
        print("missing repos_dir")
        return 1
    results = [process_repo(c) for c in sorted(args.repos_dir.iterdir()) if c.is_dir()]
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
