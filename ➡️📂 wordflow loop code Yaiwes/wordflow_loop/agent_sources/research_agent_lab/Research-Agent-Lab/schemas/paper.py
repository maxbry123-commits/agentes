from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id


@dataclass(slots=True)
class Paper:
    title: str
    abstract: str = ""
    paper_id: str = field(default_factory=lambda: new_id("paper"))
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str = ""
    url: str = ""
    pdf_path: str = ""
    local_path: str = ""
    library: str = ""
    keywords: list[str] = field(default_factory=list)
    citation_count: int = 0
    source: str = "offline_seed"
    relevance_score: float = 0.0
    triage_reason: str = ""
