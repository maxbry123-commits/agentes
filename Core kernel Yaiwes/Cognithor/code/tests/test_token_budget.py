"""Tests for the token budget manager."""

from __future__ import annotations

from cognithor.core.token_budget import (
    CHANNEL_MULTIPLIERS,
    COMPLEXITY_BUDGETS,
    PHASE_RATIOS,
    BudgetSnapshot,
    TokenBudgetManager,
)

# --- Basic construction ---


def test_default_construction():
    mgr = TokenBudgetManager()
    assert mgr.complexity == "medium"
    assert mgr.channel == "webui"
    assert mgr.total == COMPLEXITY_BUDGETS["medium"] * CHANNEL_MULTIPLIERS["webui"]
    assert mgr.allocated == 0
    assert mgr.remaining == mgr.total
    assert mgr.exceeded is False


def test_custom_complexity_and_channel():
    mgr = TokenBudgetManager(complexity="research", channel="telegram")
    expected = int(COMPLEXITY_BUDGETS["research"] * CHANNEL_MULTIPLIERS["telegram"])
    assert mgr.total == expected
    assert mgr.complexity == "research"
    assert mgr.channel == "telegram"


def test_invalid_complexity_falls_back_to_medium():
    mgr = TokenBudgetManager(complexity="nonexistent")
    assert mgr.complexity == "medium"
    assert mgr.total == int(COMPLEXITY_BUDGETS["medium"] * CHANNEL_MULTIPLIERS.get("webui", 0.8))


def test_unknown_channel_uses_default_multiplier():
    mgr = TokenBudgetManager(channel="unknown_channel")
    # Unknown channels get 0.8 multiplier
    expected = int(COMPLEXITY_BUDGETS["medium"] * 0.8)
    assert mgr.total == expected


# --- Allocation ---


def test_allocate_within_budget():
    mgr = TokenBudgetManager(complexity="simple", channel="cli")
    assert mgr.allocate(100) is True
    assert mgr.allocated == 100
    assert mgr.remaining == mgr.total - 100
    assert mgr.exceeded is False


def test_allocate_exceeds_budget():
    mgr = TokenBudgetManager(complexity="simple", channel="cli")
    total = mgr.total
    assert mgr.allocate(total + 100) is False
    assert mgr.exceeded is True
    assert mgr.remaining == 0


def test_multiple_allocations():
    mgr = TokenBudgetManager(complexity="medium", channel="cli")
    mgr.allocate(500)
    mgr.allocate(500)
    assert mgr.allocated == 1000


def test_remaining_never_negative():
    mgr = TokenBudgetManager(complexity="simple", channel="cli")
    mgr.allocate(mgr.total + 1000)
    assert mgr.remaining == 0


# --- Phase budgets ---


def test_phase_budget_planner():
    mgr = TokenBudgetManager(complexity="medium", channel="cli")
    expected = int(mgr.total * PHASE_RATIOS["planner"])
    assert mgr.get_phase_budget("planner") == expected


def test_phase_budget_executor():
    mgr = TokenBudgetManager(complexity="complex", channel="webui")
    expected = int(mgr.total * PHASE_RATIOS["executor"])
    assert mgr.get_phase_budget("executor") == expected


def test_phase_budget_formulate():
    mgr = TokenBudgetManager(complexity="research", channel="telegram")
    expected = int(mgr.total * PHASE_RATIOS["formulate"])
    assert mgr.get_phase_budget("formulate") == expected


def test_phase_budget_unknown_phase():
    mgr = TokenBudgetManager()
    assert mgr.get_phase_budget("nonexistent") == 0


def test_phase_budgets_sum_to_total():
    mgr = TokenBudgetManager(complexity="complex", channel="cli")
    total_phases = sum(mgr.get_phase_budget(p) for p in PHASE_RATIOS)
    # Allow rounding error of 1
    assert abs(total_phases - mgr.total) <= len(PHASE_RATIOS)


# --- Complexity detection ---


def test_detect_simple():
    assert TokenBudgetManager.detect_complexity("hallo") == "simple"
    assert TokenBudgetManager.detect_complexity("was ist Python?") == "simple"
    assert TokenBudgetManager.detect_complexity("danke") == "simple"


def test_detect_medium():
    assert TokenBudgetManager.detect_complexity(
        "Erklaere mir den Unterschied zwischen Listen und Tupeln in Python"
    ) in ("medium", "research")


def test_detect_complex():
    result = TokenBudgetManager.detect_complexity(
        "implementiere eine REST API mit FastAPI und deploy auf Docker"
    )
    assert result == "complex"


def test_detect_research():
    result = TokenBudgetManager.detect_complexity(
        "Recherchiere ausfuehrlich die Vor- und Nachteile von Kubernetes vs Docker Swarm"
    )
    assert result == "research"


def test_detect_by_tool_count():
    assert TokenBudgetManager.detect_complexity("do stuff", tool_count=5) == "research"
    assert TokenBudgetManager.detect_complexity("do stuff", tool_count=3) == "complex"


def test_detect_empty_message():
    assert TokenBudgetManager.detect_complexity("") == "simple"


def test_detect_long_message():
    long_msg = " ".join(["word"] * 60)
    assert TokenBudgetManager.detect_complexity(long_msg) == "complex"


# --- Snapshot ---


def test_snapshot():
    mgr = TokenBudgetManager(complexity="complex", channel="discord")
    mgr.allocate(1000)
    snap = mgr.snapshot()

    assert isinstance(snap, BudgetSnapshot)
    assert snap.total == mgr.total
    assert snap.allocated == 1000
    assert snap.remaining == mgr.total - 1000
    assert snap.exceeded is False
    assert snap.complexity == "complex"
    assert snap.channel == "discord"
    assert "planner" in snap.phase_budgets
    assert "executor" in snap.phase_budgets
    assert "formulate" in snap.phase_budgets


# --- Channel multipliers ---


def test_telegram_has_small_budget():
    telegram = TokenBudgetManager(complexity="medium", channel="telegram")
    webui = TokenBudgetManager(complexity="medium", channel="webui")
    assert telegram.total < webui.total


def test_voice_has_smallest_budget():
    voice = TokenBudgetManager(complexity="medium", channel="voice")
    telegram = TokenBudgetManager(complexity="medium", channel="telegram")
    assert voice.total < telegram.total


def test_cli_same_as_webui():
    cli = TokenBudgetManager(complexity="medium", channel="cli")
    webui = TokenBudgetManager(complexity="medium", channel="webui")
    assert cli.total == webui.total
