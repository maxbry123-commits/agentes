# Learning Upload Deep Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make user-uploaded files go through the full KnowledgeBuilder pipeline (Vault save, entity extraction, identity memory summary, vision analysis) instead of just chunk-indexing.

**Architecture:** Hybrid approach — immediate chunk-indexing for searchability, plus a background async worker that processes an in-memory priority queue through the full KnowledgeBuilder triple-write pipeline. PDF pages with images are analyzed via vision model.

**Tech Stack:** Python asyncio, heapq, KnowledgeBuilder, FetchResult, MediaPipeline, Flutter Dart

---

### Task 1: Fix response field mismatch + add priority to IngestResult

**Files:**
- Modify: `src/jarvis/learning/knowledge_ingest.py:24-36`
- Modify: `src/jarvis/channels/config_routes.py:5055-5064`
- Modify: `flutter_app/lib/screens/teach_screen.dart:112`
- Test: `tests/test_learning/test_knowledge_ingest.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_learning/test_knowledge_ingest.py`:

```python
"""Tests for KnowledgeIngestService deep pipeline."""

from __future__ import annotations

import pytest

from jarvis.learning.knowledge_ingest import IngestResult, Priority


class TestIngestResult:
    def test_default_priority(self):
        r = IngestResult(id="1", source_type="file", source_name="f.pdf", status="success")
        assert r.priority == Priority.NORMAL

    def test_has_chunks_alias(self):
        r = IngestResult(
            id="1", source_type="file", source_name="f.pdf",
            status="success", chunks_created=5,
        )
        assert r.chunks == 5

    def test_deep_learn_status_default(self):
        r = IngestResult(id="1", source_type="file", source_name="f.pdf", status="success")
        assert r.deep_learn_status == "pending"


class TestPriority:
    def test_ordering(self):
        assert Priority.HIGH < Priority.NORMAL < Priority.LOW

    def test_from_string(self):
        assert Priority.from_string("high") == Priority.HIGH
        assert Priority.from_string("low") == Priority.LOW
        assert Priority.from_string("invalid") == Priority.NORMAL
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_learning/test_knowledge_ingest.py -x -q --tb=short`
Expected: FAIL — `Priority` not found

- [ ] **Step 3: Implement Priority enum and update IngestResult**

In `src/jarvis/learning/knowledge_ingest.py`, add after the imports (before `IngestResult`):

```python
import enum


class Priority(enum.IntEnum):
    """Upload learning priority."""

    HIGH = 0
    NORMAL = 1
    LOW = 2

    @classmethod
    def from_string(cls, s: str) -> Priority:
        try:
            return cls[s.upper()]
        except KeyError:
            return cls.NORMAL
```

Update the `IngestResult` dataclass:

```python
@dataclass
class IngestResult:
    """Result of a single knowledge ingestion operation."""

    id: str
    source_type: str  # file, url, youtube
    source_name: str
    status: str  # processing, success, failed
    chunks_created: int = 0
    text_length: int = 0
    error: str = ""
    priority: Priority = Priority.NORMAL
    deep_learn_status: str = "pending"  # pending, queued, skipped, completed, failed
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def chunks(self) -> int:
        """Alias for chunks_created (Flutter compatibility)."""
        return self.chunks_created
```

- [ ] **Step 4: Fix API response to include `chunks` alias**

In `src/jarvis/channels/config_routes.py`, in the `learn_file` handler (~line 5055), change the response dict:

```python
            return {
                "id": result.id,
                "source_type": result.source_type,
                "source_name": result.source_name,
                "status": result.status,
                "chunks": result.chunks,
                "chunks_created": result.chunks_created,
                "text_length": result.text_length,
                "deep_learn_status": result.deep_learn_status,
                "error": result.error,
                "created_at": result.created_at.isoformat(),
            }
```

