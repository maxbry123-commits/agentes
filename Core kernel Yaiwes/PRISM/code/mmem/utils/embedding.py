"""
Embedding utility — wraps sentence-transformers for vectorising nodes and edges.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from mmem.config import EmbeddingConfig, get_config


class EmbeddingModel:
    """Lazy-loading wrapper around SentenceTransformer."""

    def __init__(self, config: Optional[EmbeddingConfig] = None) -> None:
        self._config = config or get_config().embedding
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                self._config.model_name,
                device=self._config.device,
            )

    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string. Returns shape (dim,)."""
        self._load()
        vec = self._model.encode(
            text, normalize_embeddings=True, show_progress_bar=False
        )
        return np.array(vec, dtype=np.float32)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts. Returns shape (n, dim)."""
        self._load()
        vecs = self._model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=self._config.batch_size,
            show_progress_bar=False,
        )
        return np.array(vecs, dtype=np.float32)

    @property
    def dimension(self) -> int:
        return self._config.dimension


_default_embedder: EmbeddingModel | None = None


def get_embedder() -> EmbeddingModel:
    global _default_embedder
    if _default_embedder is None:
        _default_embedder = EmbeddingModel()
    return _default_embedder
