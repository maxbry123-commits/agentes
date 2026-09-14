# Evolution Engine Phase 5 — Deep Autonomous Learning

> **Spec Status:** Approved
> **Author:** Alexander Soellner + Claude Opus 4.6
> **Date:** 2026-03-28
> **Depends on:** Evolution Engine Phases 1-4 (v0.60.0)

## 1. Goal

Transform the Evolution Engine from a shallow search-and-remember system into a **fully autonomous expertise-building agent**. Given a high-level goal like "Become an expert in German insurance law", Cognithor autonomously:

1. Decomposes the goal into concrete sub-goals with the LLM
2. Discovers and fetches authoritative sources (laws, news, references)
3. Builds persistent knowledge bases (Vault + Memory + Knowledge Graph)
4. Schedules recurring updates via cron (daily news, weekly regulation checks)
5. Tests its own knowledge with self-generated exams
6. Discovers related areas beyond the literal goal (LLM exploration + graph gap analysis)
7. Creates skills that make the accumulated knowledge queryable

The system is **domain-agnostic** — insurance law, quantum physics, cooking, Kubernetes — same architecture, different content.

## 2. Architecture: DeepLearner + 6 Sub-Agents

```
EvolutionLoop (existing)
  └── DeepLearner (NEW orchestrator)
       ├── StrategyPlanner   — LLM decomposes goal into LearningPlan
       ├── ResearchAgent     — Web fetch, sitemap crawl, RSS, document parsing
       ├── KnowledgeBuilder  — Vault + Memory + Graph triple-write
       ├── ScheduleManager   — Cron jobs for recurring source updates
       ├── QualityAssessor   — Coverage check + LLM self-examination
       └── HorizonScanner    — LLM exploration + graph gap discovery
```

### Integration with Existing Code

- **Tool execution (Hybrid):** Simple operations (web_fetch, vault_save, save_to_memory) called directly via `mcp_client.call_tool()`. Complex chains (entity extraction, strategy planning) routed through PGE loop via `gateway.handle_message()`.
- **LLM access:** Direct via `llm_fn` (no PGE overhead for pure reasoning tasks).
- **Checkpointing:** Reuses Phase 4 `CheckpointStore` — checkpoint per SubGoal step.
- **Budget:** Reuses Phase 3 `CostTracker` — per-agent cost tracking.
- **Resources:** Reuses Phase 3 `ResourceMonitor` — yield when system busy.
- **Idle detection:** Reuses Phase 2 `IdleDetector` — stop immediately when user returns.

## 3. Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Tool execution | Hybrid (direct + PGE) | Security for complex ops, speed for simple ones |
| Goal decomposition | Full LLM planning, no template fallback | Must work for any domain; LLM creativity essential |
| Storage strategy | All three parallel (Vault + Memory + Graph) | 256 GB RAM, 6.8 TB disk — no reason to economize |
| Completion criteria | Coverage + Self-examination | Quantity (coverage) + Quality (self-test) together |
| Beyond-the-goal | LLM exploration + Graph discovery | Creative + structural gap detection |
| User seed sources | URLs, files, hints — optional | Accelerates planning, not required |

## 4. Data Model

### LearningPlan

```python
@dataclass
class LearningPlan:
    id: str                          # UUID
    goal: str                        # Original user goal
    goal_slug: str                   # Namespace key: "versicherungsrecht-vvg"
    created_at: str                  # ISO timestamp
    updated_at: str                  # ISO timestamp
    status: str                      # "planning" | "active" | "paused" | "completed" | "error"

    sub_goals: list[SubGoal]
    sources: list[SourceSpec]
    schedules: list[ScheduleSpec]
    seed_sources: list[SeedSource]   # User-provided starting material

    # Progress metrics
    coverage_score: float = 0.0      # 0.0-1.0
    quality_score: float = 0.0       # 0.0-1.0 (last self-exam result)
    total_chunks_indexed: int = 0
    total_entities_created: int = 0
    total_vault_entries: int = 0

    # HorizonScanner expansions
    expansions: list[str] = field(default_factory=list)
```

### SubGoal

