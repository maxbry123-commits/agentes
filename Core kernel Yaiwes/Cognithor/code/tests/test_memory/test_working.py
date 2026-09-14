"""Tests für memory/working.py · Tier 5 Session-Kontext."""

from __future__ import annotations

from cognithor.config import MemoryConfig
from cognithor.memory.chunker import _estimate_tokens
from cognithor.memory.working import STATIC_BUDGET, WorkingMemoryManager
from cognithor.models import Message, ToolResult


def _msg(role: str = "user", content: str = "x" * 400) -> Message:
    """Erstellt eine Test-Nachricht (~100 Tokens)."""
    return Message(role=role, content=content)


class TestWorkingMemoryManager:
    def test_init(self):
        wm = WorkingMemoryManager()
        assert wm.max_tokens == 32768
        assert wm.current_chat_tokens == 0
        assert wm.usage_ratio == 0.0

    def test_new_session(self):
        wm = WorkingMemoryManager()
        wm.add_message(_msg())
        wm_obj = wm.new_session("test-session")
        assert wm_obj.session_id == "test-session"
        assert len(wm.memory.chat_history) == 0

    def test_add_message(self):
        wm = WorkingMemoryManager()
        wm.add_message(_msg("user", "Hello"))
        assert len(wm.memory.chat_history) == 1
        assert wm.current_chat_tokens > 0

    def test_add_tool_result(self):
        wm = WorkingMemoryManager()
        result = ToolResult(tool_name="test", output="ok", success=True)
        wm.add_tool_result(result)
        assert len(wm.memory.tool_results) == 1

    def test_set_core_memory(self):
        wm = WorkingMemoryManager()
        wm.set_core_memory("# Test\nHello")
        assert wm.memory.core_memory_text == "# Test\nHello"

    def test_available_chat_tokens(self):
        wm = WorkingMemoryManager(max_tokens=32768)
        avail = wm.available_chat_tokens
        # Instance _static_budget includes tactical (400) which module-level STATIC_BUDGET omits
        assert avail == 32768 - wm._static_budget
        assert avail > 0

    def test_usage_ratio_grows(self):
        wm = WorkingMemoryManager(max_tokens=10000)
        r0 = wm.usage_ratio
        for _ in range(20):
            wm.add_message(_msg())
        r1 = wm.usage_ratio
        assert r1 > r0

    def test_needs_compaction(self):
        config = MemoryConfig(compaction_threshold=0.8, compaction_keep_last_n=4)
        wm = WorkingMemoryManager(config=config, max_tokens=10000)
        assert not wm.needs_compaction

        # Fill up to trigger compaction
        for _ in range(100):
            wm.add_message(_msg(content="x" * 800))  # ~200 tokens each

        assert wm.needs_compaction

    def test_compact_removes_old(self):
        config = MemoryConfig(compaction_keep_last_n=4)
        wm = WorkingMemoryManager(config=config, max_tokens=50000)

        for i in range(10):
            wm.add_message(_msg(content=f"Nachricht {i}"))

        result = wm.compact()
        assert result.messages_removed == 6  # 10 - 4
        assert result.tokens_freed > 0
        assert len(wm.memory.chat_history) == 4

    def test_compact_nothing_to_remove(self):
        config = MemoryConfig(compaction_keep_last_n=10)
        wm = WorkingMemoryManager(config=config)

        for _i in range(3):
            wm.add_message(_msg())

        result = wm.compact()
        assert result.messages_removed == 0
        assert len(wm.memory.chat_history) == 3

    def test_get_removable_messages(self):
        config = MemoryConfig(compaction_keep_last_n=3)
        wm = WorkingMemoryManager(config=config)

        for i in range(7):
            wm.add_message(_msg(content=f"Msg {i}"))

        removable = wm.get_removable_messages()
        assert len(removable) == 4  # 7 - 3
        assert "Msg 0" in removable[0].content

    def test_inject_memories(self):
        wm = WorkingMemoryManager()
        wm.inject_memories([])  # Empty is fine
        assert wm.memory.injected_memories == []

    def test_inject_procedures_max_two(self):
        wm = WorkingMemoryManager()
        wm.inject_procedures(["Proc A", "Proc B", "Proc C"])
        assert len(wm.memory.injected_procedures) == 2  # Max 2

    def test_build_context_parts(self):
        wm = WorkingMemoryManager()
        wm.set_core_memory("# Core\nI am Jarvis")
        wm.inject_procedures(["Step 1: Do thing"])

        parts = wm.build_context_parts()
        assert "core_memory" in parts
        assert "Jarvis" in parts["core_memory"]
        assert "procedures" in parts

    def test_build_context_empty(self):
        wm = WorkingMemoryManager()
        parts = wm.build_context_parts()
        assert parts == {}

    def test_budget_report(self):
        wm = WorkingMemoryManager()
        wm.add_message(_msg())
        report = wm.build_budget_report()
        assert "Token-Budget" in report
        assert "Chat verfügbar" in report
        assert "Compaction nötig" in report

    def test_set_plan(self):
        from cognithor.models import ActionPlan, PlannedAction

        wm = WorkingMemoryManager()
        plan = ActionPlan(
            goal="Test",
            steps=[PlannedAction(tool="test", rationale="Step 1")],
        )
        wm.set_plan(plan)
        assert wm.memory.active_plan is not None
        assert wm.memory.active_plan.goal == "Test"

        wm.set_plan(None)
        assert wm.memory.active_plan is None


