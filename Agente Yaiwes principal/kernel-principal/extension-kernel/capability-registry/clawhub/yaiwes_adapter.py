from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = ['package.json', 'scripts', 'packages']
RUNTIME_COMMAND = ['node', 'scripts/check-release-workflow-action-pins.mjs']

def source_probe() -> dict:
    missing=[x for x in EXPECTED if not (ROOT/x).exists()]
    if missing:
        raise RuntimeError("upstream markers missing: " + ",".join(missing))
    return {"ok": True, "root": str(ROOT), "markers": EXPECTED}

def runtime_command() -> list[str]:
    return list(RUNTIME_COMMAND)

def runtime_cwd() -> str:
    return str(ROOT)
