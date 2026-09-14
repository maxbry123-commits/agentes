"""Tests for workflow graph REST endpoints.

Uses the same FakeApp pattern as test_config_routes.py to test
the _register_workflow_graph_routes handlers directly.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from cognithor.config import CognithorConfig
from cognithor.config_manager import ConfigManager
from cognithor.core.workflows import (
    TemplateLibrary,
    WorkflowEngine,
)

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================================
# FakeApp
# ============================================================================


class FakeApp:
    """Captures registered route handlers."""

    def __init__(self) -> None:
        self.routes: dict[str, Any] = {}

    def _register(self, method: str, path: str, **kwargs: Any):
        def decorator(fn):
            self.routes[f"{method} {path}"] = fn
            return fn

        return decorator

    def get(self, path: str, **kwargs: Any):
        return self._register("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any):
        return self._register("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any):
        return self._register("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any):
        return self._register("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any):
        return self._register("DELETE", path, **kwargs)


class FakeRequest:
    """Simulates a FastAPI Request."""

    def __init__(self, body: dict[str, Any]) -> None:
        self._body = body

    async def json(self) -> dict[str, Any]:
        return self._body


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def tmp_home(tmp_path: Path) -> Path:
    home = tmp_path / ".cognithor"
    home.mkdir(parents=True, exist_ok=True)
    return home


@pytest.fixture
def config(tmp_home: Path) -> CognithorConfig:
    return CognithorConfig(cognithor_home=tmp_home)


@pytest.fixture
def config_manager(config: CognithorConfig) -> ConfigManager:
    return ConfigManager(config=config)


@pytest.fixture
def app() -> FakeApp:
    return FakeApp()


@pytest.fixture
def workflow_engine() -> WorkflowEngine:
    return WorkflowEngine()


@pytest.fixture
def template_library() -> TemplateLibrary:
    return TemplateLibrary(load_builtins=True)


@pytest.fixture
def gateway(workflow_engine: WorkflowEngine, template_library: TemplateLibrary) -> MagicMock:
    gw = MagicMock()
    gw._workflow_engine = workflow_engine
    gw._template_library = template_library
    gw._dag_workflow_engine = None
    return gw


@pytest.fixture
def registered_app(app: FakeApp, config_manager: ConfigManager, gateway: MagicMock) -> FakeApp:
    from cognithor.channels.config_routes import create_config_routes

    create_config_routes(app, config_manager, gateway=gateway)
    return app


# ============================================================================
# Route Registration
# ============================================================================


class TestWorkflowRouteRegistration:
    def test_templates_route_exists(self, registered_app: FakeApp) -> None:
        assert "GET /api/v1/workflows/templates" in registered_app.routes

    def test_instances_route_exists(self, registered_app: FakeApp) -> None:
        assert "GET /api/v1/workflows/instances" in registered_app.routes

    def test_stats_route_exists(self, registered_app: FakeApp) -> None:
        assert "GET /api/v1/workflows/stats" in registered_app.routes

    def test_dag_runs_route_exists(self, registered_app: FakeApp) -> None:
        assert "GET /api/v1/workflows/dag/runs" in registered_app.routes

    def test_start_instance_route_exists(self, registered_app: FakeApp) -> None:
        assert "POST /api/v1/workflows/instances" in registered_app.routes

    def test_dag_run_detail_route_exists(self, registered_app: FakeApp) -> None:
        assert "GET /api/v1/workflows/dag/runs/{run_id}" in registered_app.routes

    def test_template_detail_route_exists(self, registered_app: FakeApp) -> None:
        assert "GET /api/v1/workflows/templates/{template_id}" in registered_app.routes


# ============================================================================
# Templates
# ============================================================================


class TestTemplateEndpoints:
    async def test_list_templates(self, registered_app: FakeApp) -> None:
        handler = registered_app.routes["GET /api/v1/workflows/templates"]
        result = await handler()
        assert result["count"] == 4  # 4 built-in templates
        assert len(result["templates"]) == 4

    async def test_list_templates_no_library(
        self, app: FakeApp, config_manager: ConfigManager
    ) -> None:
        gw = MagicMock()
        gw._workflow_engine = None
        gw._template_library = None
        gw._dag_workflow_engine = None
        from cognithor.channels.config_routes import create_config_routes

        create_config_routes(app, config_manager, gateway=gw)
        handler = app.routes["GET /api/v1/workflows/templates"]
        result = await handler()
        assert result["count"] == 0

    async def test_get_template_found(self, registered_app: FakeApp) -> None:
        handler = registered_app.routes["GET /api/v1/workflows/templates/{template_id}"]
        result = await handler("wf-onboarding")
        assert result["name"] == "Team-Onboarding"
        assert result["template_id"] == "wf-onboarding"

    async def test_get_template_not_found(self, registered_app: FakeApp) -> None:
        handler = registered_app.routes["GET /api/v1/workflows/templates/{template_id}"]
        result = await handler("nonexistent")
        assert result["status"] == 404


# ============================================================================
# Simple Workflow Instances
# ============================================================================


class TestInstanceEndpoints:
    async def test_list_instances_empty(self, registered_app: FakeApp) -> None:
        handler = registered_app.routes["GET /api/v1/workflows/instances"]
        result = await handler()
        assert result["instances"] == []

    async def test_start_instance(self, registered_app: FakeApp) -> None:
        handler = registered_app.routes["POST /api/v1/workflows/instances"]
        req = FakeRequest({"template_id": "wf-onboarding"})
        result = await handler(req)
        assert result["status"] == "ok"
        assert result["instance"]["template_name"] == "Team-Onboarding"

    async def test_start_instance_unknown_template(self, registered_app: FakeApp) -> None:
        handler = registered_app.routes["POST /api/v1/workflows/instances"]
        req = FakeRequest({"template_id": "nonexistent"})
        result = await handler(req)
        assert result["status"] == 404

    async def test_list_after_start(self, registered_app: FakeApp) -> None:
        start = registered_app.routes["POST /api/v1/workflows/instances"]
        await start(FakeRequest({"template_id": "wf-onboarding"}))
        handler = registered_app.routes["GET /api/v1/workflows/instances"]
        result = await handler()
        assert len(result["instances"]) == 1
        assert result["stats"]["running"] == 1

    async def test_get_instance_detail(self, registered_app: FakeApp) -> None:
        start = registered_app.routes["POST /api/v1/workflows/instances"]
        res = await start(FakeRequest({"template_id": "wf-onboarding"}))
        iid = res["instance"]["instance_id"]
        handler = registered_app.routes["GET /api/v1/workflows/instances/{instance_id}"]
        detail = await handler(iid)
        assert detail["instance_id"] == iid
        assert "steps" in detail

    async def test_get_instance_not_found(self, registered_app: FakeApp) -> None:
        handler = registered_app.routes["GET /api/v1/workflows/instances/{instance_id}"]
        result = await handler("nonexistent")
        assert result["status"] == 404


# ============================================================================
# DAG Runs
# ============================================================================


class TestDagRunEndpoints:
    async def test_list_dag_runs_no_engine(self, registered_app: FakeApp) -> None:
        handler = registered_app.routes["GET /api/v1/workflows/dag/runs"]
        result = await handler()
        assert result["runs"] == []

    async def test_list_dag_runs_with_checkpoints(
        self,
        app: FakeApp,
        config_manager: ConfigManager,
        tmp_path: Path,
    ) -> None:
        cp_dir = tmp_path / "checkpoints"
        cp_dir.mkdir()
        run_data = {
            "id": "abc123",
            "workflow_id": "wf1",
            "workflow_name": "Test WF",
            "status": "success",
            "started_at": "2026-03-04T10:00:00Z",
            "completed_at": "2026-03-04T10:01:00Z",
            "node_results": {"a": {}, "b": {}},
        }
        (cp_dir / "abc123.json").write_text(json.dumps(run_data), encoding="utf-8")

        dag_engine = MagicMock()
        dag_engine._checkpoint_dir = cp_dir

        gw = MagicMock()
        gw._workflow_engine = None
        gw._template_library = None
        gw._dag_workflow_engine = dag_engine

        from cognithor.channels.config_routes import create_config_routes

        create_config_routes(app, config_manager, gateway=gw)

        handler = app.routes["GET /api/v1/workflows/dag/runs"]
        result = await handler()
        assert len(result["runs"]) == 1
        assert result["runs"][0]["id"] == "abc123"
        assert result["runs"][0]["node_count"] == 2

    async def test_get_dag_run_detail(
        self,
        app: FakeApp,
        config_manager: ConfigManager,
        tmp_path: Path,
    ) -> None:
        cp_dir = tmp_path / "checkpoints"
        cp_dir.mkdir()
        run_data = {
            "id": "xyz789",
            "workflow_name": "Detail Test",
            "status": "failure",
            "node_results": {"n1": {"status": "success"}, "n2": {"status": "failure"}},
        }
        (cp_dir / "xyz789.json").write_text(json.dumps(run_data), encoding="utf-8")

        dag_engine = MagicMock()
        dag_engine._checkpoint_dir = cp_dir

        gw = MagicMock()
        gw._workflow_engine = None
        gw._template_library = None
        gw._dag_workflow_engine = dag_engine

        from cognithor.channels.config_routes import create_config_routes

        create_config_routes(app, config_manager, gateway=gw)

        handler = app.routes["GET /api/v1/workflows/dag/runs/{run_id}"]
        result = await handler("xyz789")
        assert result["workflow_name"] == "Detail Test"
        assert result["node_results"]["n2"]["status"] == "failure"

    async def test_get_dag_run_not_found(self, registered_app: FakeApp) -> None:
        handler = registered_app.routes["GET /api/v1/workflows/dag/runs/{run_id}"]
        result = await handler("nonexistent")
        assert result.get("status") in (404, 503)


# ============================================================================
# Stats
# ============================================================================


class TestStatsEndpoint:
    async def test_stats_basic(self, registered_app: FakeApp) -> None:
        handler = registered_app.routes["GET /api/v1/workflows/stats"]
        result = await handler()
        assert result["templates"] == 4
        assert result["simple"]["total"] == 0
        assert result["dag_runs"] == 0

    async def test_stats_after_start(self, registered_app: FakeApp) -> None:
        start = registered_app.routes["POST /api/v1/workflows/instances"]
        await start(FakeRequest({"template_id": "wf-onboarding"}))
        handler = registered_app.routes["GET /api/v1/workflows/stats"]
        result = await handler()
        assert result["simple"]["running"] == 1

    async def test_stats_with_dag_runs(
        self,
        app: FakeApp,
        config_manager: ConfigManager,
        tmp_path: Path,
    ) -> None:
        cp_dir = tmp_path / "checkpoints"
        cp_dir.mkdir()
        (cp_dir / "r1.json").write_text("{}", encoding="utf-8")
        (cp_dir / "r2.json").write_text("{}", encoding="utf-8")

        dag_engine = MagicMock()
        dag_engine._checkpoint_dir = cp_dir

        gw = MagicMock()
        gw._workflow_engine = WorkflowEngine()
        gw._template_library = TemplateLibrary(load_builtins=True)
        gw._dag_workflow_engine = dag_engine

        from cognithor.channels.config_routes import create_config_routes

        create_config_routes(app, config_manager, gateway=gw)

        handler = app.routes["GET /api/v1/workflows/stats"]
        result = await handler()
        assert result["dag_runs"] == 2
        assert result["templates"] == 4
