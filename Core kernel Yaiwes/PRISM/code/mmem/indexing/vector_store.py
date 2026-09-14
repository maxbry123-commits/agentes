"""
FAISS-backed vector store managing multiple named indexes.

Each index uses ``faiss.IndexFlatIP`` (inner product on L2-normalised
vectors = cosine similarity).  The class maintains a parallel ``list[str]``
per index that maps FAISS's internal sequential integer IDs back to the
application-level string IDs used by nodes and edges.

Persistence is handled via ``save_dir`` / ``load_dir``:
  - One ``.faiss`` file per index  (``faiss.write_index`` / ``read_index``)
  - One ``metadata.json`` sidecar with dimension, index names, and id-maps
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_INDEX_NAMES: list[str] = [
    "entity",
    "facet_point",
    "facet",
    "episode",
    "edge_belongs_to",
    "edge_relation",
    "edge_semantic",
]


class VectorStore:
    """Manages multiple named FAISS ``IndexFlatIP`` indexes."""

    def __init__(
        self,
        dimension: int = 384,
        index_names: Optional[list[str]] = None,
    ) -> None:
        self._dimension = dimension
        self._index_names: list[str] = list(index_names or DEFAULT_INDEX_NAMES)
        self._indexes: dict[str, faiss.IndexFlatIP] = {}
        self._id_maps: dict[str, list[str]] = {}

        for name in self._index_names:
            self._indexes[name] = faiss.IndexFlatIP(dimension)
            self._id_maps[name] = []

    # ── Query ─────────────────────────────────────────────────────────

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def index_names(self) -> list[str]:
        return list(self._index_names)

    def has_index(self, index_name: str) -> bool:
        """Return whether *index_name* is a registered index."""
        return index_name in self._indexes

    def count(self, index_name: str) -> int:
        """Return the number of vectors in the named index."""
        self._require_index(index_name)
        return self._indexes[index_name].ntotal

    # ── Add ───────────────────────────────────────────────────────────

    def add(
        self,
        index_name: str,
        ids: list[str],
        embeddings: np.ndarray,
    ) -> None:
        """Append vectors to the named index.

        Parameters
        ----------
        index_name : registered index name
        ids        : string IDs matching each row of *embeddings*
        embeddings : ``(n, dimension)`` float32 array, **already L2-normalised**
        """
        self._require_index(index_name)
        if len(ids) == 0:
            return
        emb = self._validate_embeddings(embeddings, expected_rows=len(ids))
        self._indexes[index_name].add(emb)
        self._id_maps[index_name].extend(ids)

    # ── Search ────────────────────────────────────────────────────────

    def search(
        self,
        index_name: str,
        query_vec: np.ndarray,
        top_k: int = 10,
    ) -> list[tuple[str, float]]:
        """Search a single index.

        Returns a list of ``(id, score)`` pairs sorted by descending score.
        Returns ``[]`` when the index is empty.
        """
        self._require_index(index_name)
        index = self._indexes[index_name]
        if index.ntotal == 0:
            return []

        effective_k = min(top_k, index.ntotal)
        qvec = self._as_query_vector(query_vec)
        scores, indices = index.search(qvec, effective_k)

        id_map = self._id_maps[index_name]
        results: list[tuple[str, float]] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0:
                continue
            results.append((id_map[idx], float(score)))
        return results

    def search_multi(
        self,
        query_vec: np.ndarray,
        top_k: int = 10,
    ) -> dict[str, list[tuple[str, float]]]:
        """Search all indexes sequentially.

        Returns ``{index_name: [(id, score), ...]}`` for every registered
        index (empty indexes map to ``[]``).
        """
        out: dict[str, list[tuple[str, float]]] = {}
        for name in self._index_names:
            out[name] = self.search(name, query_vec, top_k=top_k)
        return out

    # ── Persistence ───────────────────────────────────────────────────

    def save_dir(self, path: Path | str) -> None:
        """Persist all indexes and id-maps to *path*."""
        dirpath = Path(path)
        dirpath.mkdir(parents=True, exist_ok=True)

        for name in self._index_names:
            faiss.write_index(
                self._indexes[name],
                str(dirpath / f"{name}.faiss"),
            )

        meta = {
            "dimension": self._dimension,
            "index_names": self._index_names,
            "id_maps": self._id_maps,
        }
        (dirpath / "metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load_dir(cls, path: Path | str) -> VectorStore:
        """Restore a ``VectorStore`` from a directory written by ``save_dir``."""
        dirpath = Path(path)
        meta_path = dirpath / "metadata.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"metadata.json not found in {dirpath}")

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        dimension: int = meta["dimension"]
        index_names: list[str] = meta["index_names"]
        id_maps: dict[str, list[str]] = meta["id_maps"]

        store = cls(dimension=dimension, index_names=index_names)

        for name in index_names:
            faiss_path = dirpath / f"{name}.faiss"
            if faiss_path.exists():
                store._indexes[name] = faiss.read_index(str(faiss_path))
            store._id_maps[name] = id_maps.get(name, [])

        return store

    # ── Internals ─────────────────────────────────────────────────────

    def _require_index(self, index_name: str) -> None:
        if index_name not in self._indexes:
            raise KeyError(
                f"Unknown index '{index_name}'. "
                f"Registered indexes: {self._index_names}"
            )

    def _validate_embeddings(
        self,
        embeddings: np.ndarray,
        expected_rows: int,
    ) -> np.ndarray:
        emb = np.ascontiguousarray(embeddings, dtype=np.float32)
        if emb.ndim == 1:
            emb = emb.reshape(1, -1)
        if emb.shape[0] != expected_rows:
            raise ValueError(
                f"Expected {expected_rows} rows, got {emb.shape[0]}"
            )
        if emb.shape[1] != self._dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self._dimension}, "
                f"got {emb.shape[1]}"
            )
        return emb

    def _as_query_vector(self, query_vec: np.ndarray) -> np.ndarray:
        qvec = np.ascontiguousarray(query_vec, dtype=np.float32)
        if qvec.ndim == 1:
            qvec = qvec.reshape(1, -1)
        if qvec.shape[1] != self._dimension:
            raise ValueError(
                f"Query dimension mismatch: expected {self._dimension}, "
                f"got {qvec.shape[1]}"
            )
        return qvec

    def __repr__(self) -> str:
        counts = {n: self._indexes[n].ntotal for n in self._index_names}
        total = sum(counts.values())
        return f"VectorStore(dim={self._dimension}, total_vectors={total}, indexes={counts})"
