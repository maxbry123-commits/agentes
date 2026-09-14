"""End-to-end critical path verification for all v0.36.1-v0.37.0 features."""

from __future__ import annotations

import asyncio
import json
import tempfile
from unittest.mock import AsyncMock, MagicMock

from cognithor.config import CognithorConfig, ensure_directory_structure


def _run(coro):
    return asyncio.run(coro)


def test_01_pipeline_callback_delivery():
    """Pipeline event reaches the channel with correct structure."""
    CognithorConfig(cognithor_home=tempfile.mkdtemp())
    mock_channel = AsyncMock()
    mock_channel.send_pipeline_event = AsyncMock()

    from cognithor.gateway.gateway import Gateway

    gw = Gateway.__new__(Gateway)
    gw._channels = {"webui": mock_channel}
    gw._running = True

    cb = gw._make_pipeline_callback("webui", "session-123")
    _run(cb("plan", "start", iteration=1))

    assert mock_channel.send_pipeline_event.called
    event = mock_channel.send_pipeline_event.call_args[0][1]
    assert event["phase"] == "plan"
    assert event["status"] == "start"
    assert event["iteration"] == 1
    assert "elapsed_ms" in event


def test_02_non_webui_channel_noop():
    """Non-WebUI channel ignores pipeline events without crash."""
    from cognithor.channels.base import Channel

    class DummyChannel(Channel):
        @property
        def name(self):
            return "dummy"

        async def start(self, handler):
            pass

        async def stop(self):
            pass

        async def send(self, message):
            pass

        async def send_streaming_token(self, session_id, token):
            pass

        async def request_approval(self, session_id, tool, params, reason):
            return True

    dummy = DummyChannel()
    _run(dummy.send_pipeline_event("sess", {"phase": "plan", "status": "start"}))


def test_03_verified_lookup_full_pipeline():
    """Verified Lookup returns answer with confidence from mocked sources."""
    cfg = CognithorConfig(cognithor_home=tempfile.mkdtemp())
    from cognithor.mcp.verified_lookup import VerifiedWebLookup

    vl = VerifiedWebLookup(cfg)
    web = AsyncMock()
    web.web_search = AsyncMock(
        return_value=(
            "1. Example\n"
            "URL: https://example.com\nSnippet: stars\n\n"
            "2. Example2\n"
            "URL: https://example2.com\nSnippet: more"
        )
    )
    web.web_fetch = AsyncMock(return_value="Cognithor has 142 GitHub stars. " * 5)
    vl._set_web_tools(web)

    async def mock_llm(prompt, model=""):
        if "Extract" in prompt:
            return json.dumps({"facts": [{"claim": "142 stars", "value": "142", "type": "number"}]})
        return json.dumps({"answer": "142 Stars", "confidence": 0.9, "discrepancies": []})

    vl._set_llm_fn(AsyncMock(side_effect=mock_llm), "test")
    result = _run(vl.verified_lookup("How many stars?", num_sources=2))
    assert "142" in result
    assert "%" in result


def test_04_locked_enforcement():
    """sync_from_mcp preserves locked tool descriptions but updates schema."""
    from pathlib import Path

    from cognithor.mcp.tool_registry_db import ToolRegistryDB

    db = ToolRegistryDB(Path(tempfile.mkdtemp()) / "test.db")
    db.upsert_tool(name="my_tool", description_en="Original", category="web")
    assert db.is_locked("my_tool") is True

    mock_mcp = MagicMock()
    mock_mcp.get_tool_schemas.return_value = {
        "my_tool": {"description": "Overwritten!", "inputSchema": {"new": True}},
    }
    db.sync_from_mcp(mock_mcp)

    tool = db.get_tool("my_tool")
    assert tool.description == "Original"
    assert tool.input_schema.get("new") is True
    db.close()