```python
@dataclass
class SubGoal:
    id: str
    title: str                       # "VVG Gesetzestext embedden"
    description: str                 # LLM-generated detail
    status: str                      # "pending" | "researching" | "building" |
                                     # "testing" | "passed" | "failed" | "expanded"
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
```

### SourceSpec

```python
@dataclass
class SourceSpec:
    url: str                         # "https://www.gesetze-im-internet.de/vvg/"
    source_type: str                 # "law" | "news" | "reference" | "academic" | "forum"
    title: str
    fetch_strategy: str              # "full_page" | "sitemap_crawl" | "api" | "rss"
    update_frequency: str            # "once" | "daily" | "weekly" | "monthly"
    priority: int = 0
    max_pages: int = 50

    last_fetched: str = ""
    pages_fetched: int = 0
    status: str = "pending"          # "pending" | "fetching" | "done" | "error"
```

### ScheduleSpec

```python
@dataclass
class ScheduleSpec:
    name: str                        # "evolution_versicherungsrecht_news"
    cron_expression: str             # "0 6 * * *"
    source_url: str
    action: str                      # "fetch_and_index" | "check_updates" | "quality_retest"
    goal_id: str
    description: str = ""
```

### SeedSource

```python
@dataclass
class SeedSource:
    content_type: str                # "url" | "file" | "hint"
    value: str                       # URL, file path, or free-text hint
    title: str = ""
    processed: bool = False
```

### QualityQuestion

```python
@dataclass
class QualityQuestion:
    question: str
    expected_answer: str
    actual_answer: str = ""
    score: float = 0.0
    passed: bool = False
```

### Persistence Layout

```
~/.cognithor/evolution/plans/
  └── versicherungsrecht-vvg/
       ├── plan.json                 # LearningPlan
       ├── subgoals/
       │    ├── vvg-gesetz.json
       │    ├── vag-aufsichtsrecht.json
       │    └── ...
       ├── quality/
       │    ├── test-2026-03-28.json
       │    └── coverage.json
       ├── uploads/                  # User-uploaded seed files
       │    └── VVG_Kommentar.pdf
       └── checkpoints/
```

### Storage Namespacing

- **Vault:** `vault/wissen/{goal_slug}/` — isolated folder per plan
- **Memory:** All chunks tagged with `topic={goal_slug}` — filterable
- **Graph:** Entities get `domain={goal_slug}` attribute — extractable subgraphs

## 5. Sub-Agent Details

### 5.1 StrategyPlanner

**Input:** Goal string + optional SeedSources
**Output:** LearningPlan with SubGoals, Sources, Schedules
**Method:** Direct `llm_fn` call with structured JSON prompt

Prompt includes seed sources if provided. LLM returns JSON with `sub_goals[]`, `sources[]`, `schedules[]`. Validated via Pydantic-like parsing with fallback retry on malformed JSON.

Also provides `replan(plan, new_context)` to extend an existing plan when HorizonScanner discovers new areas.

**Goal complexity detection:** The EvolutionLoop scout decides whether to delegate to DeepLearner based on heuristics: goal length > 10 words, contains expertise keywords ("Experte", "expert", "master", "learn everything", "deep dive"), or user explicitly created it via the Plans UI. Simple goals like "Python list comprehensions" stay in the lightweight research cycle.

### 5.2 ResearchAgent

**Input:** SourceSpec from a SubGoal
**Output:** List of `(url, raw_text)` tuples
**Method:** Direct `mcp_client.call_tool()` calls

Strategies:
- `full_page`: Single `web_fetch(url)` → Trafilatura extraction
- `sitemap_crawl`: Fetch index page → extract links → fetch each (rate-limited, max_pages cap)
- `rss`: Parse RSS feed → fetch only new entries (compare against last_fetched timestamp)
- `api`: `http_request` for structured data sources

Rate limiting: 2s between requests (existing web tools limit). Sitemap crawl: max 5 pages/minute. Idle check after every page — abort on user return.

### 5.3 KnowledgeBuilder

**Input:** Raw text + metadata (url, goal_slug, source_type)
**Output:** Vault entries, Memory chunks, Graph entities

