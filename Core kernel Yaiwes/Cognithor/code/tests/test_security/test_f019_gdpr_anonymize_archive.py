"""Tests fuer F-019: GDPR ANONYMIZE/ARCHIVE nicht implementiert.

Prueft dass:
  - ANONYMIZE tatsaechlich PII-Felder entfernt (user_id, data_summary, etc.)
  - ARCHIVE Records aus _records nach _archived verschiebt
  - DELETE weiterhin funktioniert (Regression)
  - Kombinierte Policies korrekt zusammenspielen
  - Anonymisierte Records im Log verbleiben (nicht geloescht)
  - Archivierte Records im archived-Property abrufbar sind
  - Source-Code die Fixes enthaelt
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta

from cognithor.security.gdpr import (
    DataCategory,
    DataProcessingLog,
    DataProcessingRecord,
    RetentionAction,
    RetentionEnforcer,
    RetentionPolicy,
)


def _make_enforcer(*policies: RetentionPolicy) -> RetentionEnforcer:
    return RetentionEnforcer(policies=list(policies))


def _old_record(
    record_id: str,
    category: DataCategory,
    now: datetime,
    days_old: int = 60,
    **kwargs: str,
) -> DataProcessingRecord:
    ts = (now - timedelta(days=days_old)).isoformat()
    return DataProcessingRecord(
        record_id=record_id,
        timestamp=ts,
        category=category,
        user_id=kwargs.get("user_id", "user-123"),
        data_summary=kwargs.get("data_summary", "some personal data"),
        data_hash=kwargs.get("data_hash", "abcdef1234567890"),
        purpose=kwargs.get("purpose", "answer question"),
        third_party=kwargs.get("third_party", "openai"),
    )


class TestAnonymizeAction:
    """Prueft dass ANONYMIZE PII-Felder tatsaechlich entfernt."""

    def test_anonymize_clears_user_id(self) -> None:
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="conv",
                category=DataCategory.CONVERSATION,
                retention_days=30,
                action=RetentionAction.ANONYMIZE,
            ),
        )
        log = DataProcessingLog()
        rec = _old_record("r1", DataCategory.CONVERSATION, now, user_id="sensitive-user")
        log._records.append(rec)

        enforcer.enforce(log, now=now)

        assert len(log.records) == 1
        assert log.records[0].user_id == "ANONYMIZED"

    def test_anonymize_clears_data_summary(self) -> None:
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="conv",
                category=DataCategory.CONVERSATION,
                retention_days=30,
                action=RetentionAction.ANONYMIZE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.CONVERSATION, now))

        enforcer.enforce(log, now=now)

        assert log.records[0].data_summary == ""

    def test_anonymize_clears_data_hash(self) -> None:
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="conv",
                category=DataCategory.CONVERSATION,
                retention_days=30,
                action=RetentionAction.ANONYMIZE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.CONVERSATION, now))

        enforcer.enforce(log, now=now)

        assert log.records[0].data_hash == ""

    def test_anonymize_clears_purpose(self) -> None:
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="conv",
                category=DataCategory.CONVERSATION,
                retention_days=30,
                action=RetentionAction.ANONYMIZE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.CONVERSATION, now))

        enforcer.enforce(log, now=now)

        assert log.records[0].purpose == "ANONYMIZED"

    def test_anonymize_clears_third_party(self) -> None:
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="conv",
                category=DataCategory.CONVERSATION,
                retention_days=30,
                action=RetentionAction.ANONYMIZE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(
            _old_record("r1", DataCategory.CONVERSATION, now, third_party="external-api"),
        )

        enforcer.enforce(log, now=now)

        assert log.records[0].third_party == ""

    def test_anonymize_preserves_record_id(self) -> None:
        """record_id bleibt erhalten (fuer Audit-Trail)."""
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="conv",
                category=DataCategory.CONVERSATION,
                retention_days=30,
                action=RetentionAction.ANONYMIZE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.CONVERSATION, now))

        enforcer.enforce(log, now=now)

        assert log.records[0].record_id == "r1"

    def test_anonymize_preserves_category(self) -> None:
        """Kategorie bleibt fuer Statistik erhalten."""
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="conv",
                category=DataCategory.CONVERSATION,
                retention_days=30,
                action=RetentionAction.ANONYMIZE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.CONVERSATION, now))

        enforcer.enforce(log, now=now)

        assert log.records[0].category == DataCategory.CONVERSATION

    def test_anonymize_does_not_remove_record(self) -> None:
        """Anonymisierter Record bleibt in _records (nicht geloescht)."""
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="conv",
                category=DataCategory.CONVERSATION,
                retention_days=30,
                action=RetentionAction.ANONYMIZE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.CONVERSATION, now))
        log._records.append(_old_record("r2", DataCategory.CONVERSATION, now))

        enforcer.enforce(log, now=now)

        assert len(log.records) == 2

    def test_anonymize_only_expired_records(self) -> None:
        """Nicht-abgelaufene Records bleiben unberuehrt."""
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="conv",
                category=DataCategory.CONVERSATION,
                retention_days=30,
                action=RetentionAction.ANONYMIZE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.CONVERSATION, now, days_old=60))
        fresh = DataProcessingRecord(
            record_id="r2",
            timestamp=(now - timedelta(days=5)).isoformat(),
            category=DataCategory.CONVERSATION,
            user_id="keep-me",
            data_summary="keep this",
        )
        log._records.append(fresh)

        enforcer.enforce(log, now=now)

        r2 = next(r for r in log.records if r.record_id == "r2")
        assert r2.user_id == "keep-me"
        assert r2.data_summary == "keep this"


class TestArchiveAction:
    """Prueft dass ARCHIVE Records korrekt verschiebt."""

    def test_archive_removes_from_records(self) -> None:
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="mem",
                category=DataCategory.MEMORY,
                retention_days=30,
                action=RetentionAction.ARCHIVE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.MEMORY, now))

        enforcer.enforce(log, now=now)

        assert len(log.records) == 0

    def test_archive_adds_to_archived(self) -> None:
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="mem",
                category=DataCategory.MEMORY,
                retention_days=30,
                action=RetentionAction.ARCHIVE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.MEMORY, now))

        enforcer.enforce(log, now=now)

        assert len(log.archived) == 1
        assert log.archived[0].record_id == "r1"

    def test_archive_preserves_all_data(self) -> None:
        """Archivierter Record behaelt alle Felder."""
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="mem",
                category=DataCategory.MEMORY,
                retention_days=30,
                action=RetentionAction.ARCHIVE,
            ),
        )
        log = DataProcessingLog()
        rec = _old_record(
            "r1",
            DataCategory.MEMORY,
            now,
            user_id="u1",
            data_summary="important",
            third_party="api",
        )
        log._records.append(rec)

        enforcer.enforce(log, now=now)

        archived = log.archived[0]
        assert archived.user_id == "u1"
        assert archived.data_summary == "important"
        assert archived.third_party == "api"

    def test_archive_only_expired(self) -> None:
        """Nicht-abgelaufene Records bleiben in _records."""
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="mem",
                category=DataCategory.MEMORY,
                retention_days=30,
                action=RetentionAction.ARCHIVE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.MEMORY, now, days_old=60))
        fresh = DataProcessingRecord(
            record_id="r2",
            timestamp=(now - timedelta(days=5)).isoformat(),
            category=DataCategory.MEMORY,
        )
        log._records.append(fresh)

        enforcer.enforce(log, now=now)

        assert len(log.records) == 1
        assert log.records[0].record_id == "r2"
        assert len(log.archived) == 1

    def test_archive_multiple_records(self) -> None:
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="mem",
                category=DataCategory.MEMORY,
                retention_days=30,
                action=RetentionAction.ARCHIVE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.MEMORY, now))
        log._records.append(_old_record("r2", DataCategory.MEMORY, now))

        enforcer.enforce(log, now=now)

        assert len(log.records) == 0
        assert len(log.archived) == 2

    def test_archived_property_returns_copy(self) -> None:
        """archived Property gibt Kopie zurueck (nicht die interne Liste)."""
        log = DataProcessingLog()
        rec = DataProcessingRecord(record_id="r1")
        log._archived.append(rec)

        result = log.archived
        result.clear()
        assert len(log.archived) == 1


class TestCombinedActions:
    """Prueft dass DELETE + ANONYMIZE + ARCHIVE zusammen funktionieren."""

    def test_all_three_actions(self) -> None:
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="q",
                category=DataCategory.QUERY,
                retention_days=30,
                action=RetentionAction.DELETE,
            ),
            RetentionPolicy(
                name="conv",
                category=DataCategory.CONVERSATION,
                retention_days=30,
                action=RetentionAction.ANONYMIZE,
            ),
            RetentionPolicy(
                name="mem",
                category=DataCategory.MEMORY,
                retention_days=30,
                action=RetentionAction.ARCHIVE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.QUERY, now))
        log._records.append(_old_record("r2", DataCategory.CONVERSATION, now, user_id="secret"))
        log._records.append(_old_record("r3", DataCategory.MEMORY, now))

        counts = enforcer.enforce(log, now=now)

        assert counts == {"delete": 1, "anonymize": 1, "archive": 1}
        # DELETE: r1 entfernt
        assert all(r.record_id != "r1" for r in log.records)
        # ANONYMIZE: r2 noch da, aber anonymisiert
        r2 = [r for r in log.records if r.record_id == "r2"]
        assert len(r2) == 1
        assert r2[0].user_id == "ANONYMIZED"
        # ARCHIVE: r3 in archived
        assert len(log.archived) == 1
        assert log.archived[0].record_id == "r3"
        # Gesamt: nur r2 in records
        assert len(log.records) == 1

    def test_delete_regression(self) -> None:
        """DELETE funktioniert weiterhin wie bisher."""
        now = datetime(2026, 3, 5, tzinfo=UTC)
        enforcer = _make_enforcer(
            RetentionPolicy(
                name="q",
                category=DataCategory.QUERY,
                retention_days=30,
                action=RetentionAction.DELETE,
            ),
        )
        log = DataProcessingLog()
        log._records.append(_old_record("r1", DataCategory.QUERY, now))
        log._records.append(
            DataProcessingRecord(
                record_id="r2",
                timestamp=(now - timedelta(days=5)).isoformat(),
                category=DataCategory.QUERY,
            )
        )

        counts = enforcer.enforce(log, now=now)

        assert counts == {"delete": 1}
        assert len(log.records) == 1
        assert log.records[0].record_id == "r2"
        assert len(log.archived) == 0


class TestSourceLevelChecks:
    """Prueft den Source-Code auf die Fixes."""

    def test_enforce_handles_anonymize(self) -> None:
        source = inspect.getsource(RetentionEnforcer.enforce)
        assert "ANONYMIZE" in source
        assert "ANONYMIZED" in source

    def test_enforce_handles_archive(self) -> None:
        source = inspect.getsource(RetentionEnforcer.enforce)
        assert "ARCHIVE" in source
        assert "_archived" in source

    def test_enforce_clears_pii_fields(self) -> None:
        source = inspect.getsource(RetentionEnforcer.enforce)
        assert "user_id" in source
        assert "data_summary" in source
        assert "data_hash" in source

    def test_log_has_archived_list(self) -> None:
        source = inspect.getsource(DataProcessingLog.__init__)
        assert "_archived" in source
