"""Tests for Evolution Phase 5 -- Autonomous Deep Learning.

Covers: AutonomousLearner, EvolutionRAG, EvolutionScheduler, MetaLearner,
and all Phase 5 data models.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

# ---------------------------------------------------------------------------
# Autonomous Learner
# ---------------------------------------------------------------------------
from cognithor.evolution.autonomous_learner import (
    AutonomousLearner,
    GapSource,
    ImprovementProposal,
    Insight,
    KnowledgeGap,
    LearningOutcome,
    LearningTask,
    ProposalType,
    TaskPriority,
)
from cognithor.evolution.cron_scheduler import (
    EvolutionScheduler,
    ScheduledTask,
    _cron_field_matches,
    _cron_matches,
)
from cognithor.evolution.meta_learner import (
    MetaAnalysis,
    MetaLearner,
    StrategyAdjustment,
)
from cognithor.evolution.rag_pipeline import (
    EvolutionRAG,
    RAGChunk,
    RAGDocument,
    RAGResult,
    _chunk_paragraphs,
)

# ===================================================================
# Data model serialisation tests
# ===================================================================


class TestKnowledgeGapModel:
    def test_roundtrip(self):
        gap = KnowledgeGap(
            topic="Python asyncio",
            description="User fragt haeufig nach async patterns",
            source=GapSource.USER_INTERACTION,
            confidence=0.7,
        )
        d = gap.to_dict()
        restored = KnowledgeGap.from_dict(d)
        assert restored.topic == gap.topic
        assert restored.source == GapSource.USER_INTERACTION
        assert restored.confidence == 0.7

    def test_defaults(self):
        gap = KnowledgeGap(topic="test", description="d")
        assert gap.source == GapSource.USER_INTERACTION
        assert gap.confidence == 0.0
        assert len(gap.id) == 16


class TestLearningTaskModel:
    def test_roundtrip(self):
        task = LearningTask(
            gap_id="abc123",
            query="Wie funktioniert asyncio?",
            priority=TaskPriority.HIGH,
        )
        d = task.to_dict()
        restored = LearningTask.from_dict(d)
        assert restored.gap_id == "abc123"
        assert restored.priority == TaskPriority.HIGH
        assert restored.status == "pending"


class TestLearningOutcomeModel:
    def test_roundtrip(self):
        outcome = LearningOutcome(
            task_id="t1",
            summary="Gelernt: asyncio event loop basics",
            sources=["https://docs.python.org"],
            confidence=0.8,
            chunks_created=5,
        )
        d = outcome.to_dict()
        restored = LearningOutcome.from_dict(d)
        assert restored.task_id == "t1"
        assert restored.confidence == 0.8
        assert len(restored.sources) == 1


class TestInsightModel:
    def test_roundtrip(self):
        insight = Insight(
            title="Async patterns",
            description="Mehrere Lernaufgaben zeigen Wissensbedarf",
            supporting_outcomes=["o1", "o2"],
            actionable=True,
        )
        d = insight.to_dict()
        restored = Insight.from_dict(d)
        assert restored.actionable is True
        assert len(restored.supporting_outcomes) == 2


class TestImprovementProposalModel:
    def test_roundtrip(self):
        p = ImprovementProposal(
            title="Neuer Skill: Async Helper",
            proposal_type=ProposalType.NEW_SKILL,
            description="Ein Skill fuer async code patterns",
            estimated_impact=0.8,
        )
        d = p.to_dict()
        restored = ImprovementProposal.from_dict(d)
        assert restored.proposal_type == ProposalType.NEW_SKILL
        assert restored.estimated_impact == 0.8


class TestRAGModels:
    def test_rag_document_roundtrip(self):
        doc = RAGDocument(title="Test", source="/tmp/test.txt", content="hello world")
        d = doc.to_dict()
        restored = RAGDocument.from_dict(d)
        assert restored.title == "Test"

    def test_rag_chunk_roundtrip(self):
        chunk = RAGChunk(document_id="d1", text="some text", chunk_index=2)
        d = chunk.to_dict()
        restored = RAGChunk.from_dict(d)
        assert restored.chunk_index == 2

    def test_rag_result_roundtrip(self):
        r = RAGResult(
            chunk_id="c1",
            document_id="d1",
            text="result text",
            score=0.85,
            title="Doc",
            source="/tmp/x",
        )
        d = r.to_dict()
        restored = RAGResult.from_dict(d)
        assert restored.score == 0.85


class TestScheduledTaskModel:
    def test_roundtrip(self):
        t = ScheduledTask(
            name="daily_scan",
            description="Taeglicher Web-Scan",
            cron_expression="0 8 * * *",
            action="scan",
        )
        d = t.to_dict()
        restored = ScheduledTask.from_dict(d)
        assert restored.name == "daily_scan"
        assert restored.cron_expression == "0 8 * * *"


class TestMetaAnalysisModel:
    def test_roundtrip(self):
        adj = StrategyAdjustment(
            parameter="depth",
            current_value=5.0,
            recommended_value=8.0,
            reason="Low quality",
        )
        ma = MetaAnalysis(
            total_cycles=10,
            avg_quality_score=0.65,
            avg_coverage_score=0.72,
            best_strategy="deep_research",
            worst_strategy="broad_scan",
            efficiency_score=0.55,
            trend="improving",
            adjustments=[adj],
        )
        d = ma.to_dict()
        restored = MetaAnalysis.from_dict(d)
        assert restored.total_cycles == 10
        assert restored.trend == "improving"
        assert len(restored.adjustments) == 1
        assert restored.adjustments[0].parameter == "depth"


# ===================================================================
# AutonomousLearner tests
# ===================================================================


class TestAutonomousLearnerGaps:
    async def test_no_gaps_below_min_interactions(self):
        learner = AutonomousLearner()
        gaps = await learner.identify_knowledge_gaps([{"message": "hi"}])
        assert gaps == []

    async def test_identifies_failed_query_gaps(self):
        learner = AutonomousLearner()
        interactions = [
            {"message": "was ist kubernetes?", "success": False, "topic": "kubernetes"},
            {"message": "erklaere docker", "success": True, "topic": "docker"},
            {"message": "wie geht das?", "success": True, "topic": ""},
        ]
        gaps = await learner.identify_knowledge_gaps(interactions)
        assert len(gaps) >= 1
        failed = [g for g in gaps if g.source == GapSource.FAILED_QUERY]
        assert len(failed) == 1
        assert "kubernetes" in failed[0].topic

    async def test_identifies_uncertainty_keyword_gaps(self):
        learner = AutonomousLearner()
        interactions = [
            {"message": "was ist eine closure?", "success": True, "topic": "closures"},
            {"message": "wie funktioniert GC?", "success": True, "topic": "gc"},
            {"message": "erklaere mir monads", "success": True, "topic": "monads"},
        ]
        gaps = await learner.identify_knowledge_gaps(interactions)
        assert len(gaps) >= 2  # uncertainty keywords detected

    async def test_frequent_topic_gap(self):
        learner = AutonomousLearner()
        interactions = [
            {"message": "msg1", "topic": "rust"},
            {"message": "msg2", "topic": "rust"},
            {"message": "msg3", "topic": "rust"},
        ]
        gaps = await learner.identify_knowledge_gaps(interactions)
        domain_gaps = [g for g in gaps if g.source == GapSource.MISSING_DOMAIN]
        assert len(domain_gaps) >= 1
        assert domain_gaps[0].topic == "rust"


class TestAutonomousLearnerPrioritize:
    async def test_prioritize_orders_by_priority(self):
        learner = AutonomousLearner()
        gaps = [
            KnowledgeGap(
                topic="low", description="d", source=GapSource.USER_INTERACTION, confidence=0.2
            ),
            KnowledgeGap(
                topic="high", description="d", source=GapSource.FAILED_QUERY, confidence=0.9
            ),
        ]
        tasks = await learner.prioritize_learning(gaps)
        assert len(tasks) == 2
        # Failed query should come first (HIGH priority)
        assert tasks[0].priority == TaskPriority.HIGH


class TestAutonomousLearnerExecute:
    async def test_execute_without_deep_learner(self):
        learner = AutonomousLearner()
        task = LearningTask(gap_id="g1", query="test query")
        outcome = await learner.execute_learning_task(task)
        assert outcome.task_id == task.id
        assert task.status == "completed"
        assert outcome.confidence == 0.2  # no deep learner fallback

    async def test_execute_with_deep_learner(self):
        mock_plan = AsyncMock()
        mock_plan.goal = "test"
        mock_plan.sub_goals = []
        mock_plan.sources = []
        mock_plan.total_chunks_indexed = 3

        mock_dl = AsyncMock()
        mock_dl.create_plan = AsyncMock(return_value=mock_plan)

        learner = AutonomousLearner(deep_learner=mock_dl)
        task = LearningTask(gap_id="g1", query="test query")
        outcome = await learner.execute_learning_task(task)
        assert outcome.confidence == 0.6
        assert outcome.chunks_created == 3


class TestAutonomousLearnerSynthesize:
    async def test_synthesize_empty(self):
        learner = AutonomousLearner()
        insights = await learner.synthesize_knowledge([])
        assert insights == []

    async def test_synthesize_produces_insights(self):
        learner = AutonomousLearner()
        outcomes = [
            LearningOutcome(
                task_id="t1",
                summary="Gelernt ueber Python asyncio event loops",
                confidence=0.7,
                chunks_created=5,
            ),
            LearningOutcome(
                task_id="t2",
                summary="Gelernt ueber Python asyncio coroutines",
                confidence=0.8,
                chunks_created=3,
            ),
        ]
        insights = await learner.synthesize_knowledge(outcomes)
        assert len(insights) >= 1
        # At least one should be actionable (confidence > 0.5 and chunks > 0)
        actionable = [i for i in insights if i.actionable]
        assert len(actionable) >= 1


class TestAutonomousLearnerProposals:
    async def test_propose_improvements(self):
        learner = AutonomousLearner()
        insights = [
            Insight(
                title="Python Wissen",
                description="2 Lernaufgaben. Konfidenz: 70.0%. 8 Chunks erstellt aus 3 Quellen.",
                actionable=True,
                supporting_outcomes=["o1"],
            ),
        ]
        proposals = await learner.propose_improvements(insights)
        assert len(proposals) >= 1
        assert proposals[0].status == "proposed"

    async def test_no_proposals_for_non_actionable(self):
        learner = AutonomousLearner()
        insights = [
            Insight(title="X", description="d", actionable=False),
        ]
        proposals = await learner.propose_improvements(insights)
        assert proposals == []


# ===================================================================
# EvolutionRAG tests
# ===================================================================


class TestEvolutionRAG:
    @pytest.fixture()
    def rag(self, tmp_path):
        db = tmp_path / "test_rag.db"
        return EvolutionRAG(db_path=db)

    async def test_ingest_and_query(self, rag, tmp_path):
        # Create a test file
        f = tmp_path / "doc.txt"
        f.write_text(
            "Python ist eine Programmiersprache.\n\n"
            "Sie wird haeufig fuer Data Science verwendet.\n\n"
            "Asyncio ermoeglicht asynchrone Programmierung.",
            encoding="utf-8",
        )
        doc = await rag.ingest_document(str(f))
        assert doc.title == "doc.txt"
        assert rag.document_count() == 1
        assert rag.chunk_count() >= 1

        results = await rag.query("Python Programmiersprache")
        assert len(results) >= 1
        assert results[0].score > 0

    async def test_ingest_with_metadata_content(self, rag):
        doc = await rag.ingest_document(
            "https://example.com/article",
            metadata={
                "content": "Kubernetes orchestriert Container in Clustern.",
                "title": "K8s Intro",
            },
        )
        assert doc.title == "K8s Intro"
        assert rag.document_count() == 1

    async def test_query_no_results(self, rag):
        results = await rag.query("xyznonexistent")
        assert results == []

    async def test_get_context_for_task(self, rag, tmp_path):
        f = tmp_path / "ctx.txt"
        f.write_text(
            "Docker Container werden isoliert ausgefuehrt.\n\n"
            "Images sind die Basis fuer Container.",
            encoding="utf-8",
        )
        await rag.ingest_document(str(f))
        task = LearningTask(gap_id="g1", query="Docker Container")
        ctx = await rag.get_context_for_task(task)
        assert "Docker" in ctx or "Container" in ctx


class TestChunkParagraphs:
    def test_single_paragraph(self):
        chunks = _chunk_paragraphs("Hello world, this is a test.")
        assert len(chunks) == 1

    def test_multiple_paragraphs(self):
        text = "Para one with enough text.\n\nPara two with enough text.\n\nPara three with text."
        chunks = _chunk_paragraphs(text)
        assert len(chunks) >= 1


# ===================================================================
# EvolutionScheduler tests
# ===================================================================


class TestCronFieldMatching:
    def test_wildcard(self):
        assert _cron_field_matches("*", 5) is True

    def test_exact(self):
        assert _cron_field_matches("5", 5) is True
        assert _cron_field_matches("5", 6) is False

    def test_range(self):
        assert _cron_field_matches("1-5", 3) is True
        assert _cron_field_matches("1-5", 6) is False

    def test_step(self):
        assert _cron_field_matches("*/10", 20) is True
        assert _cron_field_matches("*/10", 23) is False

    def test_comma(self):
        assert _cron_field_matches("1,3,5", 3) is True
        assert _cron_field_matches("1,3,5", 4) is False


class TestCronMatches:
    def test_every_minute(self):
        dt = datetime(2026, 4, 8, 10, 30, tzinfo=UTC)
        assert _cron_matches("* * * * *", dt) is True

    def test_specific_time(self):
        dt = datetime(2026, 4, 8, 8, 0, tzinfo=UTC)
        assert _cron_matches("0 8 * * *", dt) is True
        assert _cron_matches("0 9 * * *", dt) is False


class TestEvolutionScheduler:
    @pytest.fixture()
    def scheduler(self, tmp_path):
        return EvolutionScheduler(schedule_path=tmp_path / "schedule.json")

    def test_schedule_and_list(self, scheduler):
        task = ScheduledTask(
            name="test_task",
            description="A test",
            cron_expression="0 8 * * *",
        )
        scheduler.schedule_task(task)
        tasks = scheduler.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].name == "test_task"

    def test_get_due_tasks(self, scheduler):
        task = ScheduledTask(
            name="due_task",
            description="Should be due",
            cron_expression="30 10 * * *",
        )
        scheduler.schedule_task(task)

        # Match
        dt = datetime(2026, 4, 8, 10, 30, tzinfo=UTC)
        due = scheduler.get_due_tasks(now=dt)
        assert len(due) == 1

        # No match
        dt2 = datetime(2026, 4, 8, 10, 31, tzinfo=UTC)
        due2 = scheduler.get_due_tasks(now=dt2)
        assert len(due2) == 0

    def test_mark_completed(self, scheduler):
        task = ScheduledTask(
            name="complete_me",
            description="d",
            cron_expression="* * * * *",
        )
        scheduler.schedule_task(task)
        assert scheduler.mark_completed(task.id) is True
        assert scheduler.get_task(task.id).run_count == 1

    def test_remove_task(self, scheduler):
        task = ScheduledTask(name="rm", description="d", cron_expression="* * * * *")
        scheduler.schedule_task(task)
        assert scheduler.remove_task(task.id) is True
        assert scheduler.list_tasks() == []
        assert scheduler.remove_task("nonexistent") is False

    def test_persistence(self, tmp_path):
        path = tmp_path / "sched.json"
        s1 = EvolutionScheduler(schedule_path=path)
        task = ScheduledTask(name="persist", description="d", cron_expression="0 0 * * *")
        s1.schedule_task(task)

        # Reload
        s2 = EvolutionScheduler(schedule_path=path)
        assert len(s2.list_tasks()) == 1
        assert s2.list_tasks()[0].name == "persist"

    def test_disabled_task_not_due(self, scheduler):
        task = ScheduledTask(
            name="disabled",
            description="d",
            cron_expression="* * * * *",
            enabled=False,
        )
        scheduler.schedule_task(task)
        due = scheduler.get_due_tasks(now=datetime(2026, 4, 8, 10, 30, tzinfo=UTC))
        assert len(due) == 0


# ===================================================================
# MetaLearner tests
# ===================================================================


class TestMetaLearner:
    async def test_analyze_empty(self):
        ml = MetaLearner()
        result = await ml.analyze_cycle_history([])
        assert result.total_cycles == 0
        assert result.efficiency_score == 0.0

    async def test_analyze_basic_cycles(self):
        ml = MetaLearner()
        cycles = [
            {
                "quality_score": 0.7,
                "coverage_score": 0.8,
                "sources_fetched": 10,
                "chunks_created": 40,
                "research_rounds": 3,
            },
            {
                "quality_score": 0.6,
                "coverage_score": 0.7,
                "sources_fetched": 8,
                "chunks_created": 30,
                "research_rounds": 2,
            },
        ]
        result = await ml.analyze_cycle_history(cycles)
        assert result.total_cycles == 2
        assert result.avg_quality_score > 0
        assert result.trend in ("improving", "stable", "declining")

    async def test_trend_detection_improving(self):
        ml = MetaLearner()
        base = {"sources_fetched": 5, "chunks_created": 10}
        cycles = [
            {"quality_score": 0.3, "coverage_score": 0.3, **base},
            {"quality_score": 0.35, "coverage_score": 0.35, **base},
            {"quality_score": 0.6, "coverage_score": 0.6, **base},
            {"quality_score": 0.8, "coverage_score": 0.8, **base},
        ]
        result = await ml.analyze_cycle_history(cycles)
        assert result.trend == "improving"

    async def test_low_quality_generates_adjustments(self):
        ml = MetaLearner()
        cycles = [
            {
                "quality_score": 0.2,
                "coverage_score": 0.2,
                "sources_fetched": 3,
                "chunks_created": 5,
            },
            {
                "quality_score": 0.3,
                "coverage_score": 0.3,
                "sources_fetched": 4,
                "chunks_created": 8,
            },
        ]
        result = await ml.analyze_cycle_history(cycles)
        assert len(result.adjustments) >= 1
        params = [a.parameter for a in result.adjustments]
        assert "research_depth" in params or "source_count" in params

    async def test_get_learning_efficiency(self):
        ml = MetaLearner()
        eff = await ml.get_learning_efficiency()
        assert eff == 0.0

        await ml.analyze_cycle_history(
            [
                {
                    "quality_score": 0.8,
                    "coverage_score": 0.9,
                    "sources_fetched": 5,
                    "chunks_created": 20,
                },
            ]
        )
        eff = await ml.get_learning_efficiency()
        assert eff > 0

    async def test_recommend_strategy_adjustments(self):
        ml = MetaLearner()
        adj = await ml.recommend_strategy_adjustments()
        assert adj == []

        await ml.analyze_cycle_history(
            [
                {
                    "quality_score": 0.2,
                    "coverage_score": 0.2,
                    "sources_fetched": 3,
                    "chunks_created": 5,
                },
            ]
        )
        adj = await ml.recommend_strategy_adjustments()
        assert len(adj) >= 1


class TestStrategyAdjustmentModel:
    def test_roundtrip(self):
        a = StrategyAdjustment(
            parameter="depth",
            current_value=5.0,
            recommended_value=10.0,
            reason="Quality too low",
        )
        d = a.to_dict()
        restored = StrategyAdjustment.from_dict(d)
        assert restored.parameter == "depth"
        assert restored.recommended_value == 10.0
