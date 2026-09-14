"""Tests for jarvis.security.gdpr — GDPR Compliance Toolkit."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from cognithor.security.gdpr import (
    DEFAULT_RETENTION_POLICIES,
    AuditExporter,
    DataCategory,
    DataProcessingLog,
    DataProcessingRecord,
    ErasureManager,
    ErasureRequest,
    ErasureStatus,
    GDPRComplianceManager,
    ModelUsageLog,
    ModelUsageRecord,
    ProcessingBasis,
    RetentionAction,
    RetentionEnforcer,
    RetentionPolicy,
)

if TYPE_CHECKING:
    from pathlib import Path

# ── Enums ─────────────────────────────────────────────────────────────────


class TestEnums:
    def test_processing_basis_values(self) -> None:
        assert len(ProcessingBasis) == 6
        assert ProcessingBasis.CONSENT == "consent"
        assert ProcessingBasis.LEGITIMATE_INTEREST == "legitimate_interest"

    def test_data_category_values(self) -> None:
        assert len(DataCategory) == 8
        assert DataCategory.QUERY == "query"
        assert DataCategory.VOICE == "voice"
        assert DataCategory.CREDENTIAL == "credential"

    def test_erasure_status_values(self) -> None:
        assert len(ErasureStatus) == 5
        assert ErasureStatus.PENDING == "pending"
        assert ErasureStatus.COMPLETED == "completed"

    def test_retention_action_values(self) -> None:
        assert len(RetentionAction) == 3
        assert RetentionAction.DELETE == "delete"
        assert RetentionAction.ANONYMIZE == "anonymize"


# ── DataProcessingRecord ─────────────────────────────────────────────────


class TestDataProcessingRecord:
    def test_defaults(self) -> None:
        rec = DataProcessingRecord()
        assert rec.record_id == ""
        assert rec.category == DataCategory.QUERY
        assert rec.legal_basis == ProcessingBasis.LEGITIMATE_INTEREST
        assert rec.retention_days == 90
        assert rec.country == "DE"

    def test_round_trip(self) -> None:
        rec = DataProcessingRecord(
            record_id="dpr-001",
            user_id="u1",
            category=DataCategory.VOICE,
            purpose="transcription",
            legal_basis=ProcessingBasis.CONSENT,
            tool_name="voice_input",
            data_hash="abc123",
        )
        d = rec.to_dict()
        restored = DataProcessingRecord.from_dict(d)
        assert restored.record_id == "dpr-001"
        assert restored.category == DataCategory.VOICE
        assert restored.legal_basis == ProcessingBasis.CONSENT

    def test_to_dict_keys(self) -> None:
        rec = DataProcessingRecord(record_id="x")
        d = rec.to_dict()
        expected_keys = {
            "record_id",
            "user_id",
            "timestamp",
            "category",
            "purpose",
            "legal_basis",
            "tool_name",
            "data_summary",
            "data_hash",
            "retention_days",
            "third_party",
            "country",
        }
        assert set(d.keys()) == expected_keys


# ── DataProcessingLog ────────────────────────────────────────────────────


class TestDataProcessingLog:
    def test_record(self) -> None:
        log = DataProcessingLog()
        rec = log.record("u1", DataCategory.QUERY, "answer question", tool_name="web_search")
        assert rec.record_id == "dpr-000001"
        assert rec.user_id == "u1"
        assert rec.tool_name == "web_search"
        assert len(log.records) == 1

    def test_record_with_raw_data_generates_hash(self) -> None:
        log = DataProcessingLog()
        rec = log.record("u1", DataCategory.QUERY, "test", raw_data="Hello World")
        assert rec.data_hash != ""
        assert len(rec.data_hash) == 16

    def test_sequential_ids(self) -> None:
        log = DataProcessingLog()
        r1 = log.record("u1", DataCategory.QUERY, "a")
        r2 = log.record("u1", DataCategory.MEMORY, "b")
        assert r1.record_id == "dpr-000001"
        assert r2.record_id == "dpr-000002"

    def test_query_by_user(self) -> None:
        log = DataProcessingLog()
        log.record("u1", DataCategory.QUERY, "a")
        log.record("u2", DataCategory.QUERY, "b")
        log.record("u1", DataCategory.MEMORY, "c")
        results = log.query(user_id="u1")
        assert len(results) == 2

    def test_query_by_category(self) -> None:
        log = DataProcessingLog()
        log.record("u1", DataCategory.QUERY, "a")
        log.record("u1", DataCategory.VOICE, "b")
        results = log.query(category=DataCategory.VOICE)
        assert len(results) == 1

    def test_query_by_tool(self) -> None:
        log = DataProcessingLog()
        log.record("u1", DataCategory.QUERY, "a", tool_name="web_search")
        log.record("u1", DataCategory.QUERY, "b", tool_name="memory_search")
        results = log.query(tool_name="web_search")
        assert len(results) == 1

    def test_user_report(self) -> None:
        log = DataProcessingLog()
        log.record("u1", DataCategory.QUERY, "answer", tool_name="web_search")
        log.record("u1", DataCategory.MEMORY, "store", tool_name="memory_store")
        log.record("u2", DataCategory.QUERY, "other")
        report = log.user_report("u1")
        assert report["user_id"] == "u1"
        assert report["total_records"] == 2
        assert "query" in report["categories"]
        assert "memory" in report["categories"]
        assert "web_search" in report["tools_used"]
        assert len(report["records"]) == 2

    def test_delete_user_records(self) -> None:
        log = DataProcessingLog()
        log.record("u1", DataCategory.QUERY, "a")
        log.record("u2", DataCategory.QUERY, "b")
        log.record("u1", DataCategory.MEMORY, "c")
        deleted = log.delete_user_records("u1")
        assert deleted == 2
        assert len(log.records) == 1
        assert log.records[0].user_id == "u2"


# ── ModelUsageRecord ─────────────────────────────────────────────────────


class TestModelUsageRecord:
    def test_defaults(self) -> None:
        rec = ModelUsageRecord()
        assert rec.provider == "ollama"
        assert rec.success is True
        assert rec.contains_pii is False

    def test_round_trip(self) -> None:
        rec = ModelUsageRecord(
            record_id="mur-001",
            model_name="qwen3:8b",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        d = rec.to_dict()
        restored = ModelUsageRecord.from_dict(d)
        assert restored.model_name == "qwen3:8b"
        assert restored.total_tokens == 150


# ── ModelUsageLog ────────────────────────────────────────────────────────


class TestModelUsageLog:
    def test_record(self) -> None:
        log = ModelUsageLog()
        rec = log.record("u1", "qwen3:8b", prompt_tokens=100, completion_tokens=50)
        assert rec.record_id == "mur-000001"
        assert rec.total_tokens == 150
        assert len(log.records) == 1

    def test_record_with_raw_input(self) -> None:
        log = ModelUsageLog()
        rec = log.record("u1", "qwen3:8b", raw_input="test prompt")
        assert rec.input_hash != ""

    def test_query_by_user(self) -> None:
        log = ModelUsageLog()
        log.record("u1", "qwen3:8b")
        log.record("u2", "qwen3:32b")
        assert len(log.query(user_id="u1")) == 1

    def test_query_by_model(self) -> None:
        log = ModelUsageLog()
        log.record("u1", "qwen3:8b")
        log.record("u1", "qwen3:32b")
        assert len(log.query(model_name="qwen3:8b")) == 1

    def test_query_pii(self) -> None:
        log = ModelUsageLog()
        log.record("u1", "qwen3:8b", contains_pii=True)
        log.record("u1", "qwen3:8b", contains_pii=False)
        assert len(log.query(contains_pii=True)) == 1

    def test_usage_summary(self) -> None:
        log = ModelUsageLog()
        log.record("u1", "qwen3:8b", prompt_tokens=100, completion_tokens=50, latency_ms=200.0)
        log.record(
            "u1",
            "qwen3:8b",
            prompt_tokens=80,
            completion_tokens=40,
            latency_ms=150.0,
            contains_pii=True,
        )
        log.record("u1", "qwen3:32b", prompt_tokens=200, completion_tokens=100, success=False)
        summary = log.usage_summary()
        assert summary["qwen3:8b"]["calls"] == 2
        assert summary["qwen3:8b"]["total_tokens"] == 270
        assert summary["qwen3:8b"]["pii_calls"] == 1
        assert summary["qwen3:32b"]["errors"] == 1

    def test_delete_user_records(self) -> None:
        log = ModelUsageLog()
        log.record("u1", "qwen3:8b")
        log.record("u2", "qwen3:8b")
        deleted = log.delete_user_records("u1")
        assert deleted == 1
        assert len(log.records) == 1


# ── RetentionPolicy ──────────────────────────────────────────────────────


class TestRetentionPolicy:
    def test_round_trip(self) -> None:
        p = RetentionPolicy(
            name="test",
            category=DataCategory.VOICE,
            retention_days=30,
            action=RetentionAction.DELETE,
        )
        d = p.to_dict()
        restored = RetentionPolicy.from_dict(d)
        assert restored.name == "test"
        assert restored.category == DataCategory.VOICE
        assert restored.retention_days == 30

    def test_default_policies(self) -> None:
        assert len(DEFAULT_RETENTION_POLICIES) >= 5
        categories = {p.category for p in DEFAULT_RETENTION_POLICIES}
        assert DataCategory.QUERY in categories
        assert DataCategory.VOICE in categories
        assert DataCategory.CREDENTIAL in categories


# ── RetentionEnforcer ────────────────────────────────────────────────────


class TestRetentionEnforcer:
    def test_default_policies_loaded(self) -> None:
        enforcer = RetentionEnforcer()
        assert len(enforcer.policies) >= 5

    def test_add_policy(self) -> None:
        enforcer = RetentionEnforcer(policies=[])
        enforcer.add_policy(
            RetentionPolicy(
                name="test",
                category=DataCategory.QUERY,
                retention_days=7,
            )
        )
        assert DataCategory.QUERY in enforcer.policies

    def test_find_expired(self) -> None:
        enforcer = RetentionEnforcer(
            policies=[
                RetentionPolicy(name="q", category=DataCategory.QUERY, retention_days=30),
            ]
        )
        now = datetime(2026, 3, 5, tzinfo=UTC)
        old_time = (now - timedelta(days=60)).isoformat()
        new_time = (now - timedelta(days=10)).isoformat()

        records = [
            DataProcessingRecord(record_id="r1", timestamp=old_time, category=DataCategory.QUERY),
            DataProcessingRecord(record_id="r2", timestamp=new_time, category=DataCategory.QUERY),
        ]
        expired = enforcer.find_expired(records, now=now)
        assert len(expired) == 1
        assert expired[0][0].record_id == "r1"

    def test_immediate_deletion_policy(self) -> None:
        enforcer = RetentionEnforcer(
            policies=[
                RetentionPolicy(name="cred", category=DataCategory.CREDENTIAL, retention_days=0),
            ]
        )
        now = datetime(2026, 3, 5, tzinfo=UTC)
        records = [
            DataProcessingRecord(
                record_id="r1",
                timestamp=now.isoformat(),
                category=DataCategory.CREDENTIAL,
            ),
        ]
        expired = enforcer.find_expired(records, now=now)
        assert len(expired) == 1

    def test_enforce_deletes(self) -> None:
        enforcer = RetentionEnforcer(
            policies=[
                RetentionPolicy(
                    name="q",
                    category=DataCategory.QUERY,
                    retention_days=30,
                    action=RetentionAction.DELETE,
                ),
            ]
        )
        log = DataProcessingLog()
        now = datetime(2026, 3, 5, tzinfo=UTC)
        old_time = (now - timedelta(days=60)).isoformat()

        # Manually insert a record with old timestamp
        log._records.append(
            DataProcessingRecord(
                record_id="r1",
                user_id="u1",
                timestamp=old_time,
                category=DataCategory.QUERY,
            )
        )
        log._records.append(
            DataProcessingRecord(
                record_id="r2",
                user_id="u1",
                timestamp=now.isoformat(),
                category=DataCategory.QUERY,
            )
        )

        counts = enforcer.enforce(log, now=now)
        assert counts.get("delete", 0) == 1
        assert len(log.records) == 1
        assert log.records[0].record_id == "r2"

    def test_enforce_anonymize_counted(self) -> None:
        enforcer = RetentionEnforcer(
            policies=[
                RetentionPolicy(
                    name="conv",
                    category=DataCategory.CONVERSATION,
                    retention_days=30,
                    action=RetentionAction.ANONYMIZE,
                ),
            ]
        )
        log = DataProcessingLog()
        now = datetime(2026, 3, 5, tzinfo=UTC)
        old_time = (now - timedelta(days=60)).isoformat()

        log._records.append(
            DataProcessingRecord(
                record_id="r1",
                timestamp=old_time,
                category=DataCategory.CONVERSATION,
            )
        )
        counts = enforcer.enforce(log, now=now)
        assert counts.get("anonymize", 0) == 1
        # Anonymize doesn't delete
        assert len(log.records) == 1

    def test_no_policy_for_category(self) -> None:
        enforcer = RetentionEnforcer(policies=[])
        records = [
            DataProcessingRecord(
                record_id="r1",
                timestamp=datetime(2020, 1, 1, tzinfo=UTC).isoformat(),
                category=DataCategory.QUERY,
            ),
        ]
        expired = enforcer.find_expired(records)
        assert len(expired) == 0


# ── ErasureManager ───────────────────────────────────────────────────────


class TestErasureManager:
    def _setup(self) -> tuple[DataProcessingLog, ModelUsageLog, ErasureManager]:
        dp = DataProcessingLog()
        dp.record("u1", DataCategory.QUERY, "a")
        dp.record("u1", DataCategory.MEMORY, "b")
        dp.record("u2", DataCategory.QUERY, "c")
        mu = ModelUsageLog()
        mu.record("u1", "qwen3:8b")
        mu.record("u2", "qwen3:8b")
        em = ErasureManager()
        return dp, mu, em

    def test_request_erasure(self) -> None:
        dp, mu, em = self._setup()
        req = em.request_erasure("u1", dp, mu)
        assert req.status == ErasureStatus.COMPLETED
        assert req.records_deleted == 2
        assert req.model_records_deleted == 1
        assert len(dp.records) == 1
        assert len(mu.records) == 1

    def test_erasure_request_tracked(self) -> None:
        dp, mu, em = self._setup()
        em.request_erasure("u1", dp, mu)
        assert len(em.requests) == 1
        assert em.requests[0].request_id == "era-000001"

    def test_external_handler(self) -> None:
        dp, mu, em = self._setup()
        handler = MagicMock(return_value=5)
        em.register_handler(handler)
        req = em.request_erasure("u1", dp, mu)
        handler.assert_called_once_with("u1")
        assert "External handler: 5 records deleted" in req.erasure_log

    def test_external_handler_failure(self) -> None:
        dp, mu, em = self._setup()
        em.register_handler(MagicMock(side_effect=RuntimeError("db error")))
        req = em.request_erasure("u1", dp, mu)
        assert req.status == ErasureStatus.PARTIALLY_COMPLETED
        assert any("failed" in entry for entry in req.erasure_log)

    def test_erasure_to_dict(self) -> None:
        req = ErasureRequest(
            request_id="era-001",
            user_id="u1",
            status=ErasureStatus.COMPLETED,
            records_deleted=3,
        )
        d = req.to_dict()
        assert d["request_id"] == "era-001"
        assert d["status"] == "completed"


# ── AuditExporter ────────────────────────────────────────────────────────


class TestAuditExporter:
    def _setup(self) -> AuditExporter:
        dp = DataProcessingLog()
        dp.record("u1", DataCategory.QUERY, "search", tool_name="web_search")
        dp.record("u2", DataCategory.MEMORY, "store", tool_name="memory_store")
        mu = ModelUsageLog()
        mu.record("u1", "qwen3:8b", prompt_tokens=100, contains_pii=True)
        em = ErasureManager()
        re = RetentionEnforcer()
        return AuditExporter(dp, mu, em, re)

    def test_to_json(self) -> None:
        exp = self._setup()
        j = exp.to_json()
        data = json.loads(j)
        assert data["summary"]["total_processing_records"] == 2
        assert data["summary"]["total_model_usage_records"] == 1
        assert data["summary"]["pii_invocations"] == 1

    def test_to_json_filtered_by_user(self) -> None:
        exp = self._setup()
        j = exp.to_json(user_id="u1")
        data = json.loads(j)
        assert data["summary"]["total_processing_records"] == 1
        assert data["user_id"] == "u1"

    def test_to_markdown(self) -> None:
        exp = self._setup()
        md = exp.to_markdown()
        assert "GDPR Compliance Audit Report" in md
        assert "web_search" in md
        assert "Retention Policies" in md

    def test_save_json(self, tmp_path: Path) -> None:
        exp = self._setup()
        out = tmp_path / "audit.json"
        exp.save_json(out)
        data = json.loads(out.read_text())
        assert "summary" in data


# ── GDPRComplianceManager ───────────────────────────────────────────────


class TestGDPRComplianceManager:
    def test_log_processing(self) -> None:
        mgr = GDPRComplianceManager()
        rec = mgr.log_processing("u1", DataCategory.QUERY, "answer")
        assert rec.user_id == "u1"
        assert len(mgr.processing_log.records) == 1

    def test_log_model_usage(self) -> None:
        mgr = GDPRComplianceManager()
        rec = mgr.log_model_usage("u1", "qwen3:8b", prompt_tokens=100)
        assert rec.model_name == "qwen3:8b"
        assert len(mgr.usage_log.records) == 1

    def test_enforce_retention(self) -> None:
        mgr = GDPRComplianceManager(
            retention_policies=[
                RetentionPolicy(
                    name="q",
                    category=DataCategory.QUERY,
                    retention_days=1,
                    action=RetentionAction.DELETE,
                ),
            ]
        )
        now = datetime(2026, 3, 5, tzinfo=UTC)
        old_time = (now - timedelta(days=10)).isoformat()
        mgr.processing_log._records.append(
            DataProcessingRecord(
                record_id="r1",
                user_id="u1",
                timestamp=old_time,
                category=DataCategory.QUERY,
            )
        )
        counts = mgr.enforce_retention(now=now)
        assert counts.get("delete", 0) == 1

    def test_erase_user(self) -> None:
        mgr = GDPRComplianceManager()
        mgr.log_processing("u1", DataCategory.QUERY, "a")
        mgr.log_model_usage("u1", "qwen3:8b")
        mgr.log_processing("u2", DataCategory.QUERY, "b")
        req = mgr.erase_user("u1")
        assert req.status == ErasureStatus.COMPLETED
        assert req.records_deleted == 1
        assert req.model_records_deleted == 1
        assert len(mgr.processing_log.records) == 1

    def test_user_report(self) -> None:
        mgr = GDPRComplianceManager()
        mgr.log_processing("u1", DataCategory.QUERY, "search")
        report = mgr.user_report("u1")
        assert report["user_id"] == "u1"
        assert report["total_records"] == 1

    def test_compliance_summary(self) -> None:
        mgr = GDPRComplianceManager()
        mgr.log_processing("u1", DataCategory.QUERY, "a")
        mgr.log_model_usage("u1", "qwen3:8b", contains_pii=True)
        summary = mgr.compliance_summary()
        assert summary["processing_records"] == 1
        assert summary["model_usage_records"] == 1
        assert summary["pii_invocations"] == 1
        assert summary["has_retention_policies"] is True

    def test_full_workflow(self) -> None:
        """End-to-end: log, report, enforce, erase, export."""
        mgr = GDPRComplianceManager()

        # Log activities
        mgr.log_processing("u1", DataCategory.QUERY, "web search", tool_name="web_search")
        mgr.log_processing("u1", DataCategory.VOICE, "voice input")
        mgr.log_model_usage("u1", "qwen3:8b", prompt_tokens=100, contains_pii=True)
        mgr.log_processing("u2", DataCategory.QUERY, "question")

        # User report
        report = mgr.user_report("u1")
        assert report["total_records"] == 2

        # Export
        j = mgr.exporter.to_json()
        data = json.loads(j)
        assert data["summary"]["total_processing_records"] == 3

        # Erase u1
        req = mgr.erase_user("u1")
        assert req.records_deleted == 2
        assert req.model_records_deleted == 1

        # Verify u1 data gone
        assert len(mgr.processing_log.query(user_id="u1")) == 0
        assert len(mgr.usage_log.query(user_id="u1")) == 0

        # u2 data still present
        assert len(mgr.processing_log.query(user_id="u2")) == 1
