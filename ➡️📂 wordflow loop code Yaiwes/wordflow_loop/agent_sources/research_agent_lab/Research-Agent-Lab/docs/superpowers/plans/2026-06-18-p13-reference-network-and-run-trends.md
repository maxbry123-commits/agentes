# P13: Reference Network Retrieval And Run Trends Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn P12 extracted references into cross-run literature-search seeds, and turn P11 run evaluations into a small trend report before expanding LLM or experiment budgets.

**Architecture:** Persist `ExtractedReference` records into `LiteratureMemoryStore`, build deterministic reference-search seeds from high-score references, optionally feed those seeds into `LiteratureSearchAgent`, and add a run-evaluation trend reader that summarizes recent `run_evaluations` artifacts. Keep all new logic offline by default; online arXiv expansion only runs when both `--online` and `--enable-reference-expansion` are set.

**Tech Stack:** Python stdlib, existing dataclass schemas, SQLite, existing `ArtifactStore`, existing `LiteratureMemoryStore`, `unittest`, existing `video_llava` interpreter.

---

## Current Context

- P12 already creates `schemas/reference.py::ExtractedReference`.
- `ReferenceExtractorAgent` writes `state.values["extracted_references"]` and `artifacts/extracted_references/*.json`.
- `LiteratureSearchAgent` currently only uses local papers, arXiv keywords, or offline topic keyword seeds.
- `LiteratureMemoryStore.write_run_artifacts()` currently persists papers, chunks, evidence, method cards, and experiment trees, but not extracted references.
- `RunEvaluationAgent` currently writes `artifacts/run_evaluations/*.json` and `state.values["run_quality_score"]`.
- This project is not a git repository. Use explicit tests and file inspection instead of `git status`.

---

## File Structure

- Modify: `memory/literature_memory.py`
  - Add `lit_references` table, `write_reference()`, `retrieve_references()`, and persistence from `write_run_artifacts()`.
- Create: `tools/reference_seed_builder.py`
  - Deterministically converts extracted references into search queries and offline seed papers.
- Modify: `agents/literature_searcher.py`
  - Accepts `lit_memory_store`, reads high-score persisted references when reference expansion is enabled, and appends reference-derived search seeds.
- Modify: `workflows/factory.py`
  - Passes `literature_memory_store` into `LiteratureSearchAgent`.
- Modify: `app/main.py`
  - Adds `--enable-reference-expansion` and `--max-reference-seeds`.
- Create: `tools/run_evaluation_trends.py`
  - Reads recent run evaluation artifacts from `data/runs` and computes status counts, score trend, and blocking/warning frequencies.
- Modify: `app/main.py`
  - Adds `summarize-runs` CLI command for trend reports.
- Create: `tests/test_reference_memory.py`
  - Tests reference persistence and retrieval.
- Create: `tests/test_reference_seed_builder.py`
  - Tests deterministic seed generation, filtering, and deduplication.
- Modify: `tests/test_full_research_loop.py`
  - Verifies reference expansion settings are accepted by the workflow.
- Create: `tests/test_run_evaluation_trends.py`
  - Tests recent-run trend summarization from synthetic run artifacts.
- Modify: `docs/project_handoff.md`
  - Updates P13 status, commands, test count, and next-step guidance.
- Create: `docs/reference_network_retrieval.md`
  - Documents how reference expansion works and when to enable it.

---

## Task 1: Persist Extracted References In Literature Memory

**Files:**
- Modify: `memory/literature_memory.py`
- Create: `tests/test_reference_memory.py`

- [ ] **Step 1: Write failing tests for reference persistence**

Create:

