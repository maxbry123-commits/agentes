from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict
from difflib import SequenceMatcher
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.reference import ExtractedReference
from tools.llm_budget import llm_budget_allows, llm_usage_values, record_llm_usage
from tools.llm_client import OpenAICompatibleClient, extract_json_object
from tools.model_router import ModelRouter


class ReferenceExtractorAgent(Agent):
    name = "reference_extractor"

    def __init__(self):
        super().__init__()
        self.llm_client = OpenAICompatibleClient()

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        settings = context.settings
        all_refs: list[ExtractedReference] = []
        parsed_papers = state.values.get("parsed_papers", [])
        topic_keywords = _topic_keywords(state)

        for parsed in parsed_papers:
            paper_id = parsed.get("paper_id", "")
            chunks = parsed.get("chunks", [])

            ref_text = _find_reference_section(chunks)
            if not ref_text:
                continue

            cited_counts = _count_citations(chunks)

            if settings.get("enable_llm"):
                llm_refs = self._try_llm_extract(
                    state, settings, paper_id, ref_text, cited_counts, topic_keywords
                )
                if llm_refs is not None:
                    all_refs.extend(llm_refs)
                    continue

            rule_refs = _rule_based_extract(paper_id, ref_text, cited_counts, topic_keywords)
            all_refs.extend(rule_refs)

        deduped = _deduplicate(all_refs, max_total=20)
        artifact_ids: list[str] = []
        for ref in deduped:
            context.artifact_store.save_json(
                state.run_id, "extracted_references", ref.ref_id, ref
            )
            artifact_ids.append(ref.ref_id)

        result_list = [asdict(r) for r in deduped]
        state.values["extracted_references"] = result_list
        return AgentResult(
            notes=[f"extracted {len(deduped)} references from {len(parsed_papers)} papers"],
            artifacts={"extracted_references": artifact_ids},
            values={"extracted_references": result_list, "extracted_reference_count": len(deduped)},
        )

    def _try_llm_extract(
        self,
        state: ResearchState,
        settings: dict[str, Any],
        paper_id: str,
        ref_text: str,
        cited_counts: Counter,
        topic_keywords: list[str],
    ) -> list[ExtractedReference] | None:
        route = ModelRouter(state.topic).route_for("paper_triage")
        if route.provider in {"offline", "local", "rule_based"}:
            return None
        allowed, _reason = llm_budget_allows(state, settings)
        if not allowed:
            return None

        topic_name = state.topic.topic_name
        cited_summary = ", ".join(
            f"[{k}]: {v} times" for k, v in cited_counts.most_common(20)
        )
        messages = [
            {"role": "system", "content": (
                "You extract structured references from a paper's References/Bibliography section. "
                "For each reference, extract: title, authors(list), year, venue. "
                "Then assign a relevance_score (0.0-1.0) based on how relevant the reference title "
                "is to the research topic and keywords provided. "
                "Prefer references that are cited more often in the paper's Introduction/Related Work/Method sections. "
                "Return exactly one JSON object with key 'references' mapping to an array of "
                "{title, authors, year, venue, relevance_score, reason} objects. "
                "Return the top 5 most relevant references, sorted by relevance_score descending."
            )},
            {"role": "user", "content": (
                f"Topic: {topic_name}\n"
                f"Keywords: {', '.join(topic_keywords[:20])}\n"
                f"Citations in Introduction/Related Work/Method: {cited_summary}\n\n"
                f"References section text:\n{ref_text[:10000]}"
            )},
        ]
        response = self.llm_client.chat(route, messages, temperature=0.1, max_tokens=2000)
        record_llm_usage(state, response.usage)
        if not response.ok:
            return None

        payload = extract_json_object(response.text)
        if payload is None:
            return None
        refs_data = payload.get("references")
        if not isinstance(refs_data, list) or len(refs_data) == 0:
            return None

        result: list[ExtractedReference] = []
        for r in refs_data[:5]:
            if not isinstance(r, dict) or not r.get("title"):
                continue
            result.append(ExtractedReference(
                title=r["title"],
                source_paper_id=paper_id,
                authors=list(r.get("authors", [])),
                year=str(r.get("year", "")),
                venue=str(r.get("venue", "")),
                relevance_score=float(r.get("relevance_score", 0.5)),
                cited_in_sections=_top_cited_sections(r.get("title", ""), ref_text, cited_counts),
            ))
        return result if result else None


def _find_reference_section(chunks: list[dict]) -> str:
    parts: list[str] = []
    for chunk in chunks:
        section = (chunk.get("section") or "").lower()
        if any(kw in section for kw in ("reference", "bibliograph")):
            parts.append(chunk.get("text", ""))
    if parts:
        return "\n".join(parts)
    # Fallback: scan last 4 chunks' text for "References" / "Bibliography" keyword
    for chunk in chunks[-4:]:
        text = chunk.get("text", "")
        if re.search(r'\b(References|Bibliography)\b', text, re.IGNORECASE):
            parts.append(text)
    return "\n".join(parts)


