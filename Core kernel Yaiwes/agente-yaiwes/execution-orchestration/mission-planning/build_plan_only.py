"""T36 — build_plan_only. Serializable plan. No mass fetch."""
from __future__ import annotations

from typing import Any


def build_plan_only(index_url_or_list: str | list[Any]) -> dict[str, Any]:
    if isinstance(index_url_or_list, str):
        items = [{"ref": index_url_or_list}]
        source = "url"
    elif isinstance(index_url_or_list, list):
        items = []
        for it in index_url_or_list:
            if isinstance(it, dict):
                items.append(dict(it))
            else:
                items.append({"ref": str(it)})
        source = "list"
    else:
        return {"ok": False, "mode": "PLAN_ONLY", "error": "invalid_input"}

    steps = [{"action": "index", "item": it, "fetch": False} for it in items]
    return {
        "ok": True,
        "mode": "PLAN_ONLY",
        "source": source,
        "count": len(steps),
        "steps": steps,
        "fetch": False,
    }


if __name__ == "__main__":
    p = build_plan_only(["hf:a", "hf:b"])
    assert p["ok"] and p["count"] == 2 and p["fetch"] is False
    u = build_plan_only("https://example.invalid/index.json")
    assert u["source"] == "url"
    print("ok", p["mode"], p["count"])
