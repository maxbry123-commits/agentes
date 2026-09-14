# Deep Research Analyst — Design Spec

**Date:** 2026-04-16
**Author:** Alexander Söllner (with Claude)
**Status:** Approved, pending implementation plan

---

## 1. Overview

Second paid Agent Pack for Cognithor. Extracts `deep_research_v2.py` from Core and adds 6 Pro features: multi-hop research, citation graph, source triangulation, Markdown/PDF export, research history, and a dedicated Flutter Research tab. Validates that the pack architecture works for **tool-packs** (MCP tool registration) in addition to **lead-source-packs** (LeadSource registration).

**Pricing:** €65 indie (~~€119~~) / €159 commercial (~~€299~~), EUR, Lemon Squeezy.

## 2. Extraction from Core

### Files to extract

- `src/cognithor/mcp/deep_research_v2.py` (221 LOC) — `CognithorSearchProvider`, `CognithorLLMProvider`, `DeepResearchV2Tool`

### References to clean up in Core

| File | What to remove |
|---|---|
| `src/cognithor/core/executor.py` | `deep_research` entries from timeout and context-window maps |
| `src/cognithor/core/gatekeeper.py` | `deep_research` from green-list |
| `src/cognithor/core/autonomous_orchestrator.py` | `deep_research` from tool references |
| `src/cognithor/mcp/bridge.py` | `deep_research`, `deep_research_v2`, `verified_web_lookup` from tool lists |

### What stays in Core (free)

- `web_search` — DuckDuckGo multi-backend, snippet results
- `search_and_read` — fetch + Trafilatura extraction, single source
- `web_fetch` — single URL fetch

## 3. Pro Features

### 3.1 Multi-hop Research Engine

Entry query → LLM generates 2-3 sub-queries → results synthesized → LLM decides: "sufficiently answered?" or "more hops needed?" → up to 5 hops.

Each hop:
1. Generate sub-queries from gaps in current knowledge
2. Search via Cognithor's `web_search` backend (DuckDuckGo/SearXNG/Brave fallback)
3. Fetch top 3-5 URLs per sub-query via `web_fetch` + Trafilatura
4. Extract content, deduplicate
5. LLM synthesis: integrate new findings into running report draft
6. Confidence check: enough evidence? → stop or continue

Stop conditions:
- `max_hops` reached (default 5, configurable)
- LLM confidence assessment says "sufficient"
- No new information found in last hop (stagnation detection)

**Module:** `src/engine.py` — `MultiHopResearchEngine`

### 3.2 Citation Graph

Every claim in the synthesis report is annotated with `[1]`, `[2]`, etc.

Source index at the end of the report:
```
## Sources
[1] "Title of Article" — https://example.com/article (fetched 2026-04-16, confidence: 87)
[2] "Another Source" — https://other.com/page (fetched 2026-04-16, confidence: 72)
```

Confidence scoring per source:
- Base score: 50
- +20 if domain is `.edu`, `.gov`, or known authoritative news domain
- +15 if cited by multiple hops (corroborated)
- +10 if content is recent (<30 days)
- -20 if content is paywalled/truncated
- Clamped to 0-100

**Module:** `src/citations.py` — `CitationBuilder`, `Source` dataclass

### 3.3 Source Triangulation

Every core claim in the report must be supported by ≥2 independent sources.

- After synthesis, LLM is prompted: "For each factual claim in this report, list which source numbers support it."
- Claims supported by only 1 source are marked `[unverified]`
- Contradictions are explicitly flagged: "⚠ Source [2] states X, but Source [5] states Y"
- The triangulation summary is appended as a section before Sources

**Module:** `src/triangulation.py` — `TriangulationChecker`

### 3.4 Markdown + PDF Export

Reports are saved to `~/.cognithor/research/reports/`:
- `<date>-<slug>.md` — Markdown with YAML frontmatter (query, date, hops, source count, avg confidence)
- `<date>-<slug>.pdf` — Clean PDF via `fpdf2` (already a Core dependency): title, body with citation superscripts, sources section with hyperlinks, Cognithor branding in header

**Module:** `src/export.py` — `MarkdownExporter`, `PdfExporter`

### 3.5 Research History

SQLite database at `~/.cognithor/research/history.db`.

Schema:
```sql
CREATE TABLE research (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    report_md TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    hops INTEGER NOT NULL,
    confidence_avg REAL NOT NULL,
    created_at REAL NOT NULL,
    export_path_md TEXT,
    export_path_pdf TEXT
);
CREATE VIRTUAL TABLE research_fts USING fts5(query, report_md, content=research, content_rowid=rowid);
```

Full-text search over queries + report content.

**Module:** `src/history.py` — `ResearchHistory`

### 3.6 Flutter Research Tab

