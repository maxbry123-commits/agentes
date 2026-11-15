"""
Ingestion pipeline — the top-level orchestrator that turns raw text chunks
into a populated ``MemoryGraph`` with FAISS vector indexes.

Typical usage::

    pipeline = IngestionPipeline()
    for chunk in chunks:
        pipeline.ingest(chunk)
    pipeline.save_checkpoint("data/checkpoint")
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional

from mmem.config import MMemConfig, get_config
from mmem.core.edges import EdgeType
from mmem.core.graph import MemoryGraph
from mmem.indexing.vector_store import VectorStore
from mmem.utils.embedding import EmbeddingModel, get_embedder
from mmem.utils.llm import LLMClient, get_llm_client

from .consolidation import run_consolidation
from .extractor import Extractor
from .graph_builder import BuildResult, GraphBuilder

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# ChunkStore — lightweight map from chunk_id to raw text
# ═══════════════════════════════════════════════════════════════════════


class ChunkStore:
    """Stores raw chunk text keyed by chunk_id, separate from the graph."""

    def __init__(self) -> None:
        self._chunks: dict[str, str] = {}

    def add(self, chunk_id: str, text: str) -> None:
        self._chunks[chunk_id] = text

    def get(self, chunk_id: str) -> str | None:
        return self._chunks.get(chunk_id)

    def __len__(self) -> int:
        return len(self._chunks)

    def __contains__(self, chunk_id: str) -> bool:
        return chunk_id in self._chunks

    def save(self, path: Path | str) -> None:
        Path(path).write_text(
            json.dumps(self._chunks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path | str) -> ChunkStore:
        store = cls()
        p = Path(path)
        if p.exists():
            store._chunks = json.loads(p.read_text(encoding="utf-8"))
        return store


_EDGE_INDEX_MAP: dict[EdgeType, str | None] = {
    EdgeType.BELONGS_TO: None,
    EdgeType.SEMANTIC: "edge_semantic",
    EdgeType.TEMPORAL: "edge_relation",
    EdgeType.CAUSAL: "edge_relation",
    EdgeType.EVOLUTION: "edge_relation",
    EdgeType.INVOLVES_ENTITY: "edge_relation",
}


class IngestionPipeline:
    """Orchestrates chunk → extract → build → vectorise → consolidate."""

    def __init__(
        self,
        config: Optional[MMemConfig] = None,
        graph: Optional[MemoryGraph] = None,
        vector_store: Optional[VectorStore] = None,
        embedder: Optional[EmbeddingModel] = None,
        llm_client: Optional[LLMClient] = None,
        chunk_store: Optional[ChunkStore] = None,
    ) -> None:
        self._config = config or get_config()

        self._graph = graph or MemoryGraph()
        self._vs = vector_store or VectorStore(
            dimension=self._config.embedding.dimension,
        )
        self._embedder = embedder or get_embedder()
        self._chunk_store = chunk_store or ChunkStore()

        llm = llm_client or get_llm_client()
        self._extractor = Extractor(llm_client=llm, config=self._config)
        self._builder = GraphBuilder(
            self._graph, self._vs, self._embedder, self._config,
        )

        self._seen_hashes: set[str] = set()
        self._episode_count: int = 0

    # ── Public properties ─────────────────────────────────────────────

    @property
    def graph(self) -> MemoryGraph:
        return self._graph

    @property
    def vector_store(self) -> VectorStore:
        return self._vs

    @property
    def chunk_store(self) -> ChunkStore:
        return self._chunk_store

    # ── Core ingestion ────────────────────────────────────────────────

    def ingest(self, chunk: str) -> BuildResult | None:
        """Ingest a single text chunk. Returns ``None`` if deduplicated."""
        chunk_hash = _sha256(chunk)
        if chunk_hash in self._seen_hashes:
            logger.debug("Chunk already ingested (hash=%s), skipping", chunk_hash[:12])
            return None

        chunk_id = chunk_hash[:12]
        self._chunk_store.add(chunk_id, chunk)

        result = self._extractor.extract(chunk)
        if self._config.write.enable_key_sentences_embedding:
            key_sentences = self._extractor.extract_key_sentences(chunk)
        else:
            key_sentences = []
        br = self._builder.build(result, chunk_id, key_sentences=key_sentences)
        self._vectorize_and_index(br)
        self._episode_count += 1
        self._maybe_consolidate()
        self._seen_hashes.add(chunk_hash)

        return br

    # ── Stats ─────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Return a summary of the pipeline's current state."""
        return {
            "graph": self._graph.stats(),
            "vector_store": {
                name: self._vs.count(name)
                for name in self._vs.index_names
            },
            "episode_count": self._episode_count,
            "ingested_chunks": len(self._seen_hashes),
        }

    # ── Persistence ───────────────────────────────────────────────────

    def save_checkpoint(self, path: Path | str) -> None:
        """Persist full pipeline state to a directory."""
        root = Path(path)
        root.mkdir(parents=True, exist_ok=True)

        self._graph.save(root / "graph.json")
        self._vs.save_dir(root / "faiss")
        self._chunk_store.save(root / "chunks.json")

        state = {
            "seen_hashes": sorted(self._seen_hashes),
            "episode_count": self._episode_count,
        }
        (root / "pipeline_state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load_checkpoint(
        cls,
        path: Path | str,
        config: Optional[MMemConfig] = None,
        embedder: Optional[EmbeddingModel] = None,
        llm_client: Optional[LLMClient] = None,
    ) -> IngestionPipeline:
        """Restore a pipeline from a checkpoint directory."""
        root = Path(path)
        graph = MemoryGraph.load(root / "graph.json")
        vs = VectorStore.load_dir(root / "faiss")
        cs = ChunkStore.load(root / "chunks.json")

        pipeline = cls(
            config=config,
            graph=graph,
            vector_store=vs,
            embedder=embedder,
            llm_client=llm_client,
            chunk_store=cs,
        )

        state_path = root / "pipeline_state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            pipeline._seen_hashes = set(state.get("seen_hashes", []))
            pipeline._episode_count = state.get("episode_count", 0)

        return pipeline

    # ── Vectorisation ─────────────────────────────────────────────────

    def _vectorize_and_index(self, br: BuildResult) -> None:
        """Batch-embed new nodes and edges, write to FAISS.

        Skips nodes already indexed by GraphBuilder (entities and facets
        that were written eagerly for intra-chunk dedup).
        """
        skip_ids = set(br.entity_ids_already_indexed) | set(br.facet_ids_already_indexed)

        node_batches: dict[str, list[tuple[str, str]]] = {}
        for nid in br.new_node_ids:
            if nid in skip_ids:
                continue
            node = self._graph.get_node(nid)
            if node is None:
                continue
            index_name = node.node_type.value
            node_batches.setdefault(index_name, []).append(
                (nid, node.text_for_embedding),
            )

        edge_batches: dict[str, list[tuple[str, str]]] = {}
        for eid in br.new_edge_ids:
            edge = self._graph.get_edge(eid)
            if edge is None or not edge.description:
                continue
            index_name = _EDGE_INDEX_MAP.get(edge.edge_type)
            if index_name is None:
                continue
            edge_batches.setdefault(index_name, []).append(
                (eid, edge.text_for_embedding),
            )

        all_batches = {**node_batches, **edge_batches}
        for index_name, items in all_batches.items():
            if not items:
                continue
            ids = [item[0] for item in items]
            texts = [item[1] for item in items]
            embeddings = self._embedder.embed_batch(texts)
            self._vs.add(index_name, ids, embeddings)

    # ── Consolidation ─────────────────────────────────────────────────

    def _maybe_consolidate(self) -> None:
        """Trigger causal consolidation if conditions are met."""
        if not self._config.write.enable_causal_consolidation:
            return
        interval = self._config.write.causal_consolidation_interval
        if self._episode_count % interval != 0:
            return
        new_edge_ids = run_consolidation(
            self._graph, self._vs, self._extractor, self._embedder, self._config,
        )
        if new_edge_ids:
            logger.info(
                "Consolidation created %d causal edges at episode %d",
                len(new_edge_ids),
                self._episode_count,
            )


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
