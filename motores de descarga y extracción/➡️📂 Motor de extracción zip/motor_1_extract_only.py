#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, pathlib, shutil, stat, tempfile, zipfile

SCHEMA = "yaiwes.frontend.extract-only.v1"
ARCHIVE_INPUT = pathlib.Path(os.getenv("ARCHIVE_INPUT", "")).expanduser()
DEST_DIR = pathlib.Path(os.getenv("DEST_DIR", "")).expanduser()
STATE_FILE = pathlib.Path(os.getenv("STATE_FILE", ".motor1-extract-state.json")).expanduser()
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "25"))
MAX_BATCHES = int(os.getenv("MAX_BATCHES", "0"))


def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def tree_hash(root: pathlib.Path):
    h = hashlib.sha256(); files = 0; total = 0
    for p in sorted((x for x in root.rglob("*") if x.is_file()), key=lambda x: x.relative_to(root).as_posix()):
        rel = p.relative_to(root).as_posix(); digest = sha256_file(p); size = p.stat().st_size
        h.update(rel.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\0" + str(size).encode("ascii") + b"\n")
        files += 1; total += size
    return {"files": files, "bytes": total, "sha256": h.hexdigest()}


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"schema": SCHEMA, "completed": [], "failed": {}, "batches": 0}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_name(STATE_FILE.name + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, STATE_FILE)


def build_archive() -> tuple[pathlib.Path, pathlib.Path | None]:
    if ARCHIVE_INPUT.is_file():
        return ARCHIVE_INPUT, None
    if not ARCHIVE_INPUT.is_dir():
        raise RuntimeError("ARCHIVE_INPUT_NOT_FOUND")
    parts = sorted(ARCHIVE_INPUT.glob("*.zip.part-*"))
    if not parts:
        zips = sorted(ARCHIVE_INPUT.glob("*.zip"))
        if len(zips) != 1:
            raise RuntimeError("ARCHIVE_GROUP_AMBIGUOUS")
        return zips[0], None
    td = pathlib.Path(tempfile.mkdtemp(prefix="motor1-rebuild-"))
    rebuilt = td / "reconstructed.zip"
    with rebuilt.open("wb") as w:
        for p in parts:
            with p.open("rb") as r:
                shutil.copyfileobj(r, w, 1024 * 1024)
    return rebuilt, td


def safe_members(z: zipfile.ZipFile):
    out = []
    for info in z.infolist():
        name = info.filename.replace("\\", "/")
        pp = pathlib.PurePosixPath(name)
        if not name or name.startswith("/") or ".." in pp.parts:
            raise RuntimeError("UNSAFE_ZIP_PATH:" + name)
        mode = (info.external_attr >> 16) & 0o170000
        if mode == stat.S_IFLNK:
            raise RuntimeError("UNSAFE_ZIP_SYMLINK:" + name)
        if info.is_dir():
            continue
        out.append(info)
    return out


def extract_one(z: zipfile.ZipFile, info: zipfile.ZipInfo):
    target = DEST_DIR / pathlib.PurePosixPath(info.filename)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".partial")
    with z.open(info, "r") as src, tmp.open("wb") as dst:
        shutil.copyfileobj(src, dst, 1024 * 1024)
    os.replace(tmp, target)


def main():
    if not 1 <= BATCH_SIZE <= 100:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "BATCH_SIZE must be 1..100"}))
    if not str(ARCHIVE_INPUT) or not str(DEST_DIR):
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "ARCHIVE_INPUT and DEST_DIR required"}))
    archive, cleanup = build_archive(); DEST_DIR.mkdir(parents=True, exist_ok=True)
    state = load_state(); completed = set(state.get("completed", [])); batches = 0
    try:
        with zipfile.ZipFile(archive) as z:
            bad = z.testzip()
            if bad:
                raise RuntimeError("ZIP_CRC_FAIL:" + bad)
            members = safe_members(z); names = [i.filename for i in members]
            while True:
                pending = [i for i in members if i.filename not in completed]
                if not pending or (MAX_BATCHES and batches >= MAX_BATCHES):
                    break
                batch = pending[:BATCH_SIZE]
                for info in batch:
                    try:
                        extract_one(z, info); completed.add(info.filename); state.setdefault("failed", {}).pop(info.filename, None)
                    except Exception as e:
                        state.setdefault("failed", {})[info.filename] = str(e)
                batches += 1; state["batches"] = state.get("batches", 0) + 1; state["completed"] = sorted(completed); save_state(state)
        pending_count = len([n for n in names if n not in completed])
        result = {
            "schema": SCHEMA,
            "archive": str(ARCHIVE_INPUT),
            "batch_size": BATCH_SIZE,
            "total_members": len(names),
            "extracted_verified": len(completed),
            "pending": pending_count,
            "failed": len(state.get("failed", {})),
            "tree": tree_hash(DEST_DIR),
            "state_file": str(STATE_FILE),
            "verdict": "VERIFIED_CLOSED" if pending_count == 0 and not state.get("failed") else "GAPS_PENDING"
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    finally:
        if cleanup:
            shutil.rmtree(cleanup, ignore_errors=True)

if __name__ == "__main__":
    main()
