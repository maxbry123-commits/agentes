"""Tests for prompt-evolution API endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

try:
    from starlette.testclient import TestClient
except ImportError:
    TestClient = None

try:
    from fastapi import FastAPI
except ImportError:
    FastAPI = None


pytestmark = pytest.mark.skipif(
    FastAPI is None or TestClient is None,
    reason="fastapi/starlette not installed",
)


@pytest.fixture()
def app_and_gateway(tmp_path):
    """Create a minimal FastAPI app with prompt-evolution routes."""
    from cognithor.channels.config_routes import create_config_routes
    from cognithor.config import CognithorConfig, PromptEvolutionConfig
    from cognithor.config_manager import ConfigManager
    from cognithor.learning.prompt_evolution import PromptEvolutionEngine

    app = FastAPI()

    # Minimal config — ensure index dir exists for db_path property
    (tmp_path / "index").mkdir(parents=True, exist_ok=True)
    config = CognithorConfig(
        cognithor_home=tmp_path,
        prompt_evolution=PromptEvolutionConfig(enabled=True),
    )

    db_path = str(tmp_path / "pe_test.db")
    engine = PromptEvolutionEngine(db_path=db_path)
    engine.register_prompt("system_prompt", "Test prompt {tools_section}")

    gateway = MagicMock()
    gateway._prompt_evolution = engine
    gateway._improvement_gate = None
    gateway._config = config
    gateway._planner = MagicMock()

    config_manager = ConfigManager(config=config)
    create_config_routes(app, config_manager, gateway=gateway)

    yield app, gateway, engine
    engine.close()


@pytest.fixture()
def client(app_and_gateway):
    app, _, _ = app_and_gateway
    return TestClient(app)


class TestPromptEvolutionStats:
    def test_stats_returns_enabled(self, client):
        resp = client.get("/api/v1/prompt-evolution/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is True
        assert "version_count" in data
        assert "total_sessions" in data

    def test_stats_disabled_when_no_engine(self, app_and_gateway):
        app, gateway, _ = app_and_gateway
        gateway._prompt_evolution = None
        c = TestClient(app)
        resp = c.get("/api/v1/prompt-evolution/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is False


class TestPromptEvolutionEvolve:
    def test_evolve_disabled_returns_error(self, app_and_gateway):
        app, gateway, _ = app_and_gateway
        gateway._prompt_evolution = None
        c = TestClient(app)
        resp = c.post("/api/v1/prompt-evolution/evolve")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_evolve_gate_blocked(self, app_and_gateway):
        app, gateway, engine = app_and_gateway
        from cognithor.governance.improvement_gate import GateVerdict

        gate = MagicMock()
        gate.check.return_value = GateVerdict.BLOCKED
        gateway._improvement_gate = gate

        c = TestClient(app)
        resp = c.post("/api/v1/prompt-evolution/evolve")
        assert resp.status_code == 200
        data = resp.json()
        assert "gate_blocked" in data.get("error", "")


class TestPromptEvolutionToggle:
    def test_toggle_off(self, client, app_and_gateway):
        _, gateway, _ = app_and_gateway
        resp = client.post(
            "/api/v1/prompt-evolution/toggle",
            json={"enabled": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is False

    def test_toggle_on_creates_engine(self, app_and_gateway):
        app, gateway, _ = app_and_gateway
        # First disable
        gateway._prompt_evolution = None
        c = TestClient(app)
        resp = c.post(
            "/api/v1/prompt-evolution/toggle",
            json={"enabled": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is True
        assert gateway._prompt_evolution is not None
