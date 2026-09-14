"""
LLM-backed structured extraction for ingestion.

This module converts raw LLM JSON outputs into strongly-typed Pydantic models
and provides compatibility shims for legacy schema variants.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Sequence

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from mmem.config import MMemConfig, get_config
from mmem.core.nodes import Episode
from mmem.utils.llm import LLMClient, get_llm_client

logger = logging.getLogger(__name__)

from .prompts import CAUSAL_PROMPT, EXTRACTION_PROMPT, FALLBACK_EXTRACTION_PROMPT


class EntityInfo(BaseModel):
    name: str
    entity_type: str = "concept"

    @model_validator(mode="before")
    @classmethod
    def _compat_legacy_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "entity_type" not in data and "type" in data:
            data = dict(data)
            data["entity_type"] = data.get("type")
        return data

    @field_validator("name")
    @classmethod
    def _normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("entity_type")
    @classmethod
    def _normalize_entity_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        return normalized or "concept"


class FacetPointInfo(BaseModel):
    content: str
    related_entity_name: str | None = None
    timestamp_text: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _compat_legacy_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)
        if "related_entity_name" not in d and "related_entity" in d:
            d["related_entity_name"] = d.get("related_entity")
        if "timestamp_text" not in d and "timestamp" in d:
            d["timestamp_text"] = d.get("timestamp")
        return d

    @field_validator("content")
    @classmethod
    def _normalize_content(cls, value: str) -> str:
        return value.strip()

    @field_validator("related_entity_name", "timestamp_text")
    @classmethod
    def _normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class FacetInfo(BaseModel):
    theme: str
    facet_point_indices: list[int] = Field(default_factory=list)

    @field_validator("theme")
    @classmethod
    def _normalize_theme(cls, value: str) -> str:
        return value.strip()

    @field_validator("facet_point_indices")
    @classmethod
    def _normalize_indices(cls, indices: list[int]) -> list[int]:
        out: list[int] = []
        for idx in indices:
            idx_int = int(idx)
            if idx_int >= 0:
                out.append(idx_int)
        return out


class TemporalInfo(BaseModel):
    subject: str = ""
    time_expression: str = ""
    normalized_time: str | None = None
    relation: str = "at"

    @field_validator("subject", "time_expression", "relation")
    @classmethod
    def _normalize_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("normalized_time")
    @classmethod
    def _normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ExtractionResult(BaseModel):
    episode_summary: str
    entities: list[EntityInfo] = Field(default_factory=list)
    facet_points: list[FacetPointInfo] = Field(default_factory=list)
    facets: list[FacetInfo] = Field(default_factory=list)
    temporal_info: list[TemporalInfo] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _compat_legacy_shapes(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        d = dict(data)

        # Legacy shape: temporal_info as a single object with absolute/relative/resolved fields.
        temporal_raw = d.get("temporal_info")
        if temporal_raw is None:
            d["temporal_info"] = []
        elif isinstance(temporal_raw, dict):
            absolute_time = str(temporal_raw.get("absolute_time", "")).strip()
            relative_time = str(temporal_raw.get("relative_time", "")).strip()
            resolved_time = str(temporal_raw.get("resolved_time", "")).strip()
            time_expression = absolute_time or relative_time
            if time_expression:
                d["temporal_info"] = [{
                    "subject": "",
                    "time_expression": time_expression,
                    "normalized_time": resolved_time or None,
                    "relation": "at",
                }]
            else:
                d["temporal_info"] = []
        elif not isinstance(temporal_raw, list):
            d["temporal_info"] = []

        raw_fps = d.get("facet_points")
        if not isinstance(raw_fps, list):
            raw_fps = []
            d["facet_points"] = raw_fps

        content_to_index: dict[str, int] = {}
        for i, item in enumerate(raw_fps):
            if isinstance(item, dict):
                content = item.get("content")
                if isinstance(content, str):
                    normalized = content.strip()
                    if normalized and normalized not in content_to_index:
                        content_to_index[normalized] = i

        raw_facets = d.get("facets")
        if isinstance(raw_facets, list):
            converted: list[Any] = []
            for facet in raw_facets:
                if not isinstance(facet, dict):
                    converted.append(facet)
                    continue
                fd = dict(facet)

                # Legacy shape: "facet_points": list[str] or list[int]
                if "facet_point_indices" not in fd and "facet_points" in fd:
                    indices: list[int] = []
                    old_links = fd.get("facet_points")
                    if isinstance(old_links, list):
                        for item in old_links:
                            if isinstance(item, int):
                                if item >= 0:
                                    indices.append(item)
                            elif isinstance(item, str):
                                key = item.strip()
                                if key in content_to_index:
                                    indices.append(content_to_index[key])
                    fd["facet_point_indices"] = indices

                converted.append(fd)
            d["facets"] = converted
        elif raw_facets is None:
            d["facets"] = []

        return d

    @field_validator("episode_summary")
    @classmethod
    def _normalize_summary(cls, value: str) -> str:
        return value.strip()


class CausalPair(BaseModel):
    cause_id: str
    effect_id: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("cause_id", "effect_id", "description")
    @classmethod
    def _normalize_text(cls, value: str) -> str:
        return value.strip()


class CausalResponse(BaseModel):
    causal_pairs: list[CausalPair] = Field(default_factory=list)


class Extractor:
    """High-level extraction facade around LLM prompts and schema validation."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        config: Optional[MMemConfig] = None,
    ) -> None:
        self._config = config or get_config()
        self._llm = llm_client or get_llm_client()

    def extract(self, chunk: str) -> ExtractionResult:
        """Run full extraction prompt and validate typed output."""
        try:
            raw = self._llm.chat_json(
                prompt=EXTRACTION_PROMPT.format(chunk=chunk),
                model=self._config.llm.extraction_model,
                system="Return strict JSON only.",
            )
            if not raw:
                logger.warning(
                    "LLM returned empty JSON for extraction (chunk preview: %r); attempting fallback",
                    chunk[:120],
                )
                if self._config.write.enable_fallback_extractor:
                    return self._fallback_extract(chunk)
                return ExtractionResult(
                    episode_summary=chunk[:200].strip() or "(empty chunk)",
                )
            return ExtractionResult.model_validate(raw)
        except ValidationError as ve:
            logger.warning(
                "Extraction validation failed: %s (chunk preview: %r)",
                ve,
                chunk[:120],
            )
            if not self._config.write.enable_fallback_extractor:
                raise
            return self._fallback_extract(chunk)
        except Exception as e:
            logger.warning(
                "Primary extraction failed (%s: %s), attempting fallback (chunk preview: %r)",
                type(e).__name__,
                e,
                chunk[:120],
            )
            if not self._config.write.enable_fallback_extractor:
                raise
            return self._fallback_extract(chunk)

    def _fallback_extract(self, chunk: str) -> ExtractionResult:
        """Fallback extractor that returns only summary + entities.

        If even the fallback LLM call fails to produce a valid result, returns
        a minimal ExtractionResult with only a truncated chunk as summary so
        that the pipeline never crashes on a single bad chunk.
        """
        try:
            raw = self._llm.chat_json(
                prompt=FALLBACK_EXTRACTION_PROMPT.format(chunk=chunk),
                model=self._config.llm.extraction_model,
                system="Return strict JSON only.",
            )
            payload = raw if isinstance(raw, dict) else {}
            payload.setdefault("facet_points", [])
            payload.setdefault("facets", [])
            payload.setdefault("temporal_info", [])
            return ExtractionResult.model_validate(payload)
        except Exception:
            logger.warning("Fallback extraction also failed; returning minimal result")
            return ExtractionResult(
                episode_summary=chunk[:200].strip() or "(empty chunk)",
            )

    def extract_key_sentences(self, chunk: str) -> list[str]:
        """Extract 2-3 most information-dense sentences from a chunk."""
        try:
            from .prompts import KEY_SENTENCES_PROMPT
            raw = self._llm.chat_json(
                prompt=KEY_SENTENCES_PROMPT.format(chunk=chunk),
                model=self._config.llm.extraction_model,
                system="Return strict JSON only.",
                temperature=0.0,
            )
            if isinstance(raw, list):
                return [str(s).strip() for s in raw if isinstance(s, str) and s.strip()]
            # Fallback: LLM occasionally wraps the list in a dict like
            # {"sentences": [...]}. Take the first list-valued field.
            if isinstance(raw, dict):
                for value in raw.values():
                    if isinstance(value, list):
                        return [str(s).strip() for s in value if isinstance(s, str) and s.strip()]
            return []
        except Exception as exc:
            logger.warning("Key sentence extraction failed: %s", exc, exc_info=True)
            return []

    def extract_causal(self, episodes: Sequence[Episode | tuple[str, str] | dict[str, Any]]) -> list[CausalPair]:
        """Extract likely causal edges from a batch of episode summaries."""
        if not episodes:
            return []

        records = self._normalize_episode_records(episodes)
        if not records:
            return []

        events = "\n".join(f"- [{eid}] {summary}" for eid, summary in records)
        raw = self._llm.chat_json(
            prompt=CAUSAL_PROMPT.format(events=events),
            model=self._config.llm.causal_model,
            system="Return strict JSON only.",
        )

        if isinstance(raw, list):
            payload = {"causal_pairs": raw}
        elif isinstance(raw, dict):
            payload = raw
        else:
            payload = {"causal_pairs": []}

        return CausalResponse.model_validate(payload).causal_pairs

    def _normalize_episode_records(
        self,
        episodes: Sequence[Episode | tuple[str, str] | dict[str, Any]],
    ) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for item in episodes:
            if isinstance(item, Episode):
                eid = item.id.strip()
                summary = item.summary.strip()
            elif isinstance(item, tuple) and len(item) == 2:
                eid = str(item[0]).strip()
                summary = str(item[1]).strip()
            elif isinstance(item, dict):
                eid = str(item.get("id", "")).strip()
                summary = str(item.get("summary", "")).strip()
            else:
                continue

            if eid and summary:
                out.append((eid, summary))
        return out


__all__ = [
    "EntityInfo",
    "FacetPointInfo",
    "FacetInfo",
    "TemporalInfo",
    "ExtractionResult",
    "CausalPair",
    "CausalResponse",
    "Extractor",
]

