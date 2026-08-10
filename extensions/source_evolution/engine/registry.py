# -*- coding: utf-8 -*-
"""Source registry — A-SE-01. Pin store. 0% LLM."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .version_pin import VersionPinError, normalize_pin, pins_equal


class SourceRegistry:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else None
        self._pins: dict[str, dict[str, Any]] = {}
        if self.path and self.path.is_file():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for p in data.get("pins") or []:
                pin = normalize_pin(p)
                self._pins[pin["pin_id"]] = pin

    def register(self, raw: dict[str, Any]) -> dict[str, Any]:
        pin = normalize_pin(raw)
        existing = self._pins.get(pin["pin_id"])
        if existing and not pins_equal(existing, pin):
            raise VersionPinError(
                "PIN_ID_CONFLICT",
                f"{pin['pin_id']} digest mismatch",
            )
        self._pins[pin["pin_id"]] = pin
        self._persist()
        return pin

    def get(self, pin_id: str) -> dict[str, Any] | None:
        return self._pins.get(pin_id)

    def list_pins(self) -> list[dict[str, Any]]:
        return list(self._pins.values())

    def find_by_digest(self, algo: str, value: str) -> list[dict[str, Any]]:
        v = value.lower()
        return [
            p
            for p in self._pins.values()
            if p["digest"]["algo"] == algo and p["digest"]["value"] == v
        ]

    def remove(self, pin_id: str) -> bool:
        if pin_id in self._pins:
            del self._pins[pin_id]
            self._persist()
            return True
        return False

    def _persist(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema_version": "1.0", "pins": list(self._pins.values())}
        self.path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
