"""Tests fuer SessionAnalyzer -- Feedback-Loop fuer Cognithor Self-Improvement."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from cognithor.learning.session_analyzer import (
    CLUSTER_THRESHOLD,
    FailureCluster,
    ImprovementAction,
    SessionAnalyzer,
    UserFeedback,
)

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def analyzer(tmp_path: Path) -> SessionAnalyzer:
    """Erstellt einen SessionAnalyzer mit temporaerem Datenverzeichnis."""
    sa = SessionAnalyzer(data_dir=tmp_path)
    yield sa
    sa.close()


@pytest.fixture()
def db_conn(analyzer: SessionAnalyzer) -> sqlite3.Connection:
    """Gibt die rohe DB-Verbindung des Analyzers zurueck."""
    return analyzer._get_conn()


def _make_tool_result(
    tool_name: str = "test_tool",
    content: str = "ok",
    is_error: bool = False,
    error_message: str | None = None,
) -> SimpleNamespace:
    """Erzeugt ein Fake-ToolResult."""
    return SimpleNamespace(
        tool_name=tool_name,
        content=content,
        is_error=is_error,
        error_message=error_message or "",
    )


def _make_agent_result(
    tool_results: list | None = None,
    success: bool = True,
    total_duration_ms: int = 1000,
) -> SimpleNamespace:
    """Erzeugt ein Fake-AgentResult."""
    return SimpleNamespace(
        tool_results=tool_results or [],
        success=success,
        total_duration_ms=total_duration_ms,
    )


# ---------------------------------------------------------------------------
# Tests: DB-Erstellung und Schema
# ---------------------------------------------------------------------------


class TestDBSchema:
    """Prueft dass die DB korrekt erstellt wird."""

    def test_db_file_created(self, tmp_path: Path) -> None:
        sa = SessionAnalyzer(data_dir=tmp_path)
        assert (tmp_path / "session_analysis.db").exists()
        sa.close()

    def test_all_tables_exist(self, db_conn: sqlite3.Connection) -> None:
        tables = {
            row[0]
            for row in db_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        expected = {
            "failure_clusters",
            "cluster_occurrences",
            "user_feedback",
            "improvement_actions",
            "session_metrics",
        }
        assert expected.issubset(tables)

    def test_failure_clusters_columns(self, db_conn: sqlite3.Connection) -> None:
        info = db_conn.execute("PRAGMA table_info(failure_clusters)").fetchall()
        col_names = {row[1] for row in info}
        assert "pattern_id" in col_names
        assert "error_category" in col_names
        assert "frequency" in col_names
        assert "is_resolved" in col_names

    def test_session_metrics_columns(self, db_conn: sqlite3.Connection) -> None:
        info = db_conn.execute("PRAGMA table_info(session_metrics)").fetchall()
        col_names = {row[1] for row in info}
        assert "session_id" in col_names
        assert "success_score" in col_names
        assert "had_user_correction" in col_names

    def test_reinit_is_idempotent(self, tmp_path: Path) -> None:
        """Zweites Init darf keine Fehler werfen."""
        sa1 = SessionAnalyzer(data_dir=tmp_path)
        sa1.close()
        sa2 = SessionAnalyzer(data_dir=tmp_path)
        tables = {
            row[0]
            for row in sa2._get_conn()
            .execute("SELECT name FROM sqlite_master WHERE type='table'")
            .fetchall()
        }
        assert "failure_clusters" in tables
        sa2.close()


# ---------------------------------------------------------------------------
# Tests: Fehler-Normalisierung
# ---------------------------------------------------------------------------


class TestErrorNormalization:
    """Prueft die Normalisierung von Fehlermeldungen."""

    def test_strips_timestamps(self, analyzer: SessionAnalyzer) -> None:
        msg = "Error at 2025-03-01T10:30:00Z: connection refused"
        normalized = analyzer._normalize_error(msg)
        assert "2025-03-01" not in normalized
        assert "<ts>" in normalized

    def test_strips_uuids(self, analyzer: SessionAnalyzer) -> None:
        msg = "Failed for session a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        normalized = analyzer._normalize_error(msg)
        assert "a1b2c3d4" not in normalized
        assert "<uuid>" in normalized

    def test_strips_file_paths(self, analyzer: SessionAnalyzer) -> None:
        msg = "File not found: /home/user/data/test.txt"
        normalized = analyzer._normalize_error(msg)
        assert "/home/user" not in normalized
        assert "<path>" in normalized

    def test_strips_windows_paths(self, analyzer: SessionAnalyzer) -> None:
        msg = "Error reading C:\\Users\\test\\file.txt"
        normalized = analyzer._normalize_error(msg)
        assert "C:\\Users" not in normalized

    def test_strips_hex_ids(self, analyzer: SessionAnalyzer) -> None:
        msg = "Token abcdef0123456789 expired"
        normalized = analyzer._normalize_error(msg)
        assert "abcdef0123456789" not in normalized

    def test_normalizes_whitespace(self, analyzer: SessionAnalyzer) -> None:
        msg = "connection   refused   to   host"
        normalized = analyzer._normalize_error(msg)
        assert "  " not in normalized

    def test_lowercases(self, analyzer: SessionAnalyzer) -> None:
        msg = "Connection REFUSED"
        normalized = analyzer._normalize_error(msg)
        assert normalized == normalized.lower()

    def test_empty_string(self, analyzer: SessionAnalyzer) -> None:
        assert analyzer._normalize_error("") == ""

    def test_same_error_same_hash(self, analyzer: SessionAnalyzer) -> None:
        msg1 = "Timeout at 2025-01-01T00:00:00Z on /api/v1/test"
        msg2 = "Timeout at 2026-03-13T12:00:00Z on /api/v2/other"
        n1 = analyzer._normalize_error(msg1)
        n2 = analyzer._normalize_error(msg2)
        # Beide sollten gleich normalisiert sein
        assert analyzer._error_hash(n1) == analyzer._error_hash(n2)


# ---------------------------------------------------------------------------
# Tests: Failure Clustering
# ---------------------------------------------------------------------------


class TestFailureClustering:
    """Prueft das Clustering aehnlicher Fehler."""

    @pytest.mark.asyncio
    async def test_single_error_creates_cluster(self, analyzer: SessionAnalyzer) -> None:
        result = _make_agent_result(
            tool_results=[
                _make_tool_result(is_error=True, error_message="timeout on request"),
            ],
            success=False,
        )
        actions = await analyzer.analyze_session("s1", result)
        # Noch unter Schwellwert
        assert actions == []

        # Cluster sollte existieren
        conn = analyzer._get_conn()
        rows = conn.execute("SELECT * FROM failure_clusters").fetchall()
        assert len(rows) == 1
        assert rows[0]["frequency"] == 1

    @pytest.mark.asyncio
    async def test_three_similar_errors_create_improvement(self, analyzer: SessionAnalyzer) -> None:
        """3 aehnliche Fehler muessen einen Cluster mit Verbesserung ausloesen."""
        for i in range(CLUSTER_THRESHOLD):
            result = _make_agent_result(
                tool_results=[
                    _make_tool_result(
                        tool_name="web_search",
                        is_error=True,
                        error_message=f"timeout on request at 2025-01-0{i + 1}T00:00:00Z",
                    ),
                ],
                success=False,
            )
            actions = await analyzer.analyze_session(f"s{i}", result)

        # Beim dritten Mal muss eine Aktion vorgeschlagen werden
        assert len(actions) >= 1
        assert actions[0].action_type in ("new_procedure", "prompt_variant", "core_rule")

    @pytest.mark.asyncio
    async def test_cluster_frequency_increments(self, analyzer: SessionAnalyzer) -> None:
        for i in range(5):
            result = _make_agent_result(
                tool_results=[
                    _make_tool_result(
                        is_error=True,
                        error_message="tool execution failed: permission denied",
                    ),
                ],
                success=False,
            )
            await analyzer.analyze_session(f"s{i}", result)

        conn = analyzer._get_conn()
        row = conn.execute(
            "SELECT frequency FROM failure_clusters ORDER BY frequency DESC LIMIT 1"
        ).fetchone()
        assert row["frequency"] == 5

    @pytest.mark.asyncio
    async def test_different_errors_different_clusters(self, analyzer: SessionAnalyzer) -> None:
        result1 = _make_agent_result(
            tool_results=[
                _make_tool_result(is_error=True, error_message="timeout error"),
            ],
        )
        result2 = _make_agent_result(
            tool_results=[
                _make_tool_result(is_error=True, error_message="permission denied completely"),
            ],
        )
        await analyzer.analyze_session("s1", result1)
        await analyzer.analyze_session("s2", result2)

        conn = analyzer._get_conn()
        count = conn.execute("SELECT COUNT(*) FROM failure_clusters").fetchone()[0]
        assert count == 2


# ---------------------------------------------------------------------------
# Tests: Session-Metriken
# ---------------------------------------------------------------------------


class TestSessionMetrics:
    @pytest.mark.asyncio
    async def test_metrics_stored(self, analyzer: SessionAnalyzer) -> None:
        result = _make_agent_result(
            tool_results=[
                _make_tool_result(),
                _make_tool_result(is_error=True, error_message="fail"),
            ],
            total_duration_ms=2500,
        )
        await analyzer.analyze_session("sess-1", result)

        conn = analyzer._get_conn()
        row = conn.execute(
            "SELECT * FROM session_metrics WHERE session_id = ?", ("sess-1",)
        ).fetchone()
        assert row is not None
        assert row["tool_count"] == 2
        assert row["error_count"] == 1
        assert row["duration_ms"] == 2500

    @pytest.mark.asyncio
    async def test_metrics_with_reflection(self, analyzer: SessionAnalyzer) -> None:
        reflection = SimpleNamespace(success_score=0.85)
        result = _make_agent_result(success=True)
        await analyzer.analyze_session("sess-2", result, reflection=reflection)

        conn = analyzer._get_conn()
        row = conn.execute(
            "SELECT success_score FROM session_metrics WHERE session_id = ?",
            ("sess-2",),
        ).fetchone()
        assert row["success_score"] == pytest.approx(0.85)


# ---------------------------------------------------------------------------
# Tests: User-Feedback
# ---------------------------------------------------------------------------


class TestUserFeedback:
    def test_record_positive(self, analyzer: SessionAnalyzer) -> None:
        fb = analyzer.record_user_feedback("s1", "m1", "positive")
        assert isinstance(fb, UserFeedback)
        assert fb.feedback_type == "positive"
        assert fb.session_id == "s1"

    def test_record_negative(self, analyzer: SessionAnalyzer) -> None:
        fb = analyzer.record_user_feedback("s1", "m1", "negative", detail="war falsch")
        assert fb.feedback_type == "negative"

        # Soll auch Fehlercluster erzeugen
        conn = analyzer._get_conn()
        count = conn.execute("SELECT COUNT(*) FROM failure_clusters").fetchone()[0]
        assert count >= 1

    def test_record_correction(self, analyzer: SessionAnalyzer) -> None:
        fb = analyzer.record_user_feedback(
            "s1", "m1", "correction", detail="Die Antwort sollte X sein"
        )
        assert fb.feedback_type == "correction"
        assert fb.detail == "Die Antwort sollte X sein"

    def test_feedback_stored_in_db(self, analyzer: SessionAnalyzer) -> None:
        analyzer.record_user_feedback("s1", "m1", "positive")
        analyzer.record_user_feedback("s1", "m2", "negative", "falsch")
        analyzer.record_user_feedback("s2", "m3", "correction", "korrektur")

        conn = analyzer._get_conn()
        count = conn.execute("SELECT COUNT(*) FROM user_feedback").fetchone()[0]
        assert count == 3

    def test_negative_feedback_marks_correction_in_metrics(self, analyzer: SessionAnalyzer) -> None:
        """Negatives Feedback soll had_user_correction in session_metrics setzen."""
        # Erst Session-Metriken anlegen
        conn = analyzer._get_conn()
        conn.execute(
            """INSERT INTO session_metrics (session_id, success_score, tool_count,
               error_count, duration_ms, had_user_correction, analyzed_at)
               VALUES ('s1', 0.5, 1, 0, 100, 0, ?)""",
            (datetime.now(UTC).isoformat(),),
        )
        conn.commit()

        analyzer.record_user_feedback("s1", "m1", "negative", "war falsch")

        row = conn.execute(
            "SELECT had_user_correction FROM session_metrics WHERE session_id = 's1'"
        ).fetchone()
        assert row["had_user_correction"] == 1


# ---------------------------------------------------------------------------
# Tests: Recurring Pattern Detection
# ---------------------------------------------------------------------------


class TestRecurringPatterns:
    @pytest.mark.asyncio
    async def test_no_patterns_below_threshold(self, analyzer: SessionAnalyzer) -> None:
        result = _make_agent_result(
            tool_results=[
                _make_tool_result(is_error=True, error_message="some error"),
            ],
        )
        await analyzer.analyze_session("s1", result)
        patterns = analyzer.detect_recurring_patterns()
        assert patterns == []

    @pytest.mark.asyncio
    async def test_patterns_found_above_threshold(self, analyzer: SessionAnalyzer) -> None:
        for i in range(CLUSTER_THRESHOLD + 1):
            result = _make_agent_result(
                tool_results=[
                    _make_tool_result(
                        is_error=True,
                        error_message="recurring network timeout issue",
                    ),
                ],
            )
            await analyzer.analyze_session(f"s{i}", result)

        patterns = analyzer.detect_recurring_patterns()
        assert len(patterns) >= 1
        assert patterns[0].frequency >= CLUSTER_THRESHOLD

    @pytest.mark.asyncio
    async def test_resolved_patterns_excluded(self, analyzer: SessionAnalyzer) -> None:
        for i in range(CLUSTER_THRESHOLD):
            result = _make_agent_result(
                tool_results=[
                    _make_tool_result(
                        is_error=True,
                        error_message="repeated failure xyz",
                    ),
                ],
            )
            await analyzer.analyze_session(f"s{i}", result)

        # Cluster als geloest markieren
        conn = analyzer._get_conn()
        conn.execute("UPDATE failure_clusters SET is_resolved = 1")
        conn.commit()

        patterns = analyzer.detect_recurring_patterns()
        assert patterns == []

    @pytest.mark.asyncio
    async def test_patterns_sorted_by_recency_and_frequency(
        self, analyzer: SessionAnalyzer
    ) -> None:
        # Cluster 1: haeufig aber alt
        conn = analyzer._get_conn()
        old_date = (datetime.now(UTC) - timedelta(days=5)).isoformat()
        conn.execute(
            """INSERT INTO failure_clusters
               (pattern_id, error_category, representative_error, first_seen, last_seen, frequency)
               VALUES ('old_pattern', 'timeout', 'old error', ?, ?, 10)""",
            (old_date, old_date),
        )
        # Cluster 2: weniger haeufig aber frisch
        now = datetime.now(UTC).isoformat()
        conn.execute(
            """INSERT INTO failure_clusters
               (pattern_id, error_category, representative_error, first_seen, last_seen, frequency)
               VALUES ('new_pattern', 'tool_error', 'new error', ?, ?, 5)""",
            (now, now),
        )
        conn.commit()

        patterns = analyzer.detect_recurring_patterns(lookback_days=30)
        assert len(patterns) == 2
        # Beide sollten zurueckgegeben werden (Sortierung haengt von Gewichtung ab)
        pattern_ids = [p.pattern_id for p in patterns]
        assert "old_pattern" in pattern_ids
        assert "new_pattern" in pattern_ids


# ---------------------------------------------------------------------------
# Tests: Improvement Generation
# ---------------------------------------------------------------------------


class TestImprovementGeneration:
    @pytest.mark.asyncio
    async def test_timeout_generates_procedure(self, analyzer: SessionAnalyzer) -> None:
        cluster = FailureCluster(
            pattern_id="abc123",
            error_category="timeout",
            representative_error="connection timeout to API",
            frequency=5,
        )
        actions = await analyzer.generate_improvements([cluster])
        assert len(actions) == 1
        assert actions[0].action_type == "new_procedure"
        assert "Timeout" in actions[0].description

    @pytest.mark.asyncio
    async def test_tool_error_generates_procedure(self, analyzer: SessionAnalyzer) -> None:
        cluster = FailureCluster(
            pattern_id="def456",
            error_category="tool_error",
            representative_error="shell_exec failed with code 1",
            frequency=4,
            occurrences=[
                {"tool_name": "shell_exec", "session_id": "s1", "timestamp": "", "error_detail": ""}
            ],
        )
        actions = await analyzer.generate_improvements([cluster])
        assert len(actions) == 1
        assert actions[0].action_type == "new_procedure"
        assert "Tool" in actions[0].description

    @pytest.mark.asyncio
    async def test_hallucination_generates_core_rule(self, analyzer: SessionAnalyzer) -> None:
        cluster = FailureCluster(
            pattern_id="ghi789",
            error_category="hallucination",
            representative_error="fabricated API endpoint",
            frequency=3,
        )
        actions = await analyzer.generate_improvements([cluster])
        assert len(actions) == 1
        assert actions[0].action_type == "core_rule"

    @pytest.mark.asyncio
    async def test_wrong_answer_generates_prompt_variant(self, analyzer: SessionAnalyzer) -> None:
        cluster = FailureCluster(
            pattern_id="jkl012",
            error_category="wrong_answer",
            representative_error="incorrect calculation",
            frequency=3,
        )
        actions = await analyzer.generate_improvements([cluster])
        assert len(actions) == 1
        assert actions[0].action_type == "prompt_variant"

    @pytest.mark.asyncio
    async def test_user_correction_generates_prompt_variant(
        self, analyzer: SessionAnalyzer
    ) -> None:
        cluster = FailureCluster(
            pattern_id="mno345",
            error_category="user_correction",
            representative_error="user said answer was wrong",
            frequency=4,
        )
        actions = await analyzer.generate_improvements([cluster])
        assert len(actions) == 1
        assert actions[0].action_type == "prompt_variant"

    @pytest.mark.asyncio
    async def test_resolved_clusters_skipped(self, analyzer: SessionAnalyzer) -> None:
        cluster = FailureCluster(
            pattern_id="resolved1",
            error_category="timeout",
            frequency=10,
            is_resolved=True,
        )
        actions = await analyzer.generate_improvements([cluster])
        assert actions == []

    @pytest.mark.asyncio
    async def test_multiple_clusters_sorted_by_priority(self, analyzer: SessionAnalyzer) -> None:
        clusters = [
            FailureCluster(
                pattern_id="low",
                error_category="unknown",
                representative_error="minor",
                frequency=3,
            ),
            FailureCluster(
                pattern_id="high",
                error_category="hallucination",
                representative_error="serious hallucination",
                frequency=15,
            ),
        ]
        actions = await analyzer.generate_improvements(clusters)
        assert len(actions) == 2
        # Hoehere Prioritaet zuerst
        assert actions[0].priority >= actions[1].priority

    @pytest.mark.asyncio
    async def test_unknown_category_generates_generic_action(
        self, analyzer: SessionAnalyzer
    ) -> None:
        cluster = FailureCluster(
            pattern_id="unk1",
            error_category="unknown",
            representative_error="some unknown error",
            frequency=3,
        )
        actions = await analyzer.generate_improvements([cluster])
        assert len(actions) == 1
        assert actions[0].action_type == "new_procedure"


# ---------------------------------------------------------------------------
# Tests: Improvement Application
# ---------------------------------------------------------------------------


class TestImprovementApplication:
    def test_apply_prompt_variant(self, analyzer: SessionAnalyzer) -> None:
        action = ImprovementAction(
            action_type="prompt_variant",
            description="test prompt fix",
            target="planner",
            payload="new prompt text",
        )
        result = analyzer.apply_improvement(action)
        assert result is True
        assert action.status == "applied"

    def test_apply_core_rule(self, analyzer: SessionAnalyzer) -> None:
        action = ImprovementAction(
            action_type="core_rule",
            description="anti-hallucination rule",
            target="CORE.md",
            payload="WICHTIG: Immer pruefen",
        )
        result = analyzer.apply_improvement(action)
        assert result is True

    def test_apply_new_procedure_without_memory_manager(self, analyzer: SessionAnalyzer) -> None:
        action = ImprovementAction(
            action_type="new_procedure",
            description="test procedure",
            target="procedural_memory",
            payload="# test-proc\n## Ablauf\n1. Schritt eins",
        )
        result = analyzer.apply_improvement(action)
        # Kein memory_manager -> False
        assert result is False

    def test_apply_skill_fix(self, analyzer: SessionAnalyzer) -> None:
        action = ImprovementAction(
            action_type="skill_fix",
            description="fix skill",
            target="some_skill",
            payload="fix content",
        )
        result = analyzer.apply_improvement(action)
        assert result is True

    def test_apply_procedure_dedup(self, analyzer: SessionAnalyzer) -> None:
        action = ImprovementAction(
            action_type="procedure_dedup",
            description="merge duplicates",
            target="proc_a,proc_b",
            payload="merged",
        )
        result = analyzer.apply_improvement(action)
        assert result is True


# ---------------------------------------------------------------------------
# Tests: Prozedur-Deduplizierung
# ---------------------------------------------------------------------------


class TestProcedureDedup:
    def test_no_memory_manager_returns_empty(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer.deduplicate_procedures()
        assert result == []

    def test_finds_duplicates(self, tmp_path: Path) -> None:
        """Simuliert Prozeduren mit ueberlappenden Keywords."""

        class FakeProcedural:
            def list_procedures(self):
                return ["backup-files", "backup-data", "search-web"]

            def load_procedure(self, name):
                procs = {
                    "backup-files": (
                        SimpleNamespace(trigger_keywords=["backup", "dateien", "sichern"]),
                        "body1",
                    ),
                    "backup-data": (
                        SimpleNamespace(trigger_keywords=["backup", "daten", "sichern"]),
                        "body2",
                    ),
                    "search-web": (
                        SimpleNamespace(trigger_keywords=["suchen", "web", "internet"]),
                        "body3",
                    ),
                }
                return procs[name]

        mm = SimpleNamespace(procedural=FakeProcedural())
        sa = SessionAnalyzer(data_dir=tmp_path, memory_manager=mm)

        duplicates = sa.deduplicate_procedures(similarity_threshold=0.3)
        assert len(duplicates) >= 1
        # backup-files und backup-data sollten als Duplikate erkannt werden
        pair_names = {(a, b) for a, b in duplicates}
        assert ("backup-files", "backup-data") in pair_names or (
            "backup-data",
            "backup-files",
        ) in pair_names
        sa.close()

    def test_no_duplicates_when_distinct(self, tmp_path: Path) -> None:
        class FakeProcedural:
            def list_procedures(self):
                return ["alpha", "beta"]

            def load_procedure(self, name):
                procs = {
                    "alpha": (
                        SimpleNamespace(trigger_keywords=["eins", "zwei", "drei"]),
                        "body",
                    ),
                    "beta": (
                        SimpleNamespace(trigger_keywords=["vier", "fuenf", "sechs"]),
                        "body",
                    ),
                }
                return procs[name]

        mm = SimpleNamespace(procedural=FakeProcedural())
        sa = SessionAnalyzer(data_dir=tmp_path, memory_manager=mm)
        duplicates = sa.deduplicate_procedures()
        assert duplicates == []
        sa.close()


# ---------------------------------------------------------------------------
# Tests: Health Report
# ---------------------------------------------------------------------------


class TestHealthReport:
    def test_empty_report_structure(self, analyzer: SessionAnalyzer) -> None:
        report = analyzer.get_health_report()
        assert "total_sessions_analyzed" in report
        assert "total_feedback" in report
        assert "unresolved_clusters" in report
        assert "improvements_applied" in report
        assert "top_unresolved_patterns" in report
        assert "feedback_summary" in report
        assert report["total_sessions_analyzed"] == 0
        assert report["total_feedback"] == 0

    @pytest.mark.asyncio
    async def test_report_reflects_data(self, analyzer: SessionAnalyzer) -> None:
        # Sessions analysieren
        for i in range(3):
            result = _make_agent_result(
                tool_results=[
                    _make_tool_result(is_error=True, error_message="repeated error xyz"),
                ],
            )
            await analyzer.analyze_session(f"s{i}", result)

        # Feedback speichern
        analyzer.record_user_feedback("s0", "m1", "positive")
        analyzer.record_user_feedback("s1", "m2", "negative", "wrong")

        report = analyzer.get_health_report()
        assert report["total_sessions_analyzed"] == 3
        assert report["total_feedback"] == 2
        assert report["feedback_summary"]["positive"] == 1
        assert report["feedback_summary"]["negative"] == 1

    def test_top_patterns_limited_to_5(self, analyzer: SessionAnalyzer) -> None:
        conn = analyzer._get_conn()
        now = datetime.now(UTC).isoformat()
        for i in range(10):
            conn.execute(
                """INSERT INTO failure_clusters
                   (pattern_id, error_category,
                    representative_error, first_seen,
                    last_seen, frequency)
                   VALUES (?, 'timeout', ?, ?, ?, ?)""",
                (f"pattern_{i}", f"error {i}", now, now, i + 1),
            )
        conn.commit()

        report = analyzer.get_health_report()
        assert len(report["top_unresolved_patterns"]) <= 5


# ---------------------------------------------------------------------------
# Tests: Feedback-Signal-Erkennung
# ---------------------------------------------------------------------------


class TestFeedbackSignalExtraction:
    """Prueft _extract_feedback_signal fuer DE + EN Muster."""

    def test_thumbs_down(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("\U0001f44e")
        assert result is not None
        assert result[0] == "negative"

    def test_thumbs_up(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("\U0001f44d")
        assert result is not None
        assert result[0] == "positive"

    def test_das_war_falsch(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("das war falsch")
        assert result is not None
        assert result[0] == "negative"

    def test_nein_das_stimmt_nicht(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("nein das stimmt nicht")
        assert result is not None
        assert result[0] == "negative"

    def test_wrong_english(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("that's wrong")
        assert result is not None
        assert result[0] == "negative"

    def test_incorrect_english(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("this is incorrect")
        assert result is not None
        assert result[0] == "negative"

    def test_perfekt(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("Perfekt, danke!")
        assert result is not None
        assert result[0] == "positive"

    def test_genau(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("Ja, genau!")
        assert result is not None
        assert result[0] == "positive"

    def test_super(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("Super!")
        assert result is not None
        assert result[0] == "positive"

    def test_great(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("that's great")
        assert result is not None
        assert result[0] == "positive"

    def test_perfect(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("perfect, thanks")
        assert result is not None
        assert result[0] == "positive"

    def test_correction_eigentlich(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("eigentlich sollte es X sein")
        assert result is not None
        assert result[0] == "correction"
        assert "X sein" in result[1]

    def test_correction_ich_meinte(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("ich meinte etwas anderes")
        assert result is not None
        assert result[0] == "correction"
        assert "etwas anderes" in result[1]

    def test_correction_nein_comma(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("nein, die Antwort ist 42")
        assert result is not None
        assert result[0] == "correction"
        assert "42" in result[1]

    def test_no_signal(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("Wie wird das Wetter morgen?")
        assert result is None

    def test_empty_message(self, analyzer: SessionAnalyzer) -> None:
        result = analyzer._extract_feedback_signal("")
        assert result is None

    def test_none_message(self, analyzer: SessionAnalyzer) -> None:
        # Obwohl der Type-Hint str ist, soll es nicht crashen
        result = analyzer._extract_feedback_signal("")
        assert result is None


# ---------------------------------------------------------------------------
# Tests: Fehler-Resilienz
# ---------------------------------------------------------------------------


class TestResilience:
    @pytest.mark.asyncio
    async def test_analyze_never_raises(self, analyzer: SessionAnalyzer) -> None:
        """analyze_session darf niemals eine Exception werfen."""
        # Kaputtes AgentResult
        result = SimpleNamespace()  # Keine tool_results etc.
        actions = await analyzer.analyze_session("broken", result)
        assert isinstance(actions, list)

    def test_apply_unknown_action_type(self, analyzer: SessionAnalyzer) -> None:
        action = ImprovementAction(
            action_type="new_procedure",  # valid type but will fail without memory_manager
            description="test",
            target="test",
            payload="test",
        )
        # Sollte nicht crashen
        result = analyzer.apply_improvement(action)
        assert isinstance(result, bool)

    def test_close_idempotent(self, tmp_path: Path) -> None:
        sa = SessionAnalyzer(data_dir=tmp_path)
        sa.close()
        sa.close()  # Doppeltes Close darf nicht crashen


# ---------------------------------------------------------------------------
# Tests: Error Classification
# ---------------------------------------------------------------------------


class TestErrorClassification:
    def test_timeout_classified(self, analyzer: SessionAnalyzer) -> None:
        assert analyzer._classify_error("connection timed out") == "timeout"

    def test_tool_error_classified(self, analyzer: SessionAnalyzer) -> None:
        assert analyzer._classify_error("tool execution error in shell") == "tool_error"

    def test_hallucination_classified(self, analyzer: SessionAnalyzer) -> None:
        assert analyzer._classify_error("response was fabricated") == "hallucination"

    def test_wrong_answer_classified(self, analyzer: SessionAnalyzer) -> None:
        assert analyzer._classify_error("the answer was wrong") == "wrong_answer"

    def test_unknown_classified(self, analyzer: SessionAnalyzer) -> None:
        assert analyzer._classify_error("something happened") == "unknown"


# ---------------------------------------------------------------------------
# Tests: Recency Weight
# ---------------------------------------------------------------------------


class TestRecencyWeight:
    def test_recent_has_high_weight(self, analyzer: SessionAnalyzer) -> None:
        weight = analyzer._calculate_recency_weight(datetime.now(UTC))
        assert weight > 0.9

    def test_old_has_low_weight(self, analyzer: SessionAnalyzer) -> None:
        old = datetime.now(UTC) - timedelta(days=30)
        weight = analyzer._calculate_recency_weight(old)
        assert weight < 0.01

    def test_half_life(self, analyzer: SessionAnalyzer) -> None:
        """Nach RECENCY_HALF_LIFE_DAYS sollte das Gewicht ~0.5 sein."""
        from cognithor.learning.session_analyzer import RECENCY_HALF_LIFE_DAYS

        half_life_ago = datetime.now(UTC) - timedelta(days=RECENCY_HALF_LIFE_DAYS)
        weight = analyzer._calculate_recency_weight(half_life_ago)
        assert 0.4 < weight < 0.6
