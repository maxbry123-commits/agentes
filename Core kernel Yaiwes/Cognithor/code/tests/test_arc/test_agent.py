"""Tests for CognithorArcAgent — RL agent for ARC-AGI-3 interactive games."""

from __future__ import annotations

from cognithor.arc.agent import CognithorArcAgent


class TestAgentCreation:
    def test_create_agent(self):
        agent = CognithorArcAgent(game_id="test_001")
        assert agent.game_id == "test_001"
        assert agent.audit_trail is not None
        assert agent.memory is not None
        assert agent.adapter is not None
        assert agent.explorer is not None
        assert agent.state_graph is not None

    def test_accepts_all_params(self):
        agent = CognithorArcAgent(
            game_id="test",
            use_llm_planner=True,
            llm_call_interval=10,
            max_steps_per_level=100,
            max_resets_per_level=5,
        )
        assert agent.use_llm_planner is True
        assert agent.max_steps_per_level == 100
        assert agent.max_resets_per_level == 5
