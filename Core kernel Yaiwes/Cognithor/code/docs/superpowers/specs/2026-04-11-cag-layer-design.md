# CAG Layer — KV-Cache Preloading Design Spec

**Goal:** Eliminate retrieval latency for stable knowledge domains (Core Memory) by ensuring the LLM's KV-cache is pre-warmed with that content. For HTTP-based backends (Ollama, llama.cpp server, vLLM), this means generating a deterministic, stable system-message prefix that triggers the backend's automatic prefix caching. For native llama-cpp-python, this means explicit KV-state save/load.

**Issue:** Feature 1 from `docs/cognithor_retrieval_extensions_prompt.md`

**Package:** `src/cognithor/memory/cag/`

---

## 1. How LLM Prefix Caching Actually Works

Most LLM inference servers (Ollama, llama.cpp server, vLLM) automatically cache the KV-state for prompt prefixes. If two sequential requests share the same first N tokens, the server skips recomputing attention for those tokens. This is automatic — no API needed.

**Our job:** Ensure the system message containing Core Memory is **deterministic and stable** across requests. If the text changes by even one character, the prefix cache is invalidated.

**What we build:**
1. A content normalizer that produces identical text from the same Core Memory regardless of whitespace/BOM/ordering
2. A hash-based change detector that knows when to signal "prefix changed"
3. A metrics collector that tracks whether the prefix was stable (cache hit) or changed (cache miss)
4. For `llama-cpp-python` native: explicit state save/load (the only backend where we manage the cache ourselves)

---

## 2. Module Structure

```
src/cognithor/memory/cag/
├── __init__.py
├── models.py              # CacheEntry, CAGMetrics, CAGStatus, CAGRefreshReport
├── content_normalizer.py  # Deterministic normalization + hashing
├── cache_store.py         # Disk persistence for normalized content + hashes
├── selectors.py           # CAGSelector — which memory tiers qualify
├── metrics.py             # CAGMetricsCollector — hit/miss/latency tracking
├── manager.py             # CAGManager — lifecycle orchestration
└── builders/
    ├── __init__.py        # get_builder(backend) factory
    ├── base.py            # CacheBuilder ABC
    ├── prefix.py          # PrefixCacheBuilder — Ollama, llama.cpp server, any OpenAI-compat
    └── native.py          # NativeLlamaCppBuilder — explicit state save/load
```

**Modified existing files:**
- `src/cognithor/config.py` — add `CAGConfig`
- `src/cognithor/memory/manager.py` — add 3 new public methods
- `src/cognithor/core/planner.py` — replace ad-hoc core_memory injection with stable CAG prefix
- `src/cognithor/gateway/gateway.py` — prepare CAG prefix before planner call

---

## 3. Data Model (`models.py`)

```python
@dataclass(frozen=True)
class CacheEntry:
    """A single cached content block."""
    cache_id: str                     # e.g. "core_memory", "semantic_tariff_book"
    content_hash: str                 # sha256 of normalized content
    normalized_text: str              # the stable, deterministic text
    token_count: int
    source_tier: str                  # "core", "semantic", "procedural"
    created_at: str                   # ISO 8601
    model_id: str                     # model this was prepared for

@dataclass
class CAGMetrics:
    prefix_hits: int = 0             # prefix identical to last call
    prefix_misses: int = 0           # prefix changed (content updated)
    total_builds: int = 0
    total_build_ms: float = 0.0
    last_prefix_hash: str = ""       # hash of last sent prefix
    cache_entries: int = 0
    total_cached_tokens: int = 0

@dataclass(frozen=True)
class CAGStatus:
    enabled: bool
    backend: str
    entries: list[CacheEntry]
    metrics: CAGMetrics

@dataclass(frozen=True)
class CAGRefreshReport:
    refreshed: list[str]              # cache_ids rebuilt
    unchanged: list[str]              # content hash same, skipped
    failed: list[tuple[str, str]]     # (cache_id, error message)
```

