"""Tests for Kanban REST API."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cognithor.kanban.api import create_kanban_router
from cognithor.kanban.engine import KanbanEngine
from cognithor.kanban.store import KanbanStore


@pytest.fixture
def client(tmp_path):
    store = KanbanStore(str(tmp_path / "kanban.db"), use_encryption=False)
    engine = KanbanEngine(store)
    app = FastAPI()
    app.include_router(create_kanban_router(engine))
    return TestClient(app)


class TestKanbanAPI:
    def test_create_task(self, client):
        resp = client.post(
            "/api/v1/kanban/tasks",
            json={
                "title": "Test task",
                "priority": "high",
                "assigned_agent": "coder",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test task"
        assert data["priority"] == "high"
        assert data["id"]

    def test_list_tasks(self, client):
        client.post("/api/v1/kanban/tasks", json={"title": "A"})
        client.post("/api/v1/kanban/tasks", json={"title": "B"})
        resp = client.get("/api/v1/kanban/tasks")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_filter_status(self, client):
        client.post("/api/v1/kanban/tasks", json={"title": "A"})
        resp = client.get("/api/v1/kanban/tasks", params={"status": "todo"})
        assert len(resp.json()) == 1
        resp2 = client.get("/api/v1/kanban/tasks", params={"status": "done"})
        assert len(resp2.json()) == 0

    def test_get_task(self, client):
        r = client.post("/api/v1/kanban/tasks", json={"title": "Test"})
        task_id = r.json()["id"]
        resp = client.get(f"/api/v1/kanban/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test"

    def test_get_task_not_found(self, client):
        resp = client.get("/api/v1/kanban/tasks/nonexistent")
        assert resp.status_code == 404

    def test_update_task(self, client):
        r = client.post("/api/v1/kanban/tasks", json={"title": "Old"})
        task_id = r.json()["id"]
        resp = client.patch(
            f"/api/v1/kanban/tasks/{task_id}",
            json={
                "title": "New",
                "assigned_agent": "researcher",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New"

    def test_delete_task(self, client):
        r = client.post("/api/v1/kanban/tasks", json={"title": "Delete"})
        task_id = r.json()["id"]
        resp = client.delete(f"/api/v1/kanban/tasks/{task_id}")
        assert resp.status_code == 204
        assert client.get(f"/api/v1/kanban/tasks/{task_id}").status_code == 404

    def test_move_task(self, client):
        r = client.post("/api/v1/kanban/tasks", json={"title": "Move"})
        task_id = r.json()["id"]
        resp = client.post(
            f"/api/v1/kanban/tasks/{task_id}/move",
            json={
                "status": "in_progress",
                "sort_order": 3,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    def test_move_invalid_transition(self, client):
        r = client.post("/api/v1/kanban/tasks", json={"title": "Bad"})
        task_id = r.json()["id"]
        resp = client.post(
            f"/api/v1/kanban/tasks/{task_id}/move",
            json={
                "status": "done",
            },
        )
        assert resp.status_code == 409

    def test_history(self, client):
        r = client.post("/api/v1/kanban/tasks", json={"title": "Track"})
        task_id = r.json()["id"]
        client.post(f"/api/v1/kanban/tasks/{task_id}/move", json={"status": "in_progress"})
        resp = client.get(f"/api/v1/kanban/tasks/{task_id}/history")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_stats(self, client):
        client.post("/api/v1/kanban/tasks", json={"title": "A"})
        client.post("/api/v1/kanban/tasks", json={"title": "B"})
        resp = client.get("/api/v1/kanban/stats")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2
