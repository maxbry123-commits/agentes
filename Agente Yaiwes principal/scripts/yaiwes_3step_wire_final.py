from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path.cwd()
ROOT = REPO / "Agente Yaiwes principal"
EXT = ROOT / "kernel-principal" / "extension-kernel"
BUS_DIR = EXT / "plugin-bus"
ABI = EXT / "abi-mount" / "wordflow-loop"
REGISTRY_DIR = EXT / "capability-registry"
CONTRACTS = REGISTRY_DIR / "wordflow-loop-contracts"
EVIDENCE = REGISTRY_DIR / "wordflow-loop-evidence"

ITEMS = {
    "langgraph": {
        "id": "yaiwes.loop.langgraph",
        "role": "recurrent_graph_checkpoint",
        "kind": "marker",
        "path": "Agente Yaiwes principal/execution-orchestration/dag-executor/langgraph/SOURCE_COMMIT.txt",
        "expected": "81bf17b23123e4ef8b9d5f49fa09a0122fc2edd1",
    },
    "temporal_python": {
        "id": "yaiwes.loop.temporal_python",
        "role": "durable_execution_replay",
        "kind": "marker",
        "path": "Agente Yaiwes principal/execution-orchestration/state-machine-executor/temporal-python-sdk/SOURCE_COMMIT.txt",
        "expected": "22a9e41fd857261ee0a9bb5ce57f439d93e7f88d",
    },
    "prefect": {
        "id": "yaiwes.loop.prefect",
        "role": "flow_state_retry",
        "kind": "marker",
        "path": "Agente Yaiwes principal/execution-orchestration/dag-executor/prefect/SOURCE_COMMIT.txt",
        "expected": "6a6fe4e24cc456be30dd570aeeb1dbb6b6bef286",
    },
    "hatchet_python": {
        "id": "yaiwes.loop.hatchet_python",
        "role": "durable_task_orchestration",
        "kind": "marker",
        "path": "Agente Yaiwes principal/execution-orchestration/dag-executor/hatchet-python-sdk/SOURCE_COMMIT.txt",
        "expected": "086a63f2245416296de288a944aad1b8357e63e9",
    },
    "redun": {
        "id": "yaiwes.loop.redun",
        "role": "dag_scheduler_cache",
        "kind": "marker",
        "path": "Agente Yaiwes principal/execution-orchestration/dag-executor/redun/SOURCE_COMMIT.txt",
        "expected": "49a299b223bc345b999aaa40daa6876f105089e1",
    },
    "loop_engineer": {
        "id": "yaiwes.loop.loop_engineer",
        "role": "serial_loop_runtime_recovery",
        "kind": "marker",
        "path": "Agente Yaiwes principal/execution-orchestration/deterministic-execution/loop-engineer/SOURCE_COMMIT.txt",
        "expected": "0ca97d7c7e8a2e20e986d18e273c6171a2684d30",
    },
    "capability_registration": {
        "id": "yaiwes.runtime.capability_registration",
        "role": "capability_registry_registration",
        "kind": "gitblob",
        "path": "Agente Yaiwes principal/kernel-principal/extension-kernel/capability-registry/capability_registration.py",
        "expected": "d205e86d0379844162e612317b2737ed8b62ece9",
    },
    "classifier_hook": {
        "id": "yaiwes.runtime.classifier_hook",
        "role": "classifier_scheduler_hook",
        "kind": "gitblob",
        "path": "Agente Yaiwes principal/execution-orchestration/classifier-scheduler/classifier_hook.py",
        "expected": "fa48204b973eccf4fa66d3b322932399995df5bb",
    },
    "instance_pool": {
        "id": "yaiwes.runtime.instance_pool",
        "role": "execution_instance_pool",
        "kind": "gitblob",
        "path": "Agente Yaiwes principal/execution-engine-pool/instance_pool.py",
        "expected": "cf537a34515baac2cc9919c59ca40c4c09da0672",
    },
    "programming_instance": {
        "id": "yaiwes.runtime.programming_instance",
        "role": "programming_pipeline_instance",
        "kind": "gitblob",
        "path": "Agente Yaiwes principal/execution-orchestration/programming-pipeline/programming_instance.py",
        "expected": "1dd88384765a182f1f299bfeb119d42ac00ec324",
    },
    "usage_metering": {
        "id": "yaiwes.runtime.usage_metering",
        "role": "runtime_usage_metering",
        "kind": "gitblob",
        "path": "Agente Yaiwes principal/observability/usage_metering.py",
        "expected": "d4f1393d1430cafc80540562e38ed548f034a087",
    },
}


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def verify_source(cfg: dict) -> bool:
    p = REPO / cfg["path"]
    if cfg["kind"] == "marker":
        return p.is_file() and p.read_text(encoding="utf-8").strip() == cfg["expected"]
    return p.is_file() and git_blob_sha(p) == cfg["expected"]