```python
# tests/test_reference_memory.py
from __future__ import annotations

from tempfile import TemporaryDirectory
from pathlib import Path
from unittest import TestCase, main

from memory.literature_memory import LiteratureMemoryStore


class ReferenceMemoryTest(TestCase):
    def test_write_and_retrieve_references_by_scope(self):
        with TemporaryDirectory() as tmp:
            store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
            store.write_reference({
                "ref_id": "ref_a",
                "title": "Diffusion Models for Pedestrian Trajectory Prediction",
                "source_paper_id": "paper_a",
                "authors": ["A. Researcher"],
                "year": "2024",
                "venue": "CVPR",
                "relevance_score": 0.91,
                "cited_in_sections": ["[1]", "[3]"],
            }, "intent_led_virat")

            refs = store.retrieve_references("intent_led_virat", limit=5)

            self.assertEqual(len(refs), 1)
            self.assertEqual(refs[0]["ref_id"], "ref_a")
            self.assertEqual(refs[0]["title"], "Diffusion Models for Pedestrian Trajectory Prediction")
            self.assertEqual(refs[0]["authors"], ["A. Researcher"])
            self.assertEqual(refs[0]["relevance_score"], 0.91)

    def test_retrieve_references_filters_by_min_score(self):
        with TemporaryDirectory() as tmp:
            store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
            store.write_reference({
                "ref_id": "low",
                "title": "Generic Image Classification",
                "source_paper_id": "paper_a",
                "relevance_score": 0.1,
            }, "scope_a")
            store.write_reference({
                "ref_id": "high",
                "title": "Language Conditioned Motion Forecasting",
                "source_paper_id": "paper_b",
                "relevance_score": 0.8,
            }, "scope_a")

            refs = store.retrieve_references("scope_a", min_score=0.5, limit=10)

            self.assertEqual([r["ref_id"] for r in refs], ["high"])

    def test_write_run_artifacts_persists_extracted_references(self):
        with TemporaryDirectory() as tmp:
            store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
            count = store.write_run_artifacts({
                "extracted_references": [{
                    "ref_id": "ref_run",
                    "title": "Goal Conditioned Trajectory Diffusion",
                    "source_paper_id": "paper_x",
                    "year": "2025",
                    "relevance_score": 0.77,
                }]
            }, "scope_run")

            refs = store.retrieve_references("scope_run", limit=3)

            self.assertEqual(count, 1)
            self.assertEqual(len(refs), 1)
            self.assertEqual(refs[0]["title"], "Goal Conditioned Trajectory Diffusion")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_reference_memory
```

Expected: failure because `LiteratureMemoryStore.write_reference` does not exist.

- [ ] **Step 3: Add reference table and methods**

Modify `memory/literature_memory.py`.

Add `write_reference()` after `write_method_card()`:

```python
    def write_reference(self, reference: dict[str, Any], scope: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO lit_references
                    (ref_id, scope, title, source_paper_id, authors, year,
                     venue, relevance_score, cited_in_sections, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reference.get("ref_id", ""),
                    scope,
                    reference.get("title", ""),
                    reference.get("source_paper_id", ""),
                    json.dumps(reference.get("authors", []), ensure_ascii=False),
                    str(reference.get("year", "")),
                    reference.get("venue", ""),
                    float(reference.get("relevance_score", 0.0) or 0.0),
                    json.dumps(reference.get("cited_in_sections", []), ensure_ascii=False),
                    utc_now(),
                ),
            )
```

Add `retrieve_references()` before `retrieve_papers()`:

```python
    def retrieve_references(
        self, scope: str, *, min_score: float = 0.0, limit: int = 10
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT ref_id, title, source_paper_id, authors, year, venue,
                       relevance_score, cited_in_sections, created_at
                FROM lit_references
                WHERE scope = ? AND relevance_score >= ?
                ORDER BY relevance_score DESC, created_at DESC
                LIMIT ?
                """,
                (scope, min_score, limit),
            ).fetchall()
        return [
            {
                "ref_id": r[0],
                "title": r[1],
                "source_paper_id": r[2],
                "authors": json.loads(r[3]) if r[3] else [],
                "year": r[4],
                "venue": r[5],
                "relevance_score": float(r[6] or 0.0),
                "cited_in_sections": json.loads(r[7]) if r[7] else [],
                "created_at": r[8],
            }
            for r in rows
        ]
```

