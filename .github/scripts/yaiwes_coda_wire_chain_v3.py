#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('📂coda workflow persistencias')
FIELD = ROOT / '🏈 cancha deportiva de fútbol'
REGISTRY = FIELD / 'YAIWES-SWARM-NAVY-SEALS-REGISTRY.json'
FABLES = ROOT / 'Fables enchufe universal'
TEAM = 'Swarm agent team Navy seals YAIWES'
CHAIN_ID = 'yaiwes-navy-seals-persistence-chain-v3'
DT = 'yaiwes.task-state.v2'


def main() -> None:
    data = json.loads(REGISTRY.read_text(encoding='utf-8'))
    components = data.get('components', [])
    if len(components) != 24:
        raise SystemExit(f'EXPECTED_24_COMPONENTS:{len(components)}')

    names = [c['component'] for c in components]
    for i, c in enumerate(components):
        c['chain_id'] = CHAIN_ID
        c['order'] = i + 1
        c['previous'] = names[i - 1] if i else None
        c['next'] = names[i + 1] if i + 1 < len(names) else None
        c['consume'] = {'datatype': DT, 'required': ['task_id', 'payload']}
        c['expose'] = {'datatype': DT, 'provides': ['task_id', 'payload', 'checkpoint', 'evidence']}
        c['handoff'] = 'CHECKPOINT_THEN_NEXT'

        adapter = Path(c['adapter'])
        test = Path(c['test'])
        if not adapter.is_file() or not test.is_file():
            raise SystemExit(f'MISSING_LINK_FILES:{c["component"]}')

        doc = FIELD / c['component'] / 'README.md'
        text = doc.read_text(encoding='utf-8')
        marker = '\n## Cableado Swarm v3\n'
        if marker in text:
            text = text.split(marker, 1)[0].rstrip() + '\n'
        prev_name = c['previous'] or 'START'
        next_name = c['next'] or 'END'
        text += f'''\n## Cableado Swarm v3\n\n**Equipo:** {TEAM}  \n**Cadena:** `{CHAIN_ID}`  \n**Posición:** `{i+1}/24`  \n**Anterior:** `{prev_name}`  \n**Siguiente:** `{next_name}`\n\n`{prev_name} → {c['component']} → {next_name}`\n\nContrato de handoff: `{DT}`. Este eslabón recibe estado de tarea, guarda checkpoint/evidencia mediante el adapter YAIWES y entrega el estado al siguiente eslabón. El runner maestro solo carga los adapters YAIWES generados; no invoca automáticamente el código upstream.\n'''
        doc.write_text(text, encoding='utf-8')

    data['schema'] = 'yaiwes.swarm.registry/v3'
    data['chain_id'] = CHAIN_ID
    data['team'] = TEAM
    data['wiring'] = {
        'topology': 'LINEAR_PERSISTENCE_CHAIN',
        'datatype': DT,
        'entry': names[0],
        'exit': names[-1],
        'count': 24,
        'source_execution': False,
        'network_default': 'deny',
    }
    REGISTRY.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    wiring = {
        'schema': 'yaiwes.swarm.wiring/v3',
        'chain_id': CHAIN_ID,
        'team': TEAM,
        'datatype': DT,
        'count': 24,
        'links': [
            {
                'order': c['order'],
                'component': c['component'],
                'previous': c['previous'],
                'next': c['next'],
                'adapter': c['adapter'],
                'handoff': c['handoff'],
            }
            for c in components
        ],
    }
    (FIELD / 'YAIWES-SWARM-WIRING-MAP-V3.json').write_text(
        json.dumps(wiring, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    lines = [
        '# YAIWES Swarm Persistence Wiring v3',
        '',
        f'## {TEAM}',
        '',
        f'**Chain:** `{CHAIN_ID}`',
        '',
        '`INPUT → CLAIM → CHECKPOINT → VERIFY → HANDOFF → NEXT → ... → RELEASE/END`',
        '',
        '### Cadena 24/24',
        '',
    ]
    lines.extend(f"{c['order']:02d}. `{c['component']}` → `{c['next'] or 'END'}`" for c in components)
    lines += [
        '',
        '### Frontera',
        '',
        '- Solo se ejecutan adapters de persistencia YAIWES generados y verificados.',
        '- El código upstream no se autoejecuta desde este workflow.',
        '- Red denegada por defecto en el contrato de los eslabones.',
        '- Cada handoff conserva checkpoint y evidencia.',
        '',
    ]
    (FIELD / 'YAIWES-SWARM-WIRING-MAP-V3.md').write_text('\n'.join(lines), encoding='utf-8')

    runner = r'''from __future__ import annotations
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict

CHAIN_ID = "yaiwes-navy-seals-persistence-chain-v3"


def _load_adapter(adapter_path: Path):
    if adapter_path.name != "yaiwes_persistence_adapter.py" or "coda_persistence" not in adapter_path.parts:
        raise ValueError("adapter path outside generated YAIWES persistence surface")
    spec = importlib.util.spec_from_file_location("yaiwes_generated_adapter", adapter_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("adapter import failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.YaiwesPersistenceAdapter


def run_chain(registry_path: str | Path, state_root: str | Path, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    registry_path = Path(registry_path)
    repo_root = registry_path.parents[2]
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    components = registry["components"]
    if registry.get("chain_id") != CHAIN_ID or len(components) != 24:
        raise ValueError("invalid chain registry")

    state_root = Path(state_root)
    evidence = []
    handoff = {"task_id": task_id, "payload": dict(payload)}
    for component in components:
        adapter_path = repo_root / Path(component["adapter"]).relative_to(repo_root.name)
        Adapter = _load_adapter(adapter_path)
        state_file = state_root / component["component"] / f"{task_id}.json"
        adapter = Adapter(state_file)
        adapter.claim(task_id)
        adapter.checkpoint(task_id, {"chain_id": CHAIN_ID, "order": component["order"], "payload": handoff["payload"]})
        adapter.verify(task_id, {"component": component["component"], "handoff": "PASS"})
        adapter.release(task_id)
        evidence.append({"order": component["order"], "component": component["component"], "status": "RELEASED"})

    return {"chain_id": CHAIN_ID, "task_id": task_id, "payload": handoff["payload"], "links_completed": len(evidence), "evidence": evidence}
'''
    (FABLES / 'yaiwes_swarm_persistence_chain.py').write_text(runner, encoding='utf-8')

    test = r'''from pathlib import Path
import tempfile
import unittest
from yaiwes_swarm_persistence_chain import run_chain

class SwarmChainTests(unittest.TestCase):
    def test_end_to_end_24_links(self):
        repo = Path(__file__).resolve().parents[2]
        registry = repo / "🏈 cancha deportiva de fútbol" / "YAIWES-SWARM-NAVY-SEALS-REGISTRY.json"
        with tempfile.TemporaryDirectory() as td:
            result = run_chain(registry, td, "TASK-E2E-001", {"goal": "persistence-test"})
            self.assertEqual(result["links_completed"], 24)
            self.assertEqual(result["evidence"][0]["order"], 1)
            self.assertEqual(result["evidence"][-1]["order"], 24)
            self.assertTrue(all(x["status"] == "RELEASED" for x in result["evidence"]))

if __name__ == "__main__":
    unittest.main()
'''
    (FABLES / 'test_yaiwes_swarm_persistence_chain.py').write_text(test, encoding='utf-8')

    print('CHAIN_WIRED=24_OF_24')


if __name__ == '__main__':
    main()
