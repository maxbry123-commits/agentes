#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, pathlib, shutil

SCHEMA = "yaiwes.frontend.move-batches.v1"
SOURCE_DIR = pathlib.Path(os.getenv("SOURCE_DIR", "")).expanduser()
DEST_DIR = pathlib.Path(os.getenv("DEST_DIR", "")).expanduser()
STATE_FILE = pathlib.Path(os.getenv("STATE_FILE", ".motor4-move-state.json")).expanduser()
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "25"))
COLLISION_POLICY = os.getenv("COLLISION_POLICY", "fail").lower()
MAX_BATCHES = int(os.getenv("MAX_BATCHES", "0"))


def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def first_manifest():
    if not SOURCE_DIR.is_dir():
        raise RuntimeError("SOURCE_DIR_NOT_FOUND")
    rows = []
    for p in sorted((x for x in SOURCE_DIR.rglob("*") if x.is_file()), key=lambda x: x.relative_to(SOURCE_DIR).as_posix()):
        if p.resolve() == STATE_FILE.resolve():
            continue
        rows.append({"rel": p.relative_to(SOURCE_DIR).as_posix(), "bytes": p.stat().st_size, "sha256": sha256_file(p)})
    return rows


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"schema": SCHEMA, "manifest": first_manifest(), "completed": {}, "failed": {}, "batches": 0}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_name(STATE_FILE.name + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, STATE_FILE)


def move_verified(row):
    rel = pathlib.PurePosixPath(row["rel"]); src = SOURCE_DIR / rel; dst = DEST_DIR / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        if dst.exists() and sha256_file(dst) == row["sha256"]:
            return "VERIFIED_EXISTING_AFTER_MOVE"
        raise RuntimeError("SOURCE_MISSING_AND_DEST_UNVERIFIED:" + row["rel"])
    if sha256_file(src) != row["sha256"]:
        raise RuntimeError("SOURCE_CHANGED:" + row["rel"])
    if dst.exists():
        dsha = sha256_file(dst)
        if dsha == row["sha256"]:
            src.unlink(); return "DEST_IDENTICAL_SOURCE_REMOVED"
        if COLLISION_POLICY == "skip":
            return "SKIPPED_COLLISION"
        if COLLISION_POLICY != "replace":
            raise RuntimeError("DESTINATION_COLLISION:" + row["rel"])
    tmp = dst.with_name(dst.name + ".moving")
    if tmp.exists(): tmp.unlink()
    shutil.move(str(src), str(tmp))
    if sha256_file(tmp) != row["sha256"]:
        if not src.exists(): shutil.move(str(tmp), str(src))
        raise RuntimeError("MOVE_HASH_MISMATCH:" + row["rel"])
    os.replace(tmp, dst)
    if sha256_file(dst) != row["sha256"]:
        raise RuntimeError("READBACK_HASH_MISMATCH:" + row["rel"])
    return "MOVED_VERIFIED"


def cleanup_empty_dirs():
    if not SOURCE_DIR.exists(): return
    for d in sorted((x for x in SOURCE_DIR.rglob("*") if x.is_dir()), key=lambda x: len(x.parts), reverse=True):
        try: d.rmdir()
        except OSError: pass


def main():
    if not 1 <= BATCH_SIZE <= 100:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "BATCH_SIZE must be 1..100"}))
    if COLLISION_POLICY not in {"fail", "skip", "replace"}:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "COLLISION_POLICY must be fail|skip|replace"}))
    if not str(SOURCE_DIR) or not str(DEST_DIR):
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "SOURCE_DIR and DEST_DIR required"}))
    state = load_state(); completed = state.setdefault("completed", {}); batches = 0
    while True:
        pending = [r for r in state["manifest"] if r["rel"] not in completed]
        if not pending or (MAX_BATCHES and batches >= MAX_BATCHES): break
        for row in pending[:BATCH_SIZE]:
            try:
                status = move_verified(row); completed[row["rel"]] = status; state.setdefault("failed", {}).pop(row["rel"], None)
            except Exception as e:
                state.setdefault("failed", {})[row["rel"]] = str(e)
        batches += 1; state["batches"] = state.get("batches", 0) + 1; save_state(state)
        if state.get("failed") and COLLISION_POLICY == "fail": break
    cleanup_empty_dirs()
    total = len(state["manifest"]); done = len(completed); failed = len(state.get("failed", {})); pending_count = total - done
    source_remaining = sum(1 for p in SOURCE_DIR.rglob("*") if p.is_file()) if SOURCE_DIR.exists() else 0
    result = {
        "schema": SCHEMA, "batch_size": BATCH_SIZE, "collision_policy": COLLISION_POLICY,
        "total": total, "moved_or_verified": done, "failed": failed, "pending": pending_count,
        "source_files_remaining": source_remaining, "batches_total": state.get("batches", 0),
        "state_file": str(STATE_FILE), "verdict": "VERIFIED_CLOSED" if pending_count == 0 and failed == 0 else "GAPS_PENDING"
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__": main()
