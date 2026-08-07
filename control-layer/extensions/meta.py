"""Meta Extension — única extensión que el kernel carga directamente.
SOURCE: SALIDA_2_6_IDEAS_PARTE_2 Idea 5 + KER docs.

Lee extensions.yaml → descubre → carga → registra → entrega tabla de capacidades.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml


@dataclass
class MetaExtension:
    extensions_path: Path = Path("registry/extensions.yaml")
    loaded: dict[str, Any] = field(default_factory=dict)

    def discover(self) -> list[dict[str, Any]]:
        if not self.extensions_path.exists():
            return []
        with open(self.extensions_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("extensions", [])

    def load_all(self) -> dict[str, Any]:
        for ext in self.discover():
            ext_id = ext.get("id")
            if ext_id:
                self.loaded[ext_id] = ext
        return self.loaded

    def capabilities_table(self) -> list[str]:
        caps: list[str] = []
        for ext in self.loaded.values():
            caps.extend(ext.get("capabilities", []))
        return sorted(set(caps))

    def context_for_agent(self) -> dict[str, Any]:
        """Contexto que se entrega al agente antes de cada tarea."""
        return {
            "extensions_loaded": list(self.loaded.keys()),
            "capabilities": self.capabilities_table(),
            "source": "MetaExtension",
        }
