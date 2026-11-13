from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / 'package.json'
SCRIPT = ROOT / 'scripts' / 'extract-changelog-release.mjs'
EXPECTED = ['package.json', 'scripts', 'packages']


def source_probe() -> dict:
    missing=[x for x in EXPECTED if not (ROOT/x).exists()]
    if missing:
        raise RuntimeError('upstream markers missing: ' + ','.join(missing))
    if not SCRIPT.exists():
        raise RuntimeError('ClawHub dependency-free release CLI script missing')
    package = json.loads(PACKAGE.read_text())
    workspaces = package.get('workspaces') or []
    if 'packages/clawhub' not in workspaces or 'packages/schema' not in workspaces:
        raise RuntimeError('ClawHub workspace registry surface missing')
    return {
        'ok': True,
        'component': 'ClawHub',
        'classification': 'C',
        'package': package.get('name'),
        'workspaces': workspaces,
        'script': str(SCRIPT.resolve()),
    }


def runtime_command() -> list[str]:
    source_probe()
    return ['node', 'scripts/extract-changelog-release.mjs', '--help']


def runtime_cwd() -> str:
    return str(ROOT)
