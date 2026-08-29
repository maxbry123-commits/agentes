# objective_memory.py — Memoria de Estrategias y Aprendizaje

> **Archivo:** `objective_memory.py`  
> **Rol:** Persistencia, retrieval semántico, consolidación y decaimiento de experiencias  
> **Inspiración:** Open-Sable (Ultra-LTM, Inter-Agent Bridge), concepto de strategy learning

---

```python
"""
objective_memory.py
===================
Memoria de objetivos y estrategias con aprendizaje a largo plazo.

No solo almacena "task → result", sino:
    objective → strategy → execution → result → lesson → strategy_score

Inspirado en Open-Sable (Ultra-Long-Term Memory, Inter-Agent Bridge) y
en el concepto de "strategy learning" del documento original.

Uso:
    memory = ObjectiveMemory(persistence_path="data/objective_memory")

    # Almacenar experiencia
    memory.store(StrategyRecord(
        objective_description="Implementar módulo de auth",
        strategy={"approach": "jwt + rbac", "tools": ["fastapi", "sqlalchemy"]},
        result={"status": "success", "duration": 120},
        success=True,
        lesson="Usar dependency injection simplificó testing",
        success_score=0.95,
    ))

    # Recuperar estrategias similares
    similar = memory.find_similar("Implementar sistema de login", top_k=3)
    for rec in similar:
        print(f"Estrategia previa (score {rec.success_score}): {rec.strategy}")
"""

from __future__ import annotations

import json
import os
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path


@dataclass
class StrategyRecord:
    """
    Registro de una estrategia ejecutada para un objetivo.

    Este es el "átomo" de aprendizaje del sistema.
    """
    id: str
    objective_description: str
    strategy: Dict[str, Any]  # Cómo se abordó el objetivo
    result: Dict[str, Any]    # Qué pasó
    success: bool
    lesson: str               # Qué se aprendió
    success_score: float      # 0.0 - 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Metadatos de enriquecimiento
    objective_domain: Optional[str] = None  # Dominio (auth, db, ui, etc.)
    objective_complexity: Optional[float] = None  # Complejidad estimada
    execution_duration: Optional[float] = None  # Segundos
    resources_used: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    failure_type: Optional[str] = None  # Si falló, por qué

    # Para retrieval semántico
    embedding: Optional[List[float]] = None
    keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StrategyRecord:
        data = dict(data)
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ConsolidatedPattern:
    """
    Patrón consolidado de múltiples experiencias.

    Generado periódicamente por consolidación de memoria.
    """
    id: str
    pattern_description: str
    domain: str
    success_rate: float
    avg_duration: float
    common_strategies: List[Dict[str, Any]]
    common_failures: List[str]
    common_lessons: List[str]
    occurrence_count: int
    first_seen: datetime
    last_seen: datetime
    confidence: float  # Basado en cantidad de evidencia


class ObjectiveMemory:
    """
    Sistema de memoria para objetivos y estrategias.

    Características:
    - Almacenamiento persistente (JSONL)
    - Búsqueda por similitud (keyword + embedding)
    - Consolidación periódica (patrones duraderos)
    - Decaimiento temporal (olvidar lo irrelevante)
    - Ranking de estrategias por éxito
    """

    def __init__(
        self,
        persistence_path: Optional[str] = None,
        consolidation_interval: int = 100,  # Cada N registros nuevos
        decay_days: int = 90,  # Decaimiento después de 90 días
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
    ):
        self.persistence_path = Path(persistence_path) if persistence_path else None
        self.consolidation_interval = consolidation_interval
        self.decay_days = decay_days
        self.embedding_fn = embedding_fn

        self.records: List[StrategyRecord] = []
        self.patterns: List[ConsolidatedPattern] = []
        self._since_last_consolidation = 0

        if self.persistence_path:
            self._load()

    # ------------------------------------------------------------------
    # CRUD BÁSICO
    # ------------------------------------------------------------------

    def store(self, record: StrategyRecord) -> None:
        """Almacena un nuevo registro de estrategia."""
        # Generar keywords automáticamente si no están definidas
        if not record.keywords:
            record.keywords = self._extract_keywords(record.objective_description)

        # Generar embedding si hay función disponible
        if self.embedding_fn and record.embedding is None:
            record.embedding = self.embedding_fn(record.objective_description)

        self.records.append(record)
        self._since_last_consolidation += 1

        # Consolidar si es necesario
        if self._since_last_consolidation >= self.consolidation_interval:
            self._consolidate()

        # Persistir
        if self.persistence_path:
            self._append_record(record)

    def get(self, record_id: str) -> Optional[StrategyRecord]:
        """Recupera un registro por ID."""
        for rec in self.records:
            if rec.id == record_id:
                return rec
        return None

    def find_similar(
        self,
        objective_description: str,
        top_k: int = 5,
        min_success_score: float = 0.0,
        domain_filter: Optional[str] = None,
    ) -> List[StrategyRecord]:
        """
        Encuentra registros similares a un objetivo dado.

        Usa una combinación de:
        1. Similitud de embedding (si disponible)
        2. Overlap de keywords
        3. Similitud de dominio
        4. Ponderación por success_score y recencia
        """
        query_keywords = set(self._extract_keywords(objective_description))
        query_embedding = self.embedding_fn(objective_description) if self.embedding_fn else None

        scored_records = []

        for rec in self.records:
            # Filtros
            if rec.success_score < min_success_score:
                continue
            if domain_filter and rec.objective_domain != domain_filter:
                continue

            # Calcular score de similitud
            score = 0.0

            # Keyword overlap (Jaccard)
            rec_keywords = set(rec.keywords)
            if query_keywords and rec_keywords:
                intersection = query_keywords & rec_keywords
                union = query_keywords | rec_keywords
                score += len(intersection) / len(union) * 0.4

            # Embedding similarity (cosine)
            if query_embedding and rec.embedding:
                score += self._cosine_similarity(query_embedding, rec.embedding) * 0.3

            # Domain match
            # (simplificado: asumimos que el dominio se extrae de las keywords)

            # Success score boost
            score += rec.success_score * 0.2

            # Recency boost (exponential decay)
            days_old = (datetime.utcnow() - rec.timestamp).days
            recency = max(0, 1 - days_old / self.decay_days)
            score += recency * 0.1

            scored_records.append((score, rec))

        # Ordenar por score descendente
        scored_records.sort(key=lambda x: x[0], reverse=True)

        return [rec for _, rec in scored_records[:top_k]]

    def rank_strategies_for_objective(
        self,
        objective_description: str,
    ) -> List[Dict[str, Any]]:
        """
        Rankea las estrategias más efectivas para un tipo de objetivo.

        Returns:
            Lista de estrategias con métricas agregadas.
        """
        similar = self.find_similar(objective_description, top_k=20)

        # Agrupar por estrategia
        strategy_groups: Dict[str, List[StrategyRecord]] = {}
        for rec in similar:
            strat_key = json.dumps(rec.strategy, sort_keys=True)
            if strat_key not in strategy_groups:
                strategy_groups[strat_key] = []
            strategy_groups[strat_key].append(rec)

        # Calcular métricas agregadas
        ranked = []
        for strat_key, recs in strategy_groups.items():
            success_count = sum(1 for r in recs if r.success)
            total_count = len(recs)
            avg_score = sum(r.success_score for r in recs) / total_count
            avg_duration = sum(r.execution_duration or 0 for r in recs) / total_count if total_count > 0 else 0

            ranked.append({
                "strategy": json.loads(strat_key),
                "success_rate": success_count / total_count,
                "avg_success_score": avg_score,
                "avg_duration": avg_duration,
                "usage_count": total_count,
                "lessons": list(set(r.lesson for r in recs if r.lesson)),
            })

        ranked.sort(key=lambda x: (x["success_rate"], x["avg_success_score"]), reverse=True)
        return ranked

    def get_capability_map(self) -> Dict[str, Dict[str, Any]]:
        """
        Genera un mapa de capacidades basado en la memoria.

        Muestra qué tipos de objetivos el sistema ha demostrado poder resolver.
        """
        domain_stats: Dict[str, Dict[str, Any]] = {}

        for rec in self.records:
            domain = rec.objective_domain or "general"
            if domain not in domain_stats:
                domain_stats[domain] = {
                    "total_attempts": 0,
                    "successes": 0,
                    "failures": 0,
                    "avg_score": 0.0,
                    "strategies_tried": set(),
                }

            stats = domain_stats[domain]
            stats["total_attempts"] += 1
            if rec.success:
                stats["successes"] += 1
            else:
                stats["failures"] += 1
            stats["avg_score"] += rec.success_score
            stats["strategies_tried"].add(json.dumps(rec.strategy, sort_keys=True))

        # Normalizar
        for domain, stats in domain_stats.items():
            if stats["total_attempts"] > 0:
                stats["avg_score"] /= stats["total_attempts"]
            stats["success_rate"] = stats["successes"] / stats["total_attempts"] if stats["total_attempts"] > 0 else 0
            stats["strategies_tried"] = len(stats["strategies_tried"])

        return domain_stats

    # ------------------------------------------------------------------
    # CONSOLIDACIÓN
    # ------------------------------------------------------------------

    def _consolidate(self) -> None:
        """
        Consolida registros en patrones duraderos.

        Inspirado en Open-Sable Ultra-LTM: "Consolida semanas de raw memories
        en durable high-level patterns".
        """
        if len(self.records) < 10:
            return

        # Agrupar por dominio/similitud
        clusters = self._cluster_records()

        for cluster in clusters:
            if len(cluster) < 3:
                continue

            # Generar patrón consolidado
            domain = cluster[0].objective_domain or "general"
            descriptions = [r.objective_description for r in cluster]
            pattern_desc = self._generate_pattern_description(descriptions)

            successes = [r for r in cluster if r.success]
            failures = [r for r in cluster if not r.success]

            pattern = ConsolidatedPattern(
                id=self._generate_id("pattern"),
                pattern_description=pattern_desc,
                domain=domain,
                success_rate=len(successes) / len(cluster),
                avg_duration=sum(r.execution_duration or 0 for r in cluster) / len(cluster),
                common_strategies=[r.strategy for r in cluster[:3]],
                common_failures=list(set(r.failure_type for r in failures if r.failure_type)),
                common_lessons=list(set(r.lesson for r in cluster if r.lesson)),
                occurrence_count=len(cluster),
                first_seen=min(r.timestamp for r in cluster),
                last_seen=max(r.timestamp for r in cluster),
                confidence=min(1.0, len(cluster) / 10),
            )

            self.patterns.append(pattern)

        self._since_last_consolidation = 0

        # Persistir patrones
        if self.persistence_path:
            self._save_patterns()

    def _cluster_records(self) -> List[List[StrategyRecord]]:
        """Clustering simple por overlap de keywords."""
        clusters: List[List[StrategyRecord]] = []
        used = set()

        for rec in self.records:
            if rec.id in used:
                continue

            cluster = [rec]
            used.add(rec.id)
            rec_keywords = set(rec.keywords)

            for other in self.records:
                if other.id in used:
                    continue
                other_keywords = set(other.keywords)
                if rec_keywords & other_keywords:  # Hay overlap
                    cluster.append(other)
                    used.add(other.id)

            clusters.append(cluster)

        return clusters

    def _generate_pattern_description(self, descriptions: List[str]) -> str:
        """Genera una descripción de patrón a partir de múltiples descripciones."""
        # Simplificación: extraer palabras comunes
        words = []
        for desc in descriptions:
            words.extend(desc.lower().split())

        from collections import Counter
        common = Counter(words).most_common(5)
        return "Patrón: " + " ".join(w for w, _ in common)

    # ------------------------------------------------------------------
    # DECAIMIENTO
    # ------------------------------------------------------------------

    def apply_decay(self) -> int:
        """
        Aplica decaimiento temporal a los registros antiguos.

        Returns:
            Número de registros eliminados.
        """
        cutoff = datetime.utcnow() - timedelta(days=self.decay_days)
        original_count = len(self.records)

        self.records = [
            r for r in self.records
            if r.timestamp > cutoff or r.success_score > 0.8  # Conservar los muy exitosos
        ]

        removed = original_count - len(self.records)

        if removed > 0 and self.persistence_path:
            self._save_all()

        return removed

    # ------------------------------------------------------------------
    # PERSISTENCIA
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Carga registros desde disco."""
        if not self.persistence_path:
            return

        records_file = self.persistence_path / "records.jsonl"
        if records_file.exists():
            with open(records_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self.records.append(StrategyRecord.from_dict(data))
                        except Exception:
                            pass

        patterns_file = self.persistence_path / "patterns.jsonl"
        if patterns_file.exists():
            with open(patterns_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self.patterns.append(ConsolidatedPattern(**data))
                        except Exception:
                            pass

    def _append_record(self, record: StrategyRecord) -> None:
        """Añade un registro al archivo JSONL."""
        if not self.persistence_path:
            return

        self.persistence_path.mkdir(parents=True, exist_ok=True)
        records_file = self.persistence_path / "records.jsonl"

        with open(records_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), default=str) + "\n")

    def _save_all(self) -> None:
        """Guarda todos los registros (sobrescribe)."""
        if not self.persistence_path:
            return

        self.persistence_path.mkdir(parents=True, exist_ok=True)
        records_file = self.persistence_path / "records.jsonl"

        with open(records_file, "w", encoding="utf-8") as f:
            for rec in self.records:
                f.write(json.dumps(rec.to_dict(), default=str) + "\n")

    def _save_patterns(self) -> None:
        """Guarda los patrones consolidados."""
        if not self.persistence_path:
            return

        patterns_file = self.persistence_path / "patterns.jsonl"
        with open(patterns_file, "w", encoding="utf-8") as f:
            for pat in self.patterns:
                f.write(json.dumps(asdict(pat), default=str) + "\n")

    # ------------------------------------------------------------------
    # UTILIDADES
    # ------------------------------------------------------------------

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrae keywords de una descripción."""
        # Simplificación: palabras significativas
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "implementar", "módulo", "sistema", "de", "la", "el", "en", "un", "una"}
        words = text.lower().split()
        return [w for w in words if len(w) > 3 and w not in stopwords][:10]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calcula similitud coseno entre dos vectores."""
        if not a or not b or len(a) != len(b):
            return 0.0

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def _generate_id(self, prefix: str) -> str:
        """Genera un ID único."""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

```
