from __future__ import annotations
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent

def is_working_day(iso_date: str, calendar: str = "usa.core.UnitedStates") -> dict:
    import importlib
    y, m, d = (int(p) for p in iso_date.split("-"))
    mod_name, cls_name = calendar.rsplit(".", 1)
    mod = importlib.import_module("workalendar." + mod_name)
    cal = getattr(mod, cls_name)()
    day = date(y, m, d)
    return {
        "date": iso_date,
        "calendar": calendar,
        "working": bool(cal.is_working_day(day)),
        "source": str(_ROOT),
    }
