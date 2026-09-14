"""End-to-end integration tests for the Observer flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from cognithor.config import CognithorConfig
from cognithor.core.observer import PGEReloopDirective, ResponseEnvelope


class TestPGEReloopDirectiveHandling:
    async def test_directive_triggers_planner_reentry(self, tmp_path):
        """A ResponseEnvelope with directive causes the PGE phase to re-enter planning."""
        from cognithor.gateway.observer_directive import handle_observer_directive

        cfg = CognithorConfig(cognithor_home=tmp_path / ".cognithor")
        session_state: dict = {
            "seen_observer_feedback_hashes": set(),
            "pge_iteration_count": 0,
        }

        directive = PGEReloopDirective(
            reason="tool_ignorance",
            missing_data="weather data",
            suggested_tools=["web_search"],
        )

        # First time seeing this directive: should allow re-entry.
        decision = handle_observer_directive(
            directive=directive,
            session_state=session_state,
            config=cfg,
        )
        assert decision.action == "reenter_pge"
        assert "weather data" in decision.planner_feedback

        # Second time same directive: dedupe kicks in.
        decision = handle_observer_directive(
            directive=directive,
            session_state=session_state,
            config=cfg,
        )
        assert decision.action == "downgrade_to_regen"

    async def test_pge_budget_exhausted_downgrades(self, tmp_path):
        from cognithor.gateway.observer_directive import handle_observer_directive

        cfg = CognithorConfig(cognithor_home=tmp_path / ".cognithor")
        cfg.security.max_iterations = 3
        session_state: dict = {
            "seen_observer_feedback_hashes": set(),
            "pge_iteration_count": 3,  # already at cap
        }
        directive = PGEReloopDirective(
            reason="tool_ignorance",
            missing_data="x",
            suggested_tools=[],
        )
        decision = handle_observer_directive(
            directive=directive,
            session_state=session_state,
            config=cfg,
        )
        assert decision.action == "downgrade_to_regen"

    async def test_seen_hashes_set_is_pruned_when_over_100(self, tmp_path):
        from cognithor.gateway.observer_directive import handle_observer_directive

        cfg = CognithorConfig(cognithor_home=tmp_path / ".cognithor")
        session_state: dict = {
            "seen_observer_feedback_hashes": {f"hash_{i}" for i in range(100)},
            "pge_iteration_count": 0,
        }
        directive = PGEReloopDirective(
            reason="tool_ignorance",
            missing_data="fresh",
            suggested_tools=[],
        )
        handle_observer_directive(
            directive=directive,
            session_state=session_state,
            config=cfg,
        )
        # After handling: new hash added, but set pruned to at most 51 items.
        assert len(session_state["seen_observer_feedback_hashes"]) <= 51


class TestGatewayObserverIntegration:
    async def test_tool_ignorance_triggers_new_pge_iteration(self, tmp_path):
        """Envelope with directive causes Gateway PGE loop to iterate once more."""
        from cognithor.gateway.observer_directive import run_pge_with_observer_directive

        planner = AsyncMock()
        # 1st formulate call: tool_ignorance fail, directive set.
        # 2nd formulate call (after re-enter): clean response.
        planner.formulate_response = AsyncMock(
            side_effect=[
                ResponseEnvelope(
                    content="I don't know",
                    directive=PGEReloopDirective(
                        reason="tool_ignorance",
                        missing_data="recent weather",
                        suggested_tools=["web_search"],
                    ),
                ),
                ResponseEnvelope(content="It's 12C in Berlin.", directive=None),
            ]
        )

        cfg = CognithorConfig(cognithor_home=tmp_path / ".cognithor")
        session_state: dict = {
            "seen_observer_feedback_hashes": set(),
            "pge_iteration_count": 0,
        }

        final = await run_pge_with_observer_directive(
            planner=planner,
            user_message="What's the weather?",
            results=[],
            working_memory=MagicMock(session_id="s1"),
            session_state=session_state,
            config=cfg,
        )
        assert final.content == "It's 12C in Berlin."
        assert final.directive is None
        assert planner.formulate_response.call_count == 2


class TestGatewayEndToEnd:
    async def test_gateway_uses_observer_wrapper(self, tmp_path, monkeypatch):
        """Gateway._formulate_response (non-streaming) calls run_pge_with_observer_directive.

        We call _formulate_response directly with a stub planner so the test
        doesn't need Ollama running.  The assertion verifies that the module-level
        name ``run_pge_with_observer_directive`` inside gateway.py is the one
        invoked (i.e. the wiring is in place and not bypassed).
        """
        import cognithor.gateway.gateway as gw_module
        from cognithor.gateway import observer_directive as directive_module

        called = {"flag": False}
        original = directive_module.run_pge_with_observer_directive

        async def _spy(**kwargs):
            called["flag"] = True
            return await original(**kwargs)

        # gateway.py does ``from … import run_pge_with_observer_directive``,
        # so we must patch the name as it exists in the gateway module's
        # own namespace — not only in the source module.
        monkeypatch.setattr(gw_module, "run_pge_with_observer_directive", _spy)

        from cognithor.config import CognithorConfig
        from cognithor.gateway.gateway import Gateway
        from cognithor.models import WorkingMemory

        cfg = CognithorConfig(cognithor_home=tmp_path / ".cognithor")
        cfg.observer.enabled = False  # no LLM needed for observer

        # Build a Gateway instance without calling initialize() — we only need
        # _config and _planner on the instance to exercise _formulate_response.
        gw = object.__new__(Gateway)
        gw._config = cfg

        # Stub planner: formulate_response returns a clean envelope.
        planner_stub = AsyncMock()
        planner_stub.formulate_response = AsyncMock(
            return_value=ResponseEnvelope(content="ok", directive=None),
        )
        gw._planner = planner_stub

        wm = WorkingMemory()
        await gw._formulate_response(
            msg_text="hello",
            all_results=[],
            wm=wm,
            stream_callback=None,  # non-streaming path
        )

        assert called["flag"] is True, (
            "run_pge_with_observer_directive was NOT called from _formulate_response. "
            "Check that gateway.py's non-streaming path uses the wrapper."
        )