Triple-write pipeline per document:
1. **Vault:** `vault_save(title, content, folder="wissen/{goal_slug}", tags, sources)` — direct call
2. **Memory:** Chunk text (512 tokens, 64 overlap) → `save_to_memory(chunk, tier="semantic", topic=goal_slug)` — direct call
3. **Graph:** LLM extracts entities + relations → `add_entity()` + `add_relation()` — via PGE loop (complex, needs security check)

Entity extraction prompt asks LLM to return structured `{entities: [{name, type, attributes}], relations: [{source, relation, target}]}`.

### 5.4 ScheduleManager

**Input:** ScheduleSpec list from LearningPlan
**Output:** Active cron jobs

Uses `cron_engine.add_cron_job()` directly. Cron fires → IncomingMessage with `[evolution-update]` prefix → Gateway recognizes prefix → delegates to `DeepLearner.process_scheduled_update(source_spec)` → ResearchAgent fetches only new content → KnowledgeBuilder indexes deltas.

### 5.5 QualityAssessor

**Input:** SubGoal with accumulated results
**Output:** coverage_score, quality_score, pass/fail, failed questions as new research targets

**Stage 1 — Coverage (no LLM):**
```
coverage = mean([
    vault_entries >= 5,
    chunks_created >= 20,
    entities_created >= 5,
    sources_fetched >= 3,
])
```
Must be >= `config.coverage_threshold` (default 0.7).

**Stage 2 — Self-Examination (LLM):**
LLM generates 5 domain questions with expected answers. Cognithor answers each using ONLY vault_search + search_memory (no web). LLM grades each answer 0.0-1.0. Must be >= `config.quality_threshold` (default 0.8).

Failed questions become new research directions for the SubGoal.

### 5.6 HorizonScanner

**Input:** Completed SubGoals, current graph state
**Output:** New SubGoals to add to the LearningPlan

**Mechanism A — LLM Exploration:**
Prompt: "Given what I've learned about [topics], what adjacent areas are critically relevant that the user probably hasn't considered?" → 3-5 expansion suggestions.

**Mechanism B — Graph Discovery:**
Find entities with high incoming reference count but low chunk depth (many relations, little content). These are structural blind spots.

Both feed into `StrategyPlanner.replan()` as new SubGoals.

## 6. Flow: Complete Cycle Example

```
Minute 0:   User enters "Werde Experte fuer deutsches Versicherungsrecht"
Minute 5:   IdleDetector triggers → Scout → DeepLearner
Minute 5-6: StrategyPlanner creates plan (8 SubGoals, 12 Sources, 2 Cron)
Minute 6-8: SubGoal 1 "VVG" → ResearchAgent crawls 215 paragraphs
Minute 8-12: KnowledgeBuilder: 215 Vault entries, 430 chunks, 45 entities
Minute 12-13: QualityAssessor: 82% quality, 1 gap found → auto-research
Minute 13-14: ScheduleManager creates 2 cron jobs (daily news, weekly BaFin)
Minute 14+: SubGoals 2-8 over next idle phases...
After all:  HorizonScanner → 4 new SubGoals → replan → cycle continues
Next day 6:00: Cron fetches versicherungsbote.de → indexes new articles
```

Every step checks IdleDetector. Every completed step creates a checkpoint. User return → immediate stop, resume later.

## 7. Error Handling

| Scenario | Strategy |
|----------|----------|
| Web fetch timeout | 3 retries (5s, 15s, 30s) → mark source "error" → LLM finds alternative |
| LLM returns invalid JSON | Retry with stricter prompt → retry simplified → mark plan "error" |
| Budget exhausted mid-SubGoal | Checkpoint progress → pause → resume next day |
| User returns during crawl | Immediate stop → checkpoint pages fetched → resume from next page |
| Contradictory information | Store both with provenance → QualityAssessor flags → research authoritative source |
| Goal too vague | StrategyPlanner asks LLM to scope into top-level areas → create broad plan |
| Source redesign breaks parsing | 3 days of parse errors → LLM suggests alternative sources |
| Concurrent plans | Round-robin by plan priority → 1 SubGoal per idle phase per plan |
| Disk space low | ResourceMonitor warns → pause indexing → user notification |

