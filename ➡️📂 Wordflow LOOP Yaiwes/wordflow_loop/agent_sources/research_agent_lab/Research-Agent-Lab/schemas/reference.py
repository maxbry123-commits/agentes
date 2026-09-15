from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id, utc_now


@dataclass(slots=True)
class ExtractedReference:
    title: str
    source_paper_id: str
    ref_id: str = field(default_factory=lambda: new_id("ref"))
    authors: list[str] = field(default_factory=list)
    year: str = ""
    venue: str = ""
    relevance_score: float = 0.0
    cited_in_sections: list[str] = field(default_factory=list)
    extracted_at: str = field(default_factory=utc_now)
