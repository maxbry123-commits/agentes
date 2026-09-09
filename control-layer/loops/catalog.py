"""Loop catalog generator — ids deterministas · 0% LLM
SOURCE: P3 · 4 levels × 9 phases × variants (hasta 1080 conceptual)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator

LEVELS = ["micro", "tarea", "fase", "proyecto"]
PHASES = [
    "leer_anclas", "plan", "ejecutar", "medir", "validar",
    "reparar", "evidencia", "checkpoint", "decidir",
]
# 30 variantes por (level, phase) → 4*9*30 = 1080
VARIANTS = [f"V{i:02d}" for i in range(1, 31)]


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    level: str
    phase: str
    variant: str

    def to_dict(self) -> dict:
        return {"id": self.id, "level": self.level, "phase": self.phase, "variant": self.variant}


def catalog_id(level: str, phase: str, variant: str) -> str:
    return f"LOOP-{level[:2].upper()}-{phase[:3].upper()}-{variant}"


def generate_catalog(limit: int | None = None) -> list[CatalogEntry]:
    out: list[CatalogEntry] = []
    for level in LEVELS:
        for phase in PHASES:
            for var in VARIANTS:
                cid = catalog_id(level, phase, var)
                out.append(CatalogEntry(id=cid, level=level, phase=phase, variant=var))
                if limit is not None and len(out) >= limit:
                    return out
    return out  # 1080


def iter_catalog() -> Iterator[CatalogEntry]:
    yield from generate_catalog()


def catalog_size() -> int:
    return len(LEVELS) * len(PHASES) * len(VARIANTS)
