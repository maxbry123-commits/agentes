# Memory Preprocessing Pipeline — Design Spec

**Date**: 2026-04-01
**Status**: Approved
**Scope**: Identity Memory only (memories.json + ChromaDB VectorStore)

## Problem

Cognithor's Identity Memory contains 3172 entries of which:
- 76% are truncated at exactly 1000 characters (mid-sentence)
- 15% are raw PDF artifacts (binary streams, `/Rect`, `endobj`)
- ~17% are near-duplicates (same first 80 characters)
- 100% have hardcoded `confidence=0.5` and `memory_type=semantic`
- 0% have meaningful tags or source differentiation

Root cause: `MemoryManager._sync_to_identity()` applies `content[:1000]` truncation with no quality filtering, no summarization, no classification, and no deduplication before insert.

## Solution

Replace raw truncation with an intelligent preprocessing pipeline in `KnowledgeBuilder`. Reset Identity Memory to genesis-only state and rebuild through normal ATL/Deep Learner operation.

### Architecture Decision: Option C

The Semantic Memory (RAG chunks in SQLite FTS5) and the Identity Memory (Cognithor's cognitive recall) serve different purposes:

| | Semantic Memory (RAG) | Identity Memory (Cognithor) |
|---|---|---|
| Purpose | Find precise text fragments | "What do I know about this topic?" |
| Granularity | 512-token chunks | 1 summary per source document |
| Query | Embedding search, FTS5 | Cognitive recall |
| Ideal | Many small, precise pieces | Few, high-quality knowledge entries |

**Decision**: KnowledgeBuilder continues chunking for RAG (unchanged). A new Step 4 in `build()` produces a single LLM-summarized entry per document for Identity Memory. The old `_sync_to_identity()` call in `index_text()` is removed.

## Data Flow

```
Web-Fetch / ATL Research
  -> KnowledgeBuilder.build()
    -> Step 1: Vault save (UNCHANGED)
    -> Step 2: Chunks -> Semantic Memory via save_to_memory (UNCHANGED)
    -> Step 3: Entity extraction -> Knowledge Graph (UNCHANGED)
    -> Step 4 (NEW): _summarize_for_identity()
        -> Quality Gate: _is_usable_content() [already exists]
        -> Source Confidence: _score_source_confidence(url)
        -> LLM Call: summary + memory_type + tags (1 call per document)
        -> JSON parsing with 4-tier fallback
        -> Dedup Check: ContentDeduplicator.content_hash()
        -> MemoryManager.sync_document_to_identity()
          -> adapter.store_from_cognithor()
```

**ATL-synthesized content** (`already_summarized=True`): Skips the LLM call in Step 4. Content goes directly to Identity with type/tags from caller and confidence from URL.

## Component Changes

### 1. `knowledge_builder.py` — New Step 4

#### New method: `_summarize_for_identity()`

```python
async def _summarize_for_identity(
    self,
    text: str,
    url: str,
    *,
    already_summarized: bool = False,
) -> None:
```

**When `already_summarized=False`** (normal web fetches):
1. Quality gate: `_is_usable_content(text)` — reject PDF artifacts, too-short
2. LLM call with prompt (see Prompt Design below)
3. Parse JSON response with 4-tier fallback
4. If `is_useful == false` -> skip
5. Dedup: `content_hash(summary)` against `_identity_seen_hashes`
6. `self._memory_manager.sync_document_to_identity(summary, type, confidence, tags)`

**When `already_summarized=True`** (ATL synthesis):
1. Quality gate: `_is_usable_content(text, min_chars=100)`
2. Source confidence from URL
3. Dedup check
4. `self._memory_manager.sync_document_to_identity(text, "semantic", confidence, [goal_slug])`

#### New constructor parameter

```python
def __init__(
    self,
    mcp_client,
    llm_fn=None,
    goal_slug="",
    knowledge_validator=None,
    goal_index=None,
    entity_llm_fn=None,
    memory_manager=None,  # NEW — optional, Step 4 skipped if None
)
```

#### New instance state

```python
self._memory_manager = memory_manager
self._identity_dedup = ContentDeduplicator(similarity_threshold=0.85)
self._identity_seen_hashes: set[str] = set()
```

#### `build()` new parameter

```python
async def build(
    self,
    fetch_result: FetchResult,
    *,
    skip_entity_extraction: bool = False,
    min_content_chars: int = 200,
    already_summarized: bool = False,  # NEW
) -> BuildResult:
```

Step 4 is called at the end of `build()`, after entity extraction. It is wrapped in try/except — failures are logged but never block the existing pipeline.

### 2. `manager.py` — New public API

#### Remove: `_sync_to_identity()` call in `index_text()` (line 490)

The call `self._sync_to_identity(text, memory_type=_tier_name, importance=0.5)` is deleted. No raw chunks enter Identity Memory anymore.

#### Keep: `_sync_to_identity()` call in `end_session()` (line 669)

Session summaries are already human-readable. This call stays but is refactored to use the new API.

#### New method: `sync_document_to_identity()`

```python
def sync_document_to_identity(
    self,
    summary: str,
    memory_type: str = "semantic",
    confidence: float = 0.5,
    tags: list[str] | None = None,
) -> None:
```

Passes through to `adapter.store_from_cognithor()` with no truncation, no modification.

#### Refactor: `_sync_to_identity()` calls `sync_document_to_identity()`

```python
def _sync_to_identity(self, content, memory_type="episodic", importance=0.5):
    self.sync_document_to_identity(
        summary=content,
        memory_type=_tier_to_im.get(memory_type, "episodic"),
        confidence=importance,
        tags=["session"],
    )
```

### 3. `adapter.py` — Extended parameters

```python
def store_from_cognithor(
    self,
    content: str,
    memory_type: str = "episodic",
    importance: float = 0.5,
    tags: list[str] | None = None,  # NEW
) -> None:
```

When `tags` is provided, uses `["cognithor"] + tags`. When `None`, falls back to current behavior `["cognithor", memory_type]`.

### 4. `loop.py` — Two changes

1. `_research()` line 1187: `synthesis[:1000]` -> `synthesis[:3000]`
2. `_create_builder_for_goal()`: pass `memory_manager=self._memory`
3. `_persist_research_result()`: pass `already_summarized=True` to `builder.build()`

### 5. `deep_learner.py` — Wire memory_manager

KnowledgeBuilder creation (line 251) gets `memory_manager=self._memory`. The Deep Learner already has `self._memory` (MemoryManager reference).

### 6. `gateway.py` / `phases/pge.py` — Verify wiring

Verify that Deep Learner and EvolutionLoop both have access to `memory_manager`. If not already wired, inject during PGE phase initialization.

## Prompt Design

```
Du bist ein Wissenskurator. Analysiere diesen Text und erstelle einen strukturierten Wissensbaustein.

Themenbereich: {goal_slug}
Quelle: {url}

Text:
{text[:4000]}

Antworte NUR mit validem JSON:
{
  "summary": "Praegnante Zusammenfassung in 3-8 Saetzen. Nur Fakten, kein Fuelltext.",
  "memory_type": "semantic|procedural|episodic",
  "tags": ["tag1", "tag2", "tag3"],
  "is_useful": true/false
}

Regeln:
- memory_type "semantic" = Fakten, Wissen, Definitionen
- memory_type "procedural" = Anleitungen, Prozesse, How-To
- memory_type "episodic" = Ereignisse, Nachrichten, zeitgebunden
- is_useful: false wenn der Text keine verwertbaren Informationen enthaelt
- tags: 2-5 thematische Schlagwoerter, deutsch
- summary: Deutsch, sachlich, nur Kernaussagen
```

Note: Confidence is NOT in the prompt. It is derived from the source URL.

## Source Confidence Scoring

```python
_TRUSTED_DOMAINS = {
    ".gov.de": 0.9, ".bund.de": 0.9, ".europa.eu": 0.9,
    "gesetze-im-internet.de": 0.9, "dejure.org": 0.9,
    "bafin.de": 0.9, "bundesbank.de": 0.9,
    "wikipedia.org": 0.7, "arxiv.org": 0.7,
    "springer.com": 0.7, "nature.com": 0.7,
    "heise.de": 0.7, "golem.de": 0.7,
    "bsi.bund.de": 0.9, "owasp.org": 0.8,
}
_LOW_TRUST_SIGNALS = ["blog", "medium.com", "reddit.com", "forum", "quora.com"]
_DEFAULT_CONFIDENCE = 0.5
```

Logic: Check URL against trusted domains (suffix match). If matched -> use mapped value. Check against low-trust signals (substring match). If matched -> 0.3. Otherwise -> 0.5.

## JSON Parsing — 4-Tier Fallback

```python
def _parse_llm_json(raw: str, fallback_content: str, url: str) -> dict:
    """Parse LLM response with graceful degradation."""
    # Tier 1: json.loads(raw)
    # Tier 2: Extract ```json ... ``` block, then json.loads
    # Tier 3: Regex extraction of individual fields
    #   "summary": re.search(r'"summary"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    #   "memory_type": re.search(r'"memory_type"\s*:\s*"(\w+)"', raw)
    #   "tags": re.findall(r'"(\w+)"', tags_match) from "tags" array
    # Tier 4: Fallback defaults
    return {
        "summary": extracted_summary or fallback_content[:800],
        "memory_type": extracted_type or "semantic",
        "tags": extracted_tags or [],
        "is_useful": True,  # assume useful if we can't parse
    }
```

No content is ever lost. Worst case: original text beginning with default classification.

## Deduplication

**Per-session** (in KnowledgeBuilder):
- `ContentDeduplicator.content_hash(summary)` checked against `_identity_seen_hashes: set[str]`
- Hash match -> skip, log `identity_dedup_skipped`
- In-memory only, resets per KnowledgeBuilder instance

**Cross-session** (existing):
- `ConsolidationPipeline` runs periodically
- Hash + fuzzy n-gram (85% threshold) over all entries
- No changes needed

## Reset Script

`scripts/reset_identity_memories.py`:

1. Backup `memories.json` -> `memories.json.bak`
2. Load JSON
3. Filter `memories` dict: keep only entries where `is_absolute_core == true`
4. Keep all other sections (`cognitive_state`, `personality`, `temporal`, etc.) unchanged
5. Atomic write back
6. ChromaDB cleanup: delete entries where `source_type == "cognithor"` and not absolute_core
7. Default: dry-run. `--execute` flag for real reset.

## Files Changed

| File | Change |
|---|---|
| `src/jarvis/evolution/knowledge_builder.py` | + `_summarize_for_identity()`, + `_score_source_confidence()`, + `_parse_llm_json()`, + `memory_manager` param, + `ContentDeduplicator`, + `already_summarized` param on `build()` |
| `src/jarvis/memory/manager.py` | + `sync_document_to_identity()`, remove `_sync_to_identity()` call in `index_text()`, refactor `_sync_to_identity()` to use new API |
| `src/jarvis/identity/adapter.py` | `store_from_cognithor()` gets `tags` parameter |
| `src/jarvis/evolution/loop.py` | `synthesis[:3000]`, `_create_builder_for_goal()` passes `memory_manager`, `_persist_research_result()` passes `already_summarized=True` |
| `src/jarvis/evolution/deep_learner.py` | KnowledgeBuilder creation gets `memory_manager` |
| `src/jarvis/gateway/phases/pge.py` | Verify `memory_manager` wiring to Deep Learner + Loop |
| `scripts/reset_identity_memories.py` | One-time reset script |
| `tests/` | Tests for all new functions |

## What Does NOT Change

- Semantic Memory pipeline (chunks, FTS5, embeddings)
- Vault storage
- Knowledge Graph / entity extraction
- CORE.md
- `_is_usable_content()` (already built, reused)
- `ConsolidationPipeline` (continues running for cross-session dedup)
- Episodic Memory
- Working Memory

## Expected Outcome

After reset + 2-3 ATL cycles with new pipeline:
- ~300-500 high-quality summarized knowledge memories (vs 3172 fragments)
- Each memory has correct type (semantic/procedural/episodic)
- Differentiated confidence (0.3-0.9) based on source authority
- Thematic tags in German
- No PDF artifacts, no duplicates, no mid-sentence truncation
- Cognithor's Identity reflects actual knowledge, not data fragments
