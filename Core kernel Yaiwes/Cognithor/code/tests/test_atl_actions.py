"""Tests for ATL action dispatch extensions."""

from __future__ import annotations


class TestRiskCeiling:
    def test_green_allows_green(self):
        from cognithor.evolution.loop import _check_risk_ceiling

        assert _check_risk_ceiling("research", "GREEN") is True

    def test_green_blocks_yellow(self):
        from cognithor.evolution.loop import _check_risk_ceiling

        assert _check_risk_ceiling("file_management", "GREEN") is False

    def test_yellow_allows_all(self):
        from cognithor.evolution.loop import _check_risk_ceiling

        assert _check_risk_ceiling("file_management", "YELLOW") is True
        assert _check_risk_ceiling("research", "YELLOW") is True

    def test_unknown_action_is_yellow(self):
        from cognithor.evolution.loop import _check_risk_ceiling

        assert _check_risk_ceiling("unknown_thing", "GREEN") is False
        assert _check_risk_ceiling("unknown_thing", "YELLOW") is True
