# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Tests for HashlineAuditor."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from cognithor.hashline.audit import HashlineAuditor
from cognithor.hashline.models import EditIntent, EditResult

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def auditor(tmp_path: Path) -> HashlineAuditor:
    return HashlineAuditor(data_dir=tmp_path)


@pytest.fixture
def sample_intent(tmp_path: Path) -> EditIntent:
    return EditIntent(
        file_path=tmp_path / "test.py",
        target_line=5,
        target_hash="Xk",
        operation="replace",
        new_content="new content",
    )


@pytest.fixture
def sample_result(tmp_path: Path) -> EditResult:
    return EditResult(
        success=True,
        operation="replace",
        file_path=tmp_path / "test.py",
        line_number=5,
        old_content="old content",
        new_content="new content",
        audit_hash="abc123",
    )


class TestLogEdit:
    def test_returns_sha256_hash(
        self,
        auditor: HashlineAuditor,
        sample_result: EditResult,
        sample_intent: EditIntent,
    ) -> None:
        h = auditor.log_edit(sample_result, sample_intent, "agent-1")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex

    def test_appends_to_file(
        self,
        auditor: HashlineAuditor,
        sample_result: EditResult,
        sample_intent: EditIntent,
        tmp_path: Path,
    ) -> None:
        auditor.log_edit(sample_result, sample_intent, "agent-1")
        audit_file = tmp_path / "hashline_audit.jsonl"
        assert audit_file.exists()
        lines = audit_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["type"] == "edit"
        assert entry["agent_id"] == "agent-1"
        assert entry["success"] is True


class TestLogRead:
    def test_log_read_entry(
        self,
        auditor: HashlineAuditor,
        tmp_path: Path,
    ) -> None:
        h = auditor.log_read(tmp_path / "file.py", 42, "agent-2")
        assert len(h) == 64
        audit_file = tmp_path / "hashline_audit.jsonl"
        lines = audit_file.read_text(encoding="utf-8").strip().split("\n")
        entry = json.loads(lines[0])
        assert entry["type"] == "read"
        assert entry["line_count"] == 42


class TestGetFileHistory:
    def test_returns_entries_for_file(
        self,
        auditor: HashlineAuditor,
        sample_result: EditResult,
        sample_intent: EditIntent,
        tmp_path: Path,
    ) -> None:
        auditor.log_edit(sample_result, sample_intent, "agent-1")
        auditor.log_read(tmp_path / "test.py", 10, "agent-2")
        history = auditor.get_file_history(tmp_path / "test.py")
        assert len(history) == 2
        # Newest first
        assert history[0]["type"] == "read"
        assert history[1]["type"] == "edit"

    def test_limit_parameter(
        self,
        auditor: HashlineAuditor,
        tmp_path: Path,
    ) -> None:
        for i in range(10):
            auditor.log_read(tmp_path / "test.py", i, f"agent-{i}")
        history = auditor.get_file_history(tmp_path / "test.py", limit=3)
        assert len(history) == 3

    def test_empty_history(
        self,
        auditor: HashlineAuditor,
        tmp_path: Path,
    ) -> None:
        history = auditor.get_file_history(tmp_path / "nonexistent.py")
        assert history == []


class TestAppendOnly:
    def test_multiple_appends(
        self,
        auditor: HashlineAuditor,
        sample_result: EditResult,
        sample_intent: EditIntent,
        tmp_path: Path,
    ) -> None:
        auditor.log_edit(sample_result, sample_intent, "agent-1")
        auditor.log_edit(sample_result, sample_intent, "agent-2")
        auditor.log_read(tmp_path / "other.py", 5, "agent-3")
        audit_file = tmp_path / "hashline_audit.jsonl"
        lines = audit_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3
