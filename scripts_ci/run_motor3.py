#!/usr/bin/env python3
"""
CI helper (NOT a motor): locates the immutable motor_3_copy_batches.py inside
the `agentes` checkout, verifies its blob sha against MOTOR-CODE-LOCK.json
(fail-closed if it does not match), then runs it unmodified as a subprocess
with the SOURCE_DIR/DEST_DIR/etc. environment variables the workflow already
set. This script never embeds the motor's emoji-heavy path in a shell
command line, which is what caused a prior workflow-file write to fail.

This script does not alter the motor's logic in any way.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import subprocess
import sys

AGENTES_ROOT = pathlib.Path(__file__).resolve().parent.parent

MOTOR_ROOT = (
    AGENTES_ROOT
    / "➡️\U0001f4c2motores de descarga extracción copiado movimiento archivos agentes"
)
MOTOR3_PATH = MOTOR_ROOT / "➡️\U0001f4c2motor de copiar archivos" / "motor_3_copy_batches.py"
LOCK_PATH = MOTOR_ROOT / "MOTOR-CODE-LOCK.json"


def git_blob_sha(path: pathlib.Path) -> str:
    # Reproduces `git hash-object <file>` without shelling out with the
    # emoji path (avoids any quoting edge cases): git's blob sha is
    # sha1("blob " + len(content) + "\0" + content).
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    if not MOTOR3_PATH.exists():
        print(f"MOTOR_NOT_FOUND: {MOTOR3_PATH}")
        return 1

    if LOCK_PATH.exists():
        lock = json.loads(LOCK_PATH.read_text())
        expected = None
        for m in lock.get("motors", []):
            if m.get("id") == "motor_3_copy_batches":
                expected = m.get("canonical_blob_sha")
                break
        actual = git_blob_sha(MOTOR3_PATH)
        print(f"motor_3_copy_batches: local_blob_sha={actual} lock_expected={expected}")
        if expected and actual != expected:
            print("MOTOR_CODE_LOCK_GAP: motor_3_copy_batches.py does not match MOTOR-CODE-LOCK.json")
            return 1
    else:
        print("WARNING: MOTOR-CODE-LOCK.json not found, skipping lock verification")

    print(f"Executing immutable motor unmodified: {MOTOR3_PATH}")
    result = subprocess.run([sys.executable, str(MOTOR3_PATH)])
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
