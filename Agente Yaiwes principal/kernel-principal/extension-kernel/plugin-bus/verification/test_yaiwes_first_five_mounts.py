from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_BUS = Path(__file__).resolve().parents[1]
YAIWES_ROOT = PLUGIN_BUS.parents[3]
if str(PLUGIN_BUS) not in sys.path:
    sys.path.insert(0, str(PLUGIN_BUS))

from universal_plugin_bus_v2_integrated import (  # noqa: E402
    ComponentCandidate,
    PluginStatus,
    TargetConventions,
    UniversalPluginBus,
)

COMPONENTS = [
    (
        "APScheduler",
        YAIWES_ROOT / "execution-orchestration/task-classifier-scheduler",
        "ficha.apscheduler.v2.json",
        "adapter.py",
    ),
    (
        "AWS-Step-Functions-DS-SDK",
        YAIWES_ROOT / "execution-orchestration/state-machine-executor/aws-step-functions-ds-sdk",
        "ficha.aws_step_functions.v2.json",
        "adapter.py",
    ),
    (
        "Ajv",
        YAIWES_ROOT / "definition-registry/schema-contracts/ajv",
        "ficha.ajv.v2.json",
        "adapter.py",
    ),
    (
        "Apache-APISIX",
        YAIWES_ROOT / "mesh-routing-collaboration/apisix-api-gateway",
        "ficha.apisix.v2.json",
        "adapter.py",
    ),
    (
        "Apache-Airflow",
        YAIWES_ROOT / "execution-orchestration/dag-executor/apache-airflow",
        "ficha.airflow.v2.json",
        "adapter.py",
    ),
]


def _mount(component_root: Path, ficha_name: str, adapter_name: str):
    manifest = json.loads((component_root / ficha_name).read_text(encoding="utf-8"))
    adapter_path = component_root / adapter_name
    candidate = ComponentCandidate(
        source_code=adapter_path.read_text(encoding="utf-8"),
        language="python",
        file_paths=[str(adapter_path.relative_to(YAIWES_ROOT))],
    )
    conventions = TargetConventions(
        language="python",
        naming_style="snake_case",
        async_style="mixed",
        type_system="gradual",
    )
    bus = UniversalPluginBus()
    case_id = manifest["tribunal_case_id"]
    bus.add_tribunal_approval(case_id)
    reg = bus.enchufar(manifest, candidate, conventions, registered_by="yaiwes-integration-loop")
    pid = manifest["artifact_id"]
    assert reg.plugin_id == pid
    assert reg.status == PluginStatus.ACTIVE
    assert bus.registry.get(pid) is reg
    assert any(e["level"] == "L2_build" for e in bus.evidence.get(pid))
    bus.health.heartbeat(pid)
    assert bus.check_plugin_health(pid)
    events = manifest.get("activacion", {}).get("eventos", [])
    if events:
        assert bus.trigger_plugin(pid, events[0], {})
    return bus, reg


def test_first_five_mount_through_real_universal_plugin_bus() -> None:
    for name, root, ficha, adapter in COMPONENTS:
        assert root.is_dir(), f"missing destination: {name}: {root}"
        bus, reg = _mount(root, ficha, adapter)
        assert reg.interface_contract.plugin_id == reg.plugin_id
        assert bus.telemetry.get_spans(), name
