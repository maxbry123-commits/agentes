"""Data models and exception hierarchy for Hierarchical Document Reasoning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime
    from pathlib import Path

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class HierarchicalIndexError(Exception):
    """Base exception for hierarchical indexing errors."""


class ParserError(HierarchicalIndexError):
    """Raised when document parsing fails."""


class TreeBuildError(HierarchicalIndexError):
    """Raised when tree construction fails."""


class NodeSelectionError(HierarchicalIndexError):
    """Raised when node selection fails."""


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RawSection:
    """A flat section extracted by a parser before tree construction."""

    level: int
    title: str
    content: str
    position: int
    page: int | None = None


@dataclass(frozen=True)
class TreeNode:
    """A single node in a document tree."""

    node_id: str
    document_id: str
    parent_id: str | None
    level: int
    title: str
    summary: str
    content: str
    content_hash: str
    token_count: int
    children_ids: tuple[str, ...]
    position: int
    page_number: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentTree:
    """The full tree representation of a parsed document."""

    document_id: str
    source_path: Path
    source_hash: str
    title: str
    root_node_id: str
    nodes: Mapping[str, TreeNode]
    created_at: datetime
    parser_used: str
    total_tokens: int


@dataclass(frozen=True)
class SelectedNode:
    """A node selected during retrieval with scoring metadata."""

    node: TreeNode
    depth: int
    reasoning: str
    score: float


@dataclass(frozen=True)
class DocumentMetadata:
    """Lightweight metadata about an indexed document."""

    document_id: str
    title: str
    source_path: str
    parser_used: str
    total_tokens: int
    node_count: int
    created_at: str
