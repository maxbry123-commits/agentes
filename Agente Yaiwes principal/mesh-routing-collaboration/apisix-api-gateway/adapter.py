from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent
CLI = ROOT / "bin" / "apisix"


def _exec(args: Sequence[str], *, timeout: int = 30) -> dict:
    if not CLI.is_file():
        raise RuntimeError(f"APISIX CLI missing: {CLI}")
    proc = subprocess.run(
        [str(CLI), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    result = {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }
    if proc.returncode != 0:
        raise RuntimeError(f"APISIX fail-closed: {result}")
    return result


def version() -> dict:
    return _exec(["version"])


def verify_config() -> dict:
    return _exec(["test"])