def test_05_auto_cross_check():
    """Executor injects cross_check=True for fact questions."""
    cfg = CognithorConfig(cognithor_home=tempfile.mkdtemp())
    from cognithor.core.executor import Executor, _fact_question_var
    from cognithor.models import GateDecision, GateStatus, PlannedAction, RiskLevel

    mock_mcp = AsyncMock()
    mock_mcp.call_tool = AsyncMock(return_value=MagicMock(content="ok", is_error=False))
    ex = Executor(cfg, mock_mcp)
    ex.set_agent_context(session_id="test")
    ex.set_fact_question_context(True)

    action = PlannedAction(tool="search_and_read", params={"query": "test"})
    decision = GateDecision(
        status=GateStatus.ALLOW,
        risk_level=RiskLevel.GREEN,
        reason="ok",
        original_action=action,
        policy_name="test",
    )
    _run(ex.execute([action], [decision]))

    call_args = mock_mcp.call_tool.call_args
    params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
    assert params.get("cross_check") is True
    ex.clear_agent_context()
    assert _fact_question_var.get() is False


def test_06_sanitizer():
    """Sanitizer strips JSON artifacts, preserves text."""
    from cognithor.gateway.gateway import _sanitize_broken_llm_output

    assert '"goal"' not in _sanitize_broken_llm_output('{"goal": "x", "steps": []}')

    mixed = 'Hier ist die Antwort. ```json\n{"goal": "broken\n``` Das Ende.'
    result = _sanitize_broken_llm_output(mixed)
    assert "Antwort" in result
    assert '"goal"' not in result


def test_07_extract_plan_false_positives():
    """Braces alone dont trigger parse_failed, JSON keys do."""
    cfg = CognithorConfig(cognithor_home=tempfile.mkdtemp())
    ensure_directory_structure(cfg)
    from cognithor.core.planner import Planner

    planner = Planner(
        cfg,
        AsyncMock(),
        MagicMock(
            select_model=MagicMock(return_value="m"),
            get_model_config=MagicMock(return_value={}),
        ),
    )

    plan = planner._extract_plan("Nutze Python mit {dict comprehensions}.", "test")
    assert plan.parse_failed is False
    assert "dict comprehensions" in plan.direct_response

    plan2 = planner._extract_plan('{"goal": "test", "steps": [broken', "test")
    assert plan2.parse_failed is True


def test_08_i18n_all_keys():
    """All new i18n keys resolve in en/de/zh."""
    from cognithor.i18n import set_locale, t

    keys = [
        "verified_lookup.no_webtools",
        "verified_lookup.header",
        "verified_lookup.agreement_high",
        "verified_lookup.discrepancy_item",
        "gateway.parse_failed",
    ]
    for locale in ("en", "de", "zh"):
        set_locale(locale)
        for key in keys:
            val = t(key, confidence=95, value_a="x", count_a=1, value_b="y", count_b=2)
            assert val != key, f"{locale}/{key} not resolved!"
    set_locale("en")


def test_09_gatekeeper_green():
    """verified_web_lookup is classified as GREEN."""
    cfg = CognithorConfig(cognithor_home=tempfile.mkdtemp())
    from cognithor.core.gatekeeper import Gatekeeper
    from cognithor.models import PlannedAction, RiskLevel

    gk = Gatekeeper(cfg)
    action = PlannedAction(tool="verified_web_lookup", params={"query": "test"})
    assert gk._classify_risk(action) == RiskLevel.GREEN


def test_10_tool_registry_maps():
    """verified_web_lookup in all registry maps."""
    from cognithor.mcp.tool_registry_db import (
        _TOOL_DESCRIPTIONS_DE,
        _TOOL_DESCRIPTIONS_ZH,
        DEFAULT_EXAMPLES,
        TOOL_CATEGORIES,
        TOOL_ROLE_DEFAULTS,
    )

    assert "verified_web_lookup" in TOOL_ROLE_DEFAULTS["planner"]
    assert "verified_web_lookup" in TOOL_ROLE_DEFAULTS["researcher"]
    assert "verified_web_lookup" in TOOL_CATEGORIES
    assert "verified_web_lookup" in _TOOL_DESCRIPTIONS_DE
    assert "verified_web_lookup" in _TOOL_DESCRIPTIONS_ZH
    assert "verified_web_lookup" in DEFAULT_EXAMPLES
