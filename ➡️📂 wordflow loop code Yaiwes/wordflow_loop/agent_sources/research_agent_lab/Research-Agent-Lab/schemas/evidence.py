from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id


@dataclass(slots=True)
class Evidence:
    paper_id: str
    claim_supported: str
    quote: str
    evidence_id: str = field(default_factory=lambda: new_id("evidence"))
    section: str = "Unknown"
    page: int | None = None
    chunk_id: str = ""
    support_level: str = "inferred"
