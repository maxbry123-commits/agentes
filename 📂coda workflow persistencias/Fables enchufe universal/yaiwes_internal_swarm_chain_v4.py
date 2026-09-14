from __future__ import annotations
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
