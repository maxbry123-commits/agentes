"""
Optional LLM-based re-ranking of retrieved episodes.

Scores each episode's relevance to the query and returns the top-N.
"""

from __future__ import annotations

import logging

from mmem.config import LLMConfig
from mmem.core.graph import MemoryGraph
from mmem.core.nodes import Episode
from mmem.utils.llm import LLMClient

from .path_scorer import EpisodeBundle

logger = logging.getLogger(__name__)

# ── Prompt versions ──────────────────────────────────────────────────

# V1: 原始版本（Round3），保留用于对比回退
_RERANK_PROMPT_V1 = """Rate the relevance of each memory snippet to the question on a scale of 0-10.

Question: {question}

Snippets:
{snippets}

Return a JSON array of objects, each with "index" (integer) and "score" (0-10).
Example: [{{"index": 0, "score": 9}}, {{"index": 1, "score": 2}}]

Return ONLY the JSON array, no other text."""


# V2: 加入 multi_hop 保护，防止间接推理信息被误砍
_RERANK_PROMPT_V2 = """Rate the relevance of each memory snippet to the question on a scale of 0-10.

Scoring guide:
- 8-10: Directly answers the question or contains the key fact being asked about.
- 4-7: Contains related or background information that might help answer the question indirectly. This includes character traits, past events, or context that could support multi-step reasoning.
- 0-3: Completely unrelated to the question.

IMPORTANT: When the question requires reasoning across multiple facts (e.g., "Would X be considered Y?", "What fields would X pursue?"), snippets providing background context or character history should receive at least a moderate score (4-6), even if they don't directly mention the topic of the question.

Question: {question}

Snippets:
{snippets}

Return a JSON array of objects, each with "index" (integer) and "score" (0-10).
Example: [{{"index": 0, "score": 9}}, {{"index": 1, "score": 2}}]

Return ONLY the JSON array, no other text."""


# 当前生效版本（如需回退改为 _RERANK_PROMPT_V1）
_RERANK_PROMPT = _RERANK_PROMPT_V1


def rerank_bundles(
    question: str,
    bundles: list[EpisodeBundle],
    graph: MemoryGraph,
    llm_client: LLMClient,
    llm_config: LLMConfig,
    top_n: int = 5,
) -> list[EpisodeBundle]:
    """Re-rank bundles by LLM relevance score, return top-N."""
    if len(bundles) <= top_n:
        return bundles

    snippet_lines: list[str] = []
    for i, b in enumerate(bundles):
        ep = graph.get_node(b.episode_id)
        if ep is not None and isinstance(ep, Episode):
            snippet_lines.append(f"[{i}] {ep.summary[:400]}")
        else:
            snippet_lines.append(f"[{i}] (no summary)")

    snippets_text = "\n".join(snippet_lines)

    try:
        raw = llm_client.chat_json(
            prompt=_RERANK_PROMPT.format(question=question, snippets=snippets_text),
            model=llm_config.qa_model,
            system="Return strict JSON only.",
            temperature=0.0,
        )

        if not isinstance(raw, list):
            logger.warning("Re-ranker returned non-list, falling back to original order")
            return bundles[:top_n]

        scores: dict[int, float] = {}
        for item in raw:
            if isinstance(item, dict) and "index" in item and "score" in item:
                idx = int(item["index"])
                score = float(item["score"])
                if 0 <= idx < len(bundles):
                    scores[idx] = score

        ranked_indices = sorted(scores.keys(), key=lambda i: scores[i], reverse=True)
        return [bundles[i] for i in ranked_indices[:top_n]]

    except Exception as exc:
        logger.warning("Re-ranking failed: %s", exc, exc_info=True)
        return bundles[:top_n]
