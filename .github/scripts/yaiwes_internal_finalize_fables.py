#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("📂coda workflow persistencias")
FIELD = ROOT / "🏈 cancha deportiva de fútbol"
FABLES = ROOT / "Fables enchufe universal"
TEAM = "Swarm agent team Navy seals YAIWES"
VERSION = "YAIWES-INTERNAL-PERSISTENCE-v4.2"
CHAIN = "yaiwes-internal-navy-seals-chain-v4"
MIN_CUMULATIVE_TRANSFORMED = 299


def comps():
    xs = sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("🏈 ") and p.name != "🏈 cancha deportiva de fútbol")
    if len(xs) != 24:
        raise SystemExit(f"EXPECTED_24:{len(xs)}")
    return xs


def component_runtime_text(component: str) -> str:
    return f'''from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

TEAM = {TEAM!r}
COMPONENT = {component!r}
SCHEMA = "yaiwes.component.persistence-runtime/v4.2"


def persist_task_step(state_root: str | Path, task_id: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Persist one benign component handoff atomically."""
    root = Path(state_root) / COMPONENT
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"{{task_id}}.json"
    event = {{
        "schema": SCHEMA,
        "team": TEAM,
        "component": COMPONENT,
        "task_id": task_id,
        "payload": dict(payload or {{}}),
        "status": "RELEASED",
    }}
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(target)
    return event


def load_task_step(state_root: str | Path, task_id: str) -> Dict[str, Any] | None:
    target = Path(state_root) / COMPONENT / f"{{task_id}}.json"
    if not target.is_file():
        return None
    return json.loads(target.read_text(encoding="utf-8"))
'''


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

        code = comp / "code"
        internal = code / "yaiwes_internal"
        internal.mkdir(parents=True, exist_ok=True)
        runtime = internal / "persistence_runtime.py"
        runtime.write_text(component_runtime_text(comp.name), encoding="utf-8")
        (internal / "__init__.py").write_text("from .persistence_runtime import load_task_step, persist_task_step\n", encoding="utf-8")

        transformed_links = cumulative_links(comp, report)
        total_cumulative += len(transformed_links)
        total_runtime_sources += int(report.get("source_files", 0))

        links = list(transformed_links)
        links.append({
            "order": len(links) + 1,
            "path": "yaiwes_internal/persistence_runtime.py",
            "active_sha256": hashlib.sha256(runtime.read_bytes()).hexdigest(),
            "role": "COMPONENT_PERSISTENCE_LINK",
            "transform_kind": "GENERATED_INTERNAL_RUNTIME_V4_2",
        })

        manifest = {
            "schema": "yaiwes.internal.link-manifest/v4.2",
            "component": comp.name,
            "team": TEAM,
            "version": VERSION,
            "source_files_audited": report["source_files"],
            "last_delta_candidates": report["candidates"],
            "last_delta_changed": report["changed"],
            "active_surfaces_transformed_cumulative": len(transformed_links),
            "component_runtime": str(runtime.relative_to(code)),
            "link_count": len(links),
            "links": links,
        }
        (comp / "INTERNAL-LINK-MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        prev_name = names[i - 1] if i else None
        next_name = names[i + 1] if i + 1 < len(names) else None
        readme = f'''# {comp.name} — YAIWES Internal Persistence Architecture v4.2

## {TEAM}

**Nueva versión:** `{VERSION}`  
**Modo:** `INTERNAL_CODE_TRANSFORMATION`  
**Archivos fuente runtime auditados:** `{report['source_files']}`  
**Transformaciones acumuladas dentro de `code/`:** `{len(transformed_links)}`  
**Delta de la última pasada:** `{report['changed']}`  
**Eslabones internos totales:** `{len(links)}`  
**Runtime interno del componente:** `code/yaiwes_internal/persistence_runtime.py`

## Arquitectura nueva

`INTERNAL SOURCE → AUDIT → QUARANTINE ORIGINAL → SAFE PERSISTENCE REPLACEMENT → COMPONENT RUNTIME → CHECKPOINT → EVIDENCE → HANDOFF`

Las superficies internas detectadas con efectos externos se transformaron dentro de `code/`. Cada original previo a la cirugía queda preservado bajo `_yaiwes_upstream_quarantine/` para procedencia, y el archivo activo transformado queda registrado con SHA256 en `INTERNAL-LINK-MANIFEST.json`.

Todos los componentes, incluso aquellos sin superficies candidatas, contienen ahora un runtime interno benigno de persistencia que escribe el estado de tarea de forma atómica.

## Cadena del componente

`{prev_name or 'START'} → {comp.name} → {next_name or 'END'}`

Cada archivo transformado acumulado es un eslabón de persistencia. `persistence_runtime.py` es el eslabón ejecutable del componente y entrega estado al siguiente componente.

## Fables

Fables carga exclusivamente `code/yaiwes_internal/persistence_runtime.py` de cada componente y consume los manifiestos internos v4.2. No ejecuta los originales de cuarentena.
'''
        (comp / "README.md").write_text(readme, encoding="utf-8")

        registry.append({
            "order": i + 1,
            "component": comp.name,
            "previous": prev_name,
            "next": next_name,
            "manifest": str(comp / "INTERNAL-LINK-MANIFEST.json"),
            "component_runtime": str(comp / "code" / "yaiwes_internal" / "persistence_runtime.py"),
            "source_files_audited": report["source_files"],
            "last_delta_changed": report["changed"],
            "transformed_cumulative": len(transformed_links),
            "links": len(links),
        })

    if total_cumulative < MIN_CUMULATIVE_TRANSFORMED:
        raise SystemExit(f"CUMULATIVE_TRACE_GAP:{total_cumulative}<{MIN_CUMULATIVE_TRANSFORMED}")

    master = {
        "schema": "yaiwes.internal.swarm-registry/v4.2",
        "team": TEAM,
        "version": VERSION,
        "chain_id": CHAIN,
        "component_count": 24,
        "component_runtime_count": 24,
        "runtime_source_files_audited": total_runtime_sources,
        "transformed_files_cumulative": total_cumulative,
        "minimum_expected_cumulative": MIN_CUMULATIVE_TRANSFORMED,
        "components": registry,
    }
    FIELD.mkdir(parents=True, exist_ok=True)
    (FIELD / "YAIWES-INTERNAL-SWARM-REGISTRY-V4.json").write_text(json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8")
    (FIELD / "YAIWES-INTERNAL-CUMULATIVE-MANIFEST-V4.json").write_text(
        json.dumps({
            "schema": "yaiwes.internal.cumulative/v4.2",
            "team": TEAM,
            "component_count": 24,
            "component_runtime_count": 24,
            "transformed_files_cumulative": total_cumulative,
            "components": [
                {"component": x["component"], "transformed_cumulative": x["transformed_cumulative"], "component_runtime": x["component_runtime"], "manifest": x["manifest"]}
                for x in registry
            ],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    FABLES.mkdir(parents=True, exist_ok=True)
    runner = '''from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

CHAIN = "yaiwes-internal-navy-seals-chain-v4"


def _load_generated_runtime(runtime_path: Path):
    if runtime_path.name != "persistence_runtime.py" or runtime_path.parent.name != "yaiwes_internal":
        raise ValueError("runtime outside generated YAIWES internal surface")
    name = "yaiwes_component_runtime_" + str(abs(hash(str(runtime_path))))
    spec = importlib.util.spec_from_file_location(name, runtime_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("component runtime import failed")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def run_internal_chain(registry_path, state_root, task_id, payload):
    registry_path = Path(registry_path)
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if data.get("chain_id") != CHAIN or data.get("component_count") != 24 or data.get("component_runtime_count") != 24:
        raise ValueError("invalid internal registry")
    root = registry_path.parents[2]
    state_root = Path(state_root)
    evidence = []
    for component in data["components"]:
        manifest_path = root / component["manifest"]
        runtime_path = root / component["component_runtime"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("component") != component["component"]:
            raise ValueError("manifest component mismatch")
        mod = _load_generated_runtime(runtime_path)
        event = mod.persist_task_step(state_root, task_id, payload)
        if event.get("component") != component["component"] or event.get("status") != "RELEASED":
            raise RuntimeError("component persistence runtime failed")
        event["transformed_links_closed"] = manifest.get("active_surfaces_transformed_cumulative", 0)
        event["links_closed"] = manifest["link_count"]
        evidence.append(event)
    return {
        "chain_id": CHAIN,
        "task_id": task_id,
        "components_closed": len(evidence),
        "component_runtimes_closed": len(evidence),
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
    def test_24_component_runtimes_and_cumulative_links_close(self):
        coda = Path(__file__).resolve().parents[1]
        registry = coda / "🏈 cancha deportiva de fútbol" / "YAIWES-INTERNAL-SWARM-REGISTRY-V4.json"
        with tempfile.TemporaryDirectory() as td:
            result = run_internal_chain(registry, td, "TASK-INTERNAL-001", {"goal":"persistence"})
            self.assertEqual(result["components_closed"], 24)
            self.assertEqual(result["component_runtimes_closed"], 24)
            self.assertGreaterEqual(result["transformed_files_closed"], 299)
            self.assertTrue(all(x["status"] == "RELEASED" for x in result["evidence"]))
            self.assertTrue(all(x["links_closed"] >= 1 for x in result["evidence"]))

if __name__ == "__main__": unittest.main()
'''
    (FABLES / "test_yaiwes_internal_swarm_chain_v4.py").write_text(test, encoding="utf-8")
    print(json.dumps({
        "components": 24,
        "component_runtimes": 24,
        "chain": CHAIN,
        "transformed_files_cumulative": total_cumulative,
        "status": "WIRED",
    }))

if __name__ == "__main__": main()
