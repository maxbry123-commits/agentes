from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path

def _load_runtime(path: Path):
    name = "yaiwes_v5_runtime_" + str(abs(hash(str(path)))); spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None: raise RuntimeError("runtime import failed")
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod); return mod.PersistenceRuntime

def run_swarm(registry_path, state_root, task_id, payload=None):
    registry_path = Path(registry_path); coda = registry_path.parents[1]; data = json.loads(registry_path.read_text(encoding="utf-8"))
    if data.get("schema") != "yaiwes.internal.swarm/v5" or data.get("count") != 24: raise ValueError("bad v5 swarm registry")
    evidence = []
    for item in data["components"]:
        comp = coda / item["component"]; Runtime = _load_runtime(comp / "code" / "yaiwes_internal" / "persistence_runtime.py")
        state = Runtime(comp, Path(state_root) / item["component"] / f"{task_id}.json").run(task_id, payload)
        if state.status != "RELEASED": raise RuntimeError(f"component not released: {item['component']}")
        evidence.append({"order":item["order"],"component":item["component"],"links":len(state.checkpoints),"status":state.status})
    return {"task_id":task_id,"components_completed":len(evidence),"evidence":evidence}
