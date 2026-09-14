"""Tests fuer StrategyMemory — Meta-Reasoning Strategie-Tracking."""

from __future__ import annotations

import pytest

from cognithor.learning.strategy_memory import (
    StrategyMemory,
    StrategyRecord,
    classify_task_type,
)


@pytest.fixture()
def db_path(tmp_path):
    """Temporaerer Datenbankpfad."""
    return str(tmp_path / "strategies_test.db")


@pytest.fixture()
def mem(db_path):
    """StrategyMemory-Instanz mit temporaerer DB."""
    sm = StrategyMemory(db_path)
    yield sm
    sm.close()


# ── 1. record + query ─────────────────────────────────────────────────────


def test_record_and_query(mem: StrategyMemory) -> None:
    """Zwei Strategien speichern — best_strategy gibt die erfolgreiche zurueck."""
    mem.record(StrategyRecord("web_research", "search_first", True, 500.0, 3))
    mem.record(StrategyRecord("web_research", "scrape_direct", False, 800.0, 2))

    best = mem.best_strategy("web_research")
    assert best is not None
    assert best.strategy == "search_first"
    assert best.success_rate == 1.0
    assert best.total_uses == 1


# ── 2. no data ────────────────────────────────────────────────────────────


def test_best_strategy_no_data(mem: StrategyMemory) -> None:
    """Unbekannter Typ gibt None zurueck."""
    assert mem.best_strategy("unknown_type") is None


# ── 3. success rate calculation ───────────────────────────────────────────


def test_success_rate_calculation(mem: StrategyMemory) -> None:
    """7 Erfolge + 3 Misserfolge = 70% Erfolgsrate."""
    for _ in range(7):
        mem.record(StrategyRecord("code_execution", "plan_a", True, 200.0, 2))
    for _ in range(3):
        mem.record(StrategyRecord("code_execution", "plan_a", False, 300.0, 2))

    best = mem.best_strategy("code_execution")
    assert best is not None
    assert best.total_uses == 10
    assert abs(best.success_rate - 0.7) < 0.01


# ── 4. hint for planner ──────────────────────────────────────────────────


def test_hint_for_planner(mem: StrategyMemory) -> None:
    """Hint enthaelt Strategienamen und Prozentzahl."""
    mem.record(StrategyRecord("file_operations", "backup_first", True, 100.0, 1))
    mem.record(StrategyRecord("file_operations", "backup_first", True, 120.0, 1))

    hint = mem.get_strategy_hint("file_operations")
    assert "backup_first" in hint
    assert "100%" in hint


# ── 5. hint empty ─────────────────────────────────────────────────────────


def test_hint_empty_returns_empty(mem: StrategyMemory) -> None:
    """Keine Daten = leerer String."""
    assert mem.get_strategy_hint("nonexistent") == ""


# ── 6. classify_task_type ─────────────────────────────────────────────────


def test_classify_task() -> None:
    """Alle Aufgabentypen werden korrekt klassifiziert."""
    assert classify_task_type(["web_search", "fetch_url"]) == "web_research"
    assert classify_task_type(["run_python", "execute_code"]) == "code_execution"
    assert classify_task_type(["memory_store", "vault_recall"]) == "knowledge_management"
    assert classify_task_type(["create_pdf", "document_export"]) == "document_creation"
    assert classify_task_type(["read_file", "write_file"]) == "file_operations"
    assert classify_task_type(["shell_exec", "run_command"]) == "system_command"
    assert classify_task_type(["browser_open", "browser_click"]) == "browser_automation"
    assert classify_task_type(["send_telegram", "send_email"]) == "communication"
    assert classify_task_type(["unknown_tool"]) == "general"
    assert classify_task_type([]) == "general"


# ── 7. persistence ───────────────────────────────────────────────────────


def test_persistence(db_path: str) -> None:
    """Daten ueberleben Neustart der Instanz."""
    sm1 = StrategyMemory(db_path)
    sm1.record(StrategyRecord("web_research", "cached_search", True, 150.0, 2))
    sm1.record(StrategyRecord("web_research", "cached_search", True, 160.0, 2))
    sm1.close()

    sm2 = StrategyMemory(db_path)
    try:
        best = sm2.best_strategy("web_research")
        assert best is not None
        assert best.strategy == "cached_search"
        assert best.total_uses == 2
    finally:
        sm2.close()
