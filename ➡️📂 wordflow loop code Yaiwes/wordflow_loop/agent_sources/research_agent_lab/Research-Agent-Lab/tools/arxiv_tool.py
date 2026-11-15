from __future__ import annotations

from urllib.parse import quote_plus
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from core.tool_base import ToolInput, ToolOutput
from schemas.paper import Paper


class ArxivTool:
    name = "arxiv"

    def __init__(self, max_results: int = 5, timeout: int = 20):
        self.max_results = max_results
        self.timeout = timeout

    def call(self, tool_input: ToolInput) -> ToolOutput:
        max_results = int((tool_input.options or {}).get("max_results", self.max_results))
        url = (
            "https://export.arxiv.org/api/query?"
            f"search_query=all:{quote_plus(tool_input.query)}"
            f"&start=0&max_results={max_results}"
        )
        with urlopen(url, timeout=self.timeout) as response:
            raw = response.read()
        papers = self._parse(raw)
        return ToolOutput(items=papers, metadata={"source": "arxiv", "url": url})

    def _parse(self, raw: bytes) -> list[Paper]:
        root = ET.fromstring(raw)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers: list[Paper] = []
        for entry in root.findall("atom:entry", ns):
            title = self._text(entry, "atom:title", ns)
            abstract = self._text(entry, "atom:summary", ns)
            url = self._text(entry, "atom:id", ns)
            authors = [
                self._text(author, "atom:name", ns)
                for author in entry.findall("atom:author", ns)
            ]
            published = self._text(entry, "atom:published", ns)
            year = int(published[:4]) if published[:4].isdigit() else None
            papers.append(
                Paper(
                    title=" ".join(title.split()),
                    abstract=" ".join(abstract.split()),
                    authors=authors,
                    year=year,
                    url=url,
                    source="arxiv",
                )
            )
        return papers

    def _text(self, node: ET.Element, path: str, ns: dict[str, str]) -> str:
        child = node.find(path, ns)
        return child.text.strip() if child is not None and child.text else ""
