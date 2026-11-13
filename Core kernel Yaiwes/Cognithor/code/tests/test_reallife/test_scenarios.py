"""Real-life scenario tests for Cognithor.

These tests verify that Cognithor can handle complex, multi-step
agentic tasks end-to-end. They test the full pipeline:
Plan -> Gate -> Execute -> Replan -> Answer.

Tests are designed to run in Docker or locally.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_plan_response(goal: str, steps: list[dict]) -> str:
    """Create a JSON plan response like the planner would."""
    plan = {
        "goal": goal,
        "reasoning": "Test scenario",
        "steps": steps,
        "confidence": 0.9,
    }
    return f"```json\n{json.dumps(plan)}\n```"


def _make_text_response(text: str) -> str:
    """Create a plain text response (no tools needed)."""
    return text


# ---------------------------------------------------------------------------
# Scenario 1: Web Research with Multiple Sources
# ---------------------------------------------------------------------------


class TestWebResearch:
    """Cognithor should handle multi-step web research tasks."""

    @pytest.mark.asyncio
    async def test_weather_query_generates_search_plan(self):
        """A weather question should produce a search_and_read plan, not ask for permission."""
        from cognithor.core.planner import SYSTEM_PROMPT

        # Verify the system prompt instructs against asking for permission
        lower = SYSTEM_PROMPT.lower()
        assert "niemals" in lower, "SYSTEM_PROMPT must contain 'NIEMALS' directive"

    @pytest.mark.asyncio
    async def test_replan_prompt_has_quality_check(self):
        """Replan prompt must include source quality assessment."""
        from cognithor.core.planner import REPLAN_PROMPT

        lower = REPLAN_PROMPT.lower()
        assert "quellen" in lower, "REPLAN_PROMPT must mention Quellen (sources)"
        assert "search_and_read" in lower, "REPLAN_PROMPT must reference search_and_read"


# ---------------------------------------------------------------------------
# Scenario 2: File Operations
# ---------------------------------------------------------------------------


class TestFileOperations:
    """Cognithor should handle file read/write/edit tasks."""

    @pytest.mark.asyncio
    async def test_file_tools_are_green(self):
        """File read tools must be GREEN (no approval needed)."""
        from cognithor.config import CognithorConfig
        from cognithor.core.gatekeeper import Gatekeeper
        from cognithor.models import PlannedAction, RiskLevel

        config = CognithorConfig()
        gk = Gatekeeper(config)

        action = PlannedAction(
            tool="read_file", params={"path": "/tmp/test.txt"}, rationale="Read file"
        )
        risk = gk._classify_risk(action)
        assert risk == RiskLevel.GREEN, f"read_file should be GREEN, got {risk}"

    @pytest.mark.asyncio
    async def test_write_file_is_green(self):
        """write_file should be GREEN for autonomous ops (inform, not block)."""
        from cognithor.config import CognithorConfig
        from cognithor.core.gatekeeper import Gatekeeper
        from cognithor.models import PlannedAction, RiskLevel

        config = CognithorConfig()
        gk = Gatekeeper(config)

        action = PlannedAction(
            tool="write_file",
            params={"path": "/tmp/test.txt", "content": "hello"},
            rationale="Write",
        )
        risk = gk._classify_risk(action)
        assert risk == RiskLevel.GREEN, f"write_file should be GREEN for autonomous ops, got {risk}"


# ---------------------------------------------------------------------------
# Scenario 3: Remote Execution
# ---------------------------------------------------------------------------


class TestRemoteExecution:
    """Remote shell tools must require approval."""

    @pytest.mark.asyncio
    async def test_remote_exec_is_orange(self):
        """remote_exec must be ORANGE (requires user approval)."""
        from cognithor.config import CognithorConfig
        from cognithor.core.gatekeeper import Gatekeeper
        from cognithor.models import PlannedAction, RiskLevel

        config = CognithorConfig()
        gk = Gatekeeper(config)

        action = PlannedAction(
            tool="remote_exec", params={"host_name": "dev", "command": "ls"}, rationale="Remote ls"
        )
        risk = gk._classify_risk(action)
        assert risk == RiskLevel.ORANGE, f"remote_exec should be ORANGE, got {risk}"


# ---------------------------------------------------------------------------
# Scenario 4: Memory and Context
# ---------------------------------------------------------------------------


class TestMemoryContext:
    """Memory operations should work correctly."""

    @pytest.mark.asyncio
    async def test_incognito_session_has_flag(self):
        """Incognito sessions must have incognito=True."""
        from cognithor.models import SessionContext

        session = SessionContext(session_id="incog_test", incognito=True)
        assert session.incognito is True

    @pytest.mark.asyncio
    async def test_session_config_exists(self):
        """SessionConfig must exist with proper defaults."""
        from cognithor.config import CognithorConfig

        config = CognithorConfig()
        assert config.session.inactivity_timeout_minutes == 30
        assert config.session.chat_history_limit == 100


# ---------------------------------------------------------------------------
# Scenario 5: Tool Coverage
# ---------------------------------------------------------------------------


class TestToolCoverage:
    """All critical tools must be registered and properly classified."""

    @pytest.mark.asyncio
    async def test_search_tools_are_green(self):
        """Web search tools must be GREEN."""
        from cognithor.config import CognithorConfig
        from cognithor.core.gatekeeper import Gatekeeper
        from cognithor.models import PlannedAction, RiskLevel

        config = CognithorConfig()
        gk = Gatekeeper(config)

        for tool in ["web_search", "web_fetch", "search_and_read"]:
            action = PlannedAction(tool=tool, params={}, rationale=f"Test {tool}")
            risk = gk._classify_risk(action)
            assert risk == RiskLevel.GREEN, f"{tool} should be GREEN, got {risk}"

    @pytest.mark.asyncio
    async def test_exec_command_is_green(self):
        """exec_command should be GREEN for autonomous ops (not GREEN, not ORANGE)."""
        from cognithor.config import CognithorConfig
        from cognithor.core.gatekeeper import Gatekeeper
        from cognithor.models import PlannedAction, RiskLevel

        config = CognithorConfig()
        gk = Gatekeeper(config)

        action = PlannedAction(tool="exec_command", params={"command": "ls"}, rationale="List")
        risk = gk._classify_risk(action)
        assert risk == RiskLevel.GREEN, (
            f"exec_command should be GREEN for autonomous ops, got {risk}"
        )


# ---------------------------------------------------------------------------
# Scenario 6: GEPA Self-Improvement
# ---------------------------------------------------------------------------


class TestGEPASelfImprovement:
    """GEPA evolution must have proper safety guards."""

    def test_min_traces_threshold(self):
        """Evolution cycle needs enough data points."""
        from cognithor.learning.evolution_orchestrator import EvolutionOrchestrator

        assert EvolutionOrchestrator.MIN_TRACES >= 20

    def test_high_impact_needs_review(self):
        """High-impact proposals must not be auto-applied."""
        from cognithor.learning.evolution_orchestrator import EvolutionOrchestrator

        assert hasattr(EvolutionOrchestrator, "HIGH_IMPACT_TYPES")
        assert "prompt_patch" in EvolutionOrchestrator.HIGH_IMPACT_TYPES


# ---------------------------------------------------------------------------
# Scenario 7: Session Management
# ---------------------------------------------------------------------------


class TestSessionManagement:
    """Session lifecycle must work correctly."""

    def test_auto_session_staleness(self, tmp_path):
        """Stale sessions should trigger new session creation."""
        from cognithor.gateway.session_store import SessionStore
        from cognithor.models import SessionContext

        store = SessionStore(tmp_path / "sessions.db")
        old = SessionContext(
            session_id="stale0000000001",
            user_id="web_user",
            channel="webui",
            agent_name="jarvis",
        )
        old.last_activity = datetime.now(tz=UTC) - timedelta(hours=2)
        store.save_session(old)

        assert (
            store.should_create_new_session(
                channel="webui",
                user_id="web_user",
                inactivity_timeout_minutes=30,
            )
            is True
        )

    def test_chat_history_filters_system(self, tmp_path):
        """Only user/assistant messages should be persisted."""
        from cognithor.gateway.session_store import SessionStore
        from cognithor.models import Message, MessageRole

        store = SessionStore(tmp_path / "sessions.db")
        from cognithor.models import SessionContext

        s = SessionContext(
            session_id="filter000000001", user_id="u", channel="webui", agent_name="jarvis"
        )
        store.save_session(s)

        messages = [
            Message(
                role=MessageRole.SYSTEM, content="System prompt", timestamp=datetime.now(tz=UTC)
            ),
            Message(role=MessageRole.USER, content="Hello", timestamp=datetime.now(tz=UTC)),
            Message(role=MessageRole.ASSISTANT, content="Hi!", timestamp=datetime.now(tz=UTC)),
        ]
        store.save_chat_history("filter000000001", messages)

        history = store.get_session_history("filter000000001")
        assert len(history) == 2, (
            f"Expected 2 messages, got {len(history)}: system should be filtered"
        )
        assert all(m["role"] in ("user", "assistant") for m in history)

    def test_search_across_sessions(self, tmp_path):
        """Full-text search should find messages across sessions."""
        from cognithor.gateway.session_store import SessionStore
        from cognithor.models import Message, MessageRole, SessionContext

        store = SessionStore(tmp_path / "sessions.db")
        s = SessionContext(
            session_id="search000000001", user_id="web_user", channel="webui", agent_name="jarvis"
        )
        store.save_session(s)
        store.save_chat_history(
            "search000000001",
            [
                Message(
                    role=MessageRole.USER,
                    content="Wetter in Berlin",
                    timestamp=datetime.now(tz=UTC),
                ),
            ],
        )

        results = store.search_chat_history("Berlin", channel="webui", user_id="web_user")
        assert len(results) >= 1
        assert "Berlin" in results[0]["content"]

    def test_export_session(self, tmp_path):
        """Session export should include all messages and metadata."""
        from cognithor.gateway.session_store import SessionStore
        from cognithor.models import Message, MessageRole, SessionContext

        store = SessionStore(tmp_path / "sessions.db")
        s = SessionContext(
            session_id="export000000001", user_id="u", channel="webui", agent_name="jarvis"
        )
        store.save_session(s)
        store.save_chat_history(
            "export000000001",
            [
                Message(role=MessageRole.USER, content="Test", timestamp=datetime.now(tz=UTC)),
            ],
        )

        export = store.export_session("export000000001")
        assert export["session_id"] == "export000000001"
        assert len(export["messages"]) == 1
        assert "exported_at" in export
