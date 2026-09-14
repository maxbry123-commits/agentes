"""Contract tests against a real local Ollama instance.

Marked ``integration`` — skipped when Ollama is unreachable.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import httpx
import pytest

from cognithor.config import CognithorConfig
from cognithor.core.model_router import OllamaClient
from cognithor.core.observer import ObserverAudit
from cognithor.core.observer_store import AuditStore

if TYPE_CHECKING:
    from pathlib import Path


def _ollama_reachable() -> bool:
    try:
        httpx.get("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _ollama_reachable(),
        reason="Ollama not reachable on localhost:11434",
    ),
]


@pytest.fixture
def live_observer(tmp_path: Path):
    cfg = CognithorConfig(cognithor_home=tmp_path / ".cognithor")
    ollama = OllamaClient(cfg)
    store = AuditStore(db_path=tmp_path / "audits.db")
    return ObserverAudit(config=cfg, ollama_client=ollama, audit_store=store)


class TestObserverLiveContracts:
    async def test_json_conformance(self, live_observer):
        """20 consecutive calls, 100% valid JSON output."""
        from tests.fixtures.observer_cases import CLEAN_CASES

        for case in CLEAN_CASES[:20]:
            result = await live_observer.audit(
                user_message=case.user_message,
                response=case.draft_response,
                tool_results=case.tool_results,
                session_id="live_test",
            )
            assert result.error_type != "parse_failed", f"JSON failed on: {case.user_message}"

    async def test_latency_budget(self, live_observer):
        """10 calls, hard cap 30s per call (qwen3:32b local), warn threshold 10s.

        The 30s hard cap matches the observer.timeout_seconds default and
        covers qwen3:32b inference on typical developer hardware.  Calls above
        10s are counted as "slow" — more than 5 slow calls triggers a failure
        so gross regressions are still caught without penalising normal LLM
        variance.
        """
        from tests.fixtures.observer_cases import CLEAN_CASES

        slow = 0
        for case in CLEAN_CASES[:10]:
            start = time.monotonic()
            await live_observer.audit(
                user_message=case.user_message,
                response=case.draft_response,
                tool_results=case.tool_results,
                session_id="live_test",
            )
            dur = time.monotonic() - start
            assert dur < 30.0, f"Observer exceeded 30s hard budget: {dur:.2f}s"
            if dur > 10.0:
                slow += 1
        if slow > 5:
            pytest.fail(f"Too many slow calls: {slow}/10 > 10s")

    async def test_hallucination_precision(self, live_observer):
        """10 known hallucination fixtures, expect detection rate >= 70%."""
        from tests.fixtures.observer_cases import HALLUCINATION_CASES

        hits = 0
        for case in HALLUCINATION_CASES[:10]:
            result = await live_observer.audit(
                user_message=case.user_message,
                response=case.draft_response,
                tool_results=case.tool_results,
                session_id="live_test",
            )
            if not result.dimensions["hallucination"].passed:
                hits += 1
        assert hits >= 7, f"Hallucination detection rate too low: {hits}/10"
