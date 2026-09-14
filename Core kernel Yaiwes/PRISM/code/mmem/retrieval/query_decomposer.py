"""
Optional query decomposition via LLM.

Generates supplementary sub-queries for aggregation or multi-event questions,
improving recall without replacing the primary query.
"""

from __future__ import annotations

import logging

from mmem.config import LLMConfig
from mmem.utils.llm import LLMClient

logger = logging.getLogger(__name__)

_DECOMPOSE_PROMPT = """Given the following question, generate 2-3 alternative search queries ONLY if the question asks about multiple events, counts, comparisons, or aggregations.

If the question is a single fact lookup (e.g., "When did X happen?", "What did Y do?", "What is X's identity?"), return an empty array [].

Question: {question}

Return a JSON array of strings, each being a short search query (3-8 words).
Example for aggregation question: ["Melanie first beach trip 2023", "Melanie second beach visit summer"]
Example for single fact question: []

Return ONLY the JSON array, no other text."""


def decompose_query(
    question: str,
    llm_client: LLMClient,
    llm_config: LLMConfig,
) -> list[str]:
    """Generate sub-queries for a question.

    Returns an empty list when the LLM judges the question to be a single-fact
    lookup, when the response is malformed, or when the API call fails.
    """
    try:
        raw = llm_client.chat_json(
            prompt=_DECOMPOSE_PROMPT.format(question=question),
            model=llm_config.extraction_model,
            system="Return strict JSON only.",
            temperature=0.0,
        )
        if isinstance(raw, list):
            return [str(q).strip() for q in raw if isinstance(q, str) and q.strip()]
        return []
    except Exception as exc:
        logger.warning("Query decomposition failed: %s", exc, exc_info=True)
        return []
