from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
PLUGIN_BUS = REPO / "kernel-principal" / "extension-kernel" / "plugin-bus"


def _python_files():
    return sorted((ROOT / "stepfunctions").rglob("*.py"))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_runtime_source_compiles():
    for path in _python_files():
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def test_xray_no_string_identity_comparisons():
    findings = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare) and any(isinstance(op, (ast.Is, ast.IsNot)) for op in node.ops):
                values = [node.left, *node.comparators]
                if any(isinstance(v, ast.Constant) and isinstance(v.value, str) for v in values):
                    findings.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert not findings, f"string identity comparisons remain: {findings}"


def test_xray_core_mutable_defaults_removed():
    targets = [
        ROOT / "stepfunctions" / "steps" / "states.py",
        ROOT / "stepfunctions" / "workflow" / "stepfunctions.py",
    ]
    findings = []
    for path in targets:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defaults = [*node.args.defaults, *[d for d in node.args.kw_defaults if d is not None]]
                for default in defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        findings.append(f"{path.name}:{node.name}:{node.lineno}")
    assert not findings, f"mutable defaults remain in core paths: {findings}"


def test_exact_xray_repairs_present():
    states = (ROOT / "stepfunctions" / "steps" / "states.py").read_text(encoding="utf-8")
    workflow = (ROOT / "stepfunctions" / "workflow" / "stepfunctions.py").read_text(encoding="utf-8")
    assert "if self.type == 'Choice':" in states
    assert "if self.type is 'Choice':" not in states
    assert "def __init__(self, steps=None):" in states
    assert "steps = [] if steps is None else steps" in states
    assert "role, tags=None, execution_input=None" in workflow
    assert "self.tags = [] if tags is None else tags" in workflow


def test_adapter_is_import_safe_and_exports_contract_surface():
    adapter = _load_module("yaiwes_aws_stepfunctions_adapter", ROOT / "adapter.py")
    assert callable(adapter.graph_to_dict)
    assert callable(adapter.graph_to_json)
    assert callable(adapter.workflow_factory)


def test_wiring_targets_exist():
    wiring = json.loads((ROOT / "WIRING.json").read_text(encoding="utf-8"))
    repo_root = ROOT.parents[3]
    for key in ("adapter", "ficha", "plugin_bus", "ficha_contract", "runtime_package", "tests"):
        assert (repo_root / wiring[key]).exists(), f"missing wiring target {key}: {wiring[key]}"


def test_ficha_v2_validates():
    contract = _load_module("yaiwes_ficha_contract_v2", PLUGIN_BUS / "ficha_contract_v2.py")
    ficha = json.loads((ROOT / "ficha.aws_step_functions.v2.json").read_text(encoding="utf-8"))
    verdict = contract.validar(ficha)
    assert verdict.valido, verdict.errores