---

## 4. Content Normalizer (`content_normalizer.py`)

Produces deterministic text from memory content:

```python
class ContentNormalizer:
    @staticmethod
    def normalize(text: str) -> str:
        """Collapse whitespace, strip BOM, normalize line endings, strip trailing whitespace per line."""
    
    @staticmethod
    def compute_hash(normalized_text: str) -> str:
        """sha256 hex digest of normalized text."""
    
    @staticmethod
    def has_changed(stored_hash: str, current_text: str) -> bool:
        """True if normalized current_text has a different hash than stored."""
```

Normalization rules:
- Strip UTF-8 BOM (`\ufeff`)
- Replace `\r\n` and `\r` with `\n`
- Collapse multiple blank lines to single blank line
- Strip trailing whitespace per line
- Strip leading/trailing whitespace from entire text
- Result is deterministic: same input → always same output

---

## 5. Cache Store (`cache_store.py`)

Persists normalized content and metadata to disk:

```
~/.cognithor/cag_cache/
├── core_memory.json          # CacheEntry as JSON
├── core_memory.txt           # normalized text (for debugging/inspection)
├── semantic_tariff_book.json
├── semantic_tariff_book.txt
└── ...
```

```python
class CacheStore:
    def __init__(self, cache_dir: Path) -> None: ...
    def save(self, entry: CacheEntry) -> None: ...       # atomic write (tmp + rename)
    def load(self, cache_id: str) -> CacheEntry | None: ...
    def delete(self, cache_id: str) -> None: ...
    def list_entries(self) -> list[CacheEntry]: ...
    def total_size_bytes(self) -> int: ...
```

No LRU eviction needed — these are small text files (Core Memory is typically <10KB). If disk fills up, that's a system-level issue, not a CAG issue.

---

## 6. Selectors (`selectors.py`)

```python
class CAGSelector:
    """Determines which memory content qualifies for prefix caching."""
    
    def select(self, memory_manager: MemoryManager) -> list[CacheCandidate]:
        """Return content blocks eligible for caching."""
```

Selection rules:
- **Always**: Core Memory (`core_memory_text`) → cache_id `"core_memory"`
- **On request**: Semantic Memory items with `cag: true` in YAML frontmatter
- **Conditional**: Procedural Memory with `times_used >= 10` and `confidence >= 0.9`
- **Never**: Working Memory, Episodic Memory, Tactical Memory (too volatile)

Returns `list[CacheCandidate]` where each has `(cache_id, content, source_tier, priority)`.

---

## 7. Builders

### 7.1 Base (`builders/base.py`)

```python
class CacheBuilder(ABC):
    @abstractmethod
    async def prepare_prefix(self, entries: list[CacheEntry], model_id: str) -> str:
        """Build the deterministic system-message prefix from cached entries."""
    
    @abstractmethod
    async def is_available(self) -> bool:
        """True if this builder can function with the current backend."""
    
    @abstractmethod
    def supports_native_state(self) -> bool:
        """True only for llama-cpp-python native (explicit KV state management)."""
```

### 7.2 PrefixCacheBuilder (`builders/prefix.py`)

Works with Ollama, llama.cpp server, vLLM, any OpenAI-compatible backend.

```python
class PrefixCacheBuilder(CacheBuilder):
    async def prepare_prefix(self, entries: list[CacheEntry], model_id: str) -> str:
        """Concatenate normalized entries into a stable system message.
        
        Format:
        [CAG:core_memory]
        <normalized core memory text>
        
        [CAG:semantic_tariff_book]
        <normalized semantic text>
        
        Order: sorted by cache_id for determinism.
        """
    
    async def is_available(self) -> bool:
        return True  # Works with any HTTP backend
    
    def supports_native_state(self) -> bool:
        return False
```

### 7.3 NativeLlamaCppBuilder (`builders/native.py`)

Only for `llama-cpp-python` direct usage (not HTTP server).

