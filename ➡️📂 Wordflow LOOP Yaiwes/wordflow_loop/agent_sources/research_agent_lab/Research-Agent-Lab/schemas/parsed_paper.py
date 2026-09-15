from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id


@dataclass(slots=True)
class PaperChunk:
    paper_id: str
    text: str
    chunk_id: str = field(default_factory=lambda: new_id("chunk"))
    page_start: int | None = None
    page_end: int | None = None
    section: str = "Unknown"


@dataclass(slots=True)
class ParsedPaper:
    paper_id: str
    title: str
    source_path: str
    parsed_paper_id: str = field(default_factory=lambda: new_id("parsed"))
    status: str = "pending"
    parser: str = ""
    page_count: int = 0
    text_excerpt: str = ""
    chunks: list[PaperChunk] = field(default_factory=list)
    error: str = ""