## 8. REST API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/evolution/plans` | List all LearningPlans (overview) |
| `GET` | `/api/v1/evolution/plans/{id}` | Plan detail with SubGoals, coverage, quality |
| `POST` | `/api/v1/evolution/plans` | Create new plan (triggers StrategyPlanner) |
| `PATCH` | `/api/v1/evolution/plans/{id}` | Pause / resume / delete plan |
| `POST` | `/api/v1/evolution/plans/{id}/test` | Trigger quality test manually |
| `GET` | `/api/v1/evolution/plans/{id}/quality` | Latest exam results |
| `POST` | `/api/v1/evolution/plans/{id}/seeds` | Add seed URL or hint |
| `POST` | `/api/v1/evolution/plans/{id}/upload` | Upload seed file (multipart) |
| `GET` | `/api/v1/evolution/plans/{id}/seeds` | List seed sources |
| `DELETE` | `/api/v1/evolution/plans/{id}/seeds/{idx}` | Remove seed |

## 9. Flutter UI

### Plans Overview Card

Shows all active/paused plans with progress bars (coverage + quality), SubGoal count, chunk/entity stats, last activity timestamp.

### Plan Detail View

- SubGoal list with status icons and coverage per goal
- Scheduled updates with next-run timestamps
- Recent quality test results with failed questions highlighted
- Horizon expansions (LLM-suggested + graph-discovered)
- Seed sources (user-provided) with processed status
- Actions: Pause, Delete, Force Quality Test, Add URL, Upload File, Add Hint

### Plan Creation Dialog

- Goal text field
- Optional seed sources: URL input, file upload (PDF/DOCX/TXT/MD/HTML), free-text hints
- Create button triggers StrategyPlanner

## 10. Config Extensions

```python
class EvolutionConfig(BaseModel):
    # ... existing Phase 1-4 fields ...

    # Deep Learning (Phase 5)
    deep_learning_enabled: bool = True
    max_concurrent_plans: int = 2          # 1-5
    max_pages_per_crawl: int = 50          # 5-500
    quality_threshold: float = 0.8         # 0.5-1.0
    coverage_threshold: float = 0.7        # 0.3-1.0
    auto_expand: bool = True               # HorizonScanner auto-adds SubGoals
```

## 11. File Structure

### New Files (7 + 7 tests)

```
src/jarvis/evolution/
    ├── models.py                # LearningPlan, SubGoal, SourceSpec, etc.
    ├── deep_learner.py          # DeepLearner orchestrator
    ├── strategy_planner.py      # Goal → LearningPlan via LLM
    ├── research_agent.py        # Web fetching + crawling
    ├── knowledge_builder.py     # Vault + Memory + Graph triple-write
    ├── schedule_manager.py      # Cron job creation
    ├── quality_assessor.py      # Coverage + self-examination
    └── horizon_scanner.py       # LLM exploration + graph discovery

tests/unit/
    ├── test_deep_learner.py
    ├── test_strategy_planner.py
    ├── test_research_agent.py
    ├── test_knowledge_builder.py
    ├── test_schedule_manager.py
    ├── test_quality_assessor.py
    └── test_horizon_scanner.py
```

### Modified Files

```
src/jarvis/evolution/loop.py         # Scout delegates to DeepLearner
src/jarvis/evolution/__init__.py     # New exports
src/jarvis/gateway/gateway.py        # DeepLearner wiring
src/jarvis/channels/config_routes.py # 10 new REST endpoints
src/jarvis/config.py                 # EvolutionConfig extensions
```

## 12. Implementation Phases

| Phase | Name | Sessions | Delivers |
|-------|------|----------|----------|
| **5A** | Data Model + StrategyPlanner | 1 | Goal → LearningPlan visible in API |
| **5B** | ResearchAgent + KnowledgeBuilder | 1-2 | SubGoals actually executed, knowledge indexed |
| **5C** | QualityAssessor + HorizonScanner + ScheduleManager | 1 | Self-testing, expansion, recurring updates |
| **5D** | Flutter UI + Seeds + Polish | 1 | Full user experience with plans dashboard |

Each phase is independently deployable and testable. Phase 5A gives immediate value (visible planning). Phase 5B is the core feature (actual knowledge building). Phase 5C adds intelligence (quality + expansion). Phase 5D completes the UX.
