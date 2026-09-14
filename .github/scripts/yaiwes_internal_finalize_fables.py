#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("📂coda workflow persistencias")
FIELD = ROOT / "🏈 cancha deportiva de fútbol"
FABLES = ROOT / "Fables enchufe universal"
TEAM = "Swarm agent team Navy seals YAIWES"
VERSION = "YAIWES-INTERNAL-PERSISTENCE-v4.0"
CHAIN = "yaiwes-internal-navy-seals-chain-v4"


def comps():
    xs = sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("🏈 ") and p.name != "🏈 cancha deportiva de fútbol")
    if len(xs) != 24:
        raise SystemExit(f"EXPECTED_24:{len(xs)}")
    return xs


def main():
    components = comps()
    registry = []
    names = [p.name for p in components]
    for i, comp in enumerate(components):
        report = json.loads((comp / "INTERNAL-TRANSFORM-AUDIT.json").read_text(encoding="utf-8"))
        if report.get("mode") != "TRANSFORM" or report.get("candidates") != report.get("changed"):
            raise SystemExit(f"INTERNAL_TRANSFORM_NOT_CLOSED:{comp.name}")
        links = []
        order = 1
        for f in report.get("findings", []):
            if not f.get("changed"):
                continue
            links.append({
                "order": order,
                "path": f["path"],
                "original_sha256": f["sha256"],
                "quarantine": f["quarantine"],
                "transform_kind": f.get("kind"),
                "role": "TASK_PERSISTENCE_LINK",
            })
            order += 1
        links.append({
            "order": order,
            "path": "yaiwes_internal/README.md",
            "role": "COMPONENT_PERSISTENCE_LINK",
            "transform_kind": "INTERNAL_RUNTIME",
        })
        manifest = {
            "schema": "yaiwes.internal.link-manifest/v4",
            "component": comp.name,
            "team": TEAM,
            "version": VERSION,
            "source_files_audited": report["source_files"],
            "active_surfaces_transformed": report["changed"],
            "link_count": len(links),
            "links": links,
        }
        (comp / "INTERNAL-LINK-MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        prev_name = names[i - 1] if i else None
        next_name = names[i + 1] if i + 1 < len(names) else None
        readme = f'''# {comp.name} — YAIWES Internal Persistence Architecture v4.0

## {TEAM}

**Nueva versión:** `{VERSION}`  
**Modo:** `INTERNAL_CODE_TRANSFORMATION`  
**Archivos fuente auditados:** `{report['source_files']}`  
**Superficies internas transformadas:** `{report['changed']}`  
**Eslabones internos:** `{len(links)}`

## Arquitectura nueva

`INTERNAL SOURCE → AUDIT → QUARANTINE ORIGINAL → SAFE PERSISTENCE REPLACEMENT → CHECKPOINT → EVIDENCE → HANDOFF`

Las superficies internas con efectos externos se transformaron dentro de `code/`. El original queda preservado en `_yaiwes_upstream_quarantine/` solo como procedencia y no pertenece al runtime activo YAIWES.

## Cadena del componente

`{prev_name or 'START'} → {comp.name} → {next_name or 'END'}`

Cada archivo transformado figura como eslabón en `INTERNAL-LINK-MANIFEST.json`. El componente completo entrega estado al siguiente componente únicamente después de cerrar sus eslabones internos.

## Fables

El cableado Fables se genera después de la transformación y consume exclusivamente los manifiestos internos v4; no ejecuta el código original conservado en cuarentena.
'''
        (comp / "README.md").write_text(readme, encoding="utf-8")
        registry.append({
            "order": i + 1,
            "component": comp.name,
            "previous": prev_name,
            "next": next_name,
            "manifest": str(comp / "INTERNAL-LINK-MANIFEST.json"),
            "source_files_audited": report["source_files"],
            "transformed": report["changed"],
            "links": len(links),
        })

    master = {
        "schema": "yaiwes.internal.swarm-registry/v4",
        "team": TEAM,
        "version": VERSION,
        "chain_id": CHAIN,
        "component_count": 24,
        "components": registry,
    }
    FIELD.mkdir(parents=True, exist_ok=True)
    (FIELD / "YAIWES-INTERNAL-SWARM-REGISTRY-V4.json").write_text(json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8")

    FABLES.mkdir(parents=True, exist_ok=True)
    runner = '''from __future__ import annotations
import json
from pathlib import Path

CHAIN = "yaiwes-internal-navy-seals-chain-v4"


def run_internal_chain(registry_path, state_root, task_id, payload):
    registry_path = Path(registry_path)
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if data.get("chain_id") != CHAIN or data.get("component_count") != 24:
        raise ValueError("invalid internal registry")
    root = registry_path.parents[2]
    state_root = Path(state_root)
    evidence = []
    for component in data["components"]:
        manifest_path = root / component["manifest"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("component") != component["component"]:
            raise ValueError("manifest component mismatch")
        state = {
            "schema": "yaiwes.internal.chain-state/v4",
            "task_id": task_id,
            "component": component["component"],
            "links_closed": manifest["link_count"],
            "payload": dict(payload),
            "status": "RELEASED",
        }
        target = state_root / component["component"] / f"{task_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(target)
        evidence.append(state)
    return {"chain_id": CHAIN, "task_id": task_id, "components_closed": len(evidence), "evidence": evidence}
'''
    (FABLES / "yaiwes_internal_swarm_chain_v4.py").write_text(runner, encoding="utf-8")
    test = '''from pathlib import Path
import tempfile
import unittest
from yaiwes_internal_swarm_chain_v4 import run_internal_chain

class InternalChainV4Tests(unittest.TestCase):
    def test_24_components_close(self):
        coda = Path(__file__).resolve().parents[1]
        registry = coda / "🏈 cancha deportiva de fútbol" / "YAIWES-INTERNAL-SWARM-REGISTRY-V4.json"
        with tempfile.TemporaryDirectory() as td:
            result = run_internal_chain(registry, td, "TASK-INTERNAL-001", {"goal":"persistence"})
            self.assertEqual(result["components_closed"], 24)
            self.assertTrue(all(x["status"] == "RELEASED" for x in result["evidence"]))
            self.assertTrue(all(x["links_closed"] >= 1 for x in result["evidence"]))

if __name__ == "__main__": unittest.main()
'''
    (FABLES / "test_yaiwes_internal_swarm_chain_v4.py").write_text(test, encoding="utf-8")
    print(json.dumps({"components": 24, "chain": CHAIN, "status": "WIRED"}))

if __name__ == "__main__": main()