8th tab in the sidebar. Only visible when the pack is loaded. Uses the same `PackPreviewOverlay` gating pattern as the Leads tab.

Screen layout:
- **Header:** Search input field + "Research" primary button
- **Active research:** Live progress indicator ("Hop 1/5 — Searching for 'LLM benchmarks 2026'..." with animated spinner)
- **Report view:** Markdown rendered with clickable citation links (opens source URL in browser)
- **History drawer/sidebar:** List of past researches — date, query preview, confidence badge (green/yellow/red), hop count
- **Action bar:** Export MD, Export PDF, Re-Run, Delete

Provider: `ResearchProvider` — fetches from `/api/v1/research/*` endpoints.

New files in Flutter:
- `lib/screens/research_screen.dart`
- `lib/providers/research_provider.dart`
- `lib/widgets/research/research_report_view.dart`
- `lib/widgets/research/research_history_list.dart`
- `lib/widgets/research/hop_progress_indicator.dart`

## 4. Pack Structure

```
deep-research-analyst/
├── pack.py                    # AgentPack subclass — registers MCP tools + REST routes
├── pack_manifest.json
├── eula.md
├── src/
│   ├── __init__.py
│   ├── engine.py              # MultiHopResearchEngine (orchestrator)
│   ├── citations.py           # CitationBuilder, Source dataclass
│   ├── triangulation.py       # TriangulationChecker
│   ├── export.py              # MarkdownExporter, PdfExporter
│   ├── history.py             # ResearchHistory (SQLite + FTS5)
│   ├── tools.py               # MCP tool definitions (deep_research_pro, research_export_*, research_history)
│   ├── routes.py              # REST endpoint handlers
│   ├── search_provider.py     # CognithorSearchProvider (from deep_research_v2.py)
│   └── llm_provider.py        # CognithorLLMProvider (from deep_research_v2.py)
├── tests/
│   ├── test_engine.py
│   ├── test_citations.py
│   ├── test_triangulation.py
│   ├── test_export.py
│   └── test_history.py
└── catalog/
    └── catalog.mdx
```

## 5. Pack Registration

```python
class Pack(AgentPack):
    def register(self, context: PackContext) -> None:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        from engine import MultiHopResearchEngine
        from history import ResearchHistory
        from tools import register_research_tools
        from routes import register_research_routes

        # Build the engine
        llm_fn = _extract_llm_fn(context.gateway)
        web_tools = _extract_web_tools(context.gateway)
        history = ResearchHistory()
        self._engine = MultiHopResearchEngine(
            llm_fn=llm_fn,
            web_tools=web_tools,
            history=history,
        )

        # Register MCP tools (new path — not leads, but mcp_client)
        if context.mcp_client:
            register_research_tools(context.mcp_client, self._engine)

        # Register REST routes for the Flutter Research tab
        if context.gateway and hasattr(context.gateway, '_api'):
            register_research_routes(context.gateway._api, self._engine, history)
```

### REST Endpoints (registered by the pack)

```
POST /api/v1/research/query          # Start a new research (async, returns research_id)
GET  /api/v1/research/{id}           # Get research result (report + sources + status)
GET  /api/v1/research/{id}/progress  # Get live progress (current hop, sub-queries, status)
GET  /api/v1/research/history        # List all past researches
DELETE /api/v1/research/{id}         # Delete a research
POST /api/v1/research/{id}/export    # Export as MD/PDF (body: {"format": "md"|"pdf"})
POST /api/v1/research/{id}/rerun     # Re-run a past research with fresh sources
```

## 6. Core Changes

### New REST endpoint

`GET /api/v1/packs/loaded` — returns list of currently loaded packs. Needed so Flutter can gate tabs for ANY pack type (not just lead-source packs).

```json
{
  "packs": [
    {"qualified_id": "cognithor-official/reddit-lead-hunter-pro", "version": "1.2.0"},
    {"qualified_id": "cognithor-official/deep-research-analyst", "version": "1.0.0"}
  ]
}
```

Wired into `channels/config_routes.py`, reads from `gateway._pack_loader.loaded()`.

### Flutter: `PacksProvider`

New provider (or extend `SourcesProvider`) that fetches `/api/v1/packs/loaded` and exposes `hasPackLoaded(qualifiedId)`. Used by `main_shell.dart` to gate the Research tab.

### `known_packs.dart` update

Add Deep Research Analyst entry with `tabId: 'research'`, icon `Icons.biotech`, color `#00BCD4` (teal).

### `main_shell.dart` update

Add Research tab conditionally — visible when `deep-research-analyst` pack is loaded (via PacksProvider), otherwise shows PackPreviewOverlay with fake research UI.

## 7. Manifest