```python
class NativeLlamaCppBuilder(CacheBuilder):
    async def build_state(self, content: str, model_path: str, target_path: Path) -> Path:
        """Create Llama instance, eval content, save_state() to binary file."""
    
    async def load_state(self, state_path: Path, model_path: str) -> Any:
        """Create Llama instance, load_state() from binary file, return context."""
    
    async def is_available(self) -> bool:
        """True if llama_cpp importable."""
        try:
            import llama_cpp
            return True
        except ImportError:
            return False
    
    def supports_native_state(self) -> bool:
        return True
```

---

## 8. Manager (`manager.py`)

```python
class CAGManager:
    def __init__(
        self,
        config: CAGConfig,
        cache_store: CacheStore,
        builder: CacheBuilder,
        selector: CAGSelector,
        memory_manager: MemoryManager,
    ) -> None: ...
    
    @property
    def is_active(self) -> bool:
        """True if CAG is enabled and builder is available."""
    
    async def build_all(self) -> CAGRefreshReport:
        """Select eligible content, normalize, hash, store. Rebuild only if changed."""
    
    async def get_stable_prefix(self, model_id: str) -> str | None:
        """Return the current stable prefix string for the Planner.
        Returns None if no content is cached or CAG is disabled.
        Tracks hit/miss in metrics."""
    
    async def invalidate(self, cache_id: str) -> None:
        """Force rebuild of a specific cache entry."""
    
    async def get_status(self) -> CAGStatus: ...
    async def get_metrics(self) -> CAGMetrics: ...
```

**Auto-rebuild hook:** When Core Memory changes (`CoreMemory.update()`), the CAGManager is notified and schedules a debounced rebuild (asyncio task, non-blocking, `rebuild_debounce_seconds` delay).

---

## 9. Integration Hooks

### Hook 1: Gateway (`gateway.py`)

Before calling the Planner, prepare the CAG prefix:

```python
# In handle_message(), before the PGE loop:
_cag_prefix = None
if hasattr(self, '_cag_manager') and self._cag_manager and self._cag_manager.is_active:
    _model_id = self._config.models.planner.name
    _cag_prefix = await self._cag_manager.get_stable_prefix(_model_id)
```

Pass `_cag_prefix` to the Planner via WorkingMemory:

```python
wm.cag_prefix = _cag_prefix  # New optional field on WorkingMemory
```

### Hook 2: Planner (`planner.py`)

In `_build_system_prompt()`, where `core_memory_text` is injected (line ~1003):

```python
if wm.cag_prefix:
    # Use the stable, pre-normalized CAG prefix instead of raw core_memory_text
    # This ensures the LLM backend's automatic prefix caching works
    core_section = wm.cag_prefix
else:
    # Original path
    core_section = f"Dein Hintergrund:\n{wm.core_memory_text[:500]}"
```

No Hook 3 needed for HTTP backends. The prefix caching is automatic.

### Hook 3 (only NativeLlamaCpp):

If `builder.supports_native_state()`, the Gateway loads the binary state and passes it to a dedicated `LlamaCppNativeBackend` (new backend class, created only when user configures `llamacpp_native`). This backend uses the pre-loaded state instead of processing the system message from text.

---

## 10. MemoryManager Methods

3 new public methods (no existing methods changed):

```python
async def enable_cag(self, backend: str | None = None) -> None:
    """Initialize CAG subsystem. Triggers initial cache build."""

async def refresh_cag_cache(self, cache_id: str | None = None) -> CAGRefreshReport:
    """Rebuild caches. If cache_id is None, rebuild all eligible."""

async def get_cag_status(self) -> CAGStatus:
    """Return current CAG state, entries, and metrics."""
```

---

## 11. Configuration

