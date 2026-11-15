# Evolution Engine Phase 5A — Data Model + StrategyPlanner

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Given a high-level learning goal, the LLM decomposes it into a structured `LearningPlan` with SubGoals, Sources, and Schedules — persisted to disk and visible via REST API.

**Architecture:** New `evolution/models.py` defines all dataclasses (LearningPlan, SubGoal, SourceSpec, etc.). New `evolution/strategy_planner.py` sends a structured prompt to the LLM and parses the JSON response into a LearningPlan. New `evolution/deep_learner.py` orchestrates the pipeline (Phase 5A only wires StrategyPlanner). The EvolutionLoop scout delegates complex goals to the DeepLearner. REST endpoints expose plan CRUD.

**Tech Stack:** Python 3.12+ (dataclasses, json, pathlib, asyncio), Pydantic (config), pytest

**Spec:** `docs/superpowers/specs/2026-03-28-evolution-phase5-deep-autonomous-learning.md`

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/jarvis/evolution/models.py` | All Phase 5 dataclasses: LearningPlan, SubGoal, SourceSpec, ScheduleSpec, SeedSource, QualityQuestion |
| Create | `src/jarvis/evolution/strategy_planner.py` | StrategyPlanner: goal → LLM prompt → parse JSON → LearningPlan |
| Create | `src/jarvis/evolution/deep_learner.py` | DeepLearner orchestrator (Phase 5A: only StrategyPlanner + persistence) |
| Modify | `src/jarvis/evolution/loop.py` | Scout detects complex goals → delegates to DeepLearner |
| Modify | `src/jarvis/evolution/__init__.py` | Export new classes |
| Modify | `src/jarvis/config.py` | Add Phase 5 fields to EvolutionConfig |
| Modify | `src/jarvis/gateway/gateway.py` | Wire DeepLearner into gateway |
| Modify | `src/jarvis/channels/config_routes.py` | REST: GET/POST/PATCH /evolution/plans |
| Create | `tests/unit/test_evolution_models.py` | Tests for dataclasses |
| Create | `tests/unit/test_strategy_planner.py` | Tests for StrategyPlanner |
| Create | `tests/unit/test_deep_learner.py` | Tests for DeepLearner |

---

### Task 1: Data Model — All Dataclasses

**Files:**
- Create: `src/jarvis/evolution/models.py`
- Create: `tests/unit/test_evolution_models.py`

- [ ] **Step 1: Write tests for LearningPlan and SubGoal**

```python
# tests/unit/test_evolution_models.py
"""Tests fuer Evolution Phase 5 Datenmodell."""

from __future__ import annotations

import json

import pytest

from jarvis.evolution.models import (
    LearningPlan,
    QualityQuestion,
    ScheduleSpec,
    SeedSource,
    SourceSpec,
    SubGoal,
)


class TestSubGoal:
    def test_create_minimal(self):
        sg = SubGoal(id="sg-1", title="VVG Grundlagen", description="Lerne VVG")
        assert sg.status == "pending"
        assert sg.priority == 0
        assert sg.chunks_created == 0

    def test_to_dict_roundtrip(self):
        sg = SubGoal(
            id="sg-1",
            title="VVG",
            description="test",
            status="researching",
            sources_fetched=["https://example.com"],
            chunks_created=42,
        )
        d = sg.to_dict()
        sg2 = SubGoal.from_dict(d)
        assert sg2.id == "sg-1"
        assert sg2.chunks_created == 42
        assert sg2.sources_fetched == ["https://example.com"]


class TestSourceSpec:
    def test_create(self):
        s = SourceSpec(
            url="https://gesetze-im-internet.de/vvg/",
            source_type="law",
            title="VVG",
            fetch_strategy="sitemap_crawl",
            update_frequency="once",
        )
        assert s.status == "pending"
        assert s.max_pages == 50

    def test_to_dict(self):
        s = SourceSpec(
            url="https://example.com",
            source_type="news",
            title="Test",
            fetch_strategy="rss",
            update_frequency="daily",
        )
        d = s.to_dict()
        assert d["fetch_strategy"] == "rss"


class TestScheduleSpec:
    def test_create(self):
        s = ScheduleSpec(
            name="test_daily",
            cron_expression="0 6 * * *",
            source_url="https://example.com",
            action="fetch_and_index",
            goal_id="plan-1",
        )
        assert s.name == "test_daily"


class TestSeedSource:
    def test_url_seed(self):
        s = SeedSource(content_type="url", value="https://example.com")
        assert not s.processed

    def test_file_seed(self):
        s = SeedSource(content_type="file", value="/path/to/doc.pdf")
        assert s.content_type == "file"

    def test_hint_seed(self):
        s = SeedSource(content_type="hint", value="BaFin ist wichtig")
        assert s.content_type == "hint"


class TestQualityQuestion:
    def test_create(self):
        q = QualityQuestion(
            question="Was ist die Widerrufsfrist?",
            expected_answer="14 Tage",
        )
        assert not q.passed
        assert q.score == 0.0


