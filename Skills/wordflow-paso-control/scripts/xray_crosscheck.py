#!/usr/bin/env python3
"""X-Ray: reconstructed tree vs source_commit del MANIFEST.jsonl."""
from __future__ import annotations
import hashlib, json, subprocess, sys, shutil
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "Download code/archivos")
MANIFEST = ROOT / "RESEARCH_DOWNLOAD_MANIFEST.jsonl"
AUDIT = Path(sys.argv[2] if len(sys.argv) > 2 else "audit")
WORK_SRC = Path(sys.argv[3] if len(sys.argv) > 3 else "work/source")
AUDIT.mkdir(parents=True, exist_ok=True)
WORK_SRC.mkdir(parents=True, exist_ok=True)

SKIP = {".git", "__MACOSX", ".DS_Store"}

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def files(root: Path) -> dict[str, Path]:
    out = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP for part in p.parts):
            continue
        rel = p.relative_to(root).as_posix()
        out[rel] = p
    return out

def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)

if not MANIFEST.exists():
    print("FAIL: missing", MANIFEST)
    sys.exit(1)

rows = [json.loads(l) for l in MANIFEST.read_text().splitlines() if l.strip()]
global_fail = 0
for row in rows:
    slug = row["slug"]
    url = row["source"]
    commit = row.get("source_commit") or ""
    extracted = ROOT / slug
    src = WORK_SRC / slug
    print(f"##### X-RAY {slug} commit={commit}")
    if not extracted.is_dir():
        print("FAIL: reconstructed dir missing", extracted)
        global_fail = 1
        continue
    if src.exists():
        shutil.rmtree(src)
    run(["git", "clone", "--no-checkout", url, str(src)])
    if commit:
        run(["git", "fetch", "--depth", "1", "origin", commit], cwd=src)
        run(["git", "checkout", "--detach", commit], cwd=src)
    else:
        run(["git", "checkout", "HEAD"], cwd=src)
    ext = files(extracted)
    srcf = files(src)
    missing = sorted(set(srcf) - set(ext))
    extra = sorted(set(ext) - set(srcf))
    mismatch = []
    for rel in sorted(set(srcf) & set(ext)):
        if sha256(srcf[rel]) != sha256(ext[rel]):
            mismatch.append(rel)
    status = "PASS"
    if missing or extra or mismatch:
        status = "FAIL"
        global_fail = 1
    def ylist(key, items):
        if not items:
            return [f"{key}: []"]
        return [f"{key}:"] + [f"  - {x}" for x in items]
    lines = [
        f"slug: {slug}",
        f"source_commit: {commit}",
        f"status: {status}",
        f"extracted_count: {len(ext)}",
        f"source_count: {len(srcf)}",
    ]
    lines += ylist("missing", missing)
    lines += ylist("extra", extra)
    lines += ylist("sha_mismatch", mismatch)
    (AUDIT / f"{slug}.xray.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{status}: {slug} missing={len(missing)} extra={len(extra)} sha={len(mismatch)}")

(AUDIT / "GLOBAL.yaml").write_text(
    f"status: {'FAIL' if global_fail else 'PASS'}\nrepos: {len(rows)}\n",
    encoding="utf-8",
)
print("X-RAY RESULT:", "FAIL" if global_fail else "PASS")
sys.exit(global_fail)
