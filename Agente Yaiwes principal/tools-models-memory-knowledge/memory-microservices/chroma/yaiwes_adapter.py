from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = ['pyproject.toml', 'chromadb']
RUNTIME_COMMAND = ['python', '-m', 'compileall', '-q', 'chromadb']

def source_probe() -> dict:
    missing=[x for x in EXPECTED if not (ROOT/x).exists()]
    if missing:
        raise RuntimeError("upstream markers missing: " + ",".join(missing))
    return {"ok": True, "root": str(ROOT), "markers": EXPECTED}

def runtime_command() -> list[str]:
    return list(RUNTIME_COMMAND)

def runtime_cwd() -> str:
    return str(ROOT)
