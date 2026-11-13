from __future__ import annotations

import builtins
import importlib
import sys

import pytest


def test_optimizers_package_imports_without_optuna(monkeypatch):
    original_import = builtins.__import__
    package_name = "evoagentx.optimizers"

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "optuna":
            raise ModuleNotFoundError("No module named 'optuna'", name="optuna")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.delitem(sys.modules, package_name, raising=False)

    module = importlib.import_module(package_name)

    assert "MapElitesOptimizer" in module.__all__
    with pytest.raises(ModuleNotFoundError, match="optional dependency 'optuna'"):
        getattr(module, "MiproOptimizer")
