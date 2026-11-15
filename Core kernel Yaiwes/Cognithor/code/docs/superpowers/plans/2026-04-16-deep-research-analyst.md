# Deep Research Analyst Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Deep Research Analyst as the second paid Agent Pack — multi-hop web research with citations, source triangulation, Markdown/PDF export, SQLite history, and a dedicated Flutter Research tab.

**Architecture:** Extract `deep_research_v2.py` from Core, delete references, add `GET /api/v1/packs/loaded`. Build the pack in `cognithor-packs/deep-research-analyst/` with 9 source modules. Register MCP tools + REST routes via `PackContext`. Flutter gets a Research tab gated on pack presence via new `PacksProvider`.

**Tech Stack:** Python 3.13, Pydantic v2, fpdf2 (PDF), SQLite + FTS5 (history), Flutter 3 + Provider, Next.js 16 (site catalog auto-sync).

**Spec:** [`docs/superpowers/specs/2026-04-16-deep-research-analyst-design.md`](../specs/2026-04-16-deep-research-analyst-design.md)

---

## File Structure

### Core changes (`D:\Jarvis\jarvis complete v20\`)

```
DELETE: src/cognithor/mcp/deep_research_v2.py
MODIFY: src/cognithor/core/executor.py         — remove deep_research entries
MODIFY: src/cognithor/core/gatekeeper.py        — remove deep_research from green-list
MODIFY: src/cognithor/core/autonomous_orchestrator.py — remove deep_research references
MODIFY: src/cognithor/mcp/bridge.py             — remove deep_research/verified_web_lookup
MODIFY: src/cognithor/channels/config_routes.py — add GET /api/v1/packs/loaded
CREATE: flutter_app/lib/providers/packs_provider.dart
CREATE: flutter_app/lib/screens/research_screen.dart
CREATE: flutter_app/lib/providers/research_provider.dart
CREATE: flutter_app/lib/widgets/research/research_report_view.dart
CREATE: flutter_app/lib/widgets/research/research_history_list.dart
CREATE: flutter_app/lib/widgets/research/hop_progress_indicator.dart
MODIFY: flutter_app/lib/data/known_packs.dart   — add deep-research-analyst entry
MODIFY: flutter_app/lib/screens/main_shell.dart  — add Research tab
MODIFY: flutter_app/lib/main.dart               — add PacksProvider + ResearchProvider
```

### Pack (`D:\Jarvis\cognithor-packs\deep-research-analyst\`)

```
CREATE: pack.py
CREATE: pack_manifest.json
CREATE: eula.md
CREATE: src/__init__.py
CREATE: src/engine.py              — MultiHopResearchEngine
CREATE: src/citations.py           — CitationBuilder, Source dataclass
CREATE: src/triangulation.py       — TriangulationChecker
CREATE: src/export.py              — MarkdownExporter, PdfExporter
CREATE: src/history.py             — ResearchHistory (SQLite + FTS5)
CREATE: src/tools.py               — MCP tool definitions
CREATE: src/routes.py              — REST endpoint handlers
CREATE: src/search_provider.py     — CognithorSearchProvider (from deep_research_v2)
CREATE: src/llm_provider.py        — CognithorLLMProvider (from deep_research_v2)
CREATE: tests/__init__.py
CREATE: tests/conftest.py
CREATE: tests/test_engine.py
CREATE: tests/test_citations.py
CREATE: tests/test_triangulation.py
CREATE: tests/test_export.py
CREATE: tests/test_history.py
CREATE: catalog/catalog.mdx
```

---

## Stage 1 — Core Cleanup + New Endpoints

### Task 1: Delete deep_research_v2.py + clean references

**Files:**
- Delete: `src/cognithor/mcp/deep_research_v2.py`
- Modify: `src/cognithor/core/executor.py`
- Modify: `src/cognithor/core/gatekeeper.py`
- Modify: `src/cognithor/core/autonomous_orchestrator.py`
- Modify: `src/cognithor/mcp/bridge.py`