```json
{
  "schema_version": 1,
  "namespace": "cognithor-official",
  "pack_id": "deep-research-analyst",
  "version": "1.0.0",
  "display_name": "Deep Research Analyst",
  "description": "Multi-hop web research with citations, source triangulation, and PDF export. Your private Perplexity replacement, fully local.",
  "license": "proprietary",
  "min_cognithor_version": ">=0.92.0",
  "entrypoint": "pack.py",
  "eula_sha256": "TO_BE_COMPUTED",
  "publisher": {
    "id": "cognithor-official",
    "display_name": "Cognithor",
    "website": "https://cognithor.ai",
    "contact_email": "support@cognithor.ai",
    "payout_provider": "lemonsqueezy"
  },
  "revenue_share": {"creator": 70, "platform": 30},
  "lead_sources": [],
  "tools": ["deep_research_pro", "research_export_md", "research_export_pdf", "research_history"],
  "checkout_url": null,
  "commercial_checkout_url": null,
  "pricing": {
    "indie": {"list_price": 119, "launch_price": 65, "post_launch_price": 79, "launch_cap": 100, "currency": "EUR"},
    "commercial": {"list_price": 299, "launch_price": 159, "post_launch_price": 199, "launch_cap": 25, "currency": "EUR"}
  }
}
```

## 8. Test Strategy

### Unit tests (in pack `tests/`)

- `test_engine.py` — Multi-hop flow with mocked LLM + mocked search. Test: 1-hop sufficient, 3-hop iterative, max-hop stop, stagnation stop.
- `test_citations.py` — Citation numbering, source dedup, confidence scoring, domain authority heuristic.
- `test_triangulation.py` — Claims with 2+ sources pass, single-source claims marked [unverified], contradictions detected.
- `test_export.py` — Markdown output has frontmatter + citations + sources section. PDF generates without crash (fpdf2).
- `test_history.py` — Save, retrieve, full-text search, delete. SQLite FTS5.

### Integration tests

- Pack install → load → MCP tools registered → `deep_research_pro` tool callable
- REST routes registered → `/api/v1/research/query` returns research_id
- History persisted → `/api/v1/research/history` returns past entries

### E2E test

Same pattern as RLH Pro:
1. `cognithor pack install deep-research-analyst.zip`
2. PackLoader discovers + loads
3. `pack.register(context)` runs without error
4. MCP tools registered
5. REST routes accessible
6. Flutter Research tab visible (with pack loaded) / PackPreviewOverlay (without)

## 9. Migration Stages

### Stage 1 — Core cleanup
Delete `deep_research_v2.py`, remove references from executor/gatekeeper/orchestrator/bridge. Add `GET /api/v1/packs/loaded`. Add `PacksProvider` to Flutter. Update `known_packs.dart` + `main_shell.dart`.

### Stage 2 — Build the pack
Create `deep-research-analyst/` in cognithor-packs repo. Port search_provider + llm_provider from the extracted file. Build engine.py, citations.py, triangulation.py, export.py, history.py, tools.py, routes.py. Write pack.py. Write manifest + EULA. Write catalog.mdx.

### Stage 3 — Tests
Unit tests for all 5 modules. Integration test for pack load + tool registration + REST. E2E test.

### Stage 4 — Flutter Research tab
`research_screen.dart`, `research_provider.dart`, widgets (report view, history list, hop progress). Wire into `main_shell.dart`. PackPreviewOverlay for uninstalled state.

### Stage 5 — Ship
Build zip, validate, push to packs repo, CI regenerates index, site shows the pack. Create LS product, upload zip, set checkout URL.

## 10. Acceptance Criteria

- [ ] `deep_research_v2.py` absent from Core
- [ ] `web_search` + `search_and_read` still work in Core without the pack
- [ ] `GET /api/v1/packs/loaded` returns loaded pack list
- [ ] Pack installs via `cognithor pack install <zip>` with EULA click-through
- [ ] PackLoader discovers and loads the pack (registers MCP tools, not LeadSource)
- [ ] `deep_research_pro` MCP tool is callable and produces a multi-hop report with citations
- [ ] Source triangulation flags single-source claims as [unverified]
- [ ] Markdown export produces valid .md with frontmatter
- [ ] PDF export produces readable .pdf with citations and branding
- [ ] Research history persists across restarts (SQLite)
- [ ] Full-text search over past researches works
- [ ] Flutter Research tab visible when pack loaded, PackPreviewOverlay when not
- [ ] Research tab shows live hop progress during active research
- [ ] Report view renders citations as clickable links
- [ ] History drawer shows past researches with confidence badges
- [ ] Export buttons work (MD + PDF download)
- [ ] Pack appears on cognithor.ai/packs after push to packs repo
- [ ] LS checkout functional
- [ ] All unit + integration + E2E tests pass
