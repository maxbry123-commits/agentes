from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_BUS = ROOT.parents[1] / "kernel-principal" / "extension-kernel" / "plugin-bus"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_adapter_exec_is_contract_inspection_safe() -> None:
    source = (ROOT / "adapter.py").read_text(encoding="utf-8")
    namespace: dict[str, object] = {"__name__": "_contract_probe_"}
    exec(compile(source, "adapter.py", "exec"), namespace)
    assert callable(namespace["build_scheduler"])
    assert callable(namespace["build_task_defaults"])
    assert callable(namespace["capability"])


def test_sync_and_async_scheduler_factories() -> None:
    adapter = _load(ROOT / "adapter.py", "yaiwes_apscheduler_adapter")
    sync_scheduler = adapter.build_scheduler()
    async_scheduler = adapter.build_scheduler(async_mode=True)
    assert sync_scheduler.__class__.__name__ == "Scheduler"
    assert async_scheduler.__class__.__name__ == "AsyncScheduler"


def test_manifest_validates_with_universal_contract() -> None:
    sys.path.insert(0, str(PLUGIN_BUS))
    try:
        contract = _load(PLUGIN_BUS / "ficha_contract_v2.py", "ficha_contract_v2")
        manifest = json.loads((ROOT / "ficha.apscheduler.v2.json").read_text(encoding="utf-8"))
        verdict = contract.validar(manifest)
        assert verdict.valido, verdict.errores
    finally:
        if sys.path and sys.path[0] == str(PLUGIN_BUS):
            sys.path.pop(0)


def test_wiring_targets_exist() -> None:
    wiring = json.loads((ROOT / "WIRING.json").read_text(encoding="utf-8"))
    assert (ROOT / wiring["adapter"]).is_file()
    assert (ROOT / wiring["manifest"]).is_file()
    assert (ROOT / wiring["source"]).is_dir()
    assert (ROOT / wiring["plugin_bus"]).is_file()
    assert (ROOT / wiring["contract_validator"]).is_file()
