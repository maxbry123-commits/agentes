#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import sys

SCHEMA = "yaiwes.repo-root-copy.v1"
ROOT_PREFIX = "➡️📂motores de descarga extracción copiado movimiento archivos "
SKILL_NAME = "➡️📂 skills descargar extraer zip copiar mover archivos readme.md"

ALLOWED_FILES = (
    SKILL_NAME,
    "➡️📂 Motor de extracción zip/motor_1_extract_only.py",
    "📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py",
    "📂Motor descarga de componentes y extracción de zip/hf_download_extract_engine.py",
    "➡️📂motor de copiar archivos/motor_3_copy_batches.py",
    "➡️📂motor de copiar archivos/motor_copy_root_to_repo.py",
    "➡️📂motor de moves archivos/motor_4_move_batches.py",
)

SOURCE_ROOT = pathlib.Path(os.getenv("SOURCE_ROOT", "")).expanduser()
DEST_ROOT = pathlib.Path(os.getenv("DEST_ROOT", "")).expanduser()
DEST_REPO_NAME = os.getenv("DEST_REPO_NAME", "").strip()
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "2"))


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fail(code: str, detail: str) -> None:
    raise SystemExit(json.dumps({
        "schema": SCHEMA,
        "verdict": code,
        "detail": detail,
    }, ensure_ascii=False, sort_keys=True))


def validate_inputs() -> None:
    if not str(SOURCE_ROOT):
        fail("SOURCE_INPUT_GAP", "SOURCE_ROOT is required")
    if not str(DEST_ROOT):
        fail("DESTINATION_INPUT_GAP", "DEST_ROOT is required")
    if not DEST_REPO_NAME:
        fail("DESTINATION_INPUT_GAP", "DEST_REPO_NAME is required")
    if not 1 <= BATCH_SIZE <= 100:
        fail("INPUT_GAP", "BATCH_SIZE must be 1..100")
    if not SOURCE_ROOT.is_dir():
        fail("SOURCE_INPUT_GAP", "SOURCE_ROOT does not exist")
    expected_name = ROOT_PREFIX + DEST_REPO_NAME
    if DEST_ROOT.name != expected_name:
        fail(
            "DESTINATION_NAME_GAP",
            f"DEST_ROOT name must be exactly: {expected_name}",
        )


def validate_source_allowlist() -> list[dict]:
    actual = sorted(
        p.relative_to(SOURCE_ROOT).as_posix()
        for p in SOURCE_ROOT.rglob("*")
        if p.is_file()
    )
    expected = sorted(ALLOWED_FILES)
    if actual != expected:
        fail(
            "SOURCE_ALLOWLIST_GAP",
            json.dumps({"expected": expected, "actual": actual}, ensure_ascii=False),
        )
    rows = []
    for rel in ALLOWED_FILES:
        path = SOURCE_ROOT / pathlib.PurePosixPath(rel)
        rows.append({
            "rel": rel,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return rows


def verify_existing_destination(rows: list[dict]) -> bool:
    if not DEST_ROOT.exists():
        return False
    actual = sorted(
        p.relative_to(DEST_ROOT).as_posix()
        for p in DEST_ROOT.rglob("*")
        if p.is_file()
    )
    if actual != sorted(ALLOWED_FILES):
        fail(
            "DESTINATION_COLLISION",
            "DEST_ROOT exists and does not match the strict allowlist",
        )
    for row in rows:
        dest = DEST_ROOT / pathlib.PurePosixPath(row["rel"])
        if sha256_file(dest) != row["sha256"]:
            fail("READBACK_HASH_MISMATCH", row["rel"])
    return True


def copy_batch(rows: list[dict], start: int) -> list[str]:
    copied = []
    for row in rows[start:start + BATCH_SIZE]:
        rel = pathlib.PurePosixPath(row["rel"])
        src = SOURCE_ROOT / rel
        dst = DEST_ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        partial = dst.with_name(dst.name + ".partial")
        if partial.exists():
            partial.unlink()
        shutil.copy2(src, partial)
        if sha256_file(partial) != row["sha256"]:
            partial.unlink(missing_ok=True)
            fail("COPY_HASH_MISMATCH", row["rel"])
        os.replace(partial, dst)
        if sha256_file(dst) != row["sha256"]:
            fail("READBACK_HASH_MISMATCH", row["rel"])
        copied.append(row["rel"])
    return copied


def main() -> None:
    validate_inputs()
    rows = validate_source_allowlist()

    if SOURCE_ROOT.resolve() == DEST_ROOT.resolve():
        fail("DESTINATION_INPUT_GAP", "SOURCE_ROOT and DEST_ROOT cannot be identical")

    if verify_existing_destination(rows):
        print(json.dumps({
            "schema": SCHEMA,
            "repo": DEST_REPO_NAME,
            "files": len(rows),
            "batch_size": BATCH_SIZE,
            "batches": 0,
            "verdict": "VERIFIED_EXISTING",
        }, ensure_ascii=False, sort_keys=True))
        return

    DEST_ROOT.mkdir(parents=True, exist_ok=False)
    copied: list[str] = []
    batches = 0
    try:
        for start in range(0, len(rows), BATCH_SIZE):
            copied.extend(copy_batch(rows, start))
            batches += 1

        actual = sorted(
            p.relative_to(DEST_ROOT).as_posix()
            for p in DEST_ROOT.rglob("*")
            if p.is_file()
        )
        if actual != sorted(ALLOWED_FILES):
            fail("DESTINATION_ALLOWLIST_GAP", "Final destination contains unexpected files")

        for row in rows:
            dest = DEST_ROOT / pathlib.PurePosixPath(row["rel"])
            if sha256_file(dest) != row["sha256"]:
                fail("READBACK_HASH_MISMATCH", row["rel"])

        print(json.dumps({
            "schema": SCHEMA,
            "repo": DEST_REPO_NAME,
            "files": len(rows),
            "batch_size": BATCH_SIZE,
            "batches": batches,
            "copied": len(copied),
            "failed": 0,
            "pending": 0,
            "verdict": "VERIFIED_CLOSED",
        }, ensure_ascii=False, sort_keys=True))
    except BaseException:
        shutil.rmtree(DEST_ROOT, ignore_errors=True)
        raise


if __name__ == "__main__":
    main()
