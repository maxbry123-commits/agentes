#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, subprocess, sys, shutil
from pathlib import Path
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "Download code/archivos")
MANIFEST = ROOT / "RESEARCH_DOWNLOAD_MANIFEST.jsonl"
AUDIT = Path(sys.argv[2] if len(sys.argv) > 2 else "audit")
WORK_SRC = Path(sys.argv[3] if len(sys.argv) > 3 else "work/source")
AUDIT.mkdir(parents=True, exist_ok=True)
WORK_SRC.mkdir(parents=True, exist_ok=True)
SKIP_DIR = {".git", "__MACOSX", ".DS_Store"}
SKIP_NAME = {"SPLIT_FILES.json"}

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def reassemble(extracted: Path) -> None:
    for split in extracted.rglob("SPLIT_FILES.json"):
        try:
            records = json.loads(split.read_text())
        except Exception:
            continue
        if not isinstance(records, list):
            continue
        for rec in records:
            rel = rec.get("path")
            cdir = rec.get("chunks_dir")
            if not rel or not cdir:
                continue
            chunks = extracted / cdir
            if not chunks.is_dir():
                chunks = extracted / Path(rel).parent / (Path(rel).name + ".chunks")
            parts = sorted(chunks.glob("*.part-*")) if chunks.is_dir() else []
            if not parts:
                continue
            dest = extracted / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("wb") as out:
                for p in parts:
                    out.write(p.read_bytes())

def files(root: Path):
    out = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIR or part.endswith(".chunks") for part in p.parts):
            continue
        if p.name in SKIP_NAME:
            continue
        out[p.relative_to(root).as_posix()] = p
    return out

def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)

if not MANIFEST.exists():
    print("FAIL missing", MANIFEST)
    sys.exit(1)
rows = [json.loads(l) for l in MANIFEST.read_text().splitlines() if l.strip()]
fail = 0
for row in rows:
    slug = row["slug"]
    url = row["source"]
    commit = row.get("source_commit") or ""
    extracted = ROOT / slug
    src = WORK_SRC / slug
    print(f"##### X-RAY {slug} {commit}")
    if not extracted.is_dir():
        print("FAIL reconstructed missing", extracted)
        fail = 1
        continue
    reassemble(extracted)
    if src.exists():
        shutil.rmtree(src)
    run(["git", "clone", "--no-checkout", url, str(src)])
    if commit:
        run(["git", "fetch", "--depth", "1", "origin", commit], cwd=src)
        run(["git", "checkout", "--detach", commit], cwd=src)
    ext = files(extracted)
    srcf = files(src)
    missing = sorted(set(srcf) - set(ext))
    extra = sorted(set(ext) - set(srcf))
    mismatch = [rel for rel in sorted(set(srcf) & set(ext)) if sha256(srcf[rel]) != sha256(ext[rel])]
    status = "FAIL" if missing or extra or mismatch else "PASS"
    if status == "FAIL":
        fail = 1
    def ylist(k, items):
        return [f"{k}: []"] if not items else [f"{k}:"] + [f"  - {x}" for x in items]
    lines = [f"slug: {slug}", f"source_commit: {commit}", f"status: {status}",
             f"extracted_count: {len(ext)}", f"source_count: {len(srcf)}"]
    lines += ylist("missing", missing) + ylist("extra", extra) + ylist("sha_mismatch", mismatch)
    (AUDIT / f"{slug}.xray.yaml").write_text("\n".join(lines) + "\n")
    print(f"{status}: {slug} missing={len(missing)} extra={len(extra)} sha={len(mismatch)}")
(AUDIT / "GLOBAL.yaml").write_text(f"status: {'FAIL' if fail else 'PASS'}\nrepos: {len(rows)}\n")
print("X-RAY RESULT:", "FAIL" if fail else "PASS")
sys.exit(fail)
