#!/usr/bin/env python3
from __future__ import annotations
import ast
import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name('yaiwes_internal_surgical_transform_v5.py')
spec = importlib.util.spec_from_file_location('yaiwes_internal_surgical_transform_v5_module', SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit('V5_IMPORT_FAILED')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

FORBIDDEN_ROOTS = {'subprocess','requests','httpx','aiohttp','socket'}
FORBIDDEN_NAMES = {'eval','exec'}
FORBIDDEN_ATTRS = {('os','system'),('os','popen')}

def call_name(node):
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        left = call_name(node.value)
        return left + (node.attr,) if left else (node.attr,)
    return ()

def python_forbidden_calls(text):
    tree = ast.parse(text)
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node.func)
        if not name:
            continue
        if name[0] in FORBIDDEN_ROOTS or name[-1] in FORBIDDEN_NAMES or tuple(name[:2]) in FORBIDDEN_ATTRS:
            hits.append('.'.join(name))
    return hits

def validate(manifests):
    errors = []
    if len(manifests) != 24:
        errors.append(f'COMPONENT_COUNT:{len(manifests)}')
    for m in manifests:
        comp = mod.ROOT / m['component']
        code = comp / 'code'
        for x in m['files']:
            active = code / x['path']
            q = code / x['quarantine'] if x.get('quarantine') else None
            if not active.is_file():
                errors.append(f"MISSING_ACTIVE:{m['component']}:{x['path']}")
                continue
            at = mod.read_text(active)
            if at is None:
                continue
            if mod.sha256_text(at) != x['active_sha256']:
                errors.append(f"ACTIVE_SHA:{m['component']}:{x['path']}")
            if q and not q.is_file():
                errors.append(f"MISSING_QUARANTINE:{m['component']}:{x['path']}")
            if x['decision'] == 'RESTORE_BENIGN' and mod.sha256_text(at) != x['original_sha256']:
                errors.append(f"BENIGN_NOT_RESTORED:{m['component']}:{x['path']}")
            if x['decision'] in {'BLOCK_OFFENSIVE','REVIEW_FAIL_CLOSED'}:
                if active.suffix.lower() == '.py':
                    try:
                        hits = python_forbidden_calls(at)
                    except SyntaxError as e:
                        errors.append(f"PY_SYNTAX:{m['component']}:{x['path']}:{e.lineno}")
                        continue
                    if hits:
                        errors.append(f"PY_FORBIDDEN_CALL:{m['component']}:{x['path']}:{','.join(hits[:3])}")
                elif any(marker in at.lower() for marker in mod.EXEC_MARKERS):
                    errors.append(f"RESIDUAL_EXECUTION:{m['component']}:{x['path']}")
        if not (code / 'yaiwes_internal' / 'persistence_runtime.py').is_file():
            errors.append(f"NO_RUNTIME:{m['component']}")
    return errors

mod.validate = validate
mod.main()
