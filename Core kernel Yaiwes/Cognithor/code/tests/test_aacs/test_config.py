"""Tests for AACS configuration."""

from __future__ import annotations

from cognithor.aacs.config import AACSConfig, AACSFeatureFlags


def test_config_defaults():
    cfg = AACSConfig()
    assert cfg.default_token_ttl == 300
    assert cfg.max_token_ttl == 3600
    assert cfg.min_token_ttl == 10
    assert cfg.max_delegation_depth == 5
    assert cfg.max_active_tokens_per_agent == 50
    assert cfg.trust_score_initial == 0.5


def test_config_validate_passes():
    cfg = AACSConfig()
    cfg.validate()


def test_config_memory_tiers():
    cfg = AACSConfig()
    assert cfg.memory_tiers[1] == "working"
    assert cfg.memory_tiers[5] == "system_config"
    assert len(cfg.memory_tiers) == 5


def test_feature_flags_defaults():
    flags = AACSFeatureFlags()
    assert flags.token_validation_enabled is False
    assert flags.enforcement_mode == "log_only"


def test_feature_flags_enforce():
    flags = AACSFeatureFlags(
        token_validation_enabled=True,
        enforcement_mode="enforce",
    )
    assert flags.token_validation_enabled
    assert flags.enforcement_mode == "enforce"
