from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

CHAIN_ID = "yaiwes-navy-seals-persistence-chain-v3"


def _load_adapter(adapter_path: Path):
    if adapter_path.name != "yaiwes_persistence_adapter.py" or "coda_persistence" not in adapter_path.parts:
        raise ValueError("adapter path outside generated YAIWES persistence surface")
    module_name = "yaiwes_generated_adapter_" + str(abs(hash(str(adapter_path))))
    spec = importlib.util.spec_from_file_location(module_name, adapter_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("adapter import failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
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
        adapter_path = repo_root / component["adapter"]
        Adapter = _load_adapter(adapter_path)
        state_file = state_root / component["component"] / f"{task_id}.json"
        adapter = Adapter(state_file)
        adapter.claim(task_id)
        adapter.checkpoint_task(task_id, {"chain_id": CHAIN_ID, "order": component["order"], "payload": handoff["payload"]})
        adapter.verify(task_id, {"component": component["component"], "handoff": "PASS"})
        adapter.release(task_id)
        evidence.append({"order": component["order"], "component": component["component"], "status": "RELEASED"})

    return {"chain_id": CHAIN_ID, "task_id": task_id, "payload": handoff["payload"], "links_completed": len(evidence), "evidence": evidence}
