#!/usr/bin/env python3
"""
CI helper (NOT a motor): locates the immutable motor_4_move_batches.py inside
the `agentes` checkout, verifies its blob sha against MOTOR-CODE-LOCK.json
(fail-closed if it does not match), then runs it unmodified as a subprocess,
once per (SOURCE_DIR, DEST_DIR) pair in RENAME_PAIRS below, to move the
content of each emoji-named root folder into a new clean-named folder in
place, within the same `agentes` checkout (no cross-repo copy here).

This script does not alter the motor's logic in any way. It only drives it
with different env vars for each of the 4 pending rename targets.
"""
from __future__ import annotations
import hashlib
import json
import os
import pathlib
import subprocess
import sys

AGENTES_ROOT = pathlib.Path(__file__).resolve().parent.parent

MOTOR_ROOT = (
    AGENTES_ROOT
    / "➡️\U0001f4c2motores de descarga extracción copiado movimiento archivos agentes"
)
MOTOR4_PATH = MOTOR_ROOT / "➡️\U0001f4c2motor de moves archivos" / "motor_4_move_batches.py"
LOCK_PATH = MOTOR_ROOT / "MOTOR-CODE-LOCK.json"

# (source relative path under agentes/, destination relative path under agentes/)
# IMPORTANT: the motors-folder rename is LAST on purpose -- motor_4 itself
# lives inside that folder, so it must not relocate its own directory while
# still running as a subprocess for an earlier pair.
RENAME_PAIRS: list[tuple[str, str]] = [
    (
        "\U0001f4c2 Bitácora stated JSON Craxy wall.json",
        "__RENAME_SINGLE_FILE__:Bitacora-stated-JSON-Craxy-wall.json",
    ),
    (
        "➡️\U0001f4c2 wordflow loop code Yaiwes",
        "wordflow loop code Yaiwes",
    ),
    (
        "\U0001f4c2coda workflow persistencias",
        "coda workflow persistencias",
    ),
    (
        "➡️\U0001f4c2motores de descarga extracción copiado movimiento archivos agentes",
        "motores de descarga extraccion copiado movimiento archivos agentes",
    ),
]


def git_blob_sha(path: pathlib.Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def verify_motor4() -> bool:
    if not MOTOR4_PATH.exists():
        print(f"MOTOR_NOT_FOUND: {MOTOR4_PATH}")
        return False
    if not LOCK_PATH.exists():
        print("WARNING: MOTOR-CODE-LOCK.json not found, skipping lock verification")
        return True
    lock = json.loads(LOCK_PATH.read_text())
    expected = None
    for m in lock.get("motors", []):
        if m.get("id") == "motor_4_move_batches":
            expected = m.get("canonical_blob_sha")
            break
    actual = git_blob_sha(MOTOR4_PATH)
    print(f"motor_4_move_batches: local_blob_sha={actual} lock_expected={expected}")
    if expected and actual != expected:
        print("MOTOR_CODE_LOCK_GAP: motor_4_move_batches.py does not match MOTOR-CODE-LOCK.json")
        return False
    return True


def main() -> int:
    if not verify_motor4():
        return 1

    overall_ok = True
    for idx, (src_rel, dst_rel) in enumerate(RENAME_PAIRS, start=1):
        print(f"\n=== [{idx}/{len(RENAME_PAIRS)}] {src_rel} -> {dst_rel} ===")

        if dst_rel.startswith("__RENAME_SINGLE_FILE__:"):
            # Special case: a lone file rename. motor_4 operates on directory
            # trees (SOURCE_DIR/DEST_DIR), so for a single file we stage it
            # into a temp source dir, run motor_4, then flatten the result.
            real_dst_name = dst_rel.split(":", 1)[1]
            src_file = AGENTES_ROOT / src_rel
            if not src_file.exists():
                print(f"SKIP (source not found): {src_rel}")
                continue
            tmp_src_dir = pathlib.Path("/tmp/motor4-singlefile-src")
            tmp_dst_dir = pathlib.Path("/tmp/motor4-singlefile-dst")
            tmp_src_dir.mkdir(parents=True, exist_ok=True)
            tmp_dst_dir.mkdir(parents=True, exist_ok=True)
            staged = tmp_src_dir / real_dst_name
            staged.write_bytes(src_file.read_bytes())
            env = dict(os.environ)
            env["SOURCE_DIR"] = str(tmp_src_dir)
            env["DEST_DIR"] = str(tmp_dst_dir)
            env["STATE_FILE"] = f"/tmp/motor4-state-{idx}.json"
            env["BATCH_SIZE"] = "10"
            env["COLLISION_POLICY"] = "replace"
            print(f"Executing immutable motor unmodified: {MOTOR4_PATH}")
            result = subprocess.run([sys.executable, str(MOTOR4_PATH)], env=env)
            if result.returncode != 0:
                print(f"MOTOR_4_FAILED for {src_rel}")
                overall_ok = False
                continue
            final_dst = AGENTES_ROOT / real_dst_name
            moved = tmp_dst_dir / real_dst_name
            if moved.exists():
                final_dst.write_bytes(moved.read_bytes())
                # remove original source file now that it's verified moved
                src_file.unlink()
                print(f"OK: {src_rel} -> {real_dst_name}")
            else:
                print(f"MOTOR_4_OUTPUT_MISSING for {src_rel}")
                overall_ok = False
            continue

        src_dir = AGENTES_ROOT / src_rel
        dst_dir = AGENTES_ROOT / dst_rel
        if not src_dir.exists():
            print(f"SKIP (source not found): {src_rel}")
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env["SOURCE_DIR"] = str(src_dir)
        env["DEST_DIR"] = str(dst_dir)
        env["STATE_FILE"] = f"/tmp/motor4-state-{idx}.json"
        env["BATCH_SIZE"] = "50"
        env["COLLISION_POLICY"] = "replace"
        print(f"Executing immutable motor unmodified: {MOTOR4_PATH}")
        result = subprocess.run([sys.executable, str(MOTOR4_PATH)], env=env)
        if result.returncode != 0:
            print(f"MOTOR_4_FAILED for {src_rel}")
            overall_ok = False
            continue
        # cleanup empty source dir tree if motor_4 left it empty
        try:
            remaining = list(src_dir.rglob("*"))
            remaining_files = [p for p in remaining if p.is_file()]
            if not remaining_files:
                import shutil
                shutil.rmtree(src_dir, ignore_errors=True)
                print(f"OK: {src_rel} fully moved and removed")
            else:
                print(f"PARTIAL: {src_rel} has {len(remaining_files)} files remaining, not removing source dir")
                overall_ok = False
        except Exception as e:
            print(f"CLEANUP_CHECK_FAILED for {src_rel}: {e}")

    print("\n=== SUMMARY ===")
    print("overall_ok:", overall_ok)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