Add this block inside `write_run_artifacts()` after method-card persistence:

```python
        for reference in state_values.get("extracted_references", []) or []:
            if isinstance(reference, dict) and reference.get("ref_id") and reference.get("title"):
                self.write_reference(reference, scope)
                count += 1
```

Add the table to `_init_db()`:

```sql
                CREATE TABLE IF NOT EXISTS lit_references (
                    ref_id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_paper_id TEXT,
                    authors TEXT,
                    year TEXT,
                    venue TEXT,
                    relevance_score REAL DEFAULT 0.0,
                    cited_in_sections TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_lit_ref_scope_score
                    ON lit_references(scope, relevance_score);
                CREATE INDEX IF NOT EXISTS idx_lit_ref_title
                    ON lit_references(title);
```

- [ ] **Step 4: Run reference memory tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_reference_memory
```

Expected: `Ran 3 tests ... OK`.

---

## Task 2: Build Deterministic Reference Search Seeds

**Files:**
- Create: `tools/reference_seed_builder.py`
- Create: `tests/test_reference_seed_builder.py`

- [ ] **Step 1: Write failing seed-builder tests**

Create:

```python
# tests/test_reference_seed_builder.py
from __future__ import annotations

from unittest import TestCase, main

from tools.reference_seed_builder import build_reference_search_seeds


class ReferenceSeedBuilderTest(TestCase):
    def test_builds_seed_from_high_score_reference_title(self):
        refs = [{
            "title": "Language Conditioned Pedestrian Trajectory Forecasting",
            "relevance_score": 0.88,
            "year": "2024",
        }]

        seeds = build_reference_search_seeds(refs, topic_keywords=["trajectory", "language"], max_seeds=5)

        self.assertEqual(seeds[0]["query"], "Language Conditioned Pedestrian Trajectory Forecasting")
        self.assertEqual(seeds[0]["source"], "reference_network")
        self.assertEqual(seeds[0]["relevance_score"], 0.88)

    def test_filters_low_score_and_short_titles(self):
        refs = [
            {"title": "AI", "relevance_score": 0.9},
            {"title": "Unrelated Classification Survey", "relevance_score": 0.1},
            {"title": "Diffusion Trajectory Prediction", "relevance_score": 0.7},
        ]

        seeds = build_reference_search_seeds(refs, topic_keywords=["trajectory"], min_score=0.3, max_seeds=5)

        self.assertEqual([s["query"] for s in seeds], ["Diffusion Trajectory Prediction"])

    def test_deduplicates_similar_titles(self):
        refs = [
            {"title": "Diffusion Models for Trajectory Prediction", "relevance_score": 0.9},
            {"title": "Diffusion Model for Trajectory Prediction", "relevance_score": 0.8},
            {"title": "Graph Neural Forecasting", "relevance_score": 0.7},
        ]

        seeds = build_reference_search_seeds(refs, topic_keywords=["trajectory"], max_seeds=5)

        self.assertEqual(len(seeds), 2)
        self.assertEqual(seeds[0]["query"], "Diffusion Models for Trajectory Prediction")

    def test_respects_max_seeds(self):
        refs = [
            {"title": f"Relevant Trajectory Paper {i}", "relevance_score": 1.0 - i * 0.01}
            for i in range(10)
        ]

        seeds = build_reference_search_seeds(refs, topic_keywords=["trajectory"], max_seeds=3)

        self.assertEqual(len(seeds), 3)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_reference_seed_builder
```

Expected: `ModuleNotFoundError: No module named 'tools.reference_seed_builder'`.

- [ ] **Step 3: Implement seed builder**

Create:

```python
# tools/reference_seed_builder.py
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any


