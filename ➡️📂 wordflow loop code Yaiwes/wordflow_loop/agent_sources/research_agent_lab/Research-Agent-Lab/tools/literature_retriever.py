from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass(slots=True)
class RetrievalResult:
    paper_id: str
    chunk_id: str
    text: str
    section: str
    score: float
    matched_terms: list[str] = field(default_factory=list)


class LiteratureRetriever:
    def __init__(self):
        self._chunks: list[dict] = []
        self._term_index: dict[str, set[int]] = defaultdict(set)
        self._doc_count: int = 0

    def index(self, papers: list[dict], parsed_papers: list[dict]) -> int:
        self._chunks.clear()
        self._term_index.clear()
        for paper in papers:
            paper_id = paper.get("paper_id", "")
            parsed = self._find_parsed(paper_id, parsed_papers)
            chunks = list((parsed or {}).get("chunks") or [])
            if not chunks:
                text = str((parsed or {}).get("text_excerpt", ""))
                if text.strip():
                    chunks = [{"paper_id": paper_id, "chunk_id": f"{paper_id}:excerpt", "section": "Unknown", "text": text}]
            for chunk in chunks:
                cid = chunk.get("chunk_id", "")
                text = str(chunk.get("text", ""))
                section = str(chunk.get("section", "Unknown"))
                self._chunks.append({
                    "paper_id": paper_id,
                    "chunk_id": cid,
                    "text": text,
                    "section": section,
                })
                idx = len(self._chunks) - 1
                for token in self._tokenize(text):
                    self._term_index[token].add(idx)
        self._doc_count = len(self._chunks)
        return self._doc_count

    def search(self, query: str, top_k: int = 10, prefer_sections: list[str] | None = None) -> list[RetrievalResult]:
        if not self._chunks:
            return []
        query_terms = self._tokenize(query)
        if not query_terms:
            return []
        scored: dict[int, float] = defaultdict(float)
        matched: dict[int, list[str]] = defaultdict(list)
        for term in query_terms:
            doc_ids = self._term_index.get(term, set())
            idf = self._idf(term, len(doc_ids))
            for doc_id in doc_ids:
                tf = self._tf(term, self._chunks[doc_id]["text"])
                scored[doc_id] += tf * idf
                matched[doc_id].append(term)
        prefer = set(s.lower() for s in (prefer_sections or []))
        for doc_id in scored:
            section = self._chunks[doc_id]["section"].lower()
            if any(p in section for p in prefer):
                scored[doc_id] *= 1.5
            elif any(p in section for p in ("method", "experiment", "result")):
                scored[doc_id] *= 1.2
        ranked = sorted(scored.items(), key=lambda item: item[1], reverse=True)
        results: list[RetrievalResult] = []
        for doc_id, score in ranked[:top_k]:
            c = self._chunks[doc_id]
            results.append(RetrievalResult(
                paper_id=c["paper_id"],
                chunk_id=c["chunk_id"],
                text=c["text"][:2000],
                section=c["section"],
                score=round(score, 4),
                matched_terms=matched[doc_id][:10],
            ))
        return results

    def _find_parsed(self, paper_id: str, parsed_papers: list[dict]) -> dict | None:
        for p in parsed_papers:
            if p.get("paper_id") == paper_id:
                return p
        return None

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z0-9\-]+", text.lower())
        return [t for t in tokens if len(t) >= 2]

    def _tf(self, term: str, text: str) -> float:
        count = text.lower().count(term)
        return 1.0 + math.log(max(1, count))

    def _idf(self, term: str, doc_freq: int) -> float:
        if self._doc_count == 0 or doc_freq == 0:
            return 0.0
        return math.log((self._doc_count + 1) / (doc_freq + 1)) + 1.0
