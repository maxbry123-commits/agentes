from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Any

from schemas.topic_pack import TopicPack


@dataclass(slots=True)
class SelectedPaperChunk:
    paper_id: str
    chunk_id: str
    text: str
    score: float
    section: str = "Unknown"
    page_start: int | None = None
    page_end: int | None = None
    matched_terms: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PaperChunkSelector:
    METHOD_TERMS = [
        "method",
        "model",
        "architecture",
        "encoder",
        "decoder",
        "diffusion",
        "denoising",
        "trajectory",
        "prediction",
        "forecast",
        "intention",
        "intent",
        "language",
        "fusion",
        "attention",
        "cross-attention",
        "experiment",
        "dataset",
        "metric",
        "ade",
        "fde",
        "ablation",
        "limitation",
    ]

    def __init__(self, max_chunks: int = 4, max_chars: int = 9000):
        self.max_chunks = max_chunks
        self.max_chars = max_chars

    def select_for_paper(
        self,
        topic: TopicPack,
        paper: dict[str, Any],
        parsed_paper: dict[str, Any] | None,
    ) -> list[SelectedPaperChunk]:
        chunks = list((parsed_paper or {}).get("chunks") or [])
        if not chunks:
            text = str((parsed_paper or {}).get("text_excerpt", "")).strip()
            if not text:
                return []
            chunks = [
                {
                    "paper_id": paper.get("paper_id", ""),
                    "chunk_id": f"{paper.get('paper_id', 'paper')}:excerpt",
                    "section": "Local PDF",
                    "text": text,
                }
            ]

        terms = self._terms(topic, paper)
        scored = [self._score_chunk(chunk, terms) for chunk in chunks]
        scored.sort(key=lambda item: item.score, reverse=True)

        selected: list[SelectedPaperChunk] = []
        total_chars = 0
        for item in scored:
            if item.score <= 0 and selected:
                continue
            if total_chars + len(item.text) > self.max_chars and selected:
                continue
            selected.append(item)
            total_chars += len(item.text)
            if len(selected) >= self.max_chunks or total_chars >= self.max_chars:
                break
        return selected

    def format_context(self, chunks: list[SelectedPaperChunk]) -> str:
        parts = []
        for index, chunk in enumerate(chunks, start=1):
            location = chunk.section
            if chunk.page_start is not None:
                location += f", page {chunk.page_start}"
            terms = ", ".join(chunk.matched_terms or [])
            parts.append(
                f"[context {index}] chunk_id={chunk.chunk_id}; section={location}; "
                f"score={chunk.score:.2f}; matched_terms={terms}\n{chunk.text}"
            )
        return "\n\n".join(parts).strip()

    def _terms(self, topic: TopicPack, paper: dict[str, Any]) -> list[str]:
        raw_terms = []
        raw_terms.extend(topic.keywords())
        raw_terms.extend(topic.domain.get("secondary_areas", []))
        raw_terms.extend(topic.experiment_metrics)
        raw_terms.append(topic.domain.get("primary_area", ""))
        raw_terms.append(paper.get("title", ""))
        raw_terms.extend(self.METHOD_TERMS)
        terms: list[str] = []
        seen = set()
        for value in raw_terms:
            for term in self._split_terms(str(value)):
                lower = term.lower()
                if len(lower) >= 3 and lower not in seen:
                    seen.add(lower)
                    terms.append(lower)
        return terms

    def _split_terms(self, text: str) -> list[str]:
        pieces = [text]
        pieces.extend(re.split(r"[^A-Za-z0-9\-]+", text))
        return [piece.strip() for piece in pieces if piece.strip()]

    def _score_chunk(self, chunk: dict[str, Any], terms: list[str]) -> SelectedPaperChunk:
        text = str(chunk.get("text", ""))
        lower = text.lower()
        section = str(chunk.get("section", "Unknown"))
        matched: list[str] = []
        score = 0.0
        for term in terms:
            if term and term in lower:
                matched.append(term)
                score += 1.0
        section_lower = section.lower()
        if any(key in section_lower for key in ["method", "experiment", "result", "ablation"]):
            score += 3.0
        if any(key in lower for key in ["we propose", "our method", "experiments", "results"]):
            score += 1.5
        return SelectedPaperChunk(
            paper_id=str(chunk.get("paper_id", "")),
            chunk_id=str(chunk.get("chunk_id", "")),
            text=text,
            score=score,
            section=section,
            page_start=chunk.get("page_start"),
            page_end=chunk.get("page_end"),
            matched_terms=matched[:16],
        )
