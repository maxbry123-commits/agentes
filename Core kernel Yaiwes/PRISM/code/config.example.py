"""
Example configuration for the PRISM memory framework.

This file documents every tunable knob exposed by `mmem/config.py`. You do NOT
need to edit it to run PRISM: the defaults below match the values reported in
the paper (Appendix C.3, Table 5), and secrets are read from environment
variables (see `.env.example`).

It is provided as a reference for anyone who wants to override hyper-parameters
programmatically, e.g.:

    from mmem.config import MMemConfig, set_config

    cfg = MMemConfig()
    cfg.retrieval.rerank_top_n = 7      # sweep the rerank pool
    cfg.llm.qa_model = "gpt-4o-mini"
    set_config(cfg)

All values shown are the library defaults. The authoritative definitions live
in `mmem/config.py`.
"""

# ── LLM ──────────────────────────────────────────────────────────────
# api_key   : read from $OPENAI_API_KEY  (never hard-code it here)
# base_url  : read from $OPENAI_BASE_URL (default https://api.openai.com/v1)
LLM = {
    "extraction_model": "gpt-4o-mini",
    "causal_model": "gpt-4o-mini",
    "qa_model": "gpt-4o-mini",
    "judge_model": "gpt-4o-mini",
    "temperature": 0.0,
    "max_retries": 3,
    "timeout": 60.0,
}

# ── Embedding ────────────────────────────────────────────────────────
EMBEDDING = {
    "model_name": "all-MiniLM-L6-v2",   # auto-downloaded from HuggingFace
    "dimension": 384,
    "batch_size": 64,
    "device": "cpu",                    # PRISM is CPU-only; no GPU required
}

# ── Write / graph construction ───────────────────────────────────────
WRITE = {
    "entity_merge_threshold": 0.90,         # Table 5
    "semantic_similarity_threshold": 0.85,  # Facet merge threshold (Table 5)
    "causal_confidence_threshold": 0.7,
    "causal_consolidation_interval": 5,     # chunks (Table 5)
    "enable_causal_consolidation": True,
}

# ── Retrieval (the four PRISM modules) ───────────────────────────────
RETRIEVAL = {
    # N1: Hierarchical Bundle Search
    "wide_search_top_k": 30,            # FAISS top-k per layer (Table 5)
    "top_k": 10,                        # bundle size K (Table 5)
    "hop_cost": 0.05,                   # hop penalty c_hop (Table 5)
    "enable_relation_paths": True,      # N1 on/off

    # N2: Query-Sensitive Edge Cost
    "edge_miss_cost": 0.9,              # c0 fallback (Table 5)
    "belongs_to_cost": 0.02,
    "temporal_discount": 0.5,           # alpha matched temporal/causal (Table 5)
    "causal_discount": 0.5,
    "evolution_discount": 0.7,          # alpha evolution under temporal (Table 5)
    "enable_query_sensitive_cost": True,  # N2 on/off

    # N3: Evidence Compression (LLM re-rank)
    "enable_reranking": True,           # N3 on/off
    "rerank_top_n": 5,                  # rerank size M (Table 5)

    # N4: Adaptive Intent Routing
    # "keyword"  -> deterministic keyword/regex routing only
    # "hybrid"   -> keyword + prototype + LLM-fallback cascade (paper N4)
    "intent_classifier_mode": "keyword",
    "intent_high_conf_threshold": 0.55,   # prototype threshold (Table 5)
    "intent_margin_threshold": 0.10,
}