def build_reference_search_seeds(
    references: list[dict[str, Any]],
    *,
    topic_keywords: list[str] | None = None,
    min_score: float = 0.3,
    max_seeds: int = 8,
) -> list[dict[str, Any]]:
    keywords = [kw.lower() for kw in (topic_keywords or []) if len(str(kw).strip()) >= 3]
    candidates: list[dict[str, Any]] = []
    for ref in references:
        title = str(ref.get("title", "")).strip()
        score = float(ref.get("relevance_score", 0.0) or 0.0)
        if len(title) < 10:
            continue
        if score < min_score:
            continue
        keyword_bonus = _keyword_bonus(title, keywords)
        candidates.append({
            "query": title,
            "source": "reference_network",
            "source_ref_id": ref.get("ref_id", ""),
            "source_paper_id": ref.get("source_paper_id", ""),
            "year": str(ref.get("year", "")),
            "venue": str(ref.get("venue", "")),
            "relevance_score": round(min(1.0, score + keyword_bonus), 4),
        })
    candidates.sort(key=lambda item: item["relevance_score"], reverse=True)
    return _dedupe_seed_queries(candidates, max_seeds=max_seeds)


def _keyword_bonus(title: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0
    title_lower = title.lower()
    hits = sum(1 for keyword in keywords[:12] if keyword in title_lower)
    return min(0.1, hits * 0.025)


def _dedupe_seed_queries(candidates: list[dict[str, Any]], *, max_seeds: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in candidates:
        query = item["query"].lower()
        duplicate = False
        for existing in result:
            ratio = SequenceMatcher(None, query, existing["query"].lower()).ratio()
            if ratio > 0.86:
                duplicate = True
                break
        if duplicate:
            continue
        result.append(item)
        if len(result) >= max_seeds:
            break
    return result
```

- [ ] **Step 4: Run seed-builder tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_reference_seed_builder
```

Expected: `Ran 4 tests ... OK`.

---

## Task 3: Feed Reference Seeds Into LiteratureSearchAgent

**Files:**
- Modify: `agents/literature_searcher.py`
- Modify: `workflows/factory.py`
- Modify: `tests/test_full_research_loop.py`
- Create: `tests/test_reference_expansion_search.py`

- [ ] **Step 1: Write failing tests for reference expansion**

Create:

```python
# tests/test_reference_expansion_search.py
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.literature_searcher import LiteratureSearchAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from memory.literature_memory import LiteratureMemoryStore
from schemas.topic_pack import TopicPack


def _topic() -> TopicPack:
    return TopicPack(
        topic_name="intent_led_virat",
        search_seeds={"keywords": ["trajectory prediction", "language condition"]},
    )


def _context(tmp: str, settings: dict, lit_store: LiteratureMemoryStore) -> AgentContext:
    from tools.tool_registry import ToolRegistry
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp)),
        memory_store=None,
        tool_registry=ToolRegistry(),
        settings=settings,
    )


class ReferenceExpansionSearchTest(TestCase):
    def test_reference_expansion_adds_offline_reference_seed_papers(self):
        with TemporaryDirectory() as tmp:
            lit_store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
            lit_store.write_reference({
                "ref_id": "ref_1",
                "title": "Language Conditioned Trajectory Diffusion",
                "source_paper_id": "paper_a",
                "relevance_score": 0.9,
            }, "intent_led_virat")
            state = ResearchState(topic=_topic())
            ctx = _context(tmp, {
                "max_papers": 3,
                "enable_reference_expansion": True,
                "max_reference_seeds": 2,
            }, lit_store)

            result = LiteratureSearchAgent(lit_memory_store=lit_store).run(state, ctx)

            papers = state.values["papers"]
            titles = [p["title"] for p in papers]
            self.assertTrue(any("Language Conditioned Trajectory Diffusion" in title for title in titles))
            self.assertIn("reference_search_seeds", result.artifacts)

    def test_reference_expansion_disabled_keeps_default_offline_keywords(self):
        with TemporaryDirectory() as tmp:
            lit_store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
            lit_store.write_reference({
                "ref_id": "ref_1",
                "title": "Reference Expansion Should Not Appear",
                "relevance_score": 0.9,
            }, "intent_led_virat")
            state = ResearchState(topic=_topic())
            ctx = _context(tmp, {"max_papers": 2, "enable_reference_expansion": False}, lit_store)

            LiteratureSearchAgent(lit_memory_store=lit_store).run(state, ctx)

            titles = [p["title"] for p in state.values["papers"]]
            self.assertFalse(any("Reference Expansion Should Not Appear" in title for title in titles))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_reference_expansion_search
```

Expected: `TypeError` because `LiteratureSearchAgent` does not accept `lit_memory_store`.

- [ ] **Step 3: Modify LiteratureSearchAgent constructor and seed flow**

Modify `agents/literature_searcher.py` imports:

```python
from memory.memory_policy import memory_scope_for_topic
from tools.reference_seed_builder import build_reference_search_seeds
```

Add constructor:

```python
    def __init__(self, lit_memory_store: object = None):
        super().__init__()
        self.lit_memory_store = lit_memory_store
```

Modify `run()` before the final fallback to `_offline_seed_papers()`:

```python
        reference_seed_papers: list[Paper] = []
        reference_seed_ids: list[str] = []
        if context.settings.get("enable_reference_expansion"):
            reference_seed_papers, reference_seed_ids = self._reference_seed_papers(
                state, context, max_papers
            )
```

Use reference seeds after local papers and arXiv keyword papers, before topic offline seeds:

```python
        if reference_seed_papers:
            existing_titles = {p.title.lower() for p in papers}
            for paper in reference_seed_papers:
                if paper.title.lower() in existing_titles:
                    continue
                papers.append(paper)
                existing_titles.add(paper.title.lower())
                if len(papers) >= max_papers:
                    break

        if not papers:
            papers = self._offline_seed_papers(state, max_papers)
```

Add helper method:

```python
    def _reference_seed_papers(
        self, state: ResearchState, context: AgentContext, max_papers: int
    ) -> tuple[list[Paper], list[str]]:
        if self.lit_memory_store is None:
            return [], []
        max_reference_seeds = int(context.settings.get("max_reference_seeds", 4) or 4)
        scope = memory_scope_for_topic(state.topic.topic_name)
        references = self.lit_memory_store.retrieve_references(
            scope, min_score=0.3, limit=max_reference_seeds * 2
        )
        seeds = build_reference_search_seeds(
            references,
            topic_keywords=state.topic.keywords(),
            max_seeds=max_reference_seeds,
        )
        papers: list[Paper] = []
        artifact_ids: list[str] = []
        for index, seed in enumerate(seeds, start=1):
            query = seed["query"]
            if context.tool_registry.has("arxiv") and context.settings.get("online"):
                output = context.tool_registry.call("arxiv", query, max_results=1)
                for item in output.items:
                    if isinstance(item, Paper):
                        papers.append(item)
                        artifact_ids.append(seed.get("source_ref_id") or f"reference_seed_{index}")
                        break
            else:
                paper = Paper(
                    title=f"Reference seed {index}: {query}",
                    abstract=(
                        "Offline reference-network seed generated from extracted references. "
                        f"source_ref_id={seed.get('source_ref_id', '')}; "
                        f"score={seed.get('relevance_score', 0.0)}"
                    ),
                    keywords=[query],
                    source="reference_seed",
                )
                papers.append(paper)
                artifact_ids.append(seed.get("source_ref_id") or paper.paper_id)
            if len(papers) >= max_papers:
                break
        state.values["reference_search_seeds"] = seeds
        return papers, artifact_ids
```

When returning `AgentResult`, include reference seed artifact ids:

```python
        artifacts = {"papers": artifact_ids}
        if reference_seed_ids:
            artifacts["reference_search_seeds"] = reference_seed_ids
        return AgentResult(
            notes=[f"collected {len(artifact_ids)} paper records"],
            artifacts=artifacts,
            values={
                "paper_count": len(artifact_ids),
                "reference_search_seed_count": len(reference_seed_ids),
            },
        )
```

- [ ] **Step 4: Pass memory store from workflow factory**

Modify `workflows/factory.py`:

```python
        LiteratureSearchAgent(lit_memory_store=literature_memory_store),
```

- [ ] **Step 5: Run reference expansion tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_reference_expansion_search
```

Expected: `Ran 2 tests ... OK`.

---

## Task 4: Add CLI Flags For Reference Expansion

**Files:**
- Modify: `app/main.py`
- Modify: `workflows/factory.py`
- Modify: `tests/test_full_research_loop.py`

- [ ] **Step 1: Add parser tests**

Append to `tests/test_full_research_loop.py` or create `tests/test_cli_parser.py`:

```python
from app.main import build_parser


class CliParserTest(TestCase):
    def test_reference_expansion_flags_parse(self):
        parser = build_parser()
        args = parser.parse_args([
            "run",
            "--topic", "topics/intent_led_virat.json",
            "--enable-reference-expansion",
            "--max-reference-seeds", "3",
        ])

        self.assertTrue(args.enable_reference_expansion)
        self.assertEqual(args.max_reference_seeds, 3)
```

- [ ] **Step 2: Run parser test to verify it fails**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_full_research_loop.CliParserTest
```

Expected: parser rejects `--enable-reference-expansion`.

- [ ] **Step 3: Add CLI arguments**

Modify `app/main.py` in `build_parser()`:

```python
    run_parser.add_argument(
        "--enable-reference-expansion",
        action="store_true",
        help="Use persisted extracted references as additional literature-search seeds",
    )
    run_parser.add_argument(
        "--max-reference-seeds",
        type=int,
        default=4,
        help="Maximum reference-network seeds to use when reference expansion is enabled",
    )
```

Pass arguments into `build_full_research_workflow()`:

```python
        enable_reference_expansion=args.enable_reference_expansion,
        max_reference_seeds=args.max_reference_seeds,
```

Modify `workflows/factory.py` signature:

```python
    enable_reference_expansion: bool = False,
    max_reference_seeds: int = 4,
```

Add to workflow settings:

```python
            "enable_reference_expansion": enable_reference_expansion,
            "max_reference_seeds": max_reference_seeds,
```

- [ ] **Step 4: Run parser test**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_full_research_loop.CliParserTest
```

Expected: `OK`.

---

## Task 5: Add Run Evaluation Trend Reader

**Files:**
- Create: `tools/run_evaluation_trends.py`
- Create: `tests/test_run_evaluation_trends.py`
- Modify: `app/main.py`

- [ ] **Step 1: Write failing trend tests**

Create:

```python
# tests/test_run_evaluation_trends.py
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from tools.run_evaluation_trends import summarize_run_evaluations


def _write_eval(root: Path, run_id: str, status: str, score: int, warnings: list[str], blocking: list[str]) -> None:
    folder = root / run_id / "artifacts" / "run_evaluations"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "eval.json").write_text(json.dumps({
        "status": status,
        "score": score,
        "warnings": warnings,
        "blocking_issues": blocking,
        "summary": [f"status={status}", f"score={score}"],
    }), encoding="utf-8")


class RunEvaluationTrendTest(TestCase):
    def test_summarizes_status_counts_and_scores(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_eval(root, "run_a", "pass", 100, [], [])
            _write_eval(root, "run_b", "needs_review", 90, ["warn one"], [])
            _write_eval(root, "run_c", "block", 65, [], ["block one"])

            summary = summarize_run_evaluations(root, limit=10)

            self.assertEqual(summary["run_count"], 3)
            self.assertEqual(summary["status_counts"]["pass"], 1)
            self.assertEqual(summary["status_counts"]["needs_review"], 1)
            self.assertEqual(summary["status_counts"]["block"], 1)
            self.assertEqual(summary["average_score"], 85.0)
            self.assertEqual(summary["latest_status"], "block")

    def test_handles_empty_runs_directory(self):
        with TemporaryDirectory() as tmp:
            summary = summarize_run_evaluations(Path(tmp), limit=5)

            self.assertEqual(summary["run_count"], 0)
            self.assertEqual(summary["status_counts"], {})
            self.assertEqual(summary["average_score"], 0.0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_evaluation_trends
```

Expected: `ModuleNotFoundError: No module named 'tools.run_evaluation_trends'`.

- [ ] **Step 3: Implement trend reader**

Create:

```python
# tools/run_evaluation_trends.py
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def summarize_run_evaluations(runs_root: Path | str, *, limit: int = 20) -> dict[str, Any]:
    root = Path(runs_root)
    run_dirs = sorted(
        [path for path in root.glob("run_*") if path.is_dir()],
        key=lambda path: path.stat().st_mtime,
    )[-limit:]
    reports: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        eval_dir = run_dir / "artifacts" / "run_evaluations"
        eval_files = sorted(eval_dir.glob("*.json")) if eval_dir.exists() else []
        if not eval_files:
            continue
        try:
            report = json.loads(eval_files[-1].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        report["_run_id"] = run_dir.name
        reports.append(report)

    scores = [int(r.get("score", 0) or 0) for r in reports]
    statuses = Counter(str(r.get("status", "unknown")) for r in reports)
    warning_counter: Counter[str] = Counter()
    blocking_counter: Counter[str] = Counter()
    for report in reports:
        warning_counter.update(str(item) for item in report.get("warnings", []) or [])
        blocking_counter.update(str(item) for item in report.get("blocking_issues", []) or [])

    latest = reports[-1] if reports else {}
    average = round(sum(scores) / len(scores), 2) if scores else 0.0
    return {
        "run_count": len(reports),
        "latest_run_id": latest.get("_run_id", ""),
        "latest_status": latest.get("status", ""),
        "latest_score": latest.get("score", 0),
        "average_score": average,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "status_counts": dict(statuses),
        "top_warnings": warning_counter.most_common(5),
        "top_blocking_issues": blocking_counter.most_common(5),
    }


def format_run_evaluation_summary(summary: dict[str, Any]) -> str:
    lines = [
        f"run_count={summary['run_count']}",
        f"latest={summary['latest_run_id']} status={summary['latest_status']} score={summary['latest_score']}",
        f"average_score={summary['average_score']} min={summary['min_score']} max={summary['max_score']}",
        f"status_counts={summary['status_counts']}",
    ]
    if summary["top_blocking_issues"]:
        lines.append("top_blocking_issues:")
        lines.extend(f"- {text} ({count})" for text, count in summary["top_blocking_issues"])
    if summary["top_warnings"]:
        lines.append("top_warnings:")
        lines.extend(f"- {text} ({count})" for text, count in summary["top_warnings"])
    return "\n".join(lines)
```

- [ ] **Step 4: Add `summarize-runs` CLI**

Modify `app/main.py` in `build_parser()`:

```python
    summarize_parser = subparsers.add_parser(
        "summarize-runs",
        help="Summarize recent run_evaluation artifacts",
    )
    summarize_parser.add_argument("--data-dir", default="data")
    summarize_parser.add_argument("--limit", type=int, default=20)
```

Modify `main()`:

```python
    if args.command == "summarize-runs":
        from tools.run_evaluation_trends import (
            format_run_evaluation_summary,
            summarize_run_evaluations,
        )
        summary = summarize_run_evaluations(Path(args.data_dir) / "runs", limit=args.limit)
        print(format_run_evaluation_summary(summary))
        return 0
```

- [ ] **Step 5: Run trend tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_evaluation_trends
```

Expected: `Ran 2 tests ... OK`.

---

## Task 6: Documentation And Handoff Update

**Files:**
- Create: `docs/reference_network_retrieval.md`
- Modify: `docs/project_handoff.md`

- [ ] **Step 1: Create reference-network guide**

Create:

```markdown
# Reference Network Retrieval

P13 connects `ReferenceExtractorAgent` output to later literature search runs.

## Data Flow

```text
LocalPaperParserAgent
→ ReferenceExtractorAgent
→ LiteratureMemoryPersistenceAgent
→ LiteratureMemoryStore.lit_references
→ LiteratureSearchAgent with --enable-reference-expansion
```

Reference expansion is cross-run by design. A run first extracts references from parsed papers. A later run can reuse persisted references as additional search seeds.

## CLI

Offline reference seed run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 4 --enable-reference-expansion --max-reference-seeds 4
```

Online arXiv expansion run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --online --enable-reference-expansion --max-reference-seeds 4
```

## Safety

- Reference expansion is disabled by default.
- Online arXiv calls require `--online`.
- DeepSeek calls still require `--enable-llm`.
- Reference seeds are deterministic and written to `state.values["reference_search_seeds"]`.
```

- [ ] **Step 2: Update project handoff**

Update `docs/project_handoff.md`:

- Change update line to `更新时间：2026-06-18（P13 完成）` only after implementation and verification pass.
- Add `lit_references` to the memory section.
- Add `--enable-reference-expansion` and `summarize-runs` to common commands.
- Update test count after all tests pass.
- Move “参考文献网络检索” and “多 run 评估趋势分析” from 下一步 to 已完成.
- Add next steps after P13:
  - P14 lightweight retrieval metrics.
  - P15 finalization check after memory persistence.

---

## Task 7: Verification

**Files:**
- All files touched above.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_reference_memory tests.test_reference_seed_builder tests.test_reference_expansion_search tests.test_run_evaluation_trends
```

Expected: all focused tests pass.

- [ ] **Step 2: Run full test suite**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p "test*.py"
```

Expected: all tests pass. Current verified baseline before P13 is `Ran 211 tests ... OK`.

- [ ] **Step 3: Run offline reference persistence smoke**

Run a normal offline workflow first:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 2
```

Expected:

```text
stage=completed
review_status=<pass or needs_human_review>
```

Then inspect `data/literature_memory.sqlite3` through a small Python query:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -c "from memory.literature_memory import LiteratureMemoryStore; s=LiteratureMemoryStore('data/literature_memory.sqlite3'); print(len(s.retrieve_references('intent_led_virat', limit=10)))"
```

Expected: integer output. If no references were extracted from the selected PDFs, output can be `0`; this is not a failure, but use a larger `--max-papers` before judging the feature.

- [ ] **Step 4: Run reference-expansion smoke**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 4 --enable-reference-expansion --max-reference-seeds 4
```

Expected:

```text
stage=completed
review_status=<pass or needs_human_review>
```

Inspect latest `state.json`:

```text
data/runs/<run_id>/state.json
```

Expected:

- `reference_search_seeds` exists when persisted references are available.
- `reference_search_seed_count` is present in agent values.
- No API call occurs unless `--enable-llm` is also set.

- [ ] **Step 5: Run trend-summary smoke**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main summarize-runs --data-dir data --limit 10
```

Expected output includes:

```text
run_count=
latest=
average_score=
status_counts=
```

- [ ] **Step 6: Optional controlled online smoke**

Run only if offline smoke passes and network access is intentionally allowed:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --online --max-papers 4 --enable-reference-expansion --max-reference-seeds 4
```

Expected:

- arXiv tool is used only for reference-derived search queries.
- Workflow completes.
- `RunEvaluationAgent` reports no new blockers caused by reference expansion.

---

## Self-Review

- Spec coverage: This plan implements the documented next steps in `docs/project_handoff.md`: reference-network retrieval and multi-run quality trend analysis.
- Placeholder scan: No `TBD`, `TODO`, or unspecified “add appropriate handling” remains. Every code step names exact functions, files, and commands.
- Type consistency: `ExtractedReference`, `extracted_references`, `reference_search_seeds`, `run_evaluations`, and `run_quality_score` match current code and artifact names.
- Risk control: Reference expansion is opt-in, offline by default, and separate from LLM/API enablement.
