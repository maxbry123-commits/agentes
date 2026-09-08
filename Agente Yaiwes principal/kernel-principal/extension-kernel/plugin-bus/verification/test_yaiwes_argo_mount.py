from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_BUS = Path(__file__).resolve().parents[1]
YAIWES_ROOT = PLUGIN_BUS.parents[2]
if str(PLUGIN_BUS) not in sys.path:
    sys.path.insert(0, str(PLUGIN_BUS))

from universal_plugin_bus_v2_integrated import ComponentCandidate, PluginStatus, TargetConventions, UniversalPluginBus

ROOT = YAIWES_ROOT / "execution-orchestration/dag-executor/argo-workflows"
FICHA = "ficha.argo-workflows.v2.json"
ADAPTER = "adapter.py"


def test_argo_mount_through_real_universal_plugin_bus() -> None:
    assert ROOT.is_dir()
    manifest = json.loads((ROOT / FICHA).read_text(encoding="utf-8"))
    adapter_path = ROOT / ADAPTER
    candidate = ComponentCandidate(
        source_code=adapter_path.read_text(encoding="utf-8"),
        language="python",
        file_paths=[str(adapter_path.relative_to(YAIWES_ROOT))],
    )
    conventions = TargetConventions(language="python", naming_style="snake_case", async_style="mixed", type_system="gradual")
    bus = UniversalPluginBus()
    bus.add_tribunal_approval(manifest["tribunal_case_id"])
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
    assert reg.interface_contract.plugin_id == pid
    assert bus.telemetry.get_spans()
