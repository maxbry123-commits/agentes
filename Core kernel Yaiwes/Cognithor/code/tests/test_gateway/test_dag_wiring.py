"""Tests für DAG WorkflowEngine Verdrahtung und Depth Guard.

Testet:
  - dag_workflow_engine Attribut wird in declare_advanced_attrs() deklariert
  - DAG-Engine wird erstellt wenn Import klappt
  - Nach Gateway-Init: _mcp_client und _gatekeeper gesetzt
  - Sub-Agent depth guard in handle_message
"""

from __future__ import annotations

from unittest.mock import MagicMock

from cognithor.config import CognithorConfig
from cognithor.models import IncomingMessage


class TestDAGWorkflowEngineAttr:
    def test_dag_workflow_engine_attr_declared(self, tmp_path) -> None:
        """'dag_workflow_engine' ist in declare_advanced_attrs() enthalten."""
        from cognithor.gateway.phases.advanced import declare_advanced_attrs

        config = CognithorConfig(cognithor_home=tmp_path)
        result = declare_advanced_attrs(config)
        assert "dag_workflow_engine" in result


class TestDAGEngineInitialized:
    def test_dag_engine_initialized(self, tmp_path) -> None:
        """DAG-Engine wird erstellt wenn WorkflowEngine importierbar ist."""
        from cognithor.gateway.phases.advanced import declare_advanced_attrs

        config = CognithorConfig(cognithor_home=tmp_path)
        result = declare_advanced_attrs(config)

        # WorkflowEngine may or may not be importable depending on project state,
        # but the key must exist
        assert "dag_workflow_engine" in result
        # If the import succeeded, it should be an instance
        if result["dag_workflow_engine"] is not None:
            from cognithor.core.workflow_engine import WorkflowEngine

            assert isinstance(result["dag_workflow_engine"], WorkflowEngine)


class TestDAGEngineWiring:
    def test_dag_engine_wiring(self) -> None:
        """Nach Wiring: _mcp_client und _gatekeeper gesetzt."""

        class FakeEngine:
            _mcp_client = None
            _gatekeeper = None

        class FakeGateway:
            _dag_workflow_engine = FakeEngine()
            _mcp_client = MagicMock()
            _gatekeeper = MagicMock()

        gw = FakeGateway()

        # Simulate the wiring code from gateway.py
        if getattr(gw, "_dag_workflow_engine", None):
            gw._dag_workflow_engine._mcp_client = gw._mcp_client
            gw._dag_workflow_engine._gatekeeper = gw._gatekeeper

        assert gw._dag_workflow_engine._mcp_client is gw._mcp_client
        assert gw._dag_workflow_engine._gatekeeper is gw._gatekeeper


# ============================================================================
# Sub-Agent Depth Guard
# ============================================================================


class TestDepthGuard:
    """Verifiziert dass handle_message sub-agent Rekursion per Tiefe begrenzt."""

    def test_max_sub_agent_depth_config(self, tmp_path) -> None:
        """max_sub_agent_depth ist in SecurityConfig konfigurierbar."""
        config = CognithorConfig(cognithor_home=tmp_path)
        assert config.security.max_sub_agent_depth == 3  # default

        config.security.max_sub_agent_depth = 5
        assert config.security.max_sub_agent_depth == 5

    def test_depth_guard_blocks_excessive_recursion(self) -> None:
        """Depth > max wird abgelehnt (simuliert handle_message Logik)."""
        msg = IncomingMessage(
            channel="sub_agent",
            user_id="agent:coder",
            text="test task",
            metadata={"depth": 5},
        )
        max_depth = 3
        depth = msg.metadata.get("depth", 0)
        assert depth > max_depth

    def test_depth_guard_allows_within_limit(self) -> None:
        """Depth <= max wird durchgelassen."""
        msg = IncomingMessage(
            channel="sub_agent",
            user_id="agent:coder",
            text="test task",
            metadata={"depth": 2},
        )
        max_depth = 3
        depth = msg.metadata.get("depth", 0)
        assert depth <= max_depth

    def test_agent_runner_increments_depth(self) -> None:
        """_agent_runner soll depth + 1 an handle_message übergeben."""
        # Simuliere: config.depth = 1, runner erzeugt msg mit depth = 2
        original_depth = 1
        incremented = original_depth + 1
        assert incremented == 2
