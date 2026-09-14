#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("📂coda workflow persistencias")
FIELD = ROOT / "🏈 cancha deportiva de fútbol"
FABLES = ROOT / "Fables enchufe universal"
TEAM = "Swarm agent team Navy seals YAIWES"
VERSION = "YAIWES-INTERNAL-PERSISTENCE-v4.1"
CHAIN = "yaiwes-internal-navy-seals-chain-v4"
MIN_CUMULATIVE_TRANSFORMED = 299


def comps():
    xs = sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("🏈 ") and p.name != "🏈 cancha deportiva de fútbol")
    if len(xs) != 24:
        raise SystemExit(f"EXPECTED_24:{len(xs)}")
    return xs


def cumulative_links(comp: Path, report: dict) -> list[dict]:
    code = comp / "code"
    quarantine = code / "_yaiwes_upstream_quarantine"
    current_by_path = {f.get("path"): f for f in report.get("findings", []) if f.get("path")}
    links = []
    if quarantine.is_dir():
        originals = sorted(p for p in quarantine.rglob("*.original") if p.is_file())
        for order, q in enumerate(originals, 1):
            qrel = q.relative_to(quarantine)
            rel_text = str(qrel)
            if not rel_text.endswith(".original"):
                continue
            active_rel = rel_text[: -len(".original")]
            active = code / active_rel
            if not active.is_file():
                raise SystemExit(f"MISSING_ACTIVE_AFTER_TRANSFORM:{comp.name}:{active_rel}")
            current = current_by_path.get(active_rel, {})
            links.append({
                "order": order,
                "path": active_rel,
                "original_sha256": hashlib.sha256(q.read_bytes()).hexdigest(),
                "active_sha256": hashlib.sha256(active.read_bytes()).hexdigest(),
                "quarantine": str(q.relative_to(code)),
                "transform_kind": current.get("kind", "CUMULATIVE_INTERNAL_TRANSFORM"),
                "role": "TASK_PERSISTENCE_LINK",
            })
    return links


