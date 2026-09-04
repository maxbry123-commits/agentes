"""Memoria bajo demanda · buscar → rankear → top-N → liberar."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .doc_registry import DocRecord, DocRegistry


@dataclass(frozen=True)
class RankedDoc:
    record: DocRecord
    score: float


def rank_docs(
    registry: DocRegistry,
    query: str,
    *,
    top_n: int = 15,
    tags: Sequence[str] | None = None,
) -> List[RankedDoc]:
    """Ranking lexical simple (parcial). No embeddings."""
    q = (query or "").lower().strip()
    tokens = [t for t in q.replace("/", " ").split() if t]
    scored: list[RankedDoc] = []
    for rec in registry:
        if tags and not any(t in rec.tags for t in tags):
            continue
        blob = f"{rec.name} {rec.summary} {' '.join(rec.tags)}".lower()
        score = 0.0
        for t in tokens:
            if t in blob:
                score += 1.0
        if rec.name.lower() in q or q in rec.name.lower():
            score += 2.0
        if score > 0:
            scored.append(RankedDoc(record=rec, score=score))
    scored.sort(key=lambda x: (-x.score, x.record.registered_at))
    return scored[: max(1, min(top_n, 20))]
