"""Tests for ObserverConfig — validation and defaults."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from cognithor.config import CognithorConfig, ObserverConfig


class TestObserverConfig:
    def test_defaults(self):
        cfg = ObserverConfig()
        assert cfg.enabled is True
        assert cfg.max_retries == 2
        assert cfg.check_hallucination is True
        assert cfg.check_sycophancy is True
        assert cfg.check_laziness is True
        assert cfg.check_tool_ignorance is True
        assert cfg.blocking_dimensions == ["hallucination", "tool_ignorance"]
        assert cfg.warning_prefix == "[Quality check flagged issues]"
        assert cfg.timeout_seconds == 30
        assert cfg.circuit_breaker_threshold == 5

    def test_rejects_unknown_dimension(self):
        with pytest.raises(ValidationError, match="Unknown dimensions"):
            ObserverConfig(blocking_dimensions=["hallucination", "pink_unicorn"])

    def test_rejects_out_of_range_retries(self):
        with pytest.raises(ValidationError):
            ObserverConfig(max_retries=-1)
        with pytest.raises(ValidationError):
            ObserverConfig(max_retries=6)

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError, match="Extra inputs"):
            ObserverConfig(unknown_field=True)

    def test_attached_to_jarvis_config(self):
        cfg = CognithorConfig()
        assert isinstance(cfg.observer, ObserverConfig)
        assert cfg.observer.enabled is True
