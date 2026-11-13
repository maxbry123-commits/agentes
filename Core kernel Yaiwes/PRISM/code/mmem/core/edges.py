"""
Edge definitions for the Inverted Cone Memory Architecture.

Six edge types:
  1. belongs_to       — hierarchical, always fine→coarse (Entity→FP→Facet→Episode)
  2. semantic         — undirected, cosine similarity > threshold (same-layer)
  3. temporal         — directed, time-sequence between Episodes / FacetPoints
  4. causal           — directed, cause→effect between Episodes (async LLM)
  5. evolution        — directed, same-entity state change across FacetPoints
  6. involves_entity  — directed shortcut, Entity→Facet or Entity→Episode

belongs_to direction convention:
  source = child (finer granularity), target = parent (coarser granularity).
  get_parent_episodes() follows out-edges; get_child_nodes() follows in-edges.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import numpy as np
from pydantic import BaseModel, Field


class EdgeType(str, Enum):
    BELONGS_TO = "belongs_to"
    SEMANTIC = "semantic"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    EVOLUTION = "evolution"
    INVOLVES_ENTITY = "involves_entity"


# Which edge types are directed
DIRECTED_EDGE_TYPES = {
    EdgeType.BELONGS_TO,
    EdgeType.TEMPORAL,
    EdgeType.CAUSAL,
    EdgeType.EVOLUTION,
    EdgeType.INVOLVES_ENTITY,
}


class Edge(BaseModel):
    """A typed, optionally weighted edge with natural-language description."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    source_id: str
    target_id: str
    edge_type: EdgeType
    description: str = ""  # NL description, vectorised for cost propagation
    weight: float = 1.0
    confidence: float = 1.0  # mainly for causal edges (LLM confidence)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    embedding: Optional[list[float]] = Field(default=None, exclude=True)

    @property
    def is_directed(self) -> bool:
        return self.edge_type in DIRECTED_EDGE_TYPES

    @property
    def text_for_embedding(self) -> str:
        return self.description

    def embedding_array(self) -> Optional[np.ndarray]:
        if self.embedding is None:
            return None
        return np.array(self.embedding, dtype=np.float32)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


# ── Helpers for creating typed edges ──────────────────────────────────

def make_belongs_to(child_id: str, parent_id: str, description: str = "") -> Edge:
    """Create a hierarchical belongs_to edge (child → parent)."""
    return Edge(
        source_id=child_id,
        target_id=parent_id,
        edge_type=EdgeType.BELONGS_TO,
        description=description or f"belongs_to ({child_id} → {parent_id})",
    )


def make_semantic(node_a: str, node_b: str, similarity: float, description: str = "") -> Edge:
    """Create an undirected semantic similarity edge."""
    return Edge(
        source_id=node_a,
        target_id=node_b,
        edge_type=EdgeType.SEMANTIC,
        weight=1.0 - similarity,  # lower weight = stronger link
        description=description,
    )


def make_temporal(earlier_id: str, later_id: str, description: str = "") -> Edge:
    """Create a directed temporal edge (earlier → later)."""
    return Edge(
        source_id=earlier_id,
        target_id=later_id,
        edge_type=EdgeType.TEMPORAL,
        description=description or "temporal sequence",
    )


def make_causal(
    cause_id: str,
    effect_id: str,
    description: str,
    confidence: float = 1.0,
) -> Edge:
    """Create a directed causal edge (cause → effect)."""
    return Edge(
        source_id=cause_id,
        target_id=effect_id,
        edge_type=EdgeType.CAUSAL,
        description=description,
        confidence=confidence,
    )


def make_evolution(
    earlier_fp_id: str,
    later_fp_id: str,
    description: str = "",
) -> Edge:
    """Create an entity-evolution edge between FacetPoints of the same entity."""
    return Edge(
        source_id=earlier_fp_id,
        target_id=later_fp_id,
        edge_type=EdgeType.EVOLUTION,
        description=description or "entity state evolution",
    )


def make_involves_entity(
    entity_id: str,
    target_id: str,
    description: str = "",
) -> Edge:
    """Create a directed shortcut edge from Entity to Facet or Episode."""
    return Edge(
        source_id=entity_id,
        target_id=target_id,
        edge_type=EdgeType.INVOLVES_ENTITY,
        description=description,
    )
