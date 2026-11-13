"""
Centralised configuration for M-Mem.

All tuneable hyper-parameters, model choices, and thresholds live here.
Values can be overridden via environment variables or at runtime.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── LLM Configuration ───────────────────────────────────────────────

class LLMConfig(BaseModel):
    api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    base_url: str = Field(
        default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
    extraction_model: str = "gpt-4o-mini"
    causal_model: str = "gpt-4o-mini"
    qa_model: str = "gpt-4o-mini"
    judge_model: str = "gpt-4o-mini"
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_retries: int = Field(default=3, ge=1, le=10)
    timeout: float = Field(default=60.0, gt=0)
    backoff_base: float = Field(default=2.0, ge=1.0, le=10.0)
    backoff_max: float = Field(default=60.0, gt=0)


# ── Embedding Configuration ─────────────────────────────────────────

class EmbeddingConfig(BaseModel):
    model_name: str = "all-MiniLM-L6-v2"
    dimension: int = Field(default=384, gt=0)
    batch_size: int = Field(default=64, gt=0)
    device: str = "cpu"


# ── Graph / Write Configuration ─────────────────────────────────────

class WriteConfig(BaseModel):
    semantic_similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    causal_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    causal_consolidation_interval: int = Field(default=5, ge=1)
    enable_causal_consolidation: bool = True
    enable_fallback_extractor: bool = True
    entity_merge_threshold: float = Field(default=0.90, ge=0.5, le=1.0)
    # Round4 experiment: extracting key sentences and appending them to the
    # Episode embedding text. Kept as negative ablation — default OFF because
    # under MiniLM-384 it trades single_hop/temporal accuracy for multi_hop.
    enable_key_sentences_embedding: bool = False


# ── Retrieval Configuration ─────────────────────────────────────────

class RetrievalConfig(BaseModel):
    # Phase 1: Anchor Discovery
    wide_search_top_k: int = Field(default=30, ge=10, le=200)

    # Phase 2: Subgraph Extraction
    max_relevant_ids: int = Field(default=80, ge=20, le=500)

    # Phase 3: Path cost parameters
    edge_miss_cost: float = Field(default=0.9, ge=0.1, le=2.0)
    hop_cost: float = Field(default=0.05, ge=0.0, le=0.5)
    belongs_to_cost: float = Field(default=0.02, ge=0.0, le=0.2)
    direct_episode_penalty: float = Field(default=0.3, ge=0.0, le=1.0)

    # Query-sensitive discounts
    temporal_discount: float = Field(default=0.5, gt=0.0, le=1.0)
    causal_discount: float = Field(default=0.5, gt=0.0, le=1.0)
    evolution_discount: float = Field(default=0.7, gt=0.0, le=1.0)

    # Phase 4: Output
    top_k: int = Field(default=10, ge=1, le=50)
    display_mode: str = "summary"
    max_facets_per_episode: int = Field(default=6, ge=1, le=10)

    # Feature flags
    enable_relation_paths: bool = True
    enable_direct_episode_penalty: bool = True
    enable_query_sensitive_cost: bool = True
    enable_adaptive_confidence: bool = False
    enable_temporal_neighbor_context: bool = False
    max_temporal_neighbors: int = Field(default=2, ge=0, le=4)
    enable_query_decomposition: bool = False
    enable_reranking: bool = False
    rerank_top_n: int = Field(default=5, ge=1, le=20)

    # Keyword lists for query intent detection
    temporal_keywords: list[str] = Field(default_factory=lambda: [
        "when", "什么时候", "之前", "之后", "多久", "哪年", "哪天",
        "first", "last", "before", "after", "during", "earlier", "later",
        "recently", "最近", "以前", "那时",
    ])
    causal_keywords: list[str] = Field(default_factory=lambda: [
        "why", "为什么", "因为", "导致", "原因", "结果",
        "because", "cause", "result", "lead to", "due to",
        "所以", "因此", "造成",
    ])

    # ── Round 5 Stage 1: IntentClassifier ──
    # Defaults are chosen so A1-A10 (which do not set these keys) keep the
    # pre-R5 keyword behavior bit-for-bit. Only R5-1+ flip `intent_classifier_mode`.
    intent_classifier_mode: str = Field(default="keyword")  # "keyword" | "hybrid"
    # Frozen thresholds matching the Stage-1-approved IntentClassifier defaults.
    intent_high_conf_threshold: float = Field(default=0.55, ge=0.0, le=1.0)
    intent_margin_threshold: float = Field(default=0.10, ge=0.0, le=1.0)
    intent_low_conf_threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    intent_secondary_margin: float = Field(default=0.15, ge=0.0, le=1.0)

    # ── Round 5 Stage 2b: Confidence-aware Top-K Quota (declared early, wired later) ──
    enable_intent_quota: bool = Field(default=False)
    quota_pre_rerank_candidates: int = Field(default=15, ge=5, le=30)

    # ── Round 5 Stage 3: Tiered edge-cost discount (declared early, wired later) ──
    enable_tiered_discount: bool = Field(default=False)


# ── Master Config ────────────────────────────────────────────────────

class MMemConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    write: WriteConfig = Field(default_factory=WriteConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    data_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "data")


# Singleton-style default config
_default_config: MMemConfig | None = None


def get_config() -> MMemConfig:
    global _default_config
    if _default_config is None:
        _default_config = MMemConfig()
    return _default_config


def set_config(config: MMemConfig) -> None:
    global _default_config
    _default_config = config