- [ ] **Step 1:** Delete the file
```bash
rm -f "D:/Jarvis/jarvis complete v20/src/cognithor/mcp/deep_research_v2.py"
```

- [ ] **Step 2:** Remove `deep_research` entries from `executor.py` — find the timeout and context-window dicts, remove `"deep_research": ...` lines

- [ ] **Step 3:** Remove `"deep_research"` from `gatekeeper.py` green-list

- [ ] **Step 4:** Remove `"deep_research"`, `"deep_research_v2"`, `"verified_web_lookup"` from `mcp/bridge.py` tool lists

- [ ] **Step 5:** Remove `"deep_research"` and `"verified_web_lookup"` from `autonomous_orchestrator.py` tool references

- [ ] **Step 6:** Verify `web_search` and `search_and_read` still referenced (they stay in Core)
```bash
grep -n "web_search\|search_and_read" src/cognithor/mcp/bridge.py | head -5
```

- [ ] **Step 7:** Run ruff + existing tests
```bash
python -m ruff check src/cognithor/mcp/ src/cognithor/core/executor.py src/cognithor/core/gatekeeper.py src/cognithor/core/autonomous_orchestrator.py
python -m pytest tests/test_packs/ tests/test_leads/ -q
```

- [ ] **Step 8:** Commit
```bash
git add -u && git commit -m "refactor(core): remove deep_research_v2 — extracted to agent pack"
```

---

### Task 2: Add GET /api/v1/packs/loaded endpoint

**Files:**
- Modify: `src/cognithor/channels/config_routes.py`

- [ ] **Step 1:** Find where the pack-related routes could go (near the existing `/api/v1/leads/sources` endpoint)

- [ ] **Step 2:** Add the endpoint:
```python
@app.get("/api/v1/packs/loaded", dependencies=deps)
async def list_loaded_packs() -> dict[str, Any]:
    """Return currently loaded packs for Flutter tab gating."""
    loader = getattr(gateway, "_pack_loader", None)
    if loader is None:
        return {"packs": []}
    return {
        "packs": [
            {
                "qualified_id": p.manifest.qualified_id,
                "version": p.manifest.version,
                "display_name": p.manifest.display_name,
                "tools": p.manifest.tools,
                "lead_sources": p.manifest.lead_sources,
            }
            for p in loader.loaded()
        ]
    }
```

- [ ] **Step 3:** Ruff check + commit
```bash
python -m ruff check src/cognithor/channels/config_routes.py
git add src/cognithor/channels/config_routes.py && git commit -m "feat(core): add GET /api/v1/packs/loaded for Flutter tab gating"
```

---

## Stage 2 — Build the Pack

### Task 3: Scaffold pack directory + port search/LLM providers

**Files:**
- Create: `cognithor-packs/deep-research-analyst/` structure
- Create: `src/search_provider.py`, `src/llm_provider.py`

- [ ] **Step 1:** Scaffold
```bash
cd "D:/Jarvis/cognithor-packs" && mkdir -p deep-research-analyst/src deep-research-analyst/tests deep-research-analyst/catalog
touch deep-research-analyst/src/__init__.py deep-research-analyst/tests/__init__.py
```

