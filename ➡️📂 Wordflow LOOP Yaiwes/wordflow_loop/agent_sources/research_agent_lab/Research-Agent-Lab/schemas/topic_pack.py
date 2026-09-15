from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from schemas.base import ensure_dict, load_mapping


@dataclass(slots=True)
class TopicPack:
    topic_name: str
    domain: dict[str, Any] = field(default_factory=dict)
    research_goal: dict[str, Any] = field(default_factory=dict)
    current_status: dict[str, Any] = field(default_factory=dict)
    search_seeds: dict[str, Any] = field(default_factory=dict)
    paper_schema: dict[str, Any] = field(default_factory=dict)
    experiment_metrics: list[str] = field(default_factory=list)
    codebase: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "TopicPack":
        topic_name = str(data.get("topic_name") or data.get("name") or "untitled_topic")
        return cls(
            topic_name=topic_name,
            domain=ensure_dict(data.get("domain")),
            research_goal=ensure_dict(data.get("research_goal")),
            current_status=ensure_dict(data.get("current_status")),
            search_seeds=ensure_dict(data.get("search_seeds")),
            paper_schema=ensure_dict(data.get("paper_schema")),
            experiment_metrics=[str(item) for item in data.get("experiment_metrics", [])],
            codebase=ensure_dict(data.get("codebase")),
            metadata=ensure_dict(data.get("metadata")),
        )

    def keywords(self) -> list[str]:
        raw = self.search_seeds.get("keywords", [])
        return [str(item) for item in raw]

    def allowed_auto_edit(self) -> list[str]:
        return [str(item) for item in self.codebase.get("allowed_auto_edit", [])]

    def protected_files(self) -> list[str]:
        return [str(item) for item in self.codebase.get("protected_files", [])]

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic_name": self.topic_name,
            "domain": self.domain,
            "research_goal": self.research_goal,
            "current_status": self.current_status,
            "search_seeds": self.search_seeds,
            "paper_schema": self.paper_schema,
            "experiment_metrics": self.experiment_metrics,
            "codebase": self.codebase,
            "metadata": self.metadata,
        }


def load_topic_pack(path: Path | str) -> TopicPack:
    return TopicPack.from_mapping(load_mapping(Path(path)))
