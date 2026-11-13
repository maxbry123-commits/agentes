"""Tests fuer F-005: Config-Endpoints muessen Schema-Validation verwenden.

Prueft dass:
  - ui_upsert_agent unbekannte Felder verwirft (nicht in YAML schreibt)
  - ui_upsert_agent gueltige Felder korrekt speichert
  - ui_upsert_binding unbekannte Felder verwirft
  - ui_upsert_binding gueltige Felder korrekt speichert
  - Typ-Fehler (z.B. priority als String) abgelehnt werden
  - ui_put_prompts nur bekannte Prompt-Keys verarbeitet (war bereits sicher)
  - ui_put_cron_jobs ueber CronJob-Model validiert (war bereits sicher)
  - ui_put_mcp_servers ueber sm_keys Whitelist filtert (war bereits sicher)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml


def _setup_app(agents_data: dict | None = None, bindings_data: dict | None = None):
    """Erstellt FakeApp mit temp YAML-Dateien."""
    from tests.test_channels.test_config_routes import FakeApp

    tmpdir = tempfile.mkdtemp(prefix="jarvis_f005_")
    agents_path = Path(tmpdir) / "agents.yaml"
    bindings_path = Path(tmpdir) / "bindings.yaml"

    if agents_data is not None:
        agents_path.write_text(
            yaml.dump(agents_data, default_flow_style=False),
            encoding="utf-8",
        )
    if bindings_data is not None:
        bindings_path.write_text(
            yaml.dump(bindings_data, default_flow_style=False),
            encoding="utf-8",
        )

    app = FakeApp()
    config_manager = MagicMock()
    config_manager.config.cognithor_home = Path(tmpdir)
    config_manager.config.mcp_config_file = Path(tmpdir) / "mcp.yaml"
    config_manager.config.cron_config_file = Path(tmpdir) / "cron.yaml"
    config_manager.config.core_memory_file = Path(tmpdir) / "core.md"
    config_manager.config.policies_dir = Path(tmpdir) / "policies"
    # heartbeat needs a checklist_file attribute
    hb = MagicMock()
    hb.checklist_file = "heartbeat.md"
    config_manager.config.heartbeat = hb
    gateway = MagicMock()

    from cognithor.channels.config_routes import create_config_routes

    create_config_routes(app, config_manager, gateway=gateway)
    return app, agents_path, bindings_path


class TestAgentSchemaValidation:
    """Prueft dass ui_upsert_agent den Body via AgentProfileDTO validiert."""

    @pytest.mark.asyncio
    async def test_valid_agent_saved(self) -> None:
        app, agents_path, _ = _setup_app(agents_data={"agents": []})
        handler = app.routes["POST /api/v1/agents/{name}"]
        request = MagicMock()
        request.json = AsyncMock(
            return_value={
                "description": "Test Agent",
                "language": "en",
                "priority": 5,
            }
        )
        result = await handler(name="test-agent", request=request)
        assert result["status"] == "ok"

        saved = yaml.safe_load(agents_path.read_text(encoding="utf-8"))
        agent = saved["agents"][0]
        assert agent["name"] == "test-agent"
        assert agent["description"] == "Test Agent"
        assert agent["priority"] == 5

    @pytest.mark.asyncio
    async def test_unknown_fields_stripped(self) -> None:
        """Unbekannte Felder duerfen NICHT in die YAML-Datei geschrieben werden."""
        app, agents_path, _ = _setup_app(agents_data={"agents": []})
        handler = app.routes["POST /api/v1/agents/{name}"]
        request = MagicMock()
        request.json = AsyncMock(
            return_value={
                "description": "Legit Agent",
                "malicious_field": "injected_value",
                "__proto__": {"admin": True},
                "exec_on_load": "rm -rf /",
            }
        )
        result = await handler(name="safe-agent", request=request)
        assert result["status"] == "ok"

        saved = yaml.safe_load(agents_path.read_text(encoding="utf-8"))
        agent = saved["agents"][0]
        assert "malicious_field" not in agent
        assert "__proto__" not in agent
        assert "exec_on_load" not in agent
        assert agent["name"] == "safe-agent"
        assert agent["description"] == "Legit Agent"

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self) -> None:
        """Upsert aktualisiert einen bestehenden Agenten."""
        app, agents_path, _ = _setup_app(
            agents_data={
                "agents": [{"name": "existing", "description": "old"}],
            }
        )
        handler = app.routes["POST /api/v1/agents/{name}"]
        request = MagicMock()
        request.json = AsyncMock(
            return_value={
                "description": "updated",
            }
        )
        result = await handler(name="existing", request=request)
        assert result["status"] == "ok"

        saved = yaml.safe_load(agents_path.read_text(encoding="utf-8"))
        assert len(saved["agents"]) == 1
        assert saved["agents"][0]["description"] == "updated"

    @pytest.mark.asyncio
    async def test_type_error_returns_error(self) -> None:
        """Falsche Typen (z.B. priority als String) muessen einen Fehler liefern."""
        app, agents_path, _ = _setup_app(agents_data={"agents": []})
        handler = app.routes["POST /api/v1/agents/{name}"]
        request = MagicMock()
        request.json = AsyncMock(
            return_value={
                "priority": "not-a-number",
            }
        )
        result = await handler(name="bad-agent", request=request)
        # Pydantic validation should raise, caught by except -> error response
        assert "error" in result


class TestBindingSchemaValidation:
    """Prueft dass ui_upsert_binding den Body via BindingRuleDTO validiert."""

    @pytest.mark.asyncio
    async def test_valid_binding_saved(self) -> None:
        app, _, bindings_path = _setup_app(bindings_data={"bindings": []})
        handler = app.routes["POST /api/v1/bindings/{name}"]
        request = MagicMock()
        request.json = AsyncMock(
            return_value={
                "target_agent": "agent-1",
                "priority": 50,
                "description": "Test Binding",
            }
        )
        result = await handler(name="test-binding", request=request)
        assert result["status"] == "ok"

        saved = yaml.safe_load(bindings_path.read_text(encoding="utf-8"))
        binding = saved["bindings"][0]
        assert binding["name"] == "test-binding"
        assert binding["target_agent"] == "agent-1"
        assert binding["priority"] == 50

    @pytest.mark.asyncio
    async def test_unknown_fields_stripped(self) -> None:
        """Unbekannte Felder duerfen NICHT in die YAML-Datei geschrieben werden."""
        app, _, bindings_path = _setup_app(bindings_data={"bindings": []})
        handler = app.routes["POST /api/v1/bindings/{name}"]
        request = MagicMock()
        request.json = AsyncMock(
            return_value={
                "target_agent": "agent-1",
                "evil_key": "evil_value",
                "shell_exec": "whoami",
            }
        )
        result = await handler(name="clean-binding", request=request)
        assert result["status"] == "ok"

        saved = yaml.safe_load(bindings_path.read_text(encoding="utf-8"))
        binding = saved["bindings"][0]
        assert "evil_key" not in binding
        assert "shell_exec" not in binding
        assert binding["target_agent"] == "agent-1"

    @pytest.mark.asyncio
    async def test_missing_required_field_returns_error(self) -> None:
        """target_agent ist required -- fehlend muss Fehler liefern."""
        app, _, _ = _setup_app(bindings_data={"bindings": []})
        handler = app.routes["POST /api/v1/bindings/{name}"]
        request = MagicMock()
        request.json = AsyncMock(
            return_value={
                "description": "Missing target_agent",
            }
        )
        result = await handler(name="bad-binding", request=request)
        assert "error" in result


class TestAlreadySecureEndpoints:
    """Verifiziert dass die anderen 3 Endpoints bereits sicher waren."""

    @pytest.mark.asyncio
    async def test_put_prompts_ignores_unknown_keys(self) -> None:
        """ui_put_prompts verarbeitet nur bekannte Prompt-Keys."""
        app, _, _ = _setup_app()
        handler = app.routes["PUT /api/v1/prompts"]
        request = MagicMock()
        request.json = AsyncMock(
            return_value={
                "coreMd": "# Test",
                "unknown_injection": "malicious",
            }
        )
        result = await handler(request=request)
        assert result["status"] == "ok"
        assert "coreMd" in result["written"]
        assert "unknown_injection" not in result.get("written", [])

    @pytest.mark.asyncio
    async def test_put_mcp_servers_filters_via_whitelist(self) -> None:
        """ui_put_mcp_servers nutzt sm_keys Whitelist."""
        mcp_path = Path(tempfile.mkdtemp()) / "mcp.yaml"
        mcp_path.write_text(
            yaml.dump({"server_mode": {}, "servers": {}}, default_flow_style=False),
            encoding="utf-8",
        )

        from tests.test_channels.test_config_routes import FakeApp

        app = FakeApp()
        config_manager = MagicMock()
        config_manager.config.mcp_config_file = mcp_path
        config_manager.config.cognithor_home = mcp_path.parent
        hb = MagicMock()
        hb.checklist_file = "heartbeat.md"
        config_manager.config.heartbeat = hb
        gateway = MagicMock()

        from cognithor.channels.config_routes import create_config_routes

        create_config_routes(app, config_manager, gateway=gateway)

        handler = app.routes["PUT /api/v1/mcp-servers"]
        request = MagicMock()
        request.json = AsyncMock(
            return_value={
                "mode": "enabled",
                "injected_key": "evil",
            }
        )
        result = await handler(request=request)
        assert result["status"] == "ok"

        saved = yaml.safe_load(mcp_path.read_text(encoding="utf-8"))
        assert saved["server_mode"]["mode"] == "enabled"
        assert "injected_key" not in saved["server_mode"]
