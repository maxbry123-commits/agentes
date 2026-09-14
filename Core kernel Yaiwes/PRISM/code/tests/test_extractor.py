"""Unit tests for ingestion extractor models and fallback behavior."""

from __future__ import annotations

import pytest

from mmem.config import MMemConfig
from mmem.ingestion.extractor import Extractor


class DummyLLM:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def chat_json(self, prompt, model=None, system=""):
        self.calls.append({
            "prompt": prompt,
            "model": model,
            "system": system,
        })
        if not self._responses:
            return {}
        return self._responses.pop(0)


class ExplodingLLM:
    """LLM mock that always raises."""

    def chat_json(self, prompt, model=None, system=""):
        raise RuntimeError("LLM is down")


class TestExtractor:
    def test_extract_parses_prompt_schema(self):
        llm = DummyLLM([{
            "episode_summary": "  Alice joined Acme in 2024.  ",
            "entities": [
                {"name": " Alice ", "entity_type": "Person"},
                {"name": " Acme ", "entity_type": "Organization"},
            ],
            "facet_points": [
                {
                    "content": "  Alice joined Acme in 2024. ",
                    "related_entity_name": " Alice ",
                    "timestamp_text": " 2024 ",
                }
            ],
            "facets": [
                {"theme": " Career ", "facet_point_indices": [0]}
            ],
            "temporal_info": [
                {
                    "subject": " Alice ",
                    "time_expression": " in 2024 ",
                    "normalized_time": " 2024 ",
                    "relation": " at ",
                }
            ],
        }])
        extractor = Extractor(llm_client=llm)

        result = extractor.extract("chunk text")
        assert result.episode_summary == "Alice joined Acme in 2024."
        assert result.entities[0].name == "Alice"
        assert result.entities[0].entity_type == "person"
        assert result.facet_points[0].related_entity_name == "Alice"
        assert result.facets[0].facet_point_indices == [0]
        assert result.temporal_info[0].time_expression == "in 2024"

    def test_extract_supports_legacy_schema(self):
        llm = DummyLLM([{
            "episode_summary": "A summary",
            "entities": [{"name": "Alice", "type": "person"}],
            "facet_points": [{
                "content": "Alice moved to NYC",
                "related_entity": "Alice",
                "timestamp": "2022",
            }],
            "facets": [{
                "theme": "Life",
                "facet_points": ["Alice moved to NYC"],
            }],
            "temporal_info": {
                "absolute_time": "2022",
                "relative_time": "",
                "resolved_time": "2022-01-01",
            },
        }])
        extractor = Extractor(llm_client=llm)

        result = extractor.extract("chunk text")
        assert result.entities[0].entity_type == "person"
        assert result.facet_points[0].related_entity_name == "Alice"
        assert result.facet_points[0].timestamp_text == "2022"
        assert result.facets[0].facet_point_indices == [0]
        assert len(result.temporal_info) == 1
        assert result.temporal_info[0].normalized_time == "2022-01-01"

    def test_extract_fallback_when_primary_invalid(self):
        llm = DummyLLM([
            {"bad": "shape"},
            {"episode_summary": "Fallback summary", "entities": [{"name": "Alice", "entity_type": "person"}]},
        ])
        extractor = Extractor(llm_client=llm)

        result = extractor.extract("chunk text")
        assert result.episode_summary == "Fallback summary"
        assert len(result.entities) == 1
        assert result.facet_points == []
        assert result.facets == []
        assert result.temporal_info == []
        assert len(llm.calls) == 2

    def test_extract_raises_when_fallback_disabled(self):
        cfg = MMemConfig()
        cfg.write.enable_fallback_extractor = False
        llm = DummyLLM([{"bad": "shape"}])
        extractor = Extractor(llm_client=llm, config=cfg)

        with pytest.raises(Exception):
            extractor.extract("chunk text")

    def test_extract_causal_formats_events_and_parses_response(self):
        llm = DummyLLM([{
            "causal_pairs": [
                {
                    "cause_id": "ep1",
                    "effect_id": "ep2",
                    "description": "Hiring caused relocation.",
                    "confidence": 0.82,
                }
            ]
        }])
        extractor = Extractor(llm_client=llm)
        pairs = extractor.extract_causal([("ep1", "Alice got hired"), ("ep2", "Alice moved")])

        assert len(pairs) == 1
        assert pairs[0].cause_id == "ep1"
        assert pairs[0].effect_id == "ep2"
        assert pairs[0].confidence == pytest.approx(0.82)
        assert "[ep1] Alice got hired" in llm.calls[0]["prompt"]
        assert "[ep2] Alice moved" in llm.calls[0]["prompt"]

    def test_fallback_returns_minimal_result_when_llm_completely_fails(self):
        extractor = Extractor(llm_client=ExplodingLLM())
        result = extractor.extract("Some chunk that should not crash the system")
        assert result.episode_summary
        assert result.facet_points == []
        assert result.facets == []
        assert result.temporal_info == []

    def test_fallback_minimal_result_truncates_long_chunk(self):
        long_chunk = "x" * 500
        extractor = Extractor(llm_client=ExplodingLLM())
        result = extractor.extract(long_chunk)
        assert len(result.episode_summary) <= 200