def adapter_source(slug: str, cfg: dict) -> str:
    return f'''"""YAIWES ABI adapter for {cfg["id"]}. Does not execute vendor source during registration."""\nfrom pathlib import Path\nimport hashlib\n\nPLUGIN_ID = {cfg["id"]!r}\nROLE = {cfg["role"]!r}\nSOURCE_PATH = {cfg["path"]!r}\nSOURCE_KIND = {cfg["kind"]!r}\nEXPECTED = {cfg["expected"]!r}\n\ndef _git_blob_sha(path):\n    data = path.read_bytes()\n    return hashlib.sha1((f"blob {{len(data)}}\\0").encode() + data).hexdigest()\n\ndef health(repo_root):\n    p = Path(repo_root) / SOURCE_PATH\n    if not p.is_file():\n        return False\n    if SOURCE_KIND == "marker":\n        return p.read_text(encoding="utf-8").strip() == EXPECTED\n    return _git_blob_sha(p) == EXPECTED\n\ndef descriptor():\n    return {{"plugin_id": PLUGIN_ID, "role": ROLE, "source_path": SOURCE_PATH, "source_kind": SOURCE_KIND, "expected": EXPECTED}}\n'''


def ficha(cfg: dict, adapter: str, slug: str) -> dict:
    digest = hashlib.sha256(adapter.encode()).hexdigest()
    return {
        "artifact_id": cfg["id"],
        "version": "1.0.0",
        "estado": "active",
        "contract_hash": "sha256:" + digest,
        "tribunal_case_id": f"YAIWES-3STEP-{slug.upper().replace('_','-')}",
        "contrato": {
            "rol": "transform",
            "consume": {"datatype": {"family": "json", "type": "object", "version": 1}},
            "expone": {"datatype": {"family": "json", "type": "object", "version": 1}},
        },
        "ejecucion": {"kind": "code", "transport": "importlib", "runtime_type": "compute", "idempotente": True},
        "seguridad": {"sandbox": "process", "limites": {"timeout_ms": 5000}},
        "firma": {"gpg_key_id": "YAIWES-3STEP"},
        "categoria": "pipeline",
        "etapa": "P",
        "perfiles": {"n0": {"habilitada": True, "iteraciones": 1, "simulaciones": 0, "criticas": 0, "muestras_k": 1}},
        "presupuesto": {"n0": {"max_tokens": 1, "max_ms": 5000, "max_costo_usd": 0.0}},
        "telemetria": {"metricas": ["tiempo", "errores", "health"], "span_otel": True},
        "evidencia": {"produce": ["L2_build", "L3_runtime"], "destino": "capability-registry/wordflow-loop-evidence/"},
        "failover": {"sustituible_por": [], "compensacion": "fail_closed"},
        "salud": {"metodo": "ping", "heartbeat_interval_s": 30},
    }


