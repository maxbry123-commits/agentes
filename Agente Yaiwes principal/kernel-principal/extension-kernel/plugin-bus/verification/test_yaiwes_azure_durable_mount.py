from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_BUS = Path(__file__).resolve().parents[1]
YAIWES_ROOT = PLUGIN_BUS.parents[2]
if str(PLUGIN_BUS) not in sys.path:
    sys.path.insert(0, str(PLUGIN_BUS))

from universal_plugin_bus_v2_integrated import ComponentCandidate, PluginStatus, TargetConventions, UniversalPluginBus

ROOT = YAIWES_ROOT / "execution-orchestration/state-machine-executor/azure-durable-functions"


def test_azure_durable_mount_through_real_universal_plugin_bus() -> None:
    manifest = json.loads((ROOT / "ficha.azure-durable-functions.v2.json").read_text(encoding="utf-8"))
    adapter = ROOT / "adapter.py"
    candidate = ComponentCandidate(source_code=adapter.read_text(encoding="utf-8"), language="python", file_paths=[str(adapter.relative_to(YAIWES_ROOT))])
    conventions = TargetConventions(language="python", naming_style="snake_case", async_style="mixed", type_system="gradual")
    bus = UniversalPluginBus()
    bus.add_tribunal_approval(manifest["tribunal_case_id"])
    reg = bus.enchufar(manifest, candidate, conventions, registered_by="yaiwes-integration-loop")
    pid = manifest["artifact_id"]
    assert reg.plugin_id == pid and reg.status == PluginStatus.ACTIVE
    assert bus.registry.get(pid) is reg
    assert any(e["level"] == "L2_build" for e in bus.evidence.get(pid))
    bus.health.heartbeat(pid)
    assert bus.check_plugin_health(pid)
    events = manifest.get("activacion", {}).get("eventos", [])
    if events:
        assert bus.trigger_plugin(pid, events[0], {})
    assert bus.telemetry.get_spans()
