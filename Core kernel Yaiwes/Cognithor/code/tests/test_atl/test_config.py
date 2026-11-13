"""Tests for ATL configuration."""

from __future__ import annotations

from cognithor.evolution.atl_config import ATLConfig


def test_atl_config_defaults():
    cfg = ATLConfig()
    assert cfg.enabled is False
    assert cfg.interval_minutes == 15
    assert cfg.max_actions_per_cycle == 3
    assert cfg.max_tokens_per_cycle == 4000
    assert cfg.risk_ceiling == "YELLOW"
    assert cfg.notification_level == "important"
    assert "shell_exec" in cfg.blocked_action_types


def test_atl_config_quiet_hours():
    cfg = ATLConfig(quiet_hours_start="22:00", quiet_hours_end="08:00")
    assert cfg.quiet_hours_start == "22:00"
    assert cfg.quiet_hours_end == "08:00"


def test_atl_config_validates_interval():
    cfg = ATLConfig(interval_minutes=3)
    assert cfg.interval_minutes == 5  # clamped to minimum

    cfg2 = ATLConfig(interval_minutes=120)
    assert cfg2.interval_minutes == 60  # clamped to maximum


def test_atl_config_validates_risk_ceiling():
    cfg = ATLConfig(risk_ceiling="INVALID")
    assert cfg.risk_ceiling == "YELLOW"  # falls back to default


def test_atl_config_validates_notification_level():
    cfg = ATLConfig(notification_level="invalid")
    assert cfg.notification_level == "important"  # falls back to default