def import_file(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    ABI.mkdir(parents=True, exist_ok=True)
    CONTRACTS.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    bus_path = BUS_DIR / "universal_plugin_bus_v2_integrated.py"
    ficha_path = BUS_DIR / "ficha_contract_v2.py"
    capreg_path = REGISTRY_DIR / "capability_registration.py"
    for p in (bus_path, ficha_path, capreg_path):
        if not p.is_file():
            raise RuntimeError(f"required canonical wiring file missing: {p}")

    if git_blob_sha(bus_path) != "59fd1e10b65a2b92a282508afe07790fec26af27":
        raise RuntimeError("CANONICAL_BUS_BLOB_DRIFT")
    if git_blob_sha(ficha_path) != "b27f14b4d64f77bccf53a893c49b6f20bd58e745":
        raise RuntimeError("CANONICAL_FICHA_BLOB_DRIFT")
    if git_blob_sha(capreg_path) != "d205e86d0379844162e612317b2737ed8b62ece9":
        raise RuntimeError("CAPABILITY_REGISTRATION_BLOB_DRIFT")

    sys.path.insert(0, str(BUS_DIR))
    bus_mod = import_file("yaiwes_universal_plugin_bus", bus_path)
    for symbol in ("UniversalPluginBus", "ComponentCandidate", "TargetConventions", "PluginStatus"):
        if not hasattr(bus_mod, symbol):
            raise RuntimeError(f"BUS_PUBLIC_API_MISSING:{symbol}")

    bus = bus_mod.UniversalPluginBus()
    conventions = bus_mod.TargetConventions("python", "snake_case", "sync", "gradual")
    registrations = []

    for slug, cfg in ITEMS.items():
        if not verify_source(cfg):
            raise RuntimeError(f"SOURCE_PROVENANCE_FAIL:{slug}")

        source = adapter_source(slug, cfg)
        adapter_path = ABI / f"{slug}_adapter.py"
        adapter_path.write_text(source, encoding="utf-8")
        contract = ficha(cfg, source, slug)
        (CONTRACTS / f"ficha.{slug}.v2.json").write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        candidate = bus_mod.ComponentCandidate(source, "python", [str(adapter_path.relative_to(REPO))])
        bus.add_tribunal_approval(contract["tribunal_case_id"])
        reg = bus.enchufar(contract, candidate, conventions, registered_by="yaiwes-3step-step2")
        if reg.status != bus_mod.PluginStatus.ACTIVE:
            raise RuntimeError(f"PLUGIN_NOT_ACTIVE:{slug}:{reg.status}")
        bus.health.heartbeat(cfg["id"])
        if not bus.check_plugin_health(cfg["id"]):
            raise RuntimeError(f"BUS_HEALTH_FAIL:{slug}")
        adapter_mod = import_file(f"yaiwes_abi_{slug}", adapter_path)
        if not adapter_mod.health(REPO):
            raise RuntimeError(f"SOURCE_HEALTH_FAIL:{slug}")

        ev = bus.evidence.get(cfg["id"])
        levels = [x["level"] for x in ev]
        if "L2_build" not in levels:
            raise RuntimeError(f"EVIDENCE_FAIL:{slug}")
        registrations.append({
            "slug": slug,
            "plugin_id": reg.plugin_id,
            "slot": reg.slot_number,
            "status": reg.status.value,
            "role": cfg["role"],
            "source_path": cfg["path"],
            "source_proof": cfg["expected"],
            "health": True,
            "evidence_levels": levels,
            "contract_fingerprint": reg.interface_contract.fingerprint,
        })

    active = bus.registry.list_active()
    if len(active) != len(ITEMS):
        raise RuntimeError(f"REGISTRY_COUNT_FAIL:{len(active)}/{len(ITEMS)}")

    registry = {
        "contract": "tel.workflow/v4",
        "wiring_step": 2,
        "canonical_bus_path": str(bus_path.relative_to(REPO)),
        "canonical_bus_blob": git_blob_sha(bus_path),
        "canonical_ficha_blob": git_blob_sha(ficha_path),
        "active_count": len(registrations),
        "merkle_root": bus.registry.get_merkle_root(),
        "registrations": registrations,
    }
    (REGISTRY_DIR / "wordflow_loop_plugin_registry.json").write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "step": 2,
        "status": "PASS_REAL",
        "wired": len(registrations),
        "healthy": sum(1 for r in registrations if r["health"]),
        "canonical_bus_preserved": True,
        "vendor_exec_during_registration": False,
        "registry_merkle_root": registry["merkle_root"],
    }
    (EVIDENCE / "STEP2_WIRING.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"YAIWES_STEP2_WIRING=PASS {len(registrations)}/{len(ITEMS)}")
    print(f"YAIWES_STEP2_HEALTH=PASS {evidence['healthy']}/{len(ITEMS)}")
    print(f"REGISTRY_MERKLE_ROOT={registry['merkle_root']}")


if __name__ == "__main__":
    main()