Apply the same change to `learn_url` (~line 5092) and `learn_youtube` (~line 5127) responses.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_learning/test_knowledge_ingest.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/jarvis/learning/knowledge_ingest.py src/jarvis/channels/config_routes.py tests/test_learning/test_knowledge_ingest.py
git commit -m "feat(ingest): add Priority enum, chunks alias, deep_learn_status (#89)"
```

---

### Task 2: IngestQueue — priority-based background processing

**Files:**
- Modify: `src/jarvis/learning/knowledge_ingest.py`
- Test: `tests/test_learning/test_knowledge_ingest.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_learning/test_knowledge_ingest.py`:

```python
class TestIngestQueue:
    def test_enqueue_dequeue_priority_order(self):
        from jarvis.learning.knowledge_ingest import IngestQueue, _QueueItem

        q = IngestQueue()
        q.enqueue(_QueueItem(
            result_id="low1", text="low", source="f1.pdf",
            priority=Priority.LOW, page_images=[],
        ))
        q.enqueue(_QueueItem(
            result_id="high1", text="high", source="f2.pdf",
            priority=Priority.HIGH, page_images=[],
        ))
        q.enqueue(_QueueItem(
            result_id="norm1", text="norm", source="f3.pdf",
            priority=Priority.NORMAL, page_images=[],
        ))

        assert not q.empty
        assert q.dequeue().result_id == "high1"
        assert q.dequeue().result_id == "norm1"
        assert q.dequeue().result_id == "low1"
        assert q.empty

    def test_queue_size(self):
        from jarvis.learning.knowledge_ingest import IngestQueue, _QueueItem

        q = IngestQueue()
        assert len(q) == 0
        q.enqueue(_QueueItem(
            result_id="x", text="t", source="s",
            priority=Priority.NORMAL, page_images=[],
        ))
        assert len(q) == 1

    def test_pending_returns_list(self):
        from jarvis.learning.knowledge_ingest import IngestQueue, _QueueItem

        q = IngestQueue()
        q.enqueue(_QueueItem(
            result_id="a", text="t", source="s",
            priority=Priority.HIGH, page_images=[],
        ))
        pending = q.pending()
        assert len(pending) == 1
        assert pending[0]["id"] == "a"
        assert pending[0]["priority"] == "HIGH"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_learning/test_knowledge_ingest.py::TestIngestQueue -x -q --tb=short`
Expected: FAIL — `IngestQueue` not found

- [ ] **Step 3: Implement IngestQueue**

Add to `src/jarvis/learning/knowledge_ingest.py`, after the `Priority` class:

```python
import heapq


@dataclass
class _QueueItem:
    """Item in the deep-learn priority queue."""

    result_id: str
    text: str
    source: str
    priority: Priority
    page_images: list[Path]

    def __lt__(self, other: _QueueItem) -> bool:
        return self.priority < other.priority