class TestTokenEstimation:
    """Tests für die verbesserte Token-Schätzung (sprachbewusst statt len/4)."""

    def test_uses_chunker_estimate(self) -> None:
        """_estimate_message_tokens nutzt _estimate_tokens aus chunker."""
        text = "Dies ist ein Test mit einigen Wörtern."
        msg = Message(role="user", content=text)
        wm = WorkingMemoryManager()
        tokens = wm._estimate_message_tokens(msg)
        # Sprachbewusste Schätzung + Overhead (10)
        expected = _estimate_tokens(text) + 10
        assert tokens == expected

    def test_german_composita_more_tokens(self) -> None:
        """Deutsche Komposita erzeugen mehr Tokens als len/4."""
        text = "Berufsunfähigkeitsversicherung Haftpflichtversicherungsgesellschaft"
        msg = Message(role="user", content=text)
        wm = WorkingMemoryManager()
        tokens = wm._estimate_message_tokens(msg)
        naive = len(text) // 4 + 10
        # Sprachbewusste Schätzung sollte höher sein als naive len/4
        assert tokens >= naive

    def test_empty_message(self) -> None:
        """Leere Nachricht ergibt Minimum-Tokens."""
        msg = Message(role="user", content="")
        wm = WorkingMemoryManager()
        tokens = wm._estimate_message_tokens(msg)
        # _estimate_tokens("") = 1 + Overhead 10
        assert tokens == 11

    def test_whitespace_only(self) -> None:
        """Whitespace-only Content ergibt Minimum-Tokens."""
        msg = Message(role="user", content="   ")
        wm = WorkingMemoryManager()
        tokens = wm._estimate_message_tokens(msg)
        assert tokens >= 11  # Minimum + Overhead


class TestConfigurableBudgets:
    """Tests für konfigurierbare Token-Budget-Verteilung."""

    def test_default_budgets(self) -> None:
        """Default-Budgets stimmen mit Modul-Konstanten überein."""
        wm = WorkingMemoryManager()
        # Instance includes BUDGET_TACTICAL (400) which module-level STATIC_BUDGET omits
        assert wm._static_budget == STATIC_BUDGET + 400

    def test_custom_budgets(self) -> None:
        """Konfigurierte Budgets werden korrekt angewendet."""
        config = MemoryConfig(
            budget_core_memory=1000,
            budget_system_prompt=1000,
            budget_procedures=1000,
            budget_injected_memories=1000,
            budget_tool_descriptions=1000,
            budget_response_reserve=1000,
        )
        wm = WorkingMemoryManager(config=config, max_tokens=32768)
        # 6x1000 custom + 400 tactical (default, not in MemoryConfig) = 6400
        assert wm._static_budget == 6400
        assert wm.available_chat_tokens == 32768 - 6400

    def test_budget_report_uses_instance_values(self) -> None:
        """Budget-Report zeigt konfigurierte Werte, nicht Modul-Konstanten."""
        config = MemoryConfig(budget_response_reserve=5000)
        wm = WorkingMemoryManager(config=config)
        report = wm.build_budget_report()
        assert "~5000" in report

    def test_compaction_with_custom_budget(self) -> None:
        """Compaction berücksichtigt konfigurierte Budgets."""
        config = MemoryConfig(
            compaction_threshold=0.5,
            compaction_keep_last_n=2,
            budget_response_reserve=500,  # Kleiner → mehr Chat-Budget
        )
        wm = WorkingMemoryManager(config=config, max_tokens=5000)
        for _ in range(20):
            wm.add_message(_msg(content="x" * 500))
        assert wm.needs_compaction
        result = wm.compact()
        assert result.messages_removed > 0
        assert len(wm.memory.chat_history) == 2
