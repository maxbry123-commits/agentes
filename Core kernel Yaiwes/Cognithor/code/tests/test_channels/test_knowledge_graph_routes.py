"""Tests for the Knowledge Graph REST API routes.

Covers stats, entities listing, entity relations, and edge cases.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

# ============================================================================
# Fake App / Request (same pattern as other route tests)
# ============================================================================


class FakeRequest:
    def __init__(self, body: dict[str, Any] | None = None) -> None:
        self._body = body or {}

    async def json(self) -> dict[str, Any]:
        return self._body


class FakeApp:
    """Minimal mock that captures route registrations."""

    def __init__(self) -> None:
        self._routes: dict[str, Any] = {}

    def get(self, path: str, **kw: Any):
        def decorator(fn):
            self._routes[f"GET {path}"] = fn
            return fn

        return decorator

    def post(self, path: str, **kw: Any):
        def decorator(fn):
            self._routes[f"POST {path}"] = fn
            return fn

        return decorator

    def patch(self, path: str, **kw: Any):
        def decorator(fn):
            self._routes[f"PATCH {path}"] = fn
            return fn

        return decorator

    def put(self, path: str, **kw: Any):
        def decorator(fn):
            self._routes[f"PUT {path}"] = fn
            return fn

        return decorator

    def delete(self, path: str, **kw: Any):
        def decorator(fn):
            self._routes[f"DELETE {path}"] = fn
            return fn

        return decorator


def _make_config_manager() -> MagicMock:
    cm = MagicMock()
    cm.config.version = "1.0.0"
    cm.config.owner_name = "test"
    cm.config.cognithor_home = MagicMock()
    cm.config.heartbeat.enabled = False
    cm.config.channels = MagicMock()
    cm.config.models.planner.name = "test"
    cm.config.models.executor.name = "test"
    cm.config.models.coder.name = "test"
    cm.config.models.embedding.name = "test"
    cm.config.llm_backend_type = "ollama"
    return cm


def _make_entity(eid: str, name: str, etype: str = "unknown", confidence: float = 0.5):
    e = MagicMock()
    e.id = eid
    e.name = name
    e.type = etype
    e.entity_type = etype
    e.confidence = confidence
    e.attributes = {}
    return e


def _make_relation(src: str, tgt: str, rtype: str = "related_to", confidence: float = 0.5):
    r = MagicMock()
    r.source_entity = src
    r.source_name = src
    r.target_entity = tgt
    r.target_name = tgt
    r.relation_type = rtype
    r.confidence = confidence
    return r


@pytest.fixture
def app_and_gateway():
    from cognithor.channels.config_routes import create_config_routes

    app = FakeApp()
    gateway = MagicMock()
    gateway._semantic_memory = None
    cm = _make_config_manager()

    create_config_routes(app, cm, gateway=gateway)
    return app, gateway


# ============================================================================
# Route Registration
# ============================================================================


class TestRegistration:
    def test_graph_stats_registered(self, app_and_gateway) -> None:
        app, _ = app_and_gateway
        assert "GET /api/v1/memory/graph/stats" in app._routes

    def test_graph_entities_registered(self, app_and_gateway) -> None:
        app, _ = app_and_gateway
        assert "GET /api/v1/memory/graph/entities" in app._routes

    def test_graph_entity_relations_registered(self, app_and_gateway) -> None:
        app, _ = app_and_gateway
        assert "GET /api/v1/memory/graph/entities/{entity_id}/relations" in app._routes


# ============================================================================
# Graph Stats
# ============================================================================


class TestGraphStats:
    async def test_stats_no_semantic_memory(self, app_and_gateway) -> None:
        app, gateway = app_and_gateway
        gateway._semantic_memory = None
        handler = app._routes["GET /api/v1/memory/graph/stats"]
        result = await handler()
        assert result["entities"] == 0
        assert result["relations"] == 0

    async def test_stats_with_entities(self, app_and_gateway) -> None:
        app, gateway = app_and_gateway
        sem = MagicMock()
        sem.entities = {
            "e1": _make_entity("e1", "Berlin", "location"),
            "e2": _make_entity("e2", "Schmidt", "person"),
            "e3": _make_entity("e3", "München", "location"),
        }
        sem.relations = [
            _make_relation("e1", "e2"),
        ]
        gateway._semantic_memory = sem
        handler = app._routes["GET /api/v1/memory/graph/stats"]
        result = await handler()
        assert result["entities"] == 3
        assert result["relations"] == 1
        assert result["entity_types"]["location"] == 2
        assert result["entity_types"]["person"] == 1


# ============================================================================
# Graph Entities
# ============================================================================


class TestGraphEntities:
    async def test_entities_no_semantic_memory(self, app_and_gateway) -> None:
        app, gateway = app_and_gateway
        gateway._semantic_memory = None
        handler = app._routes["GET /api/v1/memory/graph/entities"]
        result = await handler()
        assert result["entities"] == []
        assert result["relations"] == []

    async def test_entities_with_data(self, app_and_gateway) -> None:
        app, gateway = app_and_gateway
        sem = MagicMock()
        sem.entities = {
            "e1": _make_entity("e1", "Berlin", "location", 0.9),
            "e2": _make_entity("e2", "Schmidt", "person", 0.7),
        }
        sem.relations = [
            _make_relation("e1", "e2", "kennt", 0.6),
        ]
        gateway._semantic_memory = sem
        handler = app._routes["GET /api/v1/memory/graph/entities"]
        result = await handler()
        assert len(result["entities"]) == 2
        assert len(result["relations"]) == 1
        e1 = next(e for e in result["entities"] if e["name"] == "Berlin")
        assert e1["type"] == "location"
        assert e1["confidence"] == 0.9
        rel = result["relations"][0]
        assert rel["relation_type"] == "kennt"

    async def test_entities_empty_graph(self, app_and_gateway) -> None:
        app, gateway = app_and_gateway
        sem = MagicMock()
        sem.entities = {}
        sem.relations = []
        gateway._semantic_memory = sem
        handler = app._routes["GET /api/v1/memory/graph/entities"]
        result = await handler()
        assert result["entities"] == []
        assert result["relations"] == []


# ============================================================================
# Entity Relations
# ============================================================================


class TestEntityRelations:
    async def test_relations_no_semantic_memory(self, app_and_gateway) -> None:
        app, gateway = app_and_gateway
        gateway._semantic_memory = None
        handler = app._routes["GET /api/v1/memory/graph/entities/{entity_id}/relations"]
        result = await handler(entity_id="e1")
        assert result["relations"] == []

    async def test_relations_found(self, app_and_gateway) -> None:
        app, gateway = app_and_gateway
        sem = MagicMock()
        sem.relations = [
            _make_relation("e1", "e2", "kennt"),
            _make_relation("e3", "e1", "arbeitet_bei"),
            _make_relation("e2", "e3", "leitet"),
        ]
        gateway._semantic_memory = sem
        handler = app._routes["GET /api/v1/memory/graph/entities/{entity_id}/relations"]
        result = await handler(entity_id="e1")
        assert len(result["relations"]) == 2  # e1→e2 and e3→e1

    async def test_relations_not_found(self, app_and_gateway) -> None:
        app, gateway = app_and_gateway
        sem = MagicMock()
        sem.relations = [
            _make_relation("e2", "e3"),
        ]
        gateway._semantic_memory = sem
        handler = app._routes["GET /api/v1/memory/graph/entities/{entity_id}/relations"]
        result = await handler(entity_id="e1")
        assert result["relations"] == []
