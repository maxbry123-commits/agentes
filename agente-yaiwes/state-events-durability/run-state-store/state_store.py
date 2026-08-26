# -*- coding: utf-8 -*-
"""Minimal state store — A-WF-09. In-memory + optional JSON file. 0% LLM."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StateStore:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else None
        self._data: dict[str, Any] = {}
        if self.path and self.path.is_file():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def update(self, mapping: dict[str, Any]) -> None:
        self._data.update(mapping)

    def checkpoint(self, block_id: str, payload: dict[str, Any]) -> str:
        key = f"ckpt:{block_id}"
        self._data[key] = payload
        self._persist()
        return key

    def load_checkpoint(self, block_id: str) -> dict[str, Any] | None:
        return self._data.get(f"ckpt:{block_id}")

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def _persist(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
