"""Tests für die PersonalityEngine.

Testet:
  - Tageszeit-abhängige Grüße
  - Persönlichkeits-Direktiven basierend auf Warmth/Humor-Config
  - build_personality_block() Generierung
  - Konfigurierbarkeit via PersonalityConfig
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from cognithor.config import PersonalityConfig
from cognithor.core.personality import PersonalityEngine


@pytest.fixture()
def default_engine() -> PersonalityEngine:
    return PersonalityEngine()


@pytest.fixture()
def warm_engine() -> PersonalityEngine:
    config = PersonalityConfig(
        warmth=0.9,
        humor=0.7,
        success_celebration=True,
        follow_up_questions=True,
        greeting_enabled=True,
    )
    return PersonalityEngine(config)


@pytest.fixture()
def cold_engine() -> PersonalityEngine:
    config = PersonalityConfig(
        warmth=0.0,
        humor=0.0,
        success_celebration=False,
        follow_up_questions=False,
        greeting_enabled=False,
    )
    return PersonalityEngine(config)


class TestGetGreetingFragment:
    """Tests für Tageszeit-abhängige Grüße."""

    def test_morning_greeting(self, default_engine: PersonalityEngine) -> None:
        with patch("cognithor.core.personality.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 8
            greeting = default_engine.get_greeting_fragment()
            assert "Morgen" in greeting

    def test_afternoon_greeting(self, default_engine: PersonalityEngine) -> None:
        with patch("cognithor.core.personality.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 14
            greeting = default_engine.get_greeting_fragment()
            assert greeting == ""  # no greeting in afternoon

    def test_evening_greeting(self, default_engine: PersonalityEngine) -> None:
        with patch("cognithor.core.personality.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 19
            greeting = default_engine.get_greeting_fragment()
            assert "Abend" in greeting

    def test_night_greeting(self, default_engine: PersonalityEngine) -> None:
        with patch("cognithor.core.personality.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 2
            greeting = default_engine.get_greeting_fragment()
            assert "wach" in greeting

    def test_greeting_disabled(self, cold_engine: PersonalityEngine) -> None:
        greeting = cold_engine.get_greeting_fragment()
        assert greeting == ""


class TestGetPersonalityDirectives:
    """Tests für Persönlichkeits-Direktiven."""

    def test_default_has_warmth_directives(self, default_engine: PersonalityEngine) -> None:
        directives = default_engine.get_personality_directives()
        assert "freundlich" in directives

    def test_warm_engine_has_empathy(self, warm_engine: PersonalityEngine) -> None:
        directives = warm_engine.get_personality_directives()
        assert "Verstaendnis" in directives or "clever" in directives

    def test_warm_engine_has_humor(self, warm_engine: PersonalityEngine) -> None:
        directives = warm_engine.get_personality_directives()
        assert "Witz" in directives or "locker" in directives

    def test_cold_engine_empty(self, cold_engine: PersonalityEngine) -> None:
        directives = cold_engine.get_personality_directives()
        assert directives == ""

    def test_success_celebration(self, warm_engine: PersonalityEngine) -> None:
        directives = warm_engine.get_personality_directives()
        assert "geklappt" in directives.lower() or "Fertig" in directives

    def test_follow_up_questions(self, warm_engine: PersonalityEngine) -> None:
        directives = warm_engine.get_personality_directives()
        assert "offen" in directives.lower() or "Sinn" in directives


class TestBuildPersonalityBlock:
    """Tests für den vollständigen Personality-Block."""

    def test_block_has_header(self, default_engine: PersonalityEngine) -> None:
        block = default_engine.build_personality_block()
        assert "## Persönlichkeit" in block

    def test_cold_engine_empty_block(self, cold_engine: PersonalityEngine) -> None:
        block = cold_engine.build_personality_block()
        assert block == ""

    def test_block_contains_directives(self, warm_engine: PersonalityEngine) -> None:
        block = warm_engine.build_personality_block()
        assert "freundlich" in block
        assert len(block) > 50


class TestPersonalityConfig:
    """Tests für die PersonalityConfig."""

    def test_default_values(self) -> None:
        config = PersonalityConfig()
        assert config.warmth == 0.7
        assert config.humor == 0.3
        assert config.follow_up_questions is True
        assert config.success_celebration is True
        assert config.greeting_enabled is True

    def test_custom_values(self) -> None:
        config = PersonalityConfig(warmth=0.1, humor=0.9)
        assert config.warmth == 0.1
        assert config.humor == 0.9

    def test_engine_uses_config(self) -> None:
        config = PersonalityConfig(warmth=0.2, humor=0.0)
        engine = PersonalityEngine(config)
        assert engine.config.warmth == 0.2
        directives = engine.get_personality_directives()
        assert "Witz" not in directives
