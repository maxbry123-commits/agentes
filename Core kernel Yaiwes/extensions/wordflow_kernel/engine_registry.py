"""T20 — EngineRegistry: load(ficha) / attach(name, policy) / list().

Does not run engines.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .ficha_loader import ficha_id, load_ficha, validate_ficha


class EngineRegistry:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    def load(self, ficha: dict | Path | str) -> str:
        if isinstance(ficha, (str, Path)):
            data = load_ficha(Path(ficha))
        elif isinstance(ficha, dict):
            data = ficha
        else:
            raise TypeError("ficha must be dict or path")
        errors = validate_ficha(data)
        if errors:
            raise ValueError("ficha inválida: " + "; ".join(errors))
        name = ficha_id(data)
        assert name is not None
        self._items[name] = {"ficha": data, "policy": {}}
        return name

    def attach(self, name: str, policy: Optional[dict] = None) -> dict[str, Any]:
        if name not in self._items:
            self._items[name] = {"ficha": {"artifact_id": name, "abi_version": "0"}, "policy": {}}
        self._items[name]["policy"] = dict(policy or {})
        return self._items[name]

    def list(self) -> list[str]:
        return sorted(self._items.keys())

    def get(self, name: str) -> Optional[dict[str, Any]]:
        return self._items.get(name)


if __name__ == "__main__":
    from pathlib import Path

    reg = EngineRegistry()
    path = Path(__file__).resolve().parent / "ficha.v2.json"
    name = reg.load(path)
    assert name
    assert name in reg.list()
    assert len(reg.list()) == 1
    reg.attach(name, {"llm_control": "DENY"})
    print("ok", reg.list())