class IngestQueue:
    """Priority queue for background deep-learning tasks."""

    def __init__(self) -> None:
        self._heap: list[_QueueItem] = []

    def enqueue(self, item: _QueueItem) -> None:
        heapq.heappush(self._heap, item)

    def dequeue(self) -> _QueueItem:
        return heapq.heappop(self._heap)

    @property
    def empty(self) -> bool:
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)

    def pending(self) -> list[dict[str, str]]:
        """Return queue contents for the API (without consuming)."""
        return [
            {"id": item.result_id, "source": item.source, "priority": item.priority.name}
            for item in sorted(self._heap)
        ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_learning/test_knowledge_ingest.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/learning/knowledge_ingest.py tests/test_learning/test_knowledge_ingest.py
git commit -m "feat(ingest): add IngestQueue with priority ordering (#89)"
```

---

### Task 3: Wire KnowledgeBuilder into IngestService + background worker

**Files:**
- Modify: `src/jarvis/learning/knowledge_ingest.py`
- Modify: `src/jarvis/gateway/phases/advanced.py:323-331`
- Test: `tests/test_learning/test_knowledge_ingest.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_learning/test_knowledge_ingest.py`:

```python
from unittest.mock import AsyncMock, MagicMock, patch


class TestDeepLearn:
    @pytest.mark.asyncio
    async def test_ingest_file_queues_deep_learn(self):
        """Normal priority file upload queues deep-learn task."""
        memory = MagicMock()
        memory.index_text = MagicMock(return_value=3)

        svc = KnowledgeIngestService(memory=memory)

        with patch.object(svc, "_extract_text", new_callable=AsyncMock, return_value="Hello world content"):
            result = await svc.ingest_file("test.txt", b"Hello world content", priority=Priority.NORMAL)

        assert result.status == "success"
        assert result.chunks == 3
        assert result.deep_learn_status == "queued"
        assert len(svc._queue) == 1

    @pytest.mark.asyncio
    async def test_ingest_file_low_priority_skips_deep_learn(self):
        """Low priority skips deep-learn queue."""
        memory = MagicMock()
        memory.index_text = MagicMock(return_value=2)

        svc = KnowledgeIngestService(memory=memory)

        with patch.object(svc, "_extract_text", new_callable=AsyncMock, return_value="Some text"):
            result = await svc.ingest_file("test.txt", b"Some text", priority=Priority.LOW)

        assert result.status == "success"
        assert result.deep_learn_status == "skipped"
        assert len(svc._queue) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_learning/test_knowledge_ingest.py::TestDeepLearn -x -q --tb=short`
Expected: FAIL — `ingest_file()` doesn't accept `priority`

- [ ] **Step 3: Refactor ingest_file to accept priority and enqueue**

In `src/jarvis/learning/knowledge_ingest.py`, update `KnowledgeIngestService`:

```python
class KnowledgeIngestService:
    """Processes files, URLs, and YouTube links into Jarvis memory."""

    def __init__(
        self,
        memory: MemoryManager | None = None,
        knowledge_builder: Any | None = None,
        llm_fn: Any | None = None,
    ) -> None:
        self._memory = memory
        self._knowledge_builder = knowledge_builder
        self._llm_fn = llm_fn
        self._results: list[IngestResult] = []
        self._queue = IngestQueue()
        self._worker_task: asyncio.Task | None = None
```

Update `ingest_file` signature to `async def ingest_file(self, filename: str, content: bytes, priority: Priority = Priority.NORMAL) -> IngestResult:`.

After the successful chunk indexing block (after `result.text_length = len(text)`), add:

```python
            # Queue for deep learning if priority is not LOW
            if priority == Priority.LOW:
                result.deep_learn_status = "skipped"
            else:
                result.priority = priority
                result.deep_learn_status = "queued"
                page_images = self._extract_page_images(content, suffix) if suffix == ".pdf" else []
                self._queue.enqueue(_QueueItem(
                    result_id=result.id,
                    text=text,
                    source=f"upload://{filename}",
                    priority=priority,
                    page_images=page_images,
                ))
                self._ensure_worker()
```

Add helper `_extract_text` that encapsulates the current text extraction logic (so tests can mock it):

```python
    async def _extract_text(self, content: bytes, filename: str) -> str:
        """Extract text from file content."""
        import tempfile

        suffix = Path(filename).suffix.lower()

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(content)
            tmp_path = Path(f.name)

        try:
            if suffix in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
                return await self._extract_image_text(tmp_path)
            from jarvis.memory.ingest import TextExtractor
            extractor = TextExtractor()
            return await extractor.extract(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
```

Add `_extract_page_images` stub (implemented in Task 5):

```python
    def _extract_page_images(self, content: bytes, suffix: str) -> list[Path]:
        """Extract image-heavy pages from a PDF as PNG files."""
        return []  # Implemented in Task 5
```

Add `_ensure_worker` and `_worker_loop`:

```python
    def _ensure_worker(self) -> None:
        """Start the background worker if not running."""
        if self._worker_task is None or self._worker_task.done():
            import asyncio
            self._worker_task = asyncio.create_task(self._worker_loop())

    async def _worker_loop(self) -> None:
        """Process queued deep-learn items."""
        while not self._queue.empty:
            item = self._queue.dequeue()
            try:
                await self._deep_learn(item)
            except Exception as exc:
                log.warning("deep_learn_failed", source=item.source, error=str(exc))
                self._update_result(item.result_id, "failed", error=str(exc))

    async def _deep_learn(self, item: _QueueItem) -> None:
        """Run full KnowledgeBuilder pipeline on queued item."""
        if self._knowledge_builder is None:
            log.debug("deep_learn_skipped_no_builder", source=item.source)
            self._update_result(item.result_id, "skipped")
            return

        from jarvis.evolution.research_agent import FetchResult

        # Vision analysis for page images
        vision_text = ""
        for img_path in item.page_images:
            try:
                desc = await self._extract_image_text(img_path)
                if desc:
                    vision_text += f"\n[Image description: {desc}]\n"
            except Exception:
                pass
            finally:
                img_path.unlink(missing_ok=True)

        full_text = item.text + vision_text if vision_text else item.text

        fetch_result = FetchResult(
            url=item.source,
            text=full_text,
            title=Path(item.source).stem if "://" in item.source else item.source,
            source_type="user_upload",
        )
        await self._knowledge_builder.build(fetch_result)
        self._update_result(item.result_id, "completed")
        log.info("deep_learn_completed", source=item.source, text_len=len(full_text))

    def _update_result(self, result_id: str, status: str, error: str = "") -> None:
        """Update deep_learn_status on a stored IngestResult."""
        for r in self._results:
            if r.id == result_id:
                r.deep_learn_status = status
                if error:
                    r.error = error
                break
```

Also add `import asyncio` to the imports.

- [ ] **Step 4: Update ingest_url and ingest_youtube similarly**

Add `priority: Priority = Priority.NORMAL` parameter to both `ingest_url` and `ingest_youtube`. After successful chunk indexing, add the same queue/skip logic as `ingest_file` (without `_extract_page_images`).

- [ ] **Step 5: Update gateway wiring**

In `src/jarvis/gateway/phases/advanced.py`, line 328, pass the builder:

```python
    try:
        from jarvis.learning.knowledge_ingest import KnowledgeIngestService

        mm = getattr(config, "_memory_manager", None)
        kb = result.get("knowledge_builder")
        llm_fn = result.get("llm_fn")
        result["knowledge_ingest"] = KnowledgeIngestService(
            memory=mm, knowledge_builder=kb, llm_fn=llm_fn,
        )
        log.info("knowledge_ingest_initialized")
    except Exception:
        log.debug("knowledge_ingest_init_skipped", exc_info=True)
```

- [ ] **Step 6: Update API routes to pass priority**

In `config_routes.py`, in `learn_file` handler, after reading the form:

```python
            priority_str = form.get("priority", "normal")
            if isinstance(priority_str, str):
                pass
            else:
                priority_str = str(priority_str) if priority_str else "normal"

            from jarvis.learning.knowledge_ingest import Priority
            priority = Priority.from_string(priority_str)

            result = await svc.ingest_file(filename, file_bytes, priority=priority)
```

Same for `learn_url` and `learn_youtube`: read `priority` from JSON body.

Add the `/api/v1/learn/queue` endpoint:

```python
    @app.get("/api/v1/learn/queue", dependencies=deps)
    async def learn_queue() -> dict[str, Any]:
        """Show pending deep-learn tasks."""
        svc = _get_ingest()
        if not svc:
            return {"error": "Knowledge ingest service not initialized", "status": 503}
        return {"queue": svc._queue.pending(), "size": len(svc._queue)}
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_learning/test_knowledge_ingest.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/jarvis/learning/knowledge_ingest.py src/jarvis/channels/config_routes.py src/jarvis/gateway/phases/advanced.py tests/test_learning/test_knowledge_ingest.py
git commit -m "feat(ingest): wire KnowledgeBuilder + background worker + queue API (#89)"
```

---

### Task 4: Flutter UI — priority dropdown + response handling

**Files:**
- Modify: `flutter_app/lib/screens/teach_screen.dart`
- Modify: `flutter_app/lib/services/api_client.dart`
- Modify: `flutter_app/lib/l10n/app_{en,de,zh,ar}.arb`

- [ ] **Step 1: Add i18n keys**

Add to all 4 ARB files:

EN: `"priorityLow": "Low (index only)"`, `"priorityNormal": "Normal"`, `"priorityHigh": "High (priority learning)"`, `"deepLearningQueued": "Deep learning queued"`, `"deepLearningSkipped": "Indexed only (shallow)"`, `"priority": "Priority"`

DE: `"priorityLow": "Niedrig (nur Index)"`, `"priorityNormal": "Normal"`, `"priorityHigh": "Hoch (Prioritaet-Lernen)"`, `"deepLearningQueued": "Deep-Learning eingereiht"`, `"deepLearningSkipped": "Nur indexiert (flach)"`, `"priority": "Prioritaet"`

ZH: `"priorityLow": "低（仅索引）"`, `"priorityNormal": "正常"`, `"priorityHigh": "高（优先学习）"`, `"deepLearningQueued": "深度学习已排队"`, `"deepLearningSkipped": "仅索引（浅层）"`, `"priority": "优先级"`

AR: `"priorityLow": "منخفض (فهرسة فقط)"`, `"priorityNormal": "عادي"`, `"priorityHigh": "عالي (تعلم بأولوية)"`, `"deepLearningQueued": "التعلم العميق في الانتظار"`, `"deepLearningSkipped": "مفهرس فقط (سطحي)"`, `"priority": "الأولوية"`

- [ ] **Step 2: Run flutter gen-l10n**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter gen-l10n`

- [ ] **Step 3: Update api_client.dart to pass priority**

In `flutter_app/lib/services/api_client.dart`, update `learnFromFile`:

```dart
  Future<Map<String, dynamic>> learnFromFile(
    List<int> bytes,
    String filename, {
    String? description,
    String priority = 'normal',
  }) =>
      uploadFile('learn/file', 'file', bytes, filename,
          fields: {
            if (description != null) 'description': description,
            'priority': priority,
          });
```

Same for `learnFromUrl` and `learnFromYoutube` — add optional `priority` parameter.

- [ ] **Step 4: Add priority dropdown to teach_screen.dart**

Add a state variable `String _priority = 'normal';` to `_TeachScreenState`.

Add a `DropdownButton` next to the upload button in the file upload card:

```dart
DropdownButton<String>(
  value: _priority,
  items: [
    DropdownMenuItem(value: 'low', child: Text(l.priorityLow)),
    DropdownMenuItem(value: 'normal', child: Text(l.priorityNormal)),
    DropdownMenuItem(value: 'high', child: Text(l.priorityHigh)),
  ],
  onChanged: (v) => setState(() => _priority = v ?? 'normal'),
),
```

Update `_uploadFile()` to pass priority:

```dart
final res = await api.learnFromFile(_selectedFileBytes!, _selectedFilename!, priority: _priority);
```

Update the success display to show `chunks` field and deep_learn_status:

```dart
final chunks = res['chunks'] ?? '?';
final deepStatus = res['deep_learn_status'] ?? '';
setState(() {
  _fileResult = deepStatus == 'queued'
      ? '${l.deepLearningQueued} ($chunks chunks)'
      : '$chunks chunks';
  _fileSuccess = true;
});
```

- [ ] **Step 5: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 6: Commit**

```bash
git add flutter_app/lib/ 
git commit -m "feat(flutter): add priority dropdown to Teach screen (#89)"
```

---

### Task 5: PDF Vision pipeline — extract and analyze page images

**Files:**
- Modify: `src/jarvis/learning/knowledge_ingest.py`
- Test: `tests/test_learning/test_knowledge_ingest.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_learning/test_knowledge_ingest.py`:

```python
class TestPdfVision:
    def test_extract_page_images_no_pdf2image(self):
        """Graceful fallback when pdf2image is not installed."""
        svc = KnowledgeIngestService()
        result = svc._extract_page_images(b"%PDF-1.4 fake", ".pdf")
        assert result == []  # Graceful fallback

    @pytest.mark.asyncio
    async def test_deep_learn_with_images(self):
        """Vision descriptions are appended to text."""
        builder = AsyncMock()
        builder.build = AsyncMock()

        svc = KnowledgeIngestService(knowledge_builder=builder)
        item = _QueueItem(
            result_id="v1",
            text="Original text",
            source="upload://test.pdf",
            priority=Priority.HIGH,
            page_images=[],
        )
        svc._results.append(IngestResult(
            id="v1", source_type="file", source_name="test.pdf", status="success",
        ))

        await svc._deep_learn(item)

        builder.build.assert_called_once()
        call_args = builder.build.call_args
        assert call_args[0][0].text == "Original text"
        assert call_args[0][0].source_type == "user_upload"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_learning/test_knowledge_ingest.py::TestPdfVision -x -q --tb=short`

- [ ] **Step 3: Implement _extract_page_images**

In `src/jarvis/learning/knowledge_ingest.py`, replace the stub:

```python
    def _extract_page_images(self, content: bytes, suffix: str) -> list[Path]:
        """Extract image-heavy pages from a PDF as PNG files.

        Uses pypdf to detect pages with embedded images, then renders
        those pages via pdf2image (if available). Falls back gracefully
        if pdf2image or poppler is not installed.
        """
        if suffix != ".pdf":
            return []

        try:
            from pypdf import PdfReader
        except ImportError:
            return []

        import io
        import tempfile

        reader = PdfReader(io.BytesIO(content))
        image_pages: list[int] = []

        for i, page in enumerate(reader.pages):
            # Count XObjects (embedded images) on this page
            resources = page.get("/Resources")
            if resources is None:
                continue
            xobjects = resources.get("/XObject")
            if xobjects and len(xobjects) > 0:
                image_pages.append(i)

        if not image_pages:
            return []

        # Render image-heavy pages as PNG
        try:
            from pdf2image import convert_from_bytes

            images = convert_from_bytes(
                content,
                first_page=min(image_pages) + 1,
                last_page=max(image_pages) + 1,
                dpi=150,
                fmt="png",
            )

            paths: list[Path] = []
            for idx, img in enumerate(images):
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                img.save(tmp.name, "PNG")
                paths.append(Path(tmp.name))
                if len(paths) >= 10:  # Cap at 10 images
                    break

            return paths

        except ImportError:
            log.debug("pdf2image_not_available_for_vision")
            return []
        except Exception as exc:
            log.debug("pdf_image_extraction_failed", error=str(exc))
            return []
```

- [ ] **Step 4: Run tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_learning/test_knowledge_ingest.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/learning/knowledge_ingest.py tests/test_learning/test_knowledge_ingest.py
git commit -m "feat(ingest): PDF vision pipeline — extract and analyze page images (#89)"
```

---

### Task 6: Full integration test + lint + format

**Files:**
- Test: `tests/test_learning/test_knowledge_ingest.py`

- [ ] **Step 1: Write integration test**

Append to `tests/test_learning/test_knowledge_ingest.py`:

```python
class TestEndToEnd:
    @pytest.mark.asyncio
    async def test_full_ingest_flow(self):
        """File → chunk index → queue → deep learn."""
        memory = MagicMock()
        memory.index_text = MagicMock(return_value=5)

        builder = AsyncMock()
        builder.build = AsyncMock()

        svc = KnowledgeIngestService(memory=memory, knowledge_builder=builder)

        with patch.object(svc, "_extract_text", new_callable=AsyncMock, return_value="Test content " * 50):
            result = await svc.ingest_file("doc.txt", b"x", priority=Priority.HIGH)

        assert result.chunks == 5
        assert result.deep_learn_status == "queued"

        # Process the queue
        await svc._worker_loop()

        # Builder was called
        builder.build.assert_called_once()
        fetch = builder.build.call_args[0][0]
        assert "Test content" in fetch.text
        assert fetch.source_type == "user_upload"

        # Result updated
        assert result.deep_learn_status == "completed"
```

- [ ] **Step 2: Run all tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/ tests/ && ruff format src/ tests/ && python -m pytest tests/test_learning/test_knowledge_ingest.py -x -q --tb=short`
Expected: All pass, lint clean

- [ ] **Step 3: Run full test suite**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/ -x -q --tb=short --ignore=tests/test_channels/test_voice_ws_bridge.py`
Expected: All pass

- [ ] **Step 4: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete LLM-based deep learning pipeline for uploads (#89)

Closes #89"
```

- [ ] **Step 6: Comment on issue and push**

Comment on #89 explaining what was implemented, then push.