```python
class CAGConfig(BaseModel):
    """KV-Cache Preloading configuration."""
    enabled: bool = Field(default=False, description="Enable CAG (opt-in)")
    backend: str = Field(default="auto", description="'auto' | 'prefix' | 'llamacpp_native'")
    cache_dir: str = Field(default="~/.cognithor/cag_cache", description="Directory for cache files")
    auto_rebuild_on_change: bool = Field(default=True, description="Auto-rebuild when Core Memory changes")
    rebuild_debounce_seconds: int = Field(default=30, ge=5, le=300, description="Debounce delay for auto-rebuild")
```

Added to `MemoryConfig` as: `cag: CAGConfig = Field(default_factory=CAGConfig)`

`"auto"` selects `PrefixCacheBuilder` (works everywhere). User must explicitly set `"llamacpp_native"` to use the state-based builder.

---

## 12. WorkingMemory Extension

Add one optional field to `WorkingMemory` in `models.py`:

```python
cag_prefix: str | None = None  # Stable prefix from CAG, replaces core_memory_text if set
```

No other changes to WorkingMemory.

---

## 13. Edge Cases (9)

| # | Case | Handling |
|---|------|----------|
| 1 | Backend not available | `is_available() == False`, standard path, log warning |
| 2 | Model switch at runtime | Content hash unchanged, but LLM prefix cache auto-invalidated by backend |
| 3 | Disk full | CacheStore raises IOError, caught by manager, fallback to standard |
| 4 | Corrupt cache file | Hash mismatch on load, automatic rebuild |
| 5 | Concurrent rebuild | AsyncLock in manager |
| 6 | Content empty / <50 tokens | Skip caching, log info |
| 7 | Core Memory changed | Auto-rebuild if `auto_rebuild_on_change`, debounced |
| 8 | Schema version mismatch | Version field in JSON, rebuild on mismatch |
| 9 | NativeLlamaCpp state from different model | model_id check in metadata, refuse load, rebuild |

---

## 14. Tests

```
tests/memory/cag/
├── test_content_normalizer.py    # BOM strip, whitespace collapse, deterministic hash
├── test_cache_store.py           # Save/load/delete, atomic writes, list entries
├── test_selectors.py             # Core always, Semantic conditional, Working never
├── test_prefix_builder.py        # Stable prefix generation, sorted order, change detection
├── test_native_builder.py        # Mocked llama-cpp-python save/load state
├── test_manager.py               # build_all, get_stable_prefix, invalidate, auto-rebuild
├── test_metrics.py               # Hit/miss counting, prefix hash tracking
├── test_integration.py           # End-to-end: build → get_prefix → planner uses it
└── test_edge_cases.py            # All 9 edge cases
```

All tests deterministic. No real LLM calls. NativeLlamaCpp fully mocked.

---

## 15. Performance Targets

| Metric | Target |
|--------|--------|
| Prefix generation from cached entries | <10ms |
| Content normalization (50KB Core Memory) | <5ms |
| Cache store save (atomic write) | <20ms |
| Prefix hit rate (normal usage, no edits) | >99% |
| Auto-rebuild after Core Memory edit | <rebuild_debounce_seconds + 100ms |

---

## 16. Implementation Order

1. `models.py` — all dataclasses
2. `content_normalizer.py` + `test_content_normalizer.py`
3. `cache_store.py` + `test_cache_store.py`
4. `selectors.py` + `test_selectors.py`
5. `metrics.py` + `test_metrics.py`
6. `builders/base.py` + `builders/prefix.py` + `test_prefix_builder.py`
7. `builders/native.py` + `test_native_builder.py`
8. `manager.py` + `test_manager.py`
9. `config.py` modification — CAGConfig
10. `models.py` modification — WorkingMemory.cag_prefix field
11. `gateway.py` modification — Hook 1 (prepare prefix)
12. `planner.py` modification — Hook 2 (use prefix)
13. `manager.py` modification — 3 new MemoryManager methods
14. `test_integration.py` — end-to-end
15. `test_edge_cases.py` — all 9
16. Full test suite verification