def main():
    components = comps()
    registry = []
    names = [p.name for p in components]
    total_cumulative = 0
    total_runtime_sources = 0

    for i, comp in enumerate(components):
        report = json.loads((comp / "INTERNAL-TRANSFORM-AUDIT.json").read_text(encoding="utf-8"))
        if report.get("mode") != "TRANSFORM" or report.get("candidates") != report.get("changed"):
            raise SystemExit(f"INTERNAL_TRANSFORM_NOT_CLOSED:{comp.name}")

        transformed_links = cumulative_links(comp, report)
        total_cumulative += len(transformed_links)
        total_runtime_sources += int(report.get("source_files", 0))

        links = list(transformed_links)
        links.append({
            "order": len(links) + 1,
            "path": "yaiwes_internal/README.md",
            "role": "COMPONENT_PERSISTENCE_LINK",
            "transform_kind": "INTERNAL_RUNTIME",
        })

        manifest = {
            "schema": "yaiwes.internal.link-manifest/v4.1",
            "component": comp.name,
            "team": TEAM,
            "version": VERSION,
            "source_files_audited": report["source_files"],
            "last_delta_candidates": report["candidates"],
            "last_delta_changed": report["changed"],
            "active_surfaces_transformed_cumulative": len(transformed_links),
            "link_count": len(links),
            "links": links,
        }
        (comp / "INTERNAL-LINK-MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        prev_name = names[i - 1] if i else None
        next_name = names[i + 1] if i + 1 < len(names) else None
        readme = f'''# {comp.name} — YAIWES Internal Persistence Architecture v4.1

## {TEAM}

**Nueva versión:** `{VERSION}`  
**Modo:** `INTERNAL_CODE_TRANSFORMATION`  
**Archivos fuente runtime auditados:** `{report['source_files']}`  
**Transformaciones acumuladas dentro de `code/`:** `{len(transformed_links)}`  
**Delta de la última pasada:** `{report['changed']}`  
**Eslabones internos totales:** `{len(links)}`

## Arquitectura nueva

`INTERNAL SOURCE → AUDIT → QUARANTINE ORIGINAL → SAFE PERSISTENCE REPLACEMENT → CHECKPOINT → EVIDENCE → HANDOFF`

Las superficies internas detectadas con efectos externos se transformaron dentro de `code/`. Cada original previo a la cirugía queda preservado bajo `_yaiwes_upstream_quarantine/` para procedencia, y el archivo activo transformado queda registrado con SHA256 en `INTERNAL-LINK-MANIFEST.json`.

## Cadena del componente

`{prev_name or 'START'} → {comp.name} → {next_name or 'END'}`

Cada archivo transformado acumulado es un eslabón de persistencia. El componente completo entrega estado al siguiente componente únicamente después de cerrar sus eslabones internos.

## Fables

Fables consume exclusivamente los manifiestos internos v4.1 ya transformados. No ejecuta los originales de cuarentena.
'''
        (comp / "README.md").write_text(readme, encoding="utf-8")

        registry.append({
            "order": i + 1,
            "component": comp.name,
            "previous": prev_name,
            "next": next_name,
            "manifest": str(comp / "INTERNAL-LINK-MANIFEST.json"),
            "source_files_audited": report["source_files"],
            "last_delta_changed": report["changed"],
            "transformed_cumulative": len(transformed_links),
            "links": len(links),
        })

    if total_cumulative < MIN_CUMULATIVE_TRANSFORMED:
        raise SystemExit(f"CUMULATIVE_TRACE_GAP:{total_cumulative}<{MIN_CUMULATIVE_TRANSFORMED}")

    master = {
        "schema": "yaiwes.internal.swarm-registry/v4.1",
        "team": TEAM,
        "version": VERSION,
        "chain_id": CHAIN,
        "component_count": 24,
        "runtime_source_files_audited": total_runtime_sources,
        "transformed_files_cumulative": total_cumulative,
        "minimum_expected_cumulative": MIN_CUMULATIVE_TRANSFORMED,
        "components": registry,
    }
    FIELD.mkdir(parents=True, exist_ok=True)
    (FIELD / "YAIWES-INTERNAL-SWARM-REGISTRY-V4.json").write_text(json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8")
    (FIELD / "YAIWES-INTERNAL-CUMULATIVE-MANIFEST-V4.json").write_text(
        json.dumps({
            "schema": "yaiwes.internal.cumulative/v4.1",
            "team": TEAM,
            "component_count": 24,
            "transformed_files_cumulative": total_cumulative,
            "components": [
                {"component": x["component"], "transformed_cumulative": x["transformed_cumulative"], "manifest": x["manifest"]}
                for x in registry
            ],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

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
        internal_links = manifest.get("active_surfaces_transformed_cumulative", 0)
        state = {
            "schema": "yaiwes.internal.chain-state/v4.1",
            "task_id": task_id,
            "component": component["component"],
            "transformed_links_closed": internal_links,
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
    return {
        "chain_id": CHAIN,
        "task_id": task_id,
        "components_closed": len(evidence),
        "transformed_files_closed": sum(x["transformed_links_closed"] for x in evidence),
        "evidence": evidence,
    }
'''
    (FABLES / "yaiwes_internal_swarm_chain_v4.py").write_text(runner, encoding="utf-8")

    test = '''from pathlib import Path
import tempfile
import unittest
from yaiwes_internal_swarm_chain_v4 import run_internal_chain

class InternalChainV4Tests(unittest.TestCase):
    def test_24_components_and_cumulative_links_close(self):
        coda = Path(__file__).resolve().parents[1]
        registry = coda / "🏈 cancha deportiva de fútbol" / "YAIWES-INTERNAL-SWARM-REGISTRY-V4.json"
        with tempfile.TemporaryDirectory() as td:
            result = run_internal_chain(registry, td, "TASK-INTERNAL-001", {"goal":"persistence"})
            self.assertEqual(result["components_closed"], 24)
            self.assertGreaterEqual(result["transformed_files_closed"], 299)
            self.assertTrue(all(x["status"] == "RELEASED" for x in result["evidence"]))
            self.assertTrue(all(x["links_closed"] >= 1 for x in result["evidence"]))

if __name__ == "__main__": unittest.main()
'''
    (FABLES / "test_yaiwes_internal_swarm_chain_v4.py").write_text(test, encoding="utf-8")
    print(json.dumps({
        "components": 24,
        "chain": CHAIN,
        "transformed_files_cumulative": total_cumulative,
        "status": "WIRED",
    }))

if __name__ == "__main__": main()