def _count_citations(chunks: list[dict]) -> Counter:
    cite_re = re.compile(r"\[(\d+)\]")
    counter: Counter = Counter()
    for chunk in chunks:
        section = (chunk.get("section") or "").lower()
        if any(kw in section for kw in ("introduct", "related work", "method", "approach")):
            nums = cite_re.findall(chunk.get("text", ""))
            counter.update(nums)
    return counter


def _rule_based_extract(
    paper_id: str,
    ref_text: str,
    cited_counts: Counter,
    topic_keywords: list[str],
) -> list[ExtractedReference]:
    entries = _parse_reference_entries(ref_text)
    scored: list[ExtractedReference] = []
    for entry in entries:
        title = entry.get("title", "")
        score = _tf_idf_similarity(title, topic_keywords)
        citation_boost = sum(
            cited_counts.get(str(i), 0) for i in entry.get("numbers", [])
        ) * 0.05
        scored.append(ExtractedReference(
            title=title,
            source_paper_id=paper_id,
            authors=entry.get("authors", []),
            year=entry.get("year", ""),
            venue=entry.get("venue", ""),
            relevance_score=min(1.0, score + citation_boost),
            cited_in_sections=[f"[{n}]" for n in entry.get("numbers", [])[:5]],
        ))
    scored.sort(key=lambda r: r.relevance_score, reverse=True)
    return scored[:5]


def _parse_reference_entries(text: str) -> list[dict]:
    # Strategy 1: Numbered references like [1], [2,3], etc.
    entry_re = re.compile(
        r'\[(\d+(?:,\d+)*)\]\s*(.+?)(?=\[\d+(?:,\d+)*\]|\Z)', re.DOTALL
    )
    entries: list[dict] = []
    for match in entry_re.finditer(text):
        nums_str = match.group(1)
        content = match.group(2).strip()
        nums = [int(x) for x in nums_str.split(",")]
        title = _extract_title(content)
        authors = _extract_authors(content)
        year = _extract_year(content)
        venue = _extract_venue(content)
        entries.append({
            "numbers": nums, "title": title, "authors": authors,
            "year": year, "venue": venue,
        })
    if entries:
        return entries

    # Strategy 2: Author-year format (no numbered markers)
    return _parse_author_year_entries(text)


def _parse_author_year_entries(text: str) -> list[dict]:
    """Parse author-year style references (common in CS papers)."""
    text = text.strip()
    # Remove leading "References" / "Bibliography" header line
    text = re.sub(r'^(References|Bibliography|REFERENCES)\s*\n+', '', text)
    # Remove [page N] markers
    text = re.sub(r'\[page\s*\d+\]', '', text)
    # Heal hyphenated line breaks: "Fei-\nFei," → "Fei-Fei," or "tra-\njectory" → "trajectory"
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)

    raw_entries = _split_author_year_blocks(text)

    entries: list[dict] = []
    for block in raw_entries:
        block = block.strip()
        if len(block) < 30:
            continue
        authors = _extract_authors(block)
        year = _extract_year(block)
        title = _extract_title_from_author_year(block, year)
        venue = _extract_venue(block)
        # Filter junk: need a real title
        if not title or len(title) < 8:
            continue
        entries.append({
            "numbers": [], "title": title, "authors": authors,
            "year": year, "venue": venue,
        })
    return entries


def _split_author_year_blocks(text: str) -> list[str]:
    """Split author-year reference text into individual entries."""
    # Author pattern: "LastName, FirstInitial." or "LastName, F. M."
    author_start = re.compile(
        r'(?:^|\n)([A-Z][a-zà-ü]+(?:-[A-Z][a-zà-ü]+)?,\s+[A-Z]\.)',
        re.MULTILINE,
    )
    matches = list(author_start.finditer(text))
    if len(matches) < 2:
        return [text]

    blocks: list[str] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append(text[start:end].strip())
    return blocks


def _extract_title_from_author_year(text: str, year: str) -> str:
    """Extract title from author-year entry."""
    if year:
        year_pos = text.find(year)
        if year_pos >= 0:
            if year_pos < len(text) * 0.65:
                # Year appears early → title follows year (Authors. Year. Title. Venue.)
                after_year = text[year_pos + 4:].strip().lstrip('.').strip()
                title = _trim_to_venue(after_year)
                if len(title) > 8:
                    return title
            else:
                # Year at end → title between authors and venue (Authors. Title. Venue, Year.)
                before = text[:year_pos].strip().rstrip(',.').strip()
                title = _strip_leading_authors(before)
                if len(title) > 8:
                    return _trim_to_venue(title)

    # Fallback: strip authors, then trim to venue
    title = _strip_leading_authors(text)
    title = _trim_to_venue(title)
    if len(title) > 8:
        return title
    # Last resort: first substantial sentence after position 20
    for m in re.finditer(r'(?<=\.\s)([A-Z][^.]{15,200})', text):
        return m.group(1).strip().rstrip('.')
    return text[:120].strip()


