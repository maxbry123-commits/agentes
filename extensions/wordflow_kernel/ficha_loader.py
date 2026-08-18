"""ficha.v2 loader → register capability — S10/T10
"""
from __future__ import annotations
from pathlib import Path
import json
from typing import Dict, Any, List, Optional

class CapabilityRegistry:
    def __init__(self):
        self._caps: Dict[str, Dict[str, Any]] = {}

    def register(self, cap_id: str, ficha: Dict[str, Any]) -> None:
        self._caps[cap_id] = ficha

    def get(self, cap_id: str) -> Optional[Dict[str, Any]]:
        return self._caps.get(cap_id)

    def list(self) -> List[str]:
        return list(self._caps.keys())

def load_ficha(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"ficha inválida: {path}")
    return data

def load_and_register(path: Path, registry: CapabilityRegistry) -> str:
    ficha = load_ficha(path)
    cap_id = ficha.get("id") or ficha.get("name") or path.stem
    registry.register(str(cap_id), ficha)
    return str(cap_id)

default_cap_registry = CapabilityRegistry()
