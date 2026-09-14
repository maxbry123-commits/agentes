"""
Node definitions for the Inverted Cone Memory Architecture.

Four-layer hierarchy ordered by **retrieval granularity** (NOT semantic containment):

  Entity (cone tip, finest anchor)
    → FacetPoint (atomic fact mentioning an entity)
      → Facet (thematic group of FacetPoints)
        → Episode (cone base, coarsest — the full context chunk)

The "→" means belongs_to, always directed fine → coarse (child → parent).
This is the reverse of traditional ontology (where Entity HAS Facets HAS
FacetPoints).  Here the ordering reflects how Bundle Search starts from the
sharpest anchor (Entity) and propagates cost upward to reach Episodes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import numpy as np
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    ENTITY = "entity"
    FACET_POINT = "facet_point"
    FACET = "facet"
    EPISODE = "episode"


class NodeBase(BaseModel):
    """Base class for all memory graph nodes."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    embedding: Optional[list[float]] = Field(default=None, exclude=True)

    @property
    def node_type(self) -> NodeType:
        raise NotImplementedError

    @property
    def text_for_embedding(self) -> str:
        """Text representation used for vectorisation."""
        raise NotImplementedError

    def embedding_array(self) -> Optional[np.ndarray]:
        if self.embedding is None:
            return None
        return np.array(self.embedding, dtype=np.float32)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NodeBase):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class Entity(NodeBase):
    """
    Cone tip — the finest-grained node.
    Represents a named entity (person, place, organisation, concept).
    """

    name: str
    entity_type: str = "concept"  # person / place / org / concept

    @property
    def node_type(self) -> NodeType:
        return NodeType.ENTITY

    @property
    def text_for_embedding(self) -> str:
        return self.name


class FacetPoint(NodeBase):
    """
    Atomic factual assertion about an entity or topic.
    E.g. "张博士在 2023 年加入 MIT"
    """

    content: str
    related_entity_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    timestamp_text: Optional[str] = None  # raw temporal expression

    @property
    def node_type(self) -> NodeType:
        return NodeType.FACET_POINT

    @property
    def text_for_embedding(self) -> str:
        return self.content


class Facet(NodeBase):
    """
    Thematic dimension that groups related FacetPoints.
    E.g. "张博士的职业经历"
    """

    theme: str

    @property
    def node_type(self) -> NodeType:
        return NodeType.FACET

    @property
    def text_for_embedding(self) -> str:
        return self.theme


class Episode(NodeBase):
    """
    Cone base — the coarsest-grained node.
    A complete semantic event / knowledge unit returned to the user.
    """

    summary: str
    source_chunk_ids: list[str] = Field(default_factory=list)
    timestamp: Optional[datetime] = None
    timestamp_text: Optional[str] = None
    key_sentences: list[str] = Field(default_factory=list)

    @property
    def node_type(self) -> NodeType:
        return NodeType.EPISODE

    @property
    def text_for_embedding(self) -> str:
        """Summary + deduplicated key sentences for richer embedding."""
        if not self.key_sentences:
            return self.summary

        # Step 1: pairwise substring dedup within key_sentences.
        # Keep supersets; drop sentences contained by another.
        internally_unique: list[str] = []
        for s in self.key_sentences:
            s_lower = s.lower()
            if any(s_lower in kept.lower() for kept in internally_unique):
                continue
            internally_unique = [
                kept for kept in internally_unique
                if kept.lower() not in s_lower
            ]
            internally_unique.append(s)

        # Step 2: drop sentences already present in summary (safety layer).
        summary_lower = self.summary.lower()
        unique_sentences = [
            s for s in internally_unique
            if s.lower() not in summary_lower
        ]

        if not unique_sentences:
            return self.summary
        return self.summary + "\n\n" + " ".join(unique_sentences)


NODE_CLS_MAP: dict[NodeType, type[NodeBase]] = {
    NodeType.ENTITY: Entity,
    NodeType.FACET_POINT: FacetPoint,
    NodeType.FACET: Facet,
    NodeType.EPISODE: Episode,
}
