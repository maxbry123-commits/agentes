from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALIDATOR = ROOT / 'internal' / 'validator'
EXPECTED = ['go.mod', 'internal']


def source_probe() -> dict:
    missing=[x for x in EXPECTED if not (ROOT/x).exists()]
    if missing:
        raise RuntimeError('upstream markers missing: ' + ','.join(missing))
    if not VALIDATOR.is_dir():
        raise RuntimeError('Cerbos validator package missing')
    return {
        'ok': True,
        'component': 'Cerbos',
        'classification': 'C',
        'root': str(ROOT),
        'validator': str(VALIDATOR.resolve()),
    }


def runtime_command() -> list[str]:
    source_probe()
    return ['go', 'test', './internal/validator']


def runtime_cwd() -> str:
    return str(ROOT)
