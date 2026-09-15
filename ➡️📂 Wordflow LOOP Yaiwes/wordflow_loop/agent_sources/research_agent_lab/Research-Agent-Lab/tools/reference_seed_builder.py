from __future__ import annotations

from typing import Any


def build_reference_search_seeds(
    references: list[dict[str, Any]],
    *,
    topic_keywords: list[str] | None = None,
    min_score: float = 0.3,
    max_seeds: int = 8,
) -> list[dict[str, Any]]:
    keywords = [kw.lower() for kw in (topic_keywords or []) if len(str(kw).strip()) >= 3]
    candidates: list[dict[str, Any]] = []
    for ref in references:
        title = str(ref.get("title", "")).strip()
        score = float(ref.get("relevance_score", 0.0) or 0.0)
        if len(title) < 10:
            continue
        if score < min_score:
            continue
        keyword_bonus = _keyword_bonus(title, keywords)
        candidates.append({
            "query": title,
            "source": "reference_network",
            "source_ref_id": ref.get("ref_id", ""),
            "source_paper_id": ref.get("source_paper_id", ""),
            "year": str(ref.get("year", "")),
            "venue": str(ref.get("venue", "")),
            "relevance_score": score,
            "_sort_key": round(min(1.0, score + keyword_bonus), 4),
        })
    candidates.sort(key=lambda item: item["_sort_key"], reverse=True)
    result = _dedupe_seed_queries(candidates, max_seeds=max_seeds)
    for item in result:
        item.pop("_sort_key", None)
    return result


def _keyword_bonus(title: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0
    title_lower = title.lower()
    # Word-level matching: break long phrases into individual words
    key_words: set[str] = set()
    for kw in keywords[:20]:
        for word in str(kw).lower().split():
            w = word.strip().rstrip('.,;:!?')
            if len(w) >= 3:
                key_words.add(w)
    if not key_words:
        return 0.0
    hits = sum(1 for w in key_words if w in title_lower)
    return min(0.3, hits * 0.03)


def _dedupe_seed_queries(candidates: list[dict[str, Any]], *, max_seeds: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in candidates:
        query_words = set(item["query"].lower().split())
        duplicate = False
        for existing in result:
            existing_words = set(existing["query"].lower().split())
            intersection = query_words & existing_words
            union = query_words | existing_words
            if len(union) > 0 and len(intersection) / len(union) > 0.63:
                duplicate = True
                break
        if duplicate:
            continue
        result.append(item)
        if len(result) >= max_seeds:
            break
    return result