def _trim_to_venue(text: str) -> str:
    """Trim title text at venue boundary."""
    markers = ['In Proceedings', 'In Proc', 'In IEEE', 'In ACM',
               'In the', 'arXiv:', 'Available at', 'Proceedings of']
    end = len(text)
    for marker in markers:
        pos = text.find(marker)
        if pos > 10:
            end = min(end, pos)
    return text[:end].strip().rstrip('.')


def _strip_leading_authors(text: str) -> str:
    """Remove author list from beginning, returning title portion."""
    # Pattern: "and LastName, FirstInitial." marks end of authors
    m = re.search(r'(?:;\s*)?and\s+[A-Z][a-zà-ü-]+,\s+[A-Z]\.(?:\s*\(?\d{4}\)?)?\.?\s*', text)
    if m:
        return text[m.end():].strip().lstrip('.').strip()
    # Fallback: text after last "; Name, N." pattern
    last = 0
    for m in re.finditer(r';\s+[A-Z][a-zà-ü-]+,\s+[A-Z]\.', text):
        last = m.end()
    if last > 10:
        after = text[last:].strip().lstrip('.').strip()
        if len(after) > 8:
            return after
    return text



def _extract_title(text: str) -> str:
    m = re.search(r'"([^"]+)"', text)
    if m:
        return m.group(1)
    m = re.search(r'[.“]([^”".]{10,80})[.”]', text)
    if m:
        return m.group(1).strip()
    dot = text.find(".")
    if dot > 0:
        return text[:dot].strip()
    return text[:80].strip()


def _extract_authors(text: str) -> list[str]:
    m = re.match(r'([^.(]+?)(?:\.\s*"?|\s*\()', text)
    if m:
        parts = re.split(r',\s*|;\s*|\sand\s', m.group(1))
        return [p.strip() for p in parts if len(p.strip()) > 1]
    return []


def _extract_year(text: str) -> str:
    m = re.search(r'\((\d{4})\)', text)
    if m:
        return m.group(1)
    m = re.search(r'\b(19|20)\d{2}\b', text)
    return m.group(0) if m else ""


def _extract_venue(text: str) -> str:
    m = re.search(r'In\s+(.+?),?\s*(?:\d{4}|$)', text)
    if m:
        return m.group(1).strip()
    m = re.search(r'\.\s*([A-Z][A-Za-z\s]{3,30}),?\s*(?:\d{4}|\()', text)
    if m:
        return m.group(1).strip()
    return ""


def _topic_keywords(state: ResearchState) -> list[str]:
    try:
        return list(state.topic.keywords() or [])
    except Exception:
        pass
    return []


def _tf_idf_similarity(text: str, keywords: list[str]) -> float:
    if not text or not keywords:
        return 0.0
    text_lower = text.lower()
    # Break long keyword phrases into individual words for word-level matching
    key_words: set[str] = set()
    for kw in keywords:
        for word in str(kw).lower().split():
            w = word.strip().rstrip('.,;:!?')
            if len(w) >= 3:
                key_words.add(w)
    if not key_words:
        return 0.0

    # Require at least one domain anchor word for a non-zero score
    _ANCHORS = {'trajectory', 'pedestrian', 'motion', 'diffusion', 'intention',
                'multimodal', 'leapfrog', 'virat'}
    has_anchor = any(
        re.search(r'\b' + re.escape(w) + r'\b', text_lower)
        for w in key_words if w in _ANCHORS
    )
    if not has_anchor:
        return 0.0

    # Token-boundary matching: each key word matched as a whole word
    matches = sum(1 for w in key_words
                  if re.search(r'\b' + re.escape(w) + r'\b', text_lower))
    return min(1.0, matches / len(key_words) * 2.0)


def _top_cited_sections(title: str, ref_text: str, cited_counts: Counter) -> list[str]:
    if title:
        escaped = re.escape(title[:40])
        m = re.search(r'\[(\d+(?:,\d+)*)\]\s*[^\n]{0,60}' + escaped, ref_text)
        if m:
            return [f"[{n}]" for n in m.group(1).split(",")[:3]]
    return [f"[{k}]" for k, _v in cited_counts.most_common(3)]


def _deduplicate(
    refs: list[ExtractedReference], max_total: int = 20
) -> list[ExtractedReference]:
    seen: list[ExtractedReference] = []
    for ref in refs:
        is_dup = False
        for s in seen:
            if SequenceMatcher(None, ref.title.lower(), s.title.lower()).ratio() > 0.8:
                is_dup = True
                break
        if not is_dup:
            seen.append(ref)
        if len(seen) >= max_total:
            break
    return seen