- [ ] **Step 2:** Port `CognithorSearchProvider` from the deleted `deep_research_v2.py` into `src/search_provider.py`. Change imports from `cognithor.social` to `cognithor.leads` (or keep generic since this doesn't use leads). Use absolute imports only (no relative `.` imports).

- [ ] **Step 3:** Port `CognithorLLMProvider` into `src/llm_provider.py`.

- [ ] **Step 4:** Write `tests/conftest.py`:
```python
from __future__ import annotations
import sys
from pathlib import Path
_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))
```

---

### Task 4: Build MultiHopResearchEngine

**Files:**
- Create: `deep-research-analyst/src/engine.py`
- Create: `deep-research-analyst/tests/test_engine.py`

- [ ] **Step 1:** Write test first — mock LLM + mock search:
```python
class TestMultiHopEngine:
    async def test_single_hop_sufficient(self):
        """LLM says confident after first hop → stops."""
    async def test_multi_hop_iterative(self):
        """LLM says not confident → generates follow-up queries → 3 hops."""
    async def test_max_hops_stop(self):
        """Reaches max_hops=3 → stops even if not confident."""
    async def test_stagnation_stop(self):
        """No new info in last hop → stops early."""
    async def test_report_has_citations(self):
        """Final report contains [1], [2] citation markers."""
```

- [ ] **Step 2:** Implement `engine.py`:
```python
class MultiHopResearchEngine:
    def __init__(self, llm_fn, web_tools, history=None, max_hops=5):
        ...
    async def research(self, query: str) -> ResearchResult:
        """Run multi-hop research. Returns ResearchResult with report, sources, hops."""
        ...
```

`ResearchResult` dataclass: `id`, `query`, `report_md`, `sources` (list of `Source`), `hops`, `confidence_avg`, `created_at`.

Each hop:
1. `_generate_sub_queries(query, current_knowledge)` → LLM prompt
2. `_search_and_fetch(sub_queries)` → search provider + page fetch
3. `_synthesize(query, all_content, sources)` → LLM synthesis with citation instructions
4. `_assess_confidence(report)` → LLM: "Is this sufficient? Reply CONFIDENT or NEED_MORE with follow-up queries"

- [ ] **Step 3:** Run tests, fix until green
- [ ] **Step 4:** Commit in packs repo

---

### Task 5: Build CitationBuilder

**Files:**
- Create: `deep-research-analyst/src/citations.py`
- Create: `deep-research-analyst/tests/test_citations.py`

- [ ] **Step 1:** Write tests:
```python
class TestCitationBuilder:
    def test_number_sources_sequentially(self):
    def test_dedup_same_url(self):
    def test_confidence_scoring_edu_domain(self):
    def test_confidence_scoring_corroborated(self):
    def test_format_sources_section(self):
```

- [ ] **Step 2:** Implement:
```python
@dataclass
class Source:
    url: str
    title: str
    fetched_at: float
    confidence: int  # 0-100
    content_snippet: str = ""
    domain: str = ""
    corroborated_by: list[int] = field(default_factory=list)

class CitationBuilder:
    def add_source(self, url, title, content, ...) -> int:  # returns citation number
    def score_confidence(self, source: Source) -> int:
    def format_sources_section(self) -> str:  # "[1] Title — url (fetched ..., confidence: 87)"
    def get_sources(self) -> list[Source]:
```

- [ ] **Step 3:** Tests green, commit

---

### Task 6: Build TriangulationChecker

**Files:**
- Create: `deep-research-analyst/src/triangulation.py`
- Create: `deep-research-analyst/tests/test_triangulation.py`

- [ ] **Step 1:** Write tests:
```python
class TestTriangulation:
    async def test_claims_with_two_sources_pass(self):
    async def test_single_source_marked_unverified(self):
    async def test_contradictions_flagged(self):
    async def test_triangulation_summary_appended(self):
```

- [ ] **Step 2:** Implement:
```python
class TriangulationChecker:
    def __init__(self, llm_fn):
        ...
    async def check(self, report_md: str, sources: list[Source]) -> TriangulationResult:
        """Prompt LLM to map claims→sources. Flag single-source and contradictions."""
```

`TriangulationResult`: `verified_claims: int`, `unverified_claims: int`, `contradictions: list[str]`, `annotated_report: str`.

- [ ] **Step 3:** Tests green, commit

---

### Task 7: Build Export (Markdown + PDF)

**Files:**
- Create: `deep-research-analyst/src/export.py`
- Create: `deep-research-analyst/tests/test_export.py`

- [ ] **Step 1:** Write tests:
```python
class TestMarkdownExporter:
    def test_frontmatter_present(self):
    def test_citations_in_body(self):
    def test_sources_section_at_end(self):
    def test_file_written_to_disk(self, tmp_path):

class TestPdfExporter:
    def test_pdf_generates_without_crash(self, tmp_path):
    def test_pdf_has_title_and_sources(self, tmp_path):
```

- [ ] **Step 2:** Implement:
```python
class MarkdownExporter:
    def export(self, result: ResearchResult, path: Path) -> Path:
        """Write .md with YAML frontmatter + report + sources."""

class PdfExporter:
    def export(self, result: ResearchResult, path: Path) -> Path:
        """Write .pdf via fpdf2 with title, body, sources, branding."""
```

- [ ] **Step 3:** Tests green, commit

---

### Task 8: Build ResearchHistory

**Files:**
- Create: `deep-research-analyst/src/history.py`
- Create: `deep-research-analyst/tests/test_history.py`

- [ ] **Step 1:** Write tests:
```python
class TestResearchHistory:
    def test_save_and_retrieve(self, tmp_path):
    def test_list_all(self, tmp_path):
    def test_fulltext_search(self, tmp_path):
    def test_delete(self, tmp_path):
    def test_persistence_across_instances(self, tmp_path):
```

- [ ] **Step 2:** Implement:
```python
class ResearchHistory:
    def __init__(self, db_path: str | None = None):
        # Default: ~/.cognithor/research/history.db
    def save(self, result: ResearchResult) -> None:
    def get(self, research_id: str) -> ResearchResult | None:
    def list_all(self, limit=50, offset=0) -> list[ResearchResult]:
    def search(self, query: str) -> list[ResearchResult]:
    def delete(self, research_id: str) -> None:
```

SQLite with FTS5 virtual table for full-text search.

- [ ] **Step 3:** Tests green, commit

---

### Task 9: Build MCP tools + REST routes

**Files:**
- Create: `deep-research-analyst/src/tools.py`
- Create: `deep-research-analyst/src/routes.py`

- [ ] **Step 1:** Write `tools.py` — register MCP tools:
```python
def register_research_tools(mcp_client, engine: MultiHopResearchEngine):
    """Register: deep_research_pro, research_export_md, research_export_pdf, research_history"""
```

Tools:
- `deep_research_pro` — takes query string, returns report markdown
- `research_export_md` — takes research_id, exports to disk, returns path
- `research_export_pdf` — same but PDF
- `research_history` — takes optional search query, returns list

- [ ] **Step 2:** Write `routes.py` — REST endpoints:
```python
def register_research_routes(app, engine, history):
    @app.post("/api/v1/research/query")
    @app.get("/api/v1/research/{research_id}")
    @app.get("/api/v1/research/{research_id}/progress")
    @app.get("/api/v1/research/history")
    @app.delete("/api/v1/research/{research_id}")
    @app.post("/api/v1/research/{research_id}/export")
    @app.post("/api/v1/research/{research_id}/rerun")
```

- [ ] **Step 3:** Commit

---

### Task 10: Write pack.py + manifest + EULA + catalog

**Files:**
- Create: `deep-research-analyst/pack.py`
- Create: `deep-research-analyst/pack_manifest.json`
- Create: `deep-research-analyst/eula.md`
- Create: `deep-research-analyst/catalog/catalog.mdx`

- [ ] **Step 1:** Write `pack.py`:
```python
class Pack(AgentPack):
    def register(self, context: PackContext) -> None:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        from engine import MultiHopResearchEngine
        from history import ResearchHistory
        from search_provider import CognithorSearchProvider
        from llm_provider import CognithorLLMProvider
        from tools import register_research_tools
        from routes import register_research_routes

        # Extract LLM + web tools from gateway
        gw = context.gateway
        llm_fn = None
        web_tools = None
        if gw and hasattr(gw, "_ollama") and gw._ollama:
            model = getattr(gw._config.models.planner, "name", "qwen3:27b") if gw._config else "qwen3:27b"
            ollama = gw._ollama
            async def _llm(**kw):
                return await ollama.chat(model=model, **kw)
            llm_fn = _llm
        if gw and hasattr(gw, "_web_tools"):
            web_tools = gw._web_tools

        search = CognithorSearchProvider(web_tools) if web_tools else None
        llm = CognithorLLMProvider(llm_fn) if llm_fn else None
        history = ResearchHistory()
        self._engine = MultiHopResearchEngine(llm=llm, search=search, history=history)

        if context.mcp_client:
            register_research_tools(context.mcp_client, self._engine)
        if gw and hasattr(gw, "_api"):
            register_research_routes(gw._api, self._engine, history)
```

- [ ] **Step 2:** Write manifest (from spec §7), compute EULA hash, write catalog.mdx

- [ ] **Step 3:** Validate: `python scripts/validate_pack.py deep-research-analyst`

- [ ] **Step 4:** Commit

---

### Task 11: Pack integration test

- [ ] **Step 1:** Build zip, install locally, verify PackLoader loads it and MCP tools register:
```bash
# Build zip
python -c "..." # same zipfile pattern as RLH Pro

# Install
echo "y" | python -m cognithor pack install <zip>

# Verify load
python -c "
from cognithor.packs.loader import PackLoader
from cognithor.packs.interface import PackContext
loader = PackLoader(packs_dir=..., cognithor_version='0.92.0')
ctx = PackContext()
loader.load_all(ctx)
for p in loader.loaded():
    print(p.manifest.qualified_id, p.manifest.tools)
"
```

- [ ] **Step 2:** Run pack unit tests:
```bash
cd "D:/Jarvis/cognithor-packs/deep-research-analyst" && python -m pytest tests/ --import-mode=importlib -q
```

- [ ] **Step 3:** Commit + push packs repo. Verify CI generates index.json with 5 packs.

---

## Stage 3 — Flutter Research Tab

### Task 12: Add PacksProvider

**Files:**
- Create: `flutter_app/lib/providers/packs_provider.dart`
- Modify: `flutter_app/lib/main.dart`

- [ ] **Step 1:** Write provider that fetches `GET /api/v1/packs/loaded`:
```dart
class PacksProvider extends ChangeNotifier {
    List<LoadedPack> _packs = [];
    bool hasPackLoaded(String qualifiedId) => _packs.any((p) => p.qualifiedId == qualifiedId);
    Future<void> refresh() async { ... }
}
```

- [ ] **Step 2:** Wire into MultiProvider in `main.dart`
- [ ] **Step 3:** Commit

---

### Task 13: Add ResearchProvider

**Files:**
- Create: `flutter_app/lib/providers/research_provider.dart`

- [ ] **Step 1:** Provider that talks to `/api/v1/research/*`:
```dart
class ResearchProvider extends ChangeNotifier {
    Future<String> startResearch(String query) async { ... }  // returns research_id
    Future<ResearchResult> getResult(String id) async { ... }
    Future<List<ResearchSummary>> getHistory() async { ... }
    Future<void> deleteResearch(String id) async { ... }
    Future<String> exportResearch(String id, String format) async { ... }
}
```

- [ ] **Step 2:** Commit

---

### Task 14: Build Research widgets

**Files:**
- Create: `flutter_app/lib/widgets/research/research_report_view.dart`
- Create: `flutter_app/lib/widgets/research/research_history_list.dart`
- Create: `flutter_app/lib/widgets/research/hop_progress_indicator.dart`

- [ ] **Step 1:** `research_report_view.dart` — renders Markdown report with clickable citation links
- [ ] **Step 2:** `research_history_list.dart` — list of past researches with date, query preview, confidence badge
- [ ] **Step 3:** `hop_progress_indicator.dart` — animated progress showing current hop + sub-query
- [ ] **Step 4:** Commit

---

### Task 15: Build ResearchScreen + wire into MainShell

**Files:**
- Create: `flutter_app/lib/screens/research_screen.dart`
- Modify: `flutter_app/lib/data/known_packs.dart`
- Modify: `flutter_app/lib/screens/main_shell.dart`
- Modify: `flutter_app/lib/main.dart`

- [ ] **Step 1:** Write `research_screen.dart`:
  - Search input + "Research" button
  - Active research: HopProgressIndicator
  - Report view: ResearchReportView
  - History drawer: ResearchHistoryList
  - Action bar: Export MD, Export PDF, Re-Run, Delete

- [ ] **Step 2:** Add deep-research-analyst to `known_packs.dart`:
```dart
KnownPack(
    qualifiedId: 'cognithor-official/deep-research-analyst',
    packId: 'deep-research-analyst',
    displayName: 'Deep Research Analyst',
    tagline: 'Multi-hop web research with citations. Your private Perplexity.',
    featureBullets: [
        'Multi-hop iterative research (up to 5 hops)',
        'Citation graph with confidence scores',
        'Source triangulation — flags unverified claims',
    ],
    priceBadge: 'ab 65 EUR',
    listPriceBadge: '119 EUR',
    packDetailUrl: 'https://cognithor.ai/packs/deep-research-analyst',
    icon: Icons.biotech,
    accentColor: Color(0xFF00BCD4),
    sourceId: 'research',
)
```

- [ ] **Step 3:** Update `main_shell.dart` — add Research tab gated on `PacksProvider.hasPackLoaded('cognithor-official/deep-research-analyst')`. Show `PackPreviewOverlay` with fake research UI when not installed.

- [ ] **Step 4:** Wire `ResearchProvider` + `PacksProvider` into `main.dart` MultiProvider

- [ ] **Step 5:** Flutter analyze, commit

---

## Stage 4 — Core tests + validation

### Task 16: Core validation gate

- [ ] **Step 1:** Ruff check + format
```bash
python -m ruff check src/cognithor/ && python -m ruff format --check src/cognithor/
```

- [ ] **Step 2:** Full Core test suite
```bash
python -m pytest tests/ -q --ignore=tests/test_reallife -x
```

- [ ] **Step 3:** Flutter analyze
```bash
cd flutter_app && flutter analyze lib/
```

- [ ] **Step 4:** Commit + push Core

---

## Stage 5 — Ship

### Task 17: Push packs repo + verify site

- [ ] **Step 1:** Regenerate index.json, commit, push packs repo
- [ ] **Step 2:** Verify CI runs + deploy hook fires
- [ ] **Step 3:** Check cognithor.ai/packs — Deep Research Analyst should appear
- [ ] **Step 4:** Build zip for LS upload:
```bash
python -c "
import zipfile
from pathlib import Path
src = Path('deep-research-analyst')
out = Path('D:/Jarvis/deep-research-analyst-1.0.0.zip')
skip = {'tests', '__pycache__', '.pytest_cache'}
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in sorted(src.rglob('*')):
        if any(s in f.parts for s in skip): continue
        if f.is_file(): zf.write(f, str(f.relative_to(src.parent)))
print(f'Built: {out}')
"
```

- [ ] **Step 5:** E2E test: install → load → verify tools registered
- [ ] **Step 6:** Create LS product, upload zip, set checkout URL in manifest, push
- [ ] **Step 7:** Tag + final commit

---

## Acceptance Criteria Checklist

- [ ] `deep_research_v2.py` absent from Core
- [ ] `web_search` + `search_and_read` still work
- [ ] `GET /api/v1/packs/loaded` returns loaded packs
- [ ] Pack installs via `cognithor pack install`
- [ ] PackLoader loads the pack (MCP tools, not LeadSource)
- [ ] `deep_research_pro` produces multi-hop report with `[1]` citations
- [ ] Triangulation flags `[unverified]` claims
- [ ] Markdown export has frontmatter + sources
- [ ] PDF export readable with branding
- [ ] History persists in SQLite + FTS5 search works
- [ ] Flutter Research tab visible when pack loaded
- [ ] PackPreviewOverlay when not loaded
- [ ] Pack on cognithor.ai/packs after push
- [ ] All tests pass
