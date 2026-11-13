from __future__ import annotations
from datetime import date
from pathlib import Path
import importlib.util

_ADAPTER = Path(__file__).resolve().parent / "adapter.py"

def _load_adapter():
    spec = importlib.util.spec_from_file_location("n25_workalendar_adapter", _ADAPTER)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod

def working_day_gate(task=None, iso_date=None):
    task = task or {}
    iso = iso_date or task.get("schedule_date") or date.today().isoformat()
    calendar = task.get("calendar") or "usa.core.UnitedStates"
    result = _load_adapter().is_working_day(iso, calendar)
    result["allowed"] = bool(result.get("working"))
    return result
