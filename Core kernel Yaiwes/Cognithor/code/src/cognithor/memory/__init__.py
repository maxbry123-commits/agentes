"""Jarvis 5-Tier Cognitive Memory System. [B§4]

Public API:
    MemoryManager      -- Central interface (use this!)
    CoreMemory         -- Tier 1: Identitaet (CORE.md)
    EpisodicMemory     -- Tier 2: Daily log
    SemanticMemory     -- Tier 3: Knowledge graph
    ProceduralMemory   -- Tier 4: Learned skills
    WorkingMemoryManager -- Tier 5: Session context
    HybridSearch       -- 3-channel search
    MemoryIndex        -- SQLite Index
    EmbeddingClient    -- Embedding generation
"""

from cognithor.memory.chunker import chunk_file, chunk_text
from cognithor.memory.core_memory import CoreMemory
from cognithor.memory.embeddings import EmbeddingClient, cosine_similarity
from cognithor.memory.episodic import EpisodicMemory
from cognithor.memory.hygiene import MemoryHygieneEngine
from cognithor.memory.indexer import MemoryIndex
from cognithor.memory.integrity import (
    ContradictionDetector,
    DecisionExplainer,
    DuplicateDetector,
    IntegrityChecker,
    MemoryVersionControl,
    PlausibilityChecker,
)
from cognithor.memory.manager import MemoryManager
from cognithor.memory.procedural import ProceduralMemory
from cognithor.memory.search import HybridSearch, recency_decay
from cognithor.memory.semantic import SemanticMemory
from cognithor.memory.watcher import MemoryWatcher
from cognithor.memory.working import WorkingMemoryManager

__all__ = [
    "CoreMemory",
    "EmbeddingClient",
    "EpisodicMemory",
    "HybridSearch",
    "MemoryHygieneEngine",
    "MemoryIndex",
    "MemoryManager",
    "MemoryWatcher",
    "ProceduralMemory",
    "SemanticMemory",
    "WorkingMemoryManager",
    "chunk_file",
    "chunk_text",
    "cosine_similarity",
    "recency_decay",
]
