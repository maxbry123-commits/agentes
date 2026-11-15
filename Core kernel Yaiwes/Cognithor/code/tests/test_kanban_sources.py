"""Tests for Kanban task source adapters."""

from __future__ import annotations

from cognithor.kanban.sources import (
    ChatTaskDetector,
    CronTaskAdapter,
    EvolutionTaskAdapter,
    SystemTaskAdapter,
)


class TestChatTaskDetector:
    def test_detect_german(self):
        result = ChatTaskDetector.detect("Erstelle einen Task: Recherchiere AI News")
        assert result is not None
        assert result["title"] == "Recherchiere AI News"

    def test_detect_english(self):
        result = ChatTaskDetector.detect("Create a task: Review security audit")
        assert result is not None
        assert result["title"] == "Review security audit"

    def test_detect_kanban_tag(self):
        result = ChatTaskDetector.detect("I will do this. [KANBAN:Fix login bug]")
        assert result is not None
        assert result["title"] == "Fix login bug"

    def test_no_detection(self):
        result = ChatTaskDetector.detect("What is the weather today?")
        assert result is None

    def test_detect_neuer_task(self):
        result = ChatTaskDetector.detect("Neuer Task: Datenbank optimieren")
        assert result is not None
        assert result["title"] == "Datenbank optimieren"


class TestCronTaskAdapter:
    def test_build_task_data(self):
        data = CronTaskAdapter.build_task_data(
            job_name="morning_briefing",
            result="Briefing erstellt: 5 News, 2 CVEs",
            follow_up=False,
        )
        assert data["title"] == "Cron: morning_briefing"
        assert data["source"] == "cron"
        assert data["source_ref"] == "morning_briefing"
        assert data["status"] == "done"

    def test_build_followup(self):
        data = CronTaskAdapter.build_task_data(
            job_name="security_scan",
            result="3 critical findings",
            follow_up=True,
        )
        assert data["status"] == "todo"
        assert "3 critical findings" in data["description"]


class TestEvolutionTaskAdapter:
    def test_skill_failure(self):
        data = EvolutionTaskAdapter.from_skill_failure("web_scraper", 0.4)
        assert "web_scraper" in data["title"]
        assert data["priority"] == "high" if 0.4 > 0.5 else "medium"
        assert data["source"] == "evolution"

    def test_knowledge_gap(self):
        data = EvolutionTaskAdapter.from_knowledge_gap("quantum computing")
        assert "quantum computing" in data["title"]
        assert data["source"] == "evolution"


class TestSystemTaskAdapter:
    def test_from_recovery_failure(self):
        data = SystemTaskAdapter.from_recovery_failure("web_search", 3, "timeout")
        assert "web_search" in data["title"]
        assert data["priority"] == "urgent"
        assert data["source"] == "system"
