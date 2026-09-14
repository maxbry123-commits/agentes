"""Tests for Evolution REST API."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cognithor.evolution.api import create_evolution_router


class MockGoalManager:
    def __init__(self):
        self._goals = []

    def active_goals(self):
        return self._goals

    def all_goals(self):
        return self._goals

    def add_goal(self, goal):
        self._goals.append(goal)

    def get_goal(self, goal_id):
        return next((g for g in self._goals if g.id == goal_id), None)

    def pause_goal(self, goal_id):
        g = self.get_goal(goal_id)
        if g:
            g.status = "paused"

    def save(self):
        pass


class MockGoal:
    def __init__(self, id, title, status="active", progress=0.0, priority=3):
        self.id = id
        self.title = title
        self.status = status
        self.progress = progress
        self.priority = priority
        self.description = ""
        self.sub_goals = []
        self.success_criteria = []
        self.tags = []


class MockJournal:
    def recent(self, days=7):
        return "Day 1: Learned about insurance."


class MockDeepLearner:
    def list_plans(self):
        return []


@pytest.fixture
def client():
    gm = MockGoalManager()
    gm.add_goal(MockGoal("g1", "Insurance Expert", progress=0.4))
    gm.add_goal(MockGoal("g2", "Cybersecurity", status="paused"))

    router = create_evolution_router(
        goal_manager=gm,
        journal=MockJournal(),
        deep_learner=MockDeepLearner(),
    )
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestEvolutionAPI:
    def test_list_goals(self, client):
        resp = client.get("/api/v1/evolution/goals")
        assert resp.status_code == 200
        goals = resp.json()
        assert len(goals) == 2
        assert goals[0]["title"] == "Insurance Expert"

    def test_create_goal(self, client):
        resp = client.post(
            "/api/v1/evolution/goals",
            json={
                "title": "Learn Rust",
                "description": "Master Rust programming",
                "priority": 2,
            },
        )
        assert resp.status_code == 201

    def test_journal(self, client):
        resp = client.get("/api/v1/evolution/journal", params={"days": 7})
        assert resp.status_code == 200
        assert "insurance" in resp.json()["content"].lower()

    def test_plans(self, client):
        resp = client.get("/api/v1/evolution/plans")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_stats(self, client):
        resp = client.get("/api/v1/evolution/stats")
        assert resp.status_code == 200
        assert "total_goals" in resp.json()
