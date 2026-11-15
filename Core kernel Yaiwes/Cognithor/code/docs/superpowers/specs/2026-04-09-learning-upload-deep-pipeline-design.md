# Learning Upload Deep Pipeline

**Date:** 2026-04-09
**Issue:** #89
**Status:** Approved

## Problem

User-uploaded files via the Teach screen are only chunk-indexed into semantic memory (`memory.index_text()`). They skip the full KnowledgeBuilder pipeline that the Evolution Engine uses: no Vault save, no entity/relation extraction, no identity memory summary, no LLM-based analysis. Uploaded material is searchable but not deeply understood.

## Design

### Architecture

Upload triggers two parallel paths:

1. **Immediate** (~1s): Text extraction + chunk indexing (existing behavior, for instant searchability)
2. **Background** (10-60s): Full KnowledgeBuilder pipeline with LLM analysis, queued by priority

### Components

#### 1. Extended KnowledgeIngestService

`src/jarvis/learning/knowledge_ingest.py`

- Receives `KnowledgeBuilder` + `llm_fn` references via constructor (wired in gateway phases)
- `ingest_file(filename, data, priority)` does immediate chunk-indexing, then enqueues deep-learn task if priority != low
- New `_deep_learn(text, source, priority, page_images)` method calls `KnowledgeBuilder.build()` with a synthetic `FetchResult`
- For PDFs: extracts pages with images, sends to Vision-Model, merges descriptions with text

#### 2. IngestQueue

In-memory priority queue (`heapq`) inside `KnowledgeIngestService`.

Priority levels:
- **High (0)**: Deep-learn immediately, before other background tasks
- **Normal (1)**: Deep-learn in background (default)
- **Low (2)**: Chunks only, no deep-learn

Single async worker task processes the queue FIFO within same priority. Spawned on first enqueue, runs until queue empty.

#### 3. API Changes

`POST /api/v1/learn/file`:
- New optional form field: `priority` (low/normal/high, default: normal)
- Response: rename `chunks_created` → `chunks` (fixes Flutter mismatch)
- New response field: `deep_learn_status: "queued" | "skipped"`

`POST /api/v1/learn/url` and `POST /api/v1/learn/youtube`:
- Same priority field and deep_learn_status response

`GET /api/v1/learn/queue` (new):
- Returns pending deep-learn tasks with source, priority, status

#### 4. PDF Vision Pipeline

Inside `_deep_learn()`:
- Uses `pypdf` to detect pages with images (XObject count > 0)
- Renders image-heavy pages as PNG via `pdf2image` (if available) or `pypdf` image extraction
- Sends each image to `MediaPipeline.analyze_image()` (Ollama vision model)
- Vision descriptions appended to page text before KnowledgeBuilder processing
- Falls back gracefully if pdf2image/poppler not installed (text-only)

#### 5. Flutter Teach Screen

`flutter_app/lib/screens/teach_screen.dart`:
- Priority dropdown (Low/Normal/High) next to upload button
- Post-upload toast: "Indexed (X chunks) + Deep learning queued" or "Indexed (X chunks)" for Low
- i18n keys for priority labels in all 4 languages

#### 6. Gateway Wiring

`src/jarvis/gateway/phases/advanced.py`:
- Pass `KnowledgeBuilder` factory and `llm_fn` to `KnowledgeIngestService`
- Requires `mcp_client` for vault_save and memory tools

### Data Flow

```
User Upload (file + priority)
  |
  v
API: POST /learn/file
  |
  v
KnowledgeIngestService.ingest_file()
  |-- Immediate: TextExtractor -> memory.index_text() -> return chunk count
  |-- If priority != low:
      |-- IngestQueue.enqueue(text, images, source, priority)
          |
          v
      Background Worker (async)
          |-- Vision: analyze page images -> text descriptions
          |-- KnowledgeBuilder.build(FetchResult)
          |   |-- Vault save (full document)
          |   |-- Chunk + semantic index
          |   |-- Entity/relation extraction (knowledge graph)
          |   |-- Claims extraction + validation
          |   |-- Identity memory summary (LLM)
          |-- Update IngestResult status -> "completed"
```

### Not In Scope

- Evolution Loop integration (`inject_user_material`) — follow-up issue
- YouTube video frame extraction
- OCR for scanned PDFs (requires Tesseract)
- Streaming progress updates via WebSocket (future enhancement)

### Files to Modify

| File | Change |
|------|--------|
| `src/jarvis/learning/knowledge_ingest.py` | Add KnowledgeBuilder wiring, IngestQueue, _deep_learn(), PDF vision |
| `src/jarvis/channels/config_routes.py` | Add priority param, fix chunks field name, add /learn/queue endpoint |
| `src/jarvis/gateway/phases/advanced.py` | Wire KnowledgeBuilder + llm_fn into IngestService |
| `flutter_app/lib/screens/teach_screen.dart` | Priority dropdown, updated response handling |
| `flutter_app/lib/services/api_client.dart` | Add priority param to learnFromFile/Url/YouTube |
| `flutter_app/lib/l10n/app_{en,de,zh,ar}.arb` | Priority label translations |
| `tests/test_learning/test_knowledge_ingest.py` | Tests for deep-learn queue, priority, vision pipeline |
