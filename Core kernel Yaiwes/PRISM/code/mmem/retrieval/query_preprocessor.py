"""
Phase 0: Query preprocessing.

Detects temporal/causal/entity intent hints, strips question words to produce
a cleaner embedding query, and optionally routes hint detection to the
Round-5 hybrid :class:`IntentClassifier` instead of the legacy keyword rules.

Design invariant (Round 5 Stage 2a)
-----------------------------------
Keyword and hybrid paths MUST produce an **identical** ``vector_query`` for
the same input. The only permitted difference between the two paths is the
content of ``query_type_hints`` (and the ``classifier_used`` / ``intent_confidences``
telemetry attached in hybrid mode). This keeps R5-1 vs. A9 a clean
classifier-only ablation — any divergence in anchor discovery must be
traceable to a different hint set, nothing else.

Gated routing (Round 5 Stage 2a, v2)
------------------------------------
In ``hybrid`` mode the classifier is NOT unconditionally invoked. A keyword
pre-pass runs first; if it detects ``temporal`` or ``causal`` on a non-short
query (no ``entity_centric`` hint), the LLM classifier is skipped entirely
(``classifier_used == "keyword_gated"``). This halves LLM call rate and
latency without sacrificing hint quality: temporal/causal keyword rules are
100% precision on LoCoMo. The classifier remains authoritative for
``multi_hop`` / ``entity_centric`` / ``general`` disambiguation when keywords
are silent or ambiguous.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from mmem.config import RetrievalConfig, get_config

if TYPE_CHECKING:
    from mmem.retrieval.intent_classifier import IntentClassifier

_QUESTION_WORDS_RE = re.compile(
    r"\b(what is|what are|what was|what were|what did|what does|what do|"
    r"who is|who are|who was|who were|"
    r"how did|how does|how do|how is|how was|"
    r"where is|where did|where does|where was|"
    r"when did|when does|when was|when is|"
    r"why did|why does|why is|why was|"
    r"tell me about|can you tell me|please describe|describe)\b",
    re.IGNORECASE,
)

_TRAILING_PUNCT_RE = re.compile(r"[?？!！。，,.\s]+$")


@dataclass
class PreprocessedQuery:
    original: str
    vector_query: str
    query_type_hints: set[str] = field(default_factory=set)
    # ── Round 5 Stage 2a: IntentClassifier telemetry ──
    # Populated in hybrid mode; stays empty / "keyword" for the keyword path.
    intent_confidences: dict[str, float] = field(default_factory=dict)
    # "keyword" | "keyword_gated" | "prototype" | "llm" | "none" | "fallback"
    classifier_used: str = "keyword"


def _strip_question_words(query: str) -> str:
    """Legacy shared transform — used by BOTH the keyword and hybrid paths.

    Pulled out so the invariant "both paths produce the same vector_query" is
    enforced in one place.
    """
    vector_query = _QUESTION_WORDS_RE.sub("", query).strip()
    vector_query = _TRAILING_PUNCT_RE.sub("", vector_query).strip()
    if not vector_query:
        vector_query = query
    return vector_query


def _keyword_classify(query: str, cfg: RetrievalConfig) -> tuple[set[str], str]:
    """Legacy keyword-based intent hint detection.

    Returns ``(hints, vector_query)``. Hints follow the same rules as the
    pre-R5 implementation: temporal keyword scan, causal keyword scan,
    short-query → entity_centric, empty → general.
    """
    hints: set[str] = set()
    lower = query.lower()

    for kw in cfg.temporal_keywords:
        if kw.lower() in lower:
            hints.add("temporal")
            break

    for kw in cfg.causal_keywords:
        if kw.lower() in lower:
            hints.add("causal")
            break

    effective_words = re.findall(r"\w+", query)
    if len(effective_words) <= 3:
        hints.add("entity_centric")

    if not hints:
        hints.add("general")

    vector_query = _strip_question_words(query)
    return hints, vector_query


def preprocess_query(
    query: str,
    config: RetrievalConfig | None = None,
    intent_classifier: Optional["IntentClassifier"] = None,
) -> PreprocessedQuery:
    """Analyse a raw query and return a ``PreprocessedQuery``.

    Routing (hybrid mode):
      1. Always run the keyword pre-pass → ``(kw_hints, vector_query)``.
      2. If ``mode != "hybrid"`` or no classifier provided → legacy keyword path.
      3. Gate 1 — keyword authority: ``temporal`` or ``causal`` in ``kw_hints``
         AND ``entity_centric`` NOT in ``kw_hints`` → skip LLM classifier,
         trust keyword hints (``classifier_used="keyword_gated"``).
      4. Gate 2 — classifier fallback: call the IntentClassifier; union its
         hints with ``kw_hints``; drop spurious short-query ``entity_centric``
         when the classifier is confident the query is ``multi_hop`` / ``causal``;
         drop ``general`` whenever any real intent is present.

    The ``vector_query`` is computed by the same shared helper on both paths,
    so the two paths differ **only** in ``query_type_hints``.
    """
    cfg = config or get_config().retrieval
    query = query.strip()

    mode = getattr(cfg, "intent_classifier_mode", "keyword")

    kw_hints, vector_query = _keyword_classify(query, cfg)

    if mode != "hybrid" or intent_classifier is None:
        return PreprocessedQuery(
            original=query,
            vector_query=vector_query,
            query_type_hints=kw_hints,
            intent_confidences={},
            classifier_used="keyword",
        )

    kw_has_temporal = "temporal" in kw_hints
    kw_has_causal = "causal" in kw_hints

    if (kw_has_temporal or kw_has_causal) and "entity_centric" not in kw_hints:
        return PreprocessedQuery(
            original=query,
            vector_query=vector_query,
            query_type_hints=kw_hints,
            intent_confidences={},
            classifier_used="keyword_gated",
        )

    result = intent_classifier.classify(query)

    final_hints = kw_hints | set(result.hints)

    if (
        ("multi_hop" in result.hints or "causal" in result.hints)
        and "entity_centric" in final_hints
    ):
        final_hints.discard("entity_centric")

    if len(final_hints) > 1:
        final_hints.discard("general")

    return PreprocessedQuery(
        original=query,
        vector_query=vector_query,
        query_type_hints=final_hints,
        intent_confidences=dict(result.confidences),
        classifier_used=result.classifier_used,
    )
