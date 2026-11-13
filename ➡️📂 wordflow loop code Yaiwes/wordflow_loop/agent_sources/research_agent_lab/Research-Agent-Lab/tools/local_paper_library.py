from __future__ import annotations

from pathlib import Path
import re

from schemas.paper import Paper
from schemas.topic_pack import TopicPack


class LocalPaperLibrary:
    def scan(self, topic: TopicPack) -> list[Paper]:
        literature = topic.metadata.get("literature", {})
        dirs = [Path(path) for path in literature.get("local_paper_dirs", [])]
        patterns = literature.get("include_patterns", ["*.pdf", "*.md", "*.txt"])
        max_files = int(literature.get("max_files", 200))

        papers: list[Paper] = []
        for folder in dirs:
            if not folder.exists():
                continue
            library_name = folder.name
            for pattern in patterns:
                for path in folder.rglob(pattern):
                    if path.is_file():
                        papers.append(self._paper_from_path(path, library_name, topic))
                        if len(papers) >= max_files:
                            return self.rank(papers, topic)
        return self.rank(papers, topic)

    def rank(self, papers: list[Paper], topic: TopicPack) -> list[Paper]:
        keywords = [keyword.lower() for keyword in topic.keywords()]
        ranked: list[Paper] = []
        for paper in papers:
            text = f"{paper.title} {' '.join(paper.keywords)}".lower()
            score = 0.0
            for keyword in keywords:
                if keyword and keyword in text:
                    score += 1.0
                else:
                    for part in keyword.split():
                        if len(part) >= 4 and part in text:
                            score += 0.15
            paper.relevance_score = min(1.0, score / max(len(keywords), 1))
            paper.triage_reason = "local paper library match"
            ranked.append(paper)
        return sorted(ranked, key=lambda item: (item.relevance_score, item.title), reverse=True)

    def _paper_from_path(self, path: Path, library_name: str, topic: TopicPack) -> Paper:
        title = self._title_from_filename(path.stem)
        return Paper(
            title=title,
            abstract=f"Local library file: {path}",
            pdf_path=str(path) if path.suffix.lower() == ".pdf" else "",
            local_path=str(path),
            library=library_name,
            keywords=self._keywords_from_title(title, topic),
            source="local_paper",
        )

    def _title_from_filename(self, stem: str) -> str:
        cleaned = re.sub(r"[_]+", " ", stem)
        cleaned = re.sub(r"^\d+[-_\s]+", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or stem

    def _keywords_from_title(self, title: str, topic: TopicPack) -> list[str]:
        text = title.lower()
        hits: list[str] = []
        for keyword in topic.keywords():
            if keyword.lower() in text:
                hits.append(keyword)
        for token in ["diffusion", "trajectory", "pedestrian", "intention", "language", "transformer"]:
            if token in text and token not in hits:
                hits.append(token)
        return hits
