from __future__ import annotations
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
