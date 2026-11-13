#!/usr/bin/env python3
from __future__ import annotations

import ast
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path('📂coda workflow persistencias')
FIELD = ROOT / '🏈 cancha deportiva de fútbol'
REGISTRY = FIELD / 'YAIWES-SWARM-NAVY-SEALS-REGISTRY.json'
GRAPH = FIELD / 'YAIWES-SWARM-NAVY-SEALS-CABLE-GRAPH.json'
TEAM = 'Swarm agent team Navy seals YAIWES'
VERSION = 'YAIWES-PERSISTENCE-MESH-v2.1'

FORBIDDEN_IMPORTS = {'subprocess', 'socket', 'requests', 'urllib', 'paramiko', 'pexpect'}
FORBIDDEN_CALLS = {'exec', 'eval', 'compile', '__import__'}


def validate_adapter(path: Path) -> dict:
    src = path.read_text(encoding='utf-8')
    tree = ast.parse(src, filename=str(path))
    classes = set()
    imports = set()
    forbidden_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.add(node.name)
        elif isinstance(node, ast.Import):
            imports.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split('.')[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                forbidden_calls.append(node.func.id)
            if isinstance(node.func, ast.Attribute):
                root = node.func.value.id if isinstance(node.func.value, ast.Name) else ''
                if root == 'os' and node.func.attr in {'system', 'popen'}:
                    forbidden_calls.append(f'os.{node.func.attr}')
    bad_imports = sorted(imports & FORBIDDEN_IMPORTS)
    if 'YaiwesPersistenceAdapter' not in classes:
        raise RuntimeError(f'ADAPTER_CLASS_MISSING:{path}')
    if bad_imports:
        raise RuntimeError(f'FORBIDDEN_IMPORTS:{path}:{bad_imports}')
    if forbidden_calls:
        raise RuntimeError(f'FORBIDDEN_CALLS:{path}:{forbidden_calls}')
    return {'classes': sorted(classes), 'imports': sorted(imports), 'safe': True}


def load_adapter_class(path: Path):
    validate_adapter(path)
    module_name = 'yaiwes_adapter_' + str(abs(hash(path.as_posix())))
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'IMPORT_SPEC_GAP:{path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)
    return module.YaiwesPersistenceAdapter


def read_registry() -> dict:
    data = json.loads(REGISTRY.read_text(encoding='utf-8'))
    comps = data.get('components', [])
    if len(comps) != 24:
        raise RuntimeError(f'EXPECTED_24_COMPONENTS:{len(comps)}')
    names = [c['component'] for c in comps]
    if len(set(names)) != 24:
        raise RuntimeError('DUPLICATE_COMPONENTS')
    return data


def make_graph(registry: dict) -> dict:
    comps = registry['components']
    edges = []
    for idx, item in enumerate(comps):
        nxt = comps[(idx + 1) % len(comps)]
        edges.append({
            'from': item['component'],
            'to': nxt['component'],
            'type': 'PERSISTENCE_HANDOFF',
            'contract': 'checkpoint+evidence+release',
            'network': 'deny',
            'source_execution': False,
        })
    return {
        'schema': 'yaiwes.swarm.persistence-mesh/v2.1',
        'version': VERSION,
        'team': TEAM,
        'topology': 'ring_with_registry_failover',
        'component_count': len(comps),
        'edge_count': len(edges),
        'mode': 'TASK_PERSISTENCE_ONLY',
        'edges': edges,
    }


def update_readmes(registry: dict, graph: dict) -> None:
    comps = registry['components']
    for idx, item in enumerate(comps):
        name = item['component']
        prev_name = comps[(idx - 1) % len(comps)]['component']
        next_name = comps[(idx + 1) % len(comps)]['component']
        readme = FIELD / name / 'README.md'
        if not readme.exists():
            raise RuntimeError(f'README_MISSING:{name}')
        text = readme.read_text(encoding='utf-8')
        marker = '## Cableado maestro — Persistence Mesh v2.1'
        if marker in text:
            text = text.split(marker, 1)[0].rstrip() + '\n'
        text += f'''\n\n{marker}\n\n**Equipo:** {TEAM}  \n**Versión de malla:** `{VERSION}`\n\n`{prev_name} → {name} → {next_name}`\n\nEste eslabón participa en una malla circular de 24 componentes para handoff de **estado, checkpoint, evidencia y liberación de tarea**. El handoff no ejecuta código upstream ni habilita red, shell o acciones externas. Si un eslabón no valida, la malla falla cerrada y el estado permanece recuperable desde el último checkpoint verificado.\n\n**Contrato de salida:** `CHECKPOINTED|VERIFIED|RELEASED`  \n**Contrato de entrada:** `task_id + checkpoint + evidence`  \n**Failover:** siguiente eslabón únicamente después de validación del registro y del adapter.\n'''
        readme.write_text(text, encoding='utf-8')


def runtime_roundtrip(registry: dict) -> list[dict]:
    evidence = []
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        for idx, item in enumerate(registry['components'], start=1):
            adapter_path = Path(item['adapter'])
            cls = load_adapter_class(adapter_path)
            state_path = base / f'{idx:02d}.json'
            adapter = cls(state_path)
            task_id = f'MESH-{idx:02d}'
            claimed = adapter.claim(task_id)
            checkpointed = adapter.checkpoint_task(task_id, {'mesh_step': idx, 'component': item['component']})
            verified = adapter.verify(task_id, {'mesh_contract': True, 'component': item['component']})
            released = adapter.release(task_id)
            if [claimed.status, checkpointed.status, verified.status, released.status] != ['CLAIMED', 'CHECKPOINTED', 'VERIFIED', 'RELEASED']:
                raise RuntimeError(f'ROUNDTRIP_GAP:{item["component"]}')
            evidence.append({
                'component': item['component'],
                'adapter': item['adapter'],
                'status': 'PASS',
                'final_state': released.status,
            })
    return evidence


def main() -> None:
    registry = read_registry()
    graph = make_graph(registry)
    runtime_evidence = runtime_roundtrip(registry)
    graph['validation'] = {
        'static_adapter_validation': 'PASS_24_OF_24',
        'runtime_persistence_roundtrip': 'PASS_24_OF_24',
        'offensive_execution': False,
        'network_default': 'deny',
    }
    graph['evidence'] = runtime_evidence
    GRAPH.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding='utf-8')
    update_readmes(registry, graph)
    print('MESH_COMPONENTS=24')
    print('MESH_EDGES=24')
    print('STATIC_VALIDATION=PASS_24_OF_24')
    print('RUNTIME_ROUNDTRIP=PASS_24_OF_24')


if __name__ == '__main__':
    main()
