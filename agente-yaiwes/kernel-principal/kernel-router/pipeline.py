"""T37 — discover → map → select → load stubs. Not 49 endpoints."""
from __future__ import annotations

from typing import Any


def discover(query: str | None = None) -> list[dict[str, Any]]:
    return [{"id": "stub", "query": query or ""}]


def map_resources(discovered: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"id": d.get("id"), "mapped": True} for d in discovered]


def select(mapped: list[dict[str, Any]]) -> dict[str, Any] | None:
    return mapped[0] if mapped else None


def load(selected: dict[str, Any] | None) -> dict[str, Any]:
    if not selected:
        return {"ok": False, "loaded": False}
    return {"ok": True, "loaded": True, "id": selected.get("id")}


def run_pipeline(query: str | None = None) -> dict[str, Any]:
    d = discover(query)
    m = map_resources(d)
    s = select(m)
    l = load(s)
    return {"ok": l.get("ok", False), "stages": ["discover", "map", "select", "load"], "result": l}


if __name__ == "__main__":
    out = run_pipeline("x")
    assert out["ok"] is True
    assert out["stages"] == ["discover", "map", "select", "load"]
    print("ok", out["stages"], out["result"]["id"])
