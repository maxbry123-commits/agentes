from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "wordflow_loop" / "adapters" / "browser_use_adapter.py"
FICHA = ROOT / "wordflow_loop" / "contracts" / "ficha.browser_use.v2.json"
FICHA_MODULE = ROOT / "wordflow_loop" / "plugins" / "ficha_contract_v2.py"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_adapter_is_fail_closed_and_pinned():
    mod = load("browser_use_adapter", ADAPTER)
    d = mod.descriptor()
    assert d["version"] == "0.13.10"
    assert d["source_commit"] == "5c892e013a73e6622e6f50336e1eb0aa2c4405f2"
    assert d["execution_authorized"] is False
    assert d["requires_sandbox"] is True


def test_request_validation_and_no_execution_authority():
    mod = load("browser_use_adapter2", ADAPTER)
    r = mod.build_request("inspect docs", "https://example.com")
    assert r["entry_point"] == "browser_use.Agent"
    assert r["execution_authorized"] is False
    try:
        mod.build_request("inspect docs", "file:///etc/passwd")
    except ValueError:
        pass
    else:
        raise AssertionError("non-http(s) URL must fail closed")


def test_ficha_v2_accepts_testing_contract():
    ficha_mod = load("ficha_contract_v2", FICHA_MODULE)
    manifest = json.loads(FICHA.read_text(encoding="utf-8"))
    verdict = ficha_mod.validar(manifest)
    assert verdict.valido, verdict.errores
    assert manifest["estado"] == "testing"
    assert manifest["seguridad"]["sandbox"] == "container"
