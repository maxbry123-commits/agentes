"""
MemoryGraph — the central data structure that manages the inverted-cone
multi-relational memory graph on top of NetworkX.

Responsibilities:
  - Add / remove / lookup nodes and edges
  - Provide typed neighbourhood queries
  - Extract sub-graphs for Bundle Search
  - Serialise / deserialise the graph for persistence

Design notes
  - NetworkX MultiDiGraph is used as the backend so that parallel edges of
    different types between the same pair of nodes are supported.
  - Each NetworkX node stores the full Pydantic model in its `data` attribute.
  - Each NetworkX edge stores the full Edge model in its `data` attribute.
  - For undirected edge types (semantic), we store a single Edge object and add
    the edge in both directions so that traversal works symmetrically.

Scalability note
  All NetworkX calls are encapsulated inside MemoryGraph methods.  External
  code never touches self._g directly.  If the graph grows beyond ~50 k nodes,
  swap the internals to rustworkx or a graph DB — callers need zero changes.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Optional

import networkx as nx

from .edges import DIRECTED_EDGE_TYPES, Edge, EdgeType
from .nodes import (
    NODE_CLS_MAP,
    Entity,
    Episode,
    Facet,
    FacetPoint,
    NodeBase,
    NodeType,
)

logger = logging.getLogger(__name__)


class MemoryGraph:
    """Inverted-cone multi-relational memory graph."""

    def __init__(self) -> None:
        self._g = nx.MultiDiGraph()
        # Fast lookup indexes: node_type → {node_id: node}
        self._nodes_by_type: dict[NodeType, dict[str, NodeBase]] = defaultdict(dict)
        # edge_type → {edge_id: edge}
        self._edges_by_type: dict[EdgeType, dict[str, Edge]] = defaultdict(dict)
        # entity name (lower) → entity_id  (for deduplication)
        self._entity_name_index: dict[str, str] = {}

    # ── Node operations ──────────────────────────────────────────────

    def add_node(self, node: NodeBase) -> NodeBase:
        """Add a node to the graph. Returns the node (possibly deduplicated)."""
        if isinstance(node, Entity):
            existing_id = self._entity_name_index.get(node.name.lower())
            if existing_id is not None:
                return self._nodes_by_type[NodeType.ENTITY][existing_id]
            self._entity_name_index[node.name.lower()] = node.id

        self._g.add_node(node.id, data=node)
        self._nodes_by_type[node.node_type][node.id] = node
        return node

    def get_node(self, node_id: str) -> Optional[NodeBase]:
        if node_id not in self._g:
            return None
        node_data = self._g.nodes[node_id].get("data")
        if node_data is None:
            return None
        return node_data

    def get_nodes_by_type(self, node_type: NodeType) -> list[NodeBase]:
        return list(self._nodes_by_type[node_type].values())

    def has_node(self, node_id: str) -> bool:
        return node_id in self._g

    def remove_node(self, node_id: str) -> None:
        node = self.get_node(node_id)
        if node is None:
            return
        if isinstance(node, Entity):
            self._entity_name_index.pop(node.name.lower(), None)

        # Collect edge IDs incident to this node BEFORE removing from NetworkX.
        stale_edge_ids: list[tuple[EdgeType, str]] = []
        for _, _, attrs in self._g.out_edges(node_id, data=True):
            e: Edge = attrs["data"]
            stale_edge_ids.append((e.edge_type, e.id))
        for _, _, attrs in self._g.in_edges(node_id, data=True):
            e = attrs["data"]
            stale_edge_ids.append((e.edge_type, e.id))

        self._nodes_by_type[node.node_type].pop(node_id, None)
        self._g.remove_node(node_id)

        for et, eid in stale_edge_ids:
            self._edges_by_type[et].pop(eid, None)

    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        eid = self._entity_name_index.get(name.lower())
        if eid is None:
            return None
        return self._nodes_by_type[NodeType.ENTITY].get(eid)  # type: ignore[return-value]

    @property
    def num_nodes(self) -> int:
        return self._g.number_of_nodes()

    @property
    def num_edges(self) -> int:
        return self._g.number_of_edges()

    # ── Edge operations ──────────────────────────────────────────────

    def add_edge(self, edge: Edge) -> Edge:
        """Add a typed edge. Undirected types get mirrored automatically."""
        source_node = self.get_node(edge.source_id)
        target_node = self.get_node(edge.target_id)
        if source_node is None or target_node is None:
            raise ValueError(
                "Cannot add edge when source/target node is missing: "
                f"{edge.source_id} -> {edge.target_id}"
            )

        self._g.add_edge(
            edge.source_id,
            edge.target_id,
            key=edge.id,
            data=edge,
        )
        self._edges_by_type[edge.edge_type][edge.id] = edge

        if edge.edge_type not in DIRECTED_EDGE_TYPES:
            mirror_key = f"{edge.id}_r"
            self._g.add_edge(
                edge.target_id,
                edge.source_id,
                key=mirror_key,
                data=edge,
            )
        return edge

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        for d in self._edges_by_type.values():
            if edge_id in d:
                return d[edge_id]
        return None

    def remove_edge(self, edge_id: str) -> None:
        """Remove a single edge by its ID."""
        edge = self.get_edge(edge_id)
        if edge is None:
            return

        try:
            self._g.remove_edge(edge.source_id, edge.target_id, key=edge.id)
        except nx.NetworkXError:
            pass

        if edge.edge_type not in DIRECTED_EDGE_TYPES:
            mirror_key = f"{edge.id}_r"
            try:
                self._g.remove_edge(edge.target_id, edge.source_id, key=mirror_key)
            except nx.NetworkXError:
                pass

        self._edges_by_type[edge.edge_type].pop(edge.id, None)

    def get_edges_by_type(self, edge_type: EdgeType) -> list[Edge]:
        return list(self._edges_by_type[edge_type].values())

    def get_edges_between(
        self,
        source_id: str,
        target_id: str,
        edge_type: Optional[EdgeType] = None,
    ) -> list[Edge]:
        """Return all edges from source to target, optionally filtered by type."""
        if not self._g.has_node(source_id) or not self._g.has_node(target_id):
            return []
        edges: list[Edge] = []
        edge_data = self._g.get_edge_data(source_id, target_id)
        if edge_data is None:
            return []
        for _key, attrs in edge_data.items():
            e: Edge = attrs["data"]
            if edge_type is None or e.edge_type == edge_type:
                edges.append(e)
        return edges

    # ── Neighbourhood queries ────────────────────────────────────────

    def neighbors(
        self,
        node_id: str,
        edge_types: Optional[set[EdgeType]] = None,
        direction: str = "both",
    ) -> list[tuple[str, Edge]]:
        """
        Return (neighbour_id, edge) pairs reachable from *node_id*.

        Parameters
        ----------
        edge_types : filter by edge type (None = all)
        direction  : "out", "in", or "both"
        """
        if not self.has_node(node_id):
            return []

        results: list[tuple[str, Edge]] = []
        seen: set[tuple[str, str]] = set()

        def _append_neighbor(neighbor_id: str, edge: Edge) -> None:
            if direction == "both":
                dedup_key = (neighbor_id, edge.id)
                if dedup_key in seen:
                    return
                seen.add(dedup_key)
            results.append((neighbor_id, edge))

        if direction in ("out", "both"):
            for _, tgt, attrs in self._g.out_edges(node_id, data=True):
                e: Edge = attrs["data"]
                if edge_types is None or e.edge_type in edge_types:
                    _append_neighbor(tgt, e)

        if direction in ("in", "both"):
            for src, _, attrs in self._g.in_edges(node_id, data=True):
                e = attrs["data"]
                if edge_types is None or e.edge_type in edge_types:
                    _append_neighbor(src, e)

        return results

    def k_hop_neighbors(
        self,
        seed_ids: Iterable[str],
        k: int = 1,
        edge_types: Optional[set[EdgeType]] = None,
    ) -> set[str]:
        """BFS up to *k* hops from seed nodes, returning all visited node ids."""
        visited: set[str] = set(seed_ids)
        frontier = set(visited)
        for _ in range(k):
            next_frontier: set[str] = set()
            for nid in frontier:
                for nbr_id, _ in self.neighbors(nid, edge_types=edge_types):
                    if nbr_id not in visited:
                        next_frontier.add(nbr_id)
            visited |= next_frontier
            frontier = next_frontier
            if not frontier:
                break
        return visited

    # ── Sub-graph extraction ─────────────────────────────────────────

    def extract_subgraph(self, node_ids: set[str]) -> nx.MultiDiGraph:
        """Return the induced sub-graph over *node_ids*."""
        return self._g.subgraph(node_ids).copy()

    # ── Hierarchy traversal helpers ──────────────────────────────────

    def get_parent_episodes(self, node_id: str) -> list[Episode]:
        """Walk up belongs_to edges from any node until we reach Episodes."""
        episodes: list[Episode] = []
        visited: set[str] = set()
        stack = [node_id]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            node = self.get_node(current)
            if node is None:
                continue
            if isinstance(node, Episode):
                episodes.append(node)
                continue
            for nbr_id, edge in self.neighbors(
                current,
                edge_types={EdgeType.BELONGS_TO},
                direction="out",
            ):
                stack.append(nbr_id)
        return episodes

    def get_child_nodes(self, node_id: str, depth: int = 1) -> list[NodeBase]:
        """Walk down belongs_to edges (reverse direction) up to *depth* levels."""
        children: list[NodeBase] = []
        visited: set[str] = set()
        frontier = {node_id}
        for _ in range(depth):
            next_frontier: set[str] = set()
            for nid in frontier:
                for nbr_id, edge in self.neighbors(
                    nid,
                    edge_types={EdgeType.BELONGS_TO},
                    direction="in",
                ):
                    if nbr_id not in visited:
                        visited.add(nbr_id)
                        child = self.get_node(nbr_id)
                        if child is not None:
                            children.append(child)
                            next_frontier.add(nbr_id)
            frontier = next_frontier
        return children

    # ── Statistics ───────────────────────────────────────────────────

    def stats(self) -> dict:
        """Return a summary dict of the graph contents."""
        return {
            "total_nodes": self.num_nodes,
            "total_edges": self.num_edges,
            "nodes_by_type": {
                nt.value: len(d) for nt, d in self._nodes_by_type.items()
            },
            "edges_by_type": {
                et.value: len(d) for et, d in self._edges_by_type.items()
            },
        }

    # ── Persistence ─────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialise the graph to a JSON-friendly dict."""
        nodes: list[dict[str, Any]] = []
        for nt, bucket in self._nodes_by_type.items():
            for node in bucket.values():
                d = node.model_dump(mode="json")
                d["__node_type__"] = nt.value
                nodes.append(d)

        edges: list[dict[str, Any]] = []
        for et, bucket in self._edges_by_type.items():
            for edge in bucket.values():
                edges.append(edge.model_dump(mode="json"))

        return {"nodes": nodes, "edges": edges}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryGraph:
        """Restore a ``MemoryGraph`` from a dict produced by ``to_dict``."""
        graph = cls()
        for nd in data.get("nodes", []):
            nt_str = nd.pop("__node_type__", None)
            if nt_str is None:
                logger.warning("Skipping node without __node_type__: %s", nd.get("id"))
                continue
            try:
                nt = NodeType(nt_str)
            except ValueError:
                logger.warning("Unknown node type '%s', skipping", nt_str)
                continue
            node_cls = NODE_CLS_MAP[nt]
            node = node_cls.model_validate(nd)
            graph.add_node(node)

        for ed in data.get("edges", []):
            edge = Edge.model_validate(ed)
            try:
                graph.add_edge(edge)
            except ValueError:
                logger.warning(
                    "Skipping edge %s: missing source/target node", ed.get("id"),
                )
        return graph

    def save(self, path: Path | str) -> None:
        """Write the graph to a JSON file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path | str) -> MemoryGraph:
        """Load a graph from a JSON file written by ``save``."""
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def __repr__(self) -> str:
        s = self.stats()
        return (
            f"MemoryGraph(nodes={s['total_nodes']}, edges={s['total_edges']}, "
            f"entities={s['nodes_by_type'].get('entity', 0)}, "
            f"episodes={s['nodes_by_type'].get('episode', 0)})"
        )
