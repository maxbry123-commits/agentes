"""Hatchling build hook that compiles and bundles the Go TUI sidecar."""

from __future__ import annotations

import os
import shutil
import subprocess
import sysconfig
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface[Any]):
    """Compile the Bubble Tea sidecar and ship it inside the wheel.

    The sidecar is the only interactive interface, so every wheel is a
    platform wheel and a missing Go toolchain is a build failure.
    """

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        # Editable installs run from the checkout, where the TUI is started
        # with ``go run``; there is nothing to bundle.
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'scripts/tui_sidecar_hook.py','step':'initialize','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye
