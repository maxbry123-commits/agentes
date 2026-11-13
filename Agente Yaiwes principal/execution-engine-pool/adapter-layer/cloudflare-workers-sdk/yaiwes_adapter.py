from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
ROOT_PACKAGE = ROOT / 'package.json'
WRANGLER_PACKAGE = ROOT / 'packages' / 'wrangler' / 'package.json'
WRANGLER_BIN = ROOT / 'packages' / 'wrangler' / 'bin' / 'wrangler.js'


def source_probe() -> dict:
    for path in (ROOT_PACKAGE, WRANGLER_PACKAGE, WRANGLER_BIN):
        if not path.exists():
            raise RuntimeError(f'Cloudflare Workers SDK required surface missing: {path}')
    root_pkg = json.loads(ROOT_PACKAGE.read_text())
    wrangler_pkg = json.loads(WRANGLER_PACKAGE.read_text())
    if root_pkg.get('name') != '@cloudflare/workers-sdk':
        raise RuntimeError('unexpected Workers SDK root package')
    if wrangler_pkg.get('name') != 'wrangler':
        raise RuntimeError('wrangler package surface missing')
    if (wrangler_pkg.get('bin') or {}).get('wrangler') != './bin/wrangler.js':
        raise RuntimeError('wrangler CLI entrypoint mismatch')
    return {
        'ok': True,
        'component': 'Cloudflare-Workers-SDK',
        'package': root_pkg.get('name'),
        'wrangler_version': wrangler_pkg.get('version'),
        'entrypoint': str(WRANGLER_BIN.resolve()),
    }


def runtime_command() -> list[str]:
    source_probe()
    return ['node', '--check', 'packages/wrangler/bin/wrangler.js']


def runtime_cwd() -> str:
    return str(ROOT)
