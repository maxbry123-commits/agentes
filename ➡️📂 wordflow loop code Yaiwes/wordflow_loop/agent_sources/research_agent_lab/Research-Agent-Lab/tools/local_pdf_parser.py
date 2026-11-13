from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from schemas.parsed_paper import ParsedPaper, PaperChunk


_NUM_PREFIX = r"(?:(?:\d+|[IVX]+)\.?\d*\.?\s+)?"

_SECTION_LABELS = [
    (re.compile(r"^" + _NUM_PREFIX + r"(?:Abstract)$", re.MULTILINE | re.IGNORECASE), "Abstract"),
    (re.compile(r"^" + _NUM_PREFIX + r"(?:Introduction)$", re.MULTILINE | re.IGNORECASE), "Introduction"),
    (re.compile(r"^" + _NUM_PREFIX + r"(?:Related\s*Work|Background|Literature\s*Review)$", re.MULTILINE | re.IGNORECASE), "Related Work"),
    (re.compile(r"^" + _NUM_PREFIX + r"(?:Method(?:ology)?|Approach|Proposed\s*Method|Our\s*Method|Model\s*Architecture)$", re.MULTILINE | re.IGNORECASE), "Method"),
    (re.compile(r"^" + _NUM_PREFIX + r"(?:Experiments?|Experimental\s*(?:Setup|Results|Evaluation)|Evaluation|Implementation\s*Details)$", re.MULTILINE | re.IGNORECASE), "Experiments"),
    (re.compile(r"^" + _NUM_PREFIX + r"(?:Results?(?:\s*and\s*Discussion)?|Analysis)$", re.MULTILINE | re.IGNORECASE), "Results"),
    (re.compile(r"^" + _NUM_PREFIX + r"(?:Ablation\s*Stud(?:y|ies))$", re.MULTILINE | re.IGNORECASE), "Ablation"),
    (re.compile(r"^" + _NUM_PREFIX + r"(?:Conclusions?(?:\s+and\s+.*)?|Discussion|Limitations?|Future\s*Work)\s*$", re.MULTILINE | re.IGNORECASE), "Conclusion"),
    (re.compile(r"^(?:References?|Bibliography)$", re.MULTILINE | re.IGNORECASE), "References"),
]


def detect_sections(text: str) -> list[tuple[int, str]]:
    boundaries: list[tuple[int, str]] = []
    seen: set[int] = set()
    for pattern, label in _SECTION_LABELS:
        for match in pattern.finditer(text):
            pos = match.start()
            if pos not in seen:
                seen.add(pos)
                boundaries.append((pos, label))
    boundaries.sort(key=lambda item: item[0])
    return boundaries


def _section_at(pos: int, boundaries: list[tuple[int, str]]) -> str:
    section = "Unknown"
    for b_pos, label in boundaries:
        if pos >= b_pos:
            section = label
        else:
            break
    return section


class LocalPdfParser:
    def __init__(self, max_pages: int = 8, max_chars: int = 12000, chunk_chars: int = 1800):
        self.max_pages = max_pages
        self.max_chars = max_chars
        self.chunk_chars = chunk_chars

    def parse(self, paper: dict[str, Any]) -> ParsedPaper:
        path_text = paper.get("pdf_path") or paper.get("local_path") or ""
        parsed = ParsedPaper(
            paper_id=paper["paper_id"],
            title=paper.get("title", ""),
            source_path=path_text,
        )
        if not path_text:
            parsed.status = "no_local_path"
            return parsed

        path = Path(path_text)
        if not path.exists():
            parsed.status = "missing_file"
            parsed.error = f"file does not exist: {path}"
            return parsed

        reader_cls, parser_name = self._reader_class()
        if reader_cls is None:
            parsed.status = "parser_missing"
            parsed.error = "install pypdf or PyPDF2 to enable local PDF full-text parsing"
            return parsed

        try:
            reader = reader_cls(str(path))
            pages = getattr(reader, "pages", [])
            parsed.parser = parser_name
            parsed.page_count = len(pages)
            text_parts: list[str] = []
            for page_index, page in enumerate(pages[: self.max_pages], start=1):
                extracted = page.extract_text() or ""
                if extracted.strip():
                    text_parts.append(f"[page {page_index}]\n{extracted.strip()}")
                if sum(len(part) for part in text_parts) >= self.max_chars:
                    break
            text = "\n\n".join(text_parts)[: self.max_chars]
            parsed.text_excerpt = text
            boundaries = detect_sections(text)
            parsed.chunks = self._chunks(parsed.paper_id, text, boundaries)
            parsed.status = "parsed" if text.strip() else "empty_text"
            return parsed
        except Exception as exc:  # PDF parsing is best-effort.
            parsed.status = "parse_error"
            parsed.error = str(exc)
            return parsed

    def _reader_class(self) -> tuple[type | None, str]:
        try:
            from pypdf import PdfReader  # type: ignore

            return PdfReader, "pypdf"
        except ImportError:
            pass
        try:
            from PyPDF2 import PdfReader  # type: ignore

            return PdfReader, "PyPDF2"
        except ImportError:
            return None, ""

    def _chunks(self, paper_id: str, text: str, boundaries: list[tuple[int, str]]) -> list[PaperChunk]:
        if not text.strip():
            return []
        if not boundaries:
            return self._fixed_step_chunks(paper_id, text.strip())
        chunks: list[PaperChunk] = []
        positions = [0] + [b[0] for b in boundaries] + [len(text)]
        labels = ["Unknown"] + [b[1] for b in boundaries]
        for i in range(len(positions) - 1):
            seg = text[positions[i]:positions[i + 1]].strip()
            if not seg:
                continue
            section = labels[i]
            if len(seg) <= self.chunk_chars:
                chunks.append(PaperChunk(paper_id=paper_id, text=seg, section=section))
            else:
                for para in seg.split("\n\n"):
                    para = para.strip()
                    if para:
                        chunks.append(PaperChunk(paper_id=paper_id, text=para[:self.chunk_chars], section=section))
        return chunks

    def _fixed_step_chunks(self, paper_id: str, clean: str) -> list[PaperChunk]:
        chunks: list[PaperChunk] = []
        for start in range(0, len(clean), self.chunk_chars):
            chunk_text = clean[start : start + self.chunk_chars].strip()
            if chunk_text:
                chunks.append(PaperChunk(paper_id=paper_id, text=chunk_text, section="Unknown"))
        return chunks