class TestLearningPlan:
    def test_create_empty(self):
        plan = LearningPlan(goal="Lerne VVG")
        assert plan.id  # UUID auto-generated
        assert plan.goal_slug  # Auto-slugified
        assert plan.status == "planning"
        assert plan.sub_goals == []

    def test_goal_slug_generation(self):
        plan = LearningPlan(goal="Werde Experte fuer deutsches Versicherungsrecht!")
        assert "versicherungsrecht" in plan.goal_slug
        assert " " not in plan.goal_slug
        assert "!" not in plan.goal_slug

    def test_save_load_roundtrip(self, tmp_path):
        plan = LearningPlan(
            goal="Test Goal",
            sub_goals=[
                SubGoal(id="sg-1", title="Sub 1", description="Desc 1"),
                SubGoal(id="sg-2", title="Sub 2", description="Desc 2"),
            ],
            sources=[
                SourceSpec(
                    url="https://example.com",
                    source_type="reference",
                    title="Example",
                    fetch_strategy="full_page",
                    update_frequency="once",
                ),
            ],
            seed_sources=[
                SeedSource(content_type="url", value="https://seed.com"),
            ],
        )
        plan.save(tmp_path)
        loaded = LearningPlan.load(tmp_path / plan.id)
        assert loaded is not None
        assert loaded.goal == "Test Goal"
        assert len(loaded.sub_goals) == 2
        assert len(loaded.sources) == 1
        assert len(loaded.seed_sources) == 1

    def test_save_creates_directory_structure(self, tmp_path):
        plan = LearningPlan(goal="Test")
        plan.save(tmp_path)
        plan_dir = tmp_path / plan.id
        assert (plan_dir / "plan.json").exists()
        assert (plan_dir / "subgoals").is_dir()
        assert (plan_dir / "quality").is_dir()
        assert (plan_dir / "uploads").is_dir()

    def test_to_summary_dict(self):
        plan = LearningPlan(
            goal="Test",
            sub_goals=[
                SubGoal(id="sg-1", title="A", description="", status="passed"),
                SubGoal(id="sg-2", title="B", description="", status="pending"),
            ],
            coverage_score=0.65,
            quality_score=0.82,
            total_chunks_indexed=120,
        )
        d = plan.to_summary_dict()
        assert d["goal"] == "Test"
        assert d["sub_goals_total"] == 2
        assert d["sub_goals_done"] == 1
        assert d["coverage_score"] == 0.65
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_evolution_models.py -v`
Expected: ImportError — `jarvis.evolution.models` does not exist yet.

- [ ] **Step 3: Implement models.py**

```python
# src/jarvis/evolution/models.py
"""Data model for the Deep Autonomous Learning system (Phase 5).

Defines LearningPlan, SubGoal, SourceSpec, ScheduleSpec, SeedSource,
QualityQuestion — all with JSON serialization and file persistence.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "LearningPlan",
    "QualityQuestion",
    "ScheduleSpec",
    "SeedSource",
    "SourceSpec",
    "SubGoal",
]


def _new_id() -> str:
    return uuid.uuid4().hex[:16]


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:60] or "unnamed"


def _now_iso() -> str:
    import time

    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class QualityQuestion:
    """Self-examination question generated by QualityAssessor."""

    question: str = ""
    expected_answer: str = ""
    actual_answer: str = ""
    score: float = 0.0
    passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> QualityQuestion:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SeedSource:
    """User-provided starting material for a LearningPlan."""

    content_type: str = ""  # "url" | "file" | "hint"
    value: str = ""
    title: str = ""
    processed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SeedSource:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SourceSpec:
    """A knowledge source identified by the StrategyPlanner."""

    url: str = ""
    source_type: str = ""  # "law" | "news" | "reference" | "academic" | "forum"
    title: str = ""
    fetch_strategy: str = "full_page"  # "full_page" | "sitemap_crawl" | "api" | "rss"
    update_frequency: str = "once"  # "once" | "daily" | "weekly" | "monthly"
    priority: int = 0
    max_pages: int = 50

    last_fetched: str = ""
    pages_fetched: int = 0
    status: str = "pending"  # "pending" | "fetching" | "done" | "error"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SourceSpec:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ScheduleSpec:
    """A cron job to be created by the ScheduleManager."""

    name: str = ""
    cron_expression: str = ""  # "0 6 * * *"
    source_url: str = ""
    action: str = ""  # "fetch_and_index" | "check_updates" | "quality_retest"
    goal_id: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ScheduleSpec:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SubGoal:
    """A concrete sub-goal within a LearningPlan."""

    id: str = field(default_factory=_new_id)
    title: str = ""
    description: str = ""
    status: str = "pending"  # "pending"|"researching"|"building"|"testing"|"passed"|"failed"|"expanded"
    priority: int = 0
    parent_goal_id: str = ""

    # Results
    sources_fetched: list[str] = field(default_factory=list)
    chunks_created: int = 0
    entities_created: int = 0
    vault_entries: list[str] = field(default_factory=list)
    skills_generated: list[str] = field(default_factory=list)
    cron_jobs_created: list[str] = field(default_factory=list)

    # Quality
    coverage_score: float = 0.0
    quality_score: float = 0.0
    quality_questions: list[QualityQuestion] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["quality_questions"] = [q.to_dict() for q in self.quality_questions]
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SubGoal:
        questions = [QualityQuestion.from_dict(q) for q in d.pop("quality_questions", [])]
        filtered = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        sg = cls(**filtered)
        sg.quality_questions = questions
        return sg


@dataclass
class LearningPlan:
    """Master plan for a deep learning goal."""

    id: str = field(default_factory=_new_id)
    goal: str = ""
    goal_slug: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    status: str = "planning"  # "planning"|"active"|"paused"|"completed"|"error"

    sub_goals: list[SubGoal] = field(default_factory=list)
    sources: list[SourceSpec] = field(default_factory=list)
    schedules: list[ScheduleSpec] = field(default_factory=list)
    seed_sources: list[SeedSource] = field(default_factory=list)

    # Progress
    coverage_score: float = 0.0
    quality_score: float = 0.0
    total_chunks_indexed: int = 0
    total_entities_created: int = 0
    total_vault_entries: int = 0

    # Expansions from HorizonScanner
    expansions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.goal_slug and self.goal:
            self.goal_slug = _slugify(self.goal)

    def save(self, base_dir: Path) -> Path:
        """Save plan to disk under base_dir/{id}/plan.json."""
        plan_dir = base_dir / self.id
        plan_dir.mkdir(parents=True, exist_ok=True)
        (plan_dir / "subgoals").mkdir(exist_ok=True)
        (plan_dir / "quality").mkdir(exist_ok=True)
        (plan_dir / "uploads").mkdir(exist_ok=True)
        (plan_dir / "checkpoints").mkdir(exist_ok=True)

        self.updated_at = _now_iso()
        data = self.to_dict()
        (plan_dir / "plan.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return plan_dir

    @classmethod
    def load(cls, plan_dir: Path) -> LearningPlan | None:
        """Load plan from plan_dir/plan.json."""
        path = plan_dir / "plan.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls.from_dict(data)
        except Exception:
            return None

    @classmethod
    def list_plans(cls, base_dir: Path) -> list[LearningPlan]:
        """Load all plans from base_dir/*/plan.json."""
        plans: list[LearningPlan] = []
        if not base_dir.exists():
            return plans
        for d in sorted(base_dir.iterdir()):
            if d.is_dir():
                plan = cls.load(d)
                if plan:
                    plans.append(plan)
        return plans

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "goal_slug": self.goal_slug,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "sub_goals": [sg.to_dict() for sg in self.sub_goals],
            "sources": [s.to_dict() for s in self.sources],
            "schedules": [s.to_dict() for s in self.schedules],
            "seed_sources": [s.to_dict() for s in self.seed_sources],
            "coverage_score": self.coverage_score,
            "quality_score": self.quality_score,
            "total_chunks_indexed": self.total_chunks_indexed,
            "total_entities_created": self.total_entities_created,
            "total_vault_entries": self.total_vault_entries,
            "expansions": self.expansions,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LearningPlan:
        return cls(
            id=d.get("id", _new_id()),
            goal=d.get("goal", ""),
            goal_slug=d.get("goal_slug", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            status=d.get("status", "planning"),
            sub_goals=[SubGoal.from_dict(sg) for sg in d.get("sub_goals", [])],
            sources=[SourceSpec.from_dict(s) for s in d.get("sources", [])],
            schedules=[ScheduleSpec.from_dict(s) for s in d.get("schedules", [])],
            seed_sources=[SeedSource.from_dict(s) for s in d.get("seed_sources", [])],
            coverage_score=d.get("coverage_score", 0.0),
            quality_score=d.get("quality_score", 0.0),
            total_chunks_indexed=d.get("total_chunks_indexed", 0),
            total_entities_created=d.get("total_entities_created", 0),
            total_vault_entries=d.get("total_vault_entries", 0),
            expansions=d.get("expansions", []),
        )

    def to_summary_dict(self) -> dict[str, Any]:
        """Compact summary for API list endpoints."""
        return {
            "id": self.id,
            "goal": self.goal,
            "goal_slug": self.goal_slug,
            "status": self.status,
            "sub_goals_total": len(self.sub_goals),
            "sub_goals_done": sum(1 for sg in self.sub_goals if sg.status == "passed"),
            "coverage_score": self.coverage_score,
            "quality_score": self.quality_score,
            "total_chunks_indexed": self.total_chunks_indexed,
            "total_entities_created": self.total_entities_created,
            "total_vault_entries": self.total_vault_entries,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_evolution_models.py -v`
Expected: All 12 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/evolution/models.py tests/unit/test_evolution_models.py
git commit -m "feat(evolution): add Phase 5 data model — LearningPlan, SubGoal, SourceSpec"
```

---

### Task 2: StrategyPlanner — Goal Decomposition via LLM

**Files:**
- Create: `src/jarvis/evolution/strategy_planner.py`
- Create: `tests/unit/test_strategy_planner.py`

- [ ] **Step 1: Write tests for StrategyPlanner**

```python
# tests/unit/test_strategy_planner.py
"""Tests fuer StrategyPlanner."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from jarvis.evolution.models import LearningPlan, SeedSource
from jarvis.evolution.strategy_planner import StrategyPlanner


@pytest.fixture()
def mock_llm():
    """LLM function that returns valid plan JSON."""

    async def _llm(prompt: str) -> str:
        return json.dumps(
            {
                "sub_goals": [
                    {
                        "title": "VVG Grundlagen",
                        "description": "Lerne den Gesetzestext VVG",
                        "priority": 10,
                    },
                    {
                        "title": "Aktuelle Rechtsprechung",
                        "description": "BGH-Urteile zum VVG",
                        "priority": 5,
                    },
                ],
                "sources": [
                    {
                        "url": "https://www.gesetze-im-internet.de/vvg/",
                        "source_type": "law",
                        "title": "VVG Gesetzestext",
                        "fetch_strategy": "sitemap_crawl",
                        "update_frequency": "once",
                    },
                ],
                "schedules": [
                    {
                        "name": "versicherungsrecht_news",
                        "cron_expression": "0 6 * * *",
                        "source_url": "https://versicherungsbote.de",
                        "action": "fetch_and_index",
                        "description": "Taegliche News",
                    },
                ],
            }
        )

    return _llm


@pytest.fixture()
def mock_llm_invalid():
    """LLM function that returns invalid JSON."""

    async def _llm(prompt: str) -> str:
        return "This is not JSON at all, sorry."

    return _llm


@pytest.fixture()
def mock_llm_partial():
    """LLM function that returns valid JSON but missing fields."""

    async def _llm(prompt: str) -> str:
        return json.dumps({"sub_goals": [{"title": "Only title"}]})

    return _llm


class TestStrategyPlanner:
    @pytest.mark.asyncio
    async def test_create_plan(self, mock_llm):
        planner = StrategyPlanner(llm_fn=mock_llm)
        plan = await planner.create_plan("Werde Experte fuer Versicherungsrecht")
        assert isinstance(plan, LearningPlan)
        assert plan.goal == "Werde Experte fuer Versicherungsrecht"
        assert plan.status == "active"
        assert len(plan.sub_goals) == 2
        assert plan.sub_goals[0].title == "VVG Grundlagen"
        assert plan.sub_goals[0].priority == 10
        assert len(plan.sources) == 1
        assert plan.sources[0].fetch_strategy == "sitemap_crawl"
        assert len(plan.schedules) == 1

    @pytest.mark.asyncio
    async def test_create_plan_with_seeds(self, mock_llm):
        planner = StrategyPlanner(llm_fn=mock_llm)
        seeds = [
            SeedSource(content_type="url", value="https://example.com"),
            SeedSource(content_type="hint", value="BaFin ist relevant"),
        ]
        plan = await planner.create_plan("Versicherungsrecht", seed_sources=seeds)
        assert len(plan.seed_sources) == 2

    @pytest.mark.asyncio
    async def test_create_plan_invalid_json_retries(self, mock_llm_invalid):
        planner = StrategyPlanner(llm_fn=mock_llm_invalid, max_retries=2)
        plan = await planner.create_plan("Test")
        assert plan.status == "error"
        assert len(plan.sub_goals) == 0

    @pytest.mark.asyncio
    async def test_create_plan_partial_json(self, mock_llm_partial):
        planner = StrategyPlanner(llm_fn=mock_llm_partial)
        plan = await planner.create_plan("Test")
        assert plan.status == "active"
        assert len(plan.sub_goals) == 1
        assert plan.sub_goals[0].title == "Only title"

    @pytest.mark.asyncio
    async def test_replan_adds_subgoals(self, mock_llm):
        planner = StrategyPlanner(llm_fn=mock_llm)
        plan = LearningPlan(goal="Test", status="active")
        plan.sub_goals.append(
            __import__("jarvis.evolution.models", fromlist=["SubGoal"]).SubGoal(
                id="existing", title="Already done", description="", status="passed"
            )
        )
        updated = await planner.replan(plan, new_context="HorizonScanner found gaps")
        assert len(updated.sub_goals) >= 2  # existing + new from LLM

    @pytest.mark.asyncio
    async def test_prompt_includes_seed_sources(self, mock_llm):
        calls: list[str] = []

        async def _tracking_llm(prompt: str) -> str:
            calls.append(prompt)
            return await mock_llm(prompt)

        planner = StrategyPlanner(llm_fn=_tracking_llm)
        seeds = [SeedSource(content_type="url", value="https://seed.example.com")]
        await planner.create_plan("Test", seed_sources=seeds)
        assert "seed.example.com" in calls[0]

    @pytest.mark.asyncio
    async def test_is_complex_goal(self):
        planner = StrategyPlanner(llm_fn=AsyncMock())
        assert planner.is_complex_goal("Werde Experte fuer deutsches Versicherungsrecht")
        assert planner.is_complex_goal("deep dive into Kubernetes networking")
        assert not planner.is_complex_goal("Python list comprehensions")
        assert not planner.is_complex_goal("Was ist 2+2?")
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_strategy_planner.py -v`
Expected: ImportError — `jarvis.evolution.strategy_planner` does not exist yet.

- [ ] **Step 3: Implement strategy_planner.py**

```python
# src/jarvis/evolution/strategy_planner.py
"""StrategyPlanner — decomposes a high-level learning goal into a LearningPlan via LLM."""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Coroutine

from jarvis.evolution.models import (
    LearningPlan,
    ScheduleSpec,
    SeedSource,
    SourceSpec,
    SubGoal,
)
from jarvis.utils.logging import get_logger

log = get_logger(__name__)

__all__ = ["StrategyPlanner"]

# Keywords that signal a goal needs deep learning (not a simple search)
_COMPLEX_KEYWORDS = {
    "experte", "expert", "master", "meister", "spezialist",
    "deep dive", "umfassend", "komplett", "alles ueber", "alles über",
    "vollstaendig", "vollständig", "grundlagen bis fortgeschritten",
    "von grund auf", "zertifizierung", "certification",
}

_STRATEGY_PROMPT = """\
Du bist ein Forschungsstratege. Der User will folgendes Expertenwissen aufbauen:

Goal: "{goal}"
{seed_section}
Erstelle einen detaillierten Lernplan als JSON mit genau diesem Format:
{{
  "sub_goals": [
    {{
      "title": "Konkreter Titel",
      "description": "Was genau gelernt werden soll (2-3 Saetze)",
      "priority": 10
    }}
  ],
  "sources": [
    {{
      "url": "https://...",
      "source_type": "law|news|reference|academic|forum",
      "title": "Quellen-Titel",
      "fetch_strategy": "full_page|sitemap_crawl|rss|api",
      "update_frequency": "once|daily|weekly|monthly"
    }}
  ],
  "schedules": [
    {{
      "name": "eindeutiger_name",
      "cron_expression": "0 6 * * *",
      "source_url": "https://...",
      "action": "fetch_and_index",
      "description": "Was der Job tut"
    }}
  ]
}}

Regeln:
1. 5-15 SubGoals, vom Grundlegenden zum Spezialisierten priorisiert (10=hoechste Prio)
2. Identifiziere die BESTEN und AUTORITATIVSTEN Quellen (offizielle Seiten, nicht Wikipedia)
3. Quellen die sich aendern (News, Rundschreiben) bekommen Schedules
4. Denke ueber den Tellerrand: Was wuerde ein WAHRER Experte wissen wollen?
5. Antworte NUR mit dem JSON, kein erklaerernder Text.
"""

_REPLAN_PROMPT = """\
Du bist ein Forschungsstratege. Ein bestehender Lernplan wird erweitert.

Aktueller Plan:
- Goal: "{goal}"
- Erledigte SubGoals: {completed}
- Offene SubGoals: {pending}

Neuer Kontext: {new_context}

Erstelle ZUSAETZLICHE SubGoals und Sources als JSON (gleiches Format wie oben).
Wiederhole KEINE bereits vorhandenen SubGoals. Nur neue Erweiterungen.
Antworte NUR mit dem JSON.
"""


class StrategyPlanner:
    """Decomposes a high-level goal into a structured LearningPlan via LLM."""

    def __init__(
        self,
        llm_fn: Callable[[str], Coroutine[Any, Any, str]],
        max_retries: int = 3,
    ) -> None:
        self._llm_fn = llm_fn
        self._max_retries = max_retries

    async def create_plan(
        self,
        goal: str,
        seed_sources: list[SeedSource] | None = None,
    ) -> LearningPlan:
        """Create a new LearningPlan from a goal string."""
        seeds = seed_sources or []
        plan = LearningPlan(goal=goal, seed_sources=seeds)

        # Build prompt
        seed_section = ""
        if seeds:
            lines = []
            for s in seeds:
                label = {"url": "URL", "file": "Datei", "hint": "Hinweis"}.get(
                    s.content_type, s.content_type
                )
                lines.append(f"- {label}: {s.value}")
            seed_section = (
                "\nDer User hat folgende Startquellen bereitgestellt:\n"
                + "\n".join(lines)
                + "\n\nNutze diese als Ausgangspunkt, aber gehe darueber hinaus.\n"
            )

        prompt = _STRATEGY_PROMPT.format(goal=goal, seed_section=seed_section)

        # Call LLM with retry
        parsed = await self._call_llm_json(prompt)
        if parsed is None:
            plan.status = "error"
            log.warning("strategy_planner_failed", goal=goal[:80])
            return plan

        # Parse response into plan
        self._populate_plan(plan, parsed)
        plan.status = "active"
        log.info(
            "strategy_plan_created",
            goal=goal[:80],
            sub_goals=len(plan.sub_goals),
            sources=len(plan.sources),
            schedules=len(plan.schedules),
        )
        return plan

    async def replan(
        self,
        plan: LearningPlan,
        new_context: str,
    ) -> LearningPlan:
        """Extend an existing plan with new SubGoals based on new context."""
        completed = [sg.title for sg in plan.sub_goals if sg.status == "passed"]
        pending = [sg.title for sg in plan.sub_goals if sg.status != "passed"]

        prompt = _REPLAN_PROMPT.format(
            goal=plan.goal,
            completed=", ".join(completed) or "(keine)",
            pending=", ".join(pending) or "(keine)",
            new_context=new_context,
        )

        parsed = await self._call_llm_json(prompt)
        if parsed is None:
            log.warning("strategy_replan_failed", goal=plan.goal[:80])
            return plan

        # Add new sub_goals (don't replace existing ones)
        existing_titles = {sg.title.lower() for sg in plan.sub_goals}
        for sg_data in parsed.get("sub_goals", []):
            title = sg_data.get("title", "")
            if title.lower() not in existing_titles:
                plan.sub_goals.append(
                    SubGoal(
                        title=title,
                        description=sg_data.get("description", ""),
                        priority=sg_data.get("priority", 0),
                        parent_goal_id=plan.id,
                        status="pending",
                    )
                )

        # Add new sources
        existing_urls = {s.url for s in plan.sources}
        for src_data in parsed.get("sources", []):
            url = src_data.get("url", "")
            if url and url not in existing_urls:
                plan.sources.append(SourceSpec.from_dict(src_data))

        # Add new schedules
        existing_names = {s.name for s in plan.schedules}
        for sched_data in parsed.get("schedules", []):
            name = sched_data.get("name", "")
            if name and name not in existing_names:
                sched_data["goal_id"] = plan.id
                plan.schedules.append(ScheduleSpec.from_dict(sched_data))

        log.info("strategy_replan_complete", new_subgoals=len(plan.sub_goals) - len(existing_titles))
        return plan

    def is_complex_goal(self, goal: str) -> bool:
        """Determine if a goal requires deep learning (DeepLearner) or simple research."""
        lower = goal.lower()
        # Check for complexity keywords
        for kw in _COMPLEX_KEYWORDS:
            if kw in lower:
                return True
        # Long goals (>10 words) are likely complex
        if len(goal.split()) > 10:
            return True
        return False

    # -- Internal -------------------------------------------------------

    async def _call_llm_json(self, prompt: str) -> dict[str, Any] | None:
        """Call LLM and parse JSON response, with retries."""
        for attempt in range(self._max_retries):
            try:
                raw = await self._llm_fn(prompt)
                # Extract JSON from response (LLM might wrap in ```json blocks)
                json_str = self._extract_json(raw)
                return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                log.debug(
                    "strategy_planner_json_parse_failed",
                    attempt=attempt + 1,
                    max=self._max_retries,
                )
                if attempt < self._max_retries - 1:
                    prompt = (
                        prompt
                        + "\n\nWICHTIG: Deine letzte Antwort war kein valides JSON. "
                        "Antworte NUR mit dem JSON-Objekt, kein anderer Text."
                    )
            except Exception:
                log.debug("strategy_planner_llm_error", exc_info=True)
                return None
        return None

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON from LLM response, handling markdown code blocks."""
        # Try to find ```json ... ``` block
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Try to find raw { ... } block
        start = text.find("{")
        if start >= 0:
            # Find matching closing brace
            depth = 0
            for i, ch in enumerate(text[start:], start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1]
        return text.strip()

    @staticmethod
    def _populate_plan(plan: LearningPlan, data: dict[str, Any]) -> None:
        """Fill a LearningPlan from parsed LLM JSON."""
        for sg_data in data.get("sub_goals", []):
            plan.sub_goals.append(
                SubGoal(
                    title=sg_data.get("title", "Untitled"),
                    description=sg_data.get("description", ""),
                    priority=sg_data.get("priority", 0),
                    parent_goal_id=plan.id,
                )
            )
        # Sort by priority descending
        plan.sub_goals.sort(key=lambda sg: sg.priority, reverse=True)

        for src_data in data.get("sources", []):
            plan.sources.append(SourceSpec.from_dict(src_data))

        for sched_data in data.get("schedules", []):
            sched_data["goal_id"] = plan.id
            plan.schedules.append(ScheduleSpec.from_dict(sched_data))
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_strategy_planner.py -v`
Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/evolution/strategy_planner.py tests/unit/test_strategy_planner.py
git commit -m "feat(evolution): add StrategyPlanner — LLM-based goal decomposition"
```

---

### Task 3: DeepLearner Orchestrator (Phase 5A Scope)

**Files:**
- Create: `src/jarvis/evolution/deep_learner.py`
- Create: `tests/unit/test_deep_learner.py`

- [ ] **Step 1: Write tests for DeepLearner**

```python
# tests/unit/test_deep_learner.py
"""Tests fuer DeepLearner Orchestrator (Phase 5A)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from jarvis.evolution.deep_learner import DeepLearner
from jarvis.evolution.models import LearningPlan


@pytest.fixture()
def plans_dir(tmp_path):
    return tmp_path / "plans"


@pytest.fixture()
def mock_llm():
    async def _llm(prompt: str) -> str:
        return json.dumps(
            {
                "sub_goals": [
                    {"title": "Sub 1", "description": "Desc 1", "priority": 10},
                ],
                "sources": [
                    {
                        "url": "https://example.com",
                        "source_type": "reference",
                        "title": "Example",
                        "fetch_strategy": "full_page",
                        "update_frequency": "once",
                    },
                ],
                "schedules": [],
            }
        )

    return _llm


@pytest.fixture()
def learner(plans_dir, mock_llm):
    return DeepLearner(llm_fn=mock_llm, plans_dir=plans_dir)


class TestDeepLearner:
    @pytest.mark.asyncio
    async def test_create_plan(self, learner, plans_dir):
        plan = await learner.create_plan("Lerne Versicherungsrecht")
        assert plan.status == "active"
        assert len(plan.sub_goals) == 1
        # Plan is persisted
        assert (plans_dir / plan.id / "plan.json").exists()

    @pytest.mark.asyncio
    async def test_list_plans_empty(self, learner):
        plans = learner.list_plans()
        assert plans == []

    @pytest.mark.asyncio
    async def test_list_plans_after_create(self, learner):
        await learner.create_plan("Goal 1")
        await learner.create_plan("Goal 2")
        plans = learner.list_plans()
        assert len(plans) == 2

    @pytest.mark.asyncio
    async def test_get_plan(self, learner):
        plan = await learner.create_plan("Test")
        loaded = learner.get_plan(plan.id)
        assert loaded is not None
        assert loaded.goal == "Test"

    @pytest.mark.asyncio
    async def test_get_plan_not_found(self, learner):
        assert learner.get_plan("nonexistent") is None

    @pytest.mark.asyncio
    async def test_pause_plan(self, learner):
        plan = await learner.create_plan("Test")
        learner.update_plan_status(plan.id, "paused")
        loaded = learner.get_plan(plan.id)
        assert loaded is not None
        assert loaded.status == "paused"

    @pytest.mark.asyncio
    async def test_delete_plan(self, learner, plans_dir):
        plan = await learner.create_plan("Test")
        plan_dir = plans_dir / plan.id
        assert plan_dir.exists()
        learner.delete_plan(plan.id)
        assert not plan_dir.exists()

    @pytest.mark.asyncio
    async def test_get_next_subgoal(self, learner):
        plan = await learner.create_plan("Test")
        sg = learner.get_next_subgoal(plan.id)
        assert sg is not None
        assert sg.status == "pending"

    @pytest.mark.asyncio
    async def test_get_next_subgoal_all_done(self, learner):
        plan = await learner.create_plan("Test")
        for sg in plan.sub_goals:
            sg.status = "passed"
        plan.save(learner._plans_dir)
        assert learner.get_next_subgoal(plan.id) is None

    def test_has_active_plans_false(self, learner):
        assert not learner.has_active_plans()

    @pytest.mark.asyncio
    async def test_has_active_plans_true(self, learner):
        await learner.create_plan("Test")
        assert learner.has_active_plans()

    @pytest.mark.asyncio
    async def test_create_plan_with_seeds(self, learner):
        from jarvis.evolution.models import SeedSource

        seeds = [SeedSource(content_type="url", value="https://seed.com")]
        plan = await learner.create_plan("Test", seed_sources=seeds)
        assert len(plan.seed_sources) == 1
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_deep_learner.py -v`
Expected: ImportError — `jarvis.evolution.deep_learner` does not exist yet.

- [ ] **Step 3: Implement deep_learner.py**

```python
# src/jarvis/evolution/deep_learner.py
"""DeepLearner — orchestrates autonomous deep expertise building.

Phase 5A: StrategyPlanner + persistence.
Phase 5B+: ResearchAgent, KnowledgeBuilder, QualityAssessor, HorizonScanner, ScheduleManager.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable, Coroutine

from jarvis.evolution.models import LearningPlan, SeedSource, SubGoal
from jarvis.evolution.strategy_planner import StrategyPlanner
from jarvis.utils.logging import get_logger

log = get_logger(__name__)

__all__ = ["DeepLearner"]


class DeepLearner:
    """Orchestrates deep autonomous learning for complex goals.

    Creates and manages LearningPlans via the StrategyPlanner.
    Future phases add ResearchAgent, KnowledgeBuilder, etc.
    """

    def __init__(
        self,
        llm_fn: Callable[[str], Coroutine[Any, Any, str]],
        plans_dir: Path | str | None = None,
        mcp_client: Any = None,
        memory_manager: Any = None,
        skill_registry: Any = None,
        skill_generator: Any = None,
        cron_engine: Any = None,
        cost_tracker: Any = None,
        resource_monitor: Any = None,
        checkpoint_store: Any = None,
        config: Any = None,
        idle_detector: Any = None,
        operation_mode: str = "offline",
    ) -> None:
        self._llm_fn = llm_fn
        self._plans_dir = Path(plans_dir) if plans_dir else Path.home() / ".cognithor" / "evolution" / "plans"
        self._plans_dir.mkdir(parents=True, exist_ok=True)
        self._mcp_client = mcp_client
        self._memory = memory_manager
        self._skill_registry = skill_registry
        self._skill_gen = skill_generator
        self._cron_engine = cron_engine
        self._cost_tracker = cost_tracker
        self._resource_monitor = resource_monitor
        self._checkpoint_store = checkpoint_store
        self._config = config
        self._idle = idle_detector
        self._operation_mode = operation_mode
        self._strategy_planner = StrategyPlanner(llm_fn=llm_fn)

    # -- Plan CRUD -------------------------------------------------------

    async def create_plan(
        self,
        goal: str,
        seed_sources: list[SeedSource] | None = None,
    ) -> LearningPlan:
        """Create a new LearningPlan from a goal, persist to disk."""
        plan = await self._strategy_planner.create_plan(goal, seed_sources=seed_sources)
        plan.save(self._plans_dir)
        log.info(
            "deep_learner_plan_created",
            plan_id=plan.id[:8],
            goal=goal[:80],
            sub_goals=len(plan.sub_goals),
        )
        return plan

    def list_plans(self) -> list[LearningPlan]:
        """List all persisted LearningPlans."""
        return LearningPlan.list_plans(self._plans_dir)

    def get_plan(self, plan_id: str) -> LearningPlan | None:
        """Load a specific plan by ID."""
        return LearningPlan.load(self._plans_dir / plan_id)

    def update_plan_status(self, plan_id: str, status: str) -> bool:
        """Update plan status (pause/resume/complete) and persist."""
        plan = self.get_plan(plan_id)
        if not plan:
            return False
        plan.status = status
        plan.save(self._plans_dir)
        log.info("deep_learner_plan_status_changed", plan_id=plan_id[:8], status=status)
        return True

    def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan and all its data from disk."""
        plan_dir = self._plans_dir / plan_id
        if not plan_dir.exists():
            return False
        shutil.rmtree(plan_dir)
        log.info("deep_learner_plan_deleted", plan_id=plan_id[:8])
        return True

    def get_next_subgoal(self, plan_id: str) -> SubGoal | None:
        """Get the highest-priority pending SubGoal for a plan."""
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        pending = [sg for sg in plan.sub_goals if sg.status == "pending"]
        if not pending:
            return None
        # Already sorted by priority (highest first) from StrategyPlanner
        return pending[0]

    def has_active_plans(self) -> bool:
        """Check if there are any active plans with pending SubGoals."""
        for plan in self.list_plans():
            if plan.status == "active":
                pending = [sg for sg in plan.sub_goals if sg.status == "pending"]
                if pending:
                    return True
        return False

    def is_complex_goal(self, goal: str) -> bool:
        """Delegate complexity detection to StrategyPlanner."""
        return self._strategy_planner.is_complex_goal(goal)

    # -- Future phases will add: -----------------------------------------
    # async def run_subgoal(self, plan_id, subgoal_id) -> None
    # async def process_scheduled_update(self, source_spec) -> None
    # async def run_quality_test(self, plan_id) -> dict
    # async def run_horizon_scan(self, plan_id) -> list[str]
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_deep_learner.py -v`
Expected: All 12 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/evolution/deep_learner.py tests/unit/test_deep_learner.py
git commit -m "feat(evolution): add DeepLearner orchestrator with plan CRUD"
```

---

### Task 4: Config Extension + EvolutionLoop Integration

**Files:**
- Modify: `src/jarvis/config.py:1696-1729`
- Modify: `src/jarvis/evolution/loop.py:266-315`
- Modify: `src/jarvis/evolution/__init__.py`

- [ ] **Step 1: Add Phase 5 fields to EvolutionConfig**

In `src/jarvis/config.py`, after the `learning_goals` field (line 1728), add:

```python
    # Deep Learning (Phase 5)
    deep_learning_enabled: bool = Field(
        default=True,
        description="Enable deep learning plans (auto-promotes complex goals)",
    )
    max_concurrent_plans: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Maximum simultaneously active learning plans",
    )
    max_pages_per_crawl: int = Field(
        default=50,
        ge=5,
        le=500,
        description="Maximum pages to fetch per sitemap crawl",
    )
    quality_threshold: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="Minimum quality score to pass a SubGoal (0.0-1.0)",
    )
    coverage_threshold: float = Field(
        default=0.7,
        ge=0.3,
        le=1.0,
        description="Minimum coverage score to pass a SubGoal (0.0-1.0)",
    )
    auto_expand: bool = Field(
        default=True,
        description="HorizonScanner automatically adds new SubGoals",
    )
```

- [ ] **Step 2: Modify EvolutionLoop scout to delegate complex goals**

In `src/jarvis/evolution/loop.py`, in the `__init__` method, add attribute after `self._session_analyzer`:

```python
        self._deep_learner: Any = None  # Set by gateway after construction
```

In the `_scout()` method, insert as **new Tier 1.5** between Tier 1 (CuriosityEngine) and Tier 2 (User Goals):

```python
        # --- Tier 1.5: DeepLearner active plans ---
        if self._deep_learner and self._deep_learner.has_active_plans():
            # DeepLearner has pending work — yield a goal from active plan
            for plan in self._deep_learner.list_plans():
                if plan.status != "active":
                    continue
                sg = self._deep_learner.get_next_subgoal(plan.id)
                if sg:
                    log.info(
                        "evolution_scout_deep_plan",
                        plan=plan.goal[:40],
                        subgoal=sg.title[:40],
                    )
                    return [_LearningGoal(
                        query=f"[deep:{plan.id}:{sg.id}] {sg.title}: {sg.description}",
                        source="deep_plan",
                        target_skill=sg.id,
                    )]
```

Also modify Tier 2 (User Goals): before returning `_LearningGoal`, check if the goal is complex and auto-promote to a plan:

```python
        if goals:
            # Check for complex goals that should become deep learning plans
            if (
                self._deep_learner
                and self._config
                and getattr(self._config, "deep_learning_enabled", True)
            ):
                for g in list(goals):
                    if self._deep_learner.is_complex_goal(g):
                        log.info("evolution_promoting_to_deep_plan", goal=g[:60])
                        try:
                            await self._deep_learner.create_plan(g)
                            # Remove from simple goals list so it's handled as a plan
                            goals = [x for x in goals if x != g]
                        except Exception:
                            log.debug("evolution_promote_failed", exc_info=True)

            # Remaining simple goals
            researched = {
                r.research_topic for r in self._results[-20:] if r.research_topic
            }
            available = [g for g in goals if g not in researched]
            if available:
                selected = available[:3]
                random.shuffle(selected)
                log.info("evolution_scout_using_goals", count=len(selected), goals=selected)
                return [_LearningGoal(query=g, source="user") for g in selected]
```

- [ ] **Step 3: Update evolution/__init__.py**

```python
"""Autonomous Evolution Engine — self-improving idle-time learning."""

from jarvis.evolution.deep_learner import DeepLearner
from jarvis.evolution.idle_detector import IdleDetector
from jarvis.evolution.loop import EvolutionLoop
from jarvis.evolution.models import LearningPlan, SubGoal
from jarvis.evolution.resume import EvolutionResumer, ResumeState
from jarvis.evolution.strategy_planner import StrategyPlanner

__all__ = [
    "DeepLearner",
    "EvolutionLoop",
    "EvolutionResumer",
    "IdleDetector",
    "LearningPlan",
    "ResumeState",
    "StrategyPlanner",
    "SubGoal",
]
```

- [ ] **Step 4: Run all evolution tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_evolution.py tests/unit/test_evolution_models.py tests/unit/test_strategy_planner.py tests/unit/test_deep_learner.py tests/unit/test_evolution_resume.py -v`
Expected: All tests PASS (15 + 12 + 7 + 12 + 12 = 58 tests).

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/config.py src/jarvis/evolution/loop.py src/jarvis/evolution/__init__.py
git commit -m "feat(evolution): integrate DeepLearner into scout with auto-promote"
```

---

### Task 5: Gateway Wiring

**Files:**
- Modify: `src/jarvis/gateway/gateway.py:514-541`

- [ ] **Step 1: Wire DeepLearner into gateway**

After the existing EvolutionLoop initialization block (line 539), add:

```python
        # DeepLearner (deep autonomous learning)
        self._deep_learner = None
        if self._evolution_loop:
            try:
                from jarvis.evolution.deep_learner import DeepLearner

                self._deep_learner = DeepLearner(
                    llm_fn=getattr(self, "_llm_call", None),
                    plans_dir=self._config.jarvis_home / "evolution" / "plans",
                    mcp_client=getattr(self, "_mcp_client", None),
                    memory_manager=getattr(self, "_memory_manager", None),
                    skill_registry=getattr(self, "_skill_registry", None),
                    skill_generator=getattr(self, "_skill_generator", None),
                    cron_engine=getattr(self, "_cron_engine", None),
                    cost_tracker=self._cost_tracker,
                    resource_monitor=self._resource_monitor,
                    checkpoint_store=self._checkpoint_store,
                    config=self._config.evolution,
                    idle_detector=self._idle_detector,
                    operation_mode=op_mode,
                )
                self._evolution_loop._deep_learner = self._deep_learner
                log.info("deep_learner_initialized")
            except Exception:
                log.debug("deep_learner_init_failed", exc_info=True)
```

- [ ] **Step 2: Verify import works**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -c "from jarvis.evolution.deep_learner import DeepLearner; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/jarvis/gateway/gateway.py
git commit -m "feat(evolution): wire DeepLearner into gateway startup"
```

---

### Task 6: REST API Endpoints

**Files:**
- Modify: `src/jarvis/channels/config_routes.py`

- [ ] **Step 1: Add plan CRUD endpoints**

After the existing `evolution/goals` endpoints and before `# -- 3.4: POST /agents/{name}`, add:

```python
    @app.get("/api/v1/evolution/plans", dependencies=deps)
    async def list_evolution_plans() -> dict[str, Any]:
        """List all learning plans."""
        dl = getattr(gateway, "_deep_learner", None)
        if not dl:
            return {"plans": [], "message": "DeepLearner not available"}
        plans = dl.list_plans()
        return {"plans": [p.to_summary_dict() for p in plans]}

    @app.get("/api/v1/evolution/plans/{plan_id}", dependencies=deps)
    async def get_evolution_plan(plan_id: str) -> dict[str, Any]:
        """Get detailed plan with SubGoals."""
        dl = getattr(gateway, "_deep_learner", None)
        if not dl:
            return {"error": "DeepLearner not available"}
        plan = dl.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        return plan.to_dict()

    @app.post("/api/v1/evolution/plans", dependencies=deps)
    async def create_evolution_plan(request: Request) -> dict[str, Any]:
        """Create a new learning plan from a goal."""
        dl = getattr(gateway, "_deep_learner", None)
        if not dl:
            return {"error": "DeepLearner not available"}
        try:
            body = await request.json()
            goal = body.get("goal", "")
            if not goal:
                return {"error": "goal is required"}
            seeds_raw = body.get("seed_sources", [])
            seeds = []
            for s in seeds_raw:
                from jarvis.evolution.models import SeedSource
                seeds.append(SeedSource(
                    content_type=s.get("content_type", "hint"),
                    value=s.get("value", ""),
                    title=s.get("title", ""),
                ))
            plan = await dl.create_plan(goal, seed_sources=seeds if seeds else None)
            return plan.to_summary_dict()
        except Exception as exc:
            return {"error": str(exc)}

    @app.patch("/api/v1/evolution/plans/{plan_id}", dependencies=deps)
    async def update_evolution_plan(plan_id: str, request: Request) -> dict[str, Any]:
        """Update plan status (pause/resume/delete)."""
        dl = getattr(gateway, "_deep_learner", None)
        if not dl:
            return {"error": "DeepLearner not available"}
        try:
            body = await request.json()
            action = body.get("action", "")
            if action == "delete":
                dl.delete_plan(plan_id)
                return {"deleted": True}
            elif action in ("pause", "resume", "complete"):
                status = {"pause": "paused", "resume": "active", "complete": "completed"}[action]
                ok = dl.update_plan_status(plan_id, status)
                return {"updated": ok, "status": status}
            return {"error": f"Unknown action: {action}"}
        except Exception as exc:
            return {"error": str(exc)}
```

- [ ] **Step 2: Run a quick smoke test**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -c "from jarvis.channels.config_routes import register_system_routes; print('Import OK')"`
Expected: `Import OK`

- [ ] **Step 3: Commit**

```bash
git add src/jarvis/channels/config_routes.py
git commit -m "feat(evolution): REST API for learning plan CRUD"
```

---

### Task 7: Final Integration Test

- [ ] **Step 1: Run ALL evolution tests together**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_evolution.py tests/unit/test_evolution_models.py tests/unit/test_strategy_planner.py tests/unit/test_deep_learner.py tests/unit/test_evolution_resume.py tests/unit/test_resource_monitor.py tests/test_telemetry/test_cost_tracker.py -v`
Expected: All tests PASS (58+ evolution tests + 17 resource + 19 cost = 94+ total).

- [ ] **Step 2: Verify end-to-end import chain**

Run:
```bash
cd "D:\Jarvis\jarvis complete v20" && python -c "
from jarvis.evolution import DeepLearner, StrategyPlanner, LearningPlan, SubGoal
from jarvis.evolution.models import SourceSpec, ScheduleSpec, SeedSource, QualityQuestion
print(f'Models OK: {LearningPlan.__name__}')
print(f'Strategy OK: {StrategyPlanner.__name__}')
print(f'Deep OK: {DeepLearner.__name__}')
print('All Phase 5A imports successful')
"
```
Expected: All prints succeed.

- [ ] **Step 3: Final commit + push**

```bash
git add -A
git commit -m "feat(evolution): Phase 5A complete — Data Model + StrategyPlanner + DeepLearner

Phase 5A delivers:
- LearningPlan/SubGoal/SourceSpec data model with JSON persistence
- StrategyPlanner: LLM-based goal decomposition with retry + JSON extraction
- DeepLearner orchestrator with plan CRUD (create/list/get/pause/delete)
- EvolutionLoop scout auto-promotes complex goals to deep plans
- REST API: GET/POST/PATCH /api/v1/evolution/plans
- EvolutionConfig: 6 new fields (deep_learning_enabled, thresholds, etc.)
- Gateway wiring: DeepLearner initialized at startup
- 31 new tests (12 models + 7 strategy + 12 deep_learner)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
git push origin main
```
