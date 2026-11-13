# Context Engineering

## Overview

The context engineering subsystem manages the LLM's finite context window throughout a conversation. It is responsible for token counting, staged compaction as usage grows, message pair integrity validation, codebase indexing, entity-based retrieval, and dynamic context assembly before each LLM call. In the crate dependency graph, `opendev-context` sits between the low-level models crate and the higher-level agents/runtime crates: agents and the ReAct executor depend on it, while it depends on `opendev-models` (for shared types) and `serde_json`/`chrono`/`regex` for implementation.

## Python Architecture

### Module Structure

```
context_engineering/
    __init__.py                 # Re-exports ToolRegistry, SessionManager, etc.
    compaction.py               # ContextCompactor, ArtifactIndex, OptimizationLevel
    validated_message_list.py   # ValidatedMessageList (list subclass)
    message_pair_validator.py   # MessagePairValidator, ViolationType, Violation, ValidationResult
    context_picker/
        __init__.py
        models.py               # ContextCategory, ContextReason, ContextPiece, AssembledContext
        picker.py               # ContextPicker (the main entry point)
        tracer.py               # ContextTracer (singleton, exports to JSON)
    retrieval/
        __init__.py
        indexer.py              # CodebaseIndexer (generates SWECLI.md summaries)
        retriever.py            # ContextRetriever, EntityExtractor
        token_monitor.py        # ContextTokenMonitor (tiktoken wrapper)
    history/                    # Session persistence, undo, topic detection
    memory/                     # Playbook, embeddings, reflection
    mcp/                        # Model Context Protocol integration
    tools/                      # Tool registry, implementations, handlers, LSP
```

### Key Abstractions

- **`ValidatedMessageList(list)`** -- A `list` subclass that intercepts all mutations (`append`, `extend`, `__setitem__`, `insert`) and routes them through validated methods. Uses `threading.Lock` for thread safety. Maintains a state machine: `EXPECT_ANY <-> EXPECT_TOOL_RESULTS{pending_ids}`. Auto-completes pending tool results with synthetic errors when a new user or assistant message arrives before all tool results are supplied.

- **`MessagePairValidator`** -- Stateless validator with `@staticmethod` methods. `validate()` performs a single forward pass to detect three violation types (missing tool result, orphaned tool result, consecutive same role). `repair()` builds a corrected message list by removing orphans and inserting synthetic results. Also provides `validate_tool_results_complete()` as a pre-batch-add guard.

- **`ContextCompactor`** -- Stateful compactor that owns a `ContextTokenMonitor` and an `ArtifactIndex`. `check_usage()` returns an `OptimizationLevel` string constant. `mask_old_observations()` mutates messages in-place, replacing old tool results with `[ref: ...]` placeholders. `prune_old_tool_outputs()` is a zero-cost alternative that strips tool outputs beyond a 40K token budget. `compact()` performs full LLM-powered summarization by calling `_summarize()` through an injected HTTP client, with `_fallback_summary()` as a non-LLM alternative. `compact_with_retry()` adds replay logic if still over the limit after the first pass.

- **`ArtifactIndex`** -- Tracks files touched during a session (create/modify/read/delete) with timestamps and operation counts. Serializable via `to_dict()`/`from_dict()`. `as_summary()` produces a markdown list injected into compaction summaries so the agent retains file awareness post-compaction.

- **`OptimizationLevel`** -- String constants on a class: `NONE`, `WARNING`, `MASK`, `PRUNE`, `AGGRESSIVE`, `COMPACT`.

- **`ContextPicker`** -- Coordinates all context assembly before an LLM call: file reference injection (`@file` mentions), playbook strategy selection, system prompt assembly, and conversation history. Returns an `AssembledContext` containing messages, pieces with reasons, and token estimates. All decisions are logged as `ContextReason` objects.

- **`ContextTokenMonitor`** -- Wraps `tiktoken` for accurate BPE token counting. Used by both the compactor and the indexer.

- **`CodebaseIndexer`** -- Generates a compressed markdown overview of a project directory (structure, key files, dependencies, README excerpt). Uses `subprocess` calls to `find` and `tree`.

- **`EntityExtractor` / `ContextRetriever`** -- Regex-based extraction of files, functions, classes, variables, and actions from user input. `ContextRetriever` resolves extracted entities against the filesystem using `rg`/`grep` fallback.

### Design Patterns

- **Strategy**: `OptimizationLevel` selects between masking, pruning, and compaction strategies.
- **State Machine**: `ValidatedMessageList` tracks pending tool call IDs as a state machine (`EXPECT_ANY` / `EXPECT_TOOL_RESULTS`).
- **Template Method**: `_summarize()` tries LLM summarization, falls back to `_fallback_summary()`.
- **Singleton**: `ContextTracer` uses a module-level `_default_tracer` instance via `get_tracer()`.
- **Observer-like**: `ContextCompactor` accepts a hook manager and fires `PreCompact` events.

### SOLID Analysis

- **SRP**: Each class has a clear single responsibility (validation, compaction, indexing, retrieval).
- **OCP**: `OptimizationLevel` is open for extension but the masking/pruning logic is tightly coupled to the level values.
- **LSP**: `ValidatedMessageList(list)` is a valid LSP substitution for `list` -- all reads work identically, mutations are intercepted.
- **ISP**: `MessagePairValidator` exposes three focused static methods rather than one monolithic interface.
- **DIP**: `ContextCompactor` depends on an abstract HTTP client, not a concrete implementation. `ContextPicker` takes interfaces for session manager, config, and file operations.

## Rust Architecture

### Module Structure

```
opendev-context/src/
    lib.rs              # Module declarations, pub use re-exports
    compaction.rs       # ContextCompactor, ArtifactIndex, ArtifactEntry, OptimizationLevel, ApiMessage
    validated_list.rs   # ValidatedMessageList (wraps Vec<ApiMessage>)
    pair_validator.rs   # MessagePairValidator, ViolationType, Violation, ValidationResult
    context_picker.rs   # ContextCategory, ContextReason, ContextPiece, AssembledContext, ContextTracer
    worktree.rs         # WorktreeManager, WorktreeInfo (git worktree isolation)
    retrieval/
        mod.rs          # Re-exports
        indexer.rs      # CodebaseIndexer
        retriever.rs    # ContextRetriever, EntityExtractor, Entities, FileMatch, RetrievalContext
        token_monitor.rs # ContextTokenMonitor (heuristic len/4)
```

### Key Abstractions

- **`ValidatedMessageList`** -- A struct wrapping `Vec<ApiMessage>` with a `Mutex<HashSet<String>>` for pending tool IDs. Unlike the Python `list` subclass, the Rust version uses composition: messages are accessed via `messages()` (returning `&[ApiMessage]`) or consumed via `into_inner()`. Mutations go through `add_user()`, `add_assistant()`, `add_tool_result()` (returns `Result`), and `add_tool_results_batch()`. `replace_all()` replaces the entire message list and rebuilds pending state.

- **`MessagePairValidator`** -- A unit struct (no fields) with associated functions. `validate()` returns a `ValidationResult` with `Vec<Violation>`. `repair()` returns `(Vec<ApiMessage>, ValidationResult)`. `validate_tool_results_complete()` takes `&mut HashMap<String, serde_json::Value>` and fills in missing entries. Pattern-identical to Python but uses Rust's ownership model: `&[ApiMessage]` input, owned `Vec<ApiMessage>` output for repair.

- **`ContextCompactor`** -- Owns the `ArtifactIndex` directly (no `Box`/`Arc`). `check_usage()` takes `&mut self` and returns the `OptimizationLevel` enum. `mask_old_observations()` and `prune_old_tool_outputs()` take `&mut [ApiMessage]` (in-place mutation via mutable slice). `compact()` takes `Vec<ApiMessage>` by value and returns `Vec<ApiMessage>`. LLM-powered summarization is **not** in this crate -- only `fallback_summary()` is provided. The LLM call is handled at a higher layer (agents crate), keeping the context crate free of async/HTTP dependencies.

- **`OptimizationLevel`** -- A proper `#[derive(Debug, Clone, Copy, PartialEq, Eq)]` enum with variants `None`, `Warning`, `Mask`, `Prune`, `Aggressive`, `Compact`. Provides `as_str()` for string conversion.

- **`ArtifactIndex`** -- Uses `HashMap<String, ArtifactEntry>` where `ArtifactEntry` is a dedicated struct with typed fields. Derives `Serialize`/`Deserialize` for direct JSON persistence (replacing the Python `to_dict()`/`from_dict()` pattern).

- **`ContextPicker` data models** -- `ContextCategory` is a `#[serde(rename_all = "snake_case")]` enum. `ContextReason` and `ContextPiece` use builder-style methods (`with_tokens()`, `with_score()`, `with_order()`). `AssembledContext` derives `Serialize`/`Deserialize` for tracing export. The actual picking logic (file injection, playbook selection) is deferred to higher-level crates; `context_picker.rs` provides only the data models and `ContextTracer`.

- **`ContextTokenMonitor`** -- A stateless unit struct using a `len() / 4` heuristic instead of tiktoken. This avoids a heavy dependency on BPE tokenizer libraries, trading accuracy for zero-dependency simplicity.

- **`ApiMessage`** -- A type alias for `serde_json::Map<String, serde_json::Value>`, providing a lightweight representation for compaction operations without requiring the full `ChatMessage` model.

- **`WorktreeManager`** -- New in Rust, provides git worktree creation, listing, removal, and cleanup for subagent workspace isolation. Not present in the Python context engineering package.

### Design Patterns

- **Newtype / Composition over Inheritance**: `ValidatedMessageList` wraps `Vec` via composition instead of subclassing `list`. Access is through explicit accessor methods.
- **Builder Pattern**: `ContextReason::new().with_tokens().with_score()` and `ContextPiece::new().with_order()`.
- **Type State (lightweight)**: `OptimizationLevel` enum variants encode the compaction stage as a type-safe value instead of string constants.
- **Unit Struct as Namespace**: `MessagePairValidator` and `ContextTokenMonitor` are unit structs grouping associated functions.
- **Serde Derive**: `ArtifactIndex`, `ArtifactEntry`, `ContextReason`, `ContextPiece`, `AssembledContext` all derive `Serialize`/`Deserialize`, replacing manual `to_dict()`/`from_dict()`.

### SOLID Analysis

- **SRP**: Each module handles exactly one concern. The worktree manager is a Rust-only addition with clear boundaries.
- **OCP**: The `OptimizationLevel` enum is exhaustively matched, so adding a new level requires updating match arms (but the compiler enforces this).
- **LSP**: Not directly applicable since there is no trait hierarchy -- the crate uses concrete types. `ValidatedMessageList` does not pretend to be a `Vec`.
- **ISP**: Functions take `&[ApiMessage]` slices rather than requiring full `ValidatedMessageList`, so callers can use raw vectors for testing.
- **DIP**: The compactor does not depend on HTTP or async -- LLM summarization is pushed to the agents layer. The context picker module provides data models only, with orchestration at the application layer.

## Migration Mapping

| Python Class/Module | Rust Struct/Trait | Pattern Change | Notes |
|---|---|---|---|
| `OptimizationLevel` (string constants) | `OptimizationLevel` (enum) | String constants to exhaustive enum | Compiler-checked matching; `as_str()` for backward compat |
| `ArtifactIndex` (dict-based) | `ArtifactIndex` + `ArtifactEntry` (struct) | Dynamic dict to typed struct | Derives `Serialize`/`Deserialize` instead of `to_dict()`/`from_dict()` |
| `ContextCompactor` | `ContextCompactor` | HTTP client removed from constructor | LLM summarization pushed to agents crate; only `fallback_summary()` retained |
| `ContextCompactor.compact_with_retry()` | Not yet ported | Deferred | Retry/replay logic handled at the agents layer |
| `ContextCompactor._sanitize_for_summarization()` | Not yet ported | Deferred | Only needed when LLM summarization is wired up |
| `ContextCompactor.archive_history()` | Not yet ported | Deferred | History archival to scratch files |
| `ValidatedMessageList(list)` | `ValidatedMessageList` (struct wrapping Vec) | Inheritance to composition | `messages()` / `into_inner()` instead of direct list access |
| `ValidatedMessageList._lock` (threading.Lock) | `Mutex<HashSet<String>>` | Python Lock to Rust Mutex | Only protects `pending_tool_ids`, not the Vec itself |
| `MessagePairValidator` | `MessagePairValidator` (unit struct) | `@staticmethod` to associated functions | Functionally identical |
| `ViolationType` (Enum/auto) | `ViolationType` (enum) | Python `auto()` to Rust variants | `MissingToolResult`, `OrphanedToolResult`, `ConsecutiveSameRole` |
| `ValidationResult` (dataclass) | `ValidationResult` (struct, `Default` derive) | `@dataclass` to `#[derive(Default)]` struct | `is_valid()` is a method in both |
| `ContextPicker` (class) | Data models only in `context_picker.rs` | Orchestration deferred to app layer | Python picker does file injection, playbook, etc. inline |
| `ContextCategory` (Enum) | `ContextCategory` (enum + serde) | Direct mapping | `#[serde(rename_all = "snake_case")]` for JSON compat |
| `ContextReason` (dataclass) | `ContextReason` (struct + Display) | `@dataclass` to struct with builder methods | `with_tokens()`, `with_score()` builder pattern |
| `ContextPiece` (dataclass) | `ContextPiece` (struct + Display) | Same as above | `with_order()` builder method |
| `AssembledContext` (dataclass) | `AssembledContext` (struct + Serialize) | Direct mapping | JSON export via serde instead of manual dict construction |
| `ContextTracer` (singleton) | `ContextTracer` (unit struct) | Global singleton to stateless struct | `tracing::debug!` instead of Python logging module |
| `ContextTokenMonitor` (tiktoken) | `ContextTokenMonitor` (heuristic) | tiktoken BPE to `len() / 4` heuristic | Avoids heavy tokenizer dependency; less accurate |
| `CodebaseIndexer` | `CodebaseIndexer` | Near-identical | Added Rust/Cargo.toml detection; native `fs::read_dir` instead of `find` subprocess |
| `EntityExtractor` (class with dict patterns) | `EntityExtractor` (struct with compiled Regex) | Dict of pattern strings to pre-compiled `regex::Regex` | Compiled once in `new()`, reused across calls |
| `ContextRetriever` | `ContextRetriever` | Near-identical | Uses `rg` with `grep` fallback; native recursive file search |
| N/A | `WorktreeManager` / `WorktreeInfo` | New in Rust | Git worktree management for subagent isolation |

## Key Design Decisions

### 1. Composition over Inheritance for ValidatedMessageList

Python's `ValidatedMessageList(list)` subclasses `list` and intercepts mutations. Rust cannot subclass `Vec`, so the Rust version uses composition: a struct wrapping `Vec<ApiMessage>`. This is actually cleaner -- callers must go through `messages()` for read access, making the validation boundary explicit. The trade-off is that code using `&[ApiMessage]` directly (e.g., the compactor) must work with raw slices, which is fine since compaction operates on snapshots, not the live validated list.

### 2. LLM Summarization Pushed to Higher Layer

The Python `ContextCompactor` takes an HTTP client and calls `_summarize()` inline. The Rust version deliberately omits this, keeping the `opendev-context` crate free of async runtime and HTTP dependencies. Only `fallback_summary()` (a pure function) is provided. LLM-powered summarization is orchestrated by the agents crate, which already has access to the HTTP client and async runtime. This improves testability (the compactor can be tested without mocking HTTP) and keeps the dependency graph shallow.

### 3. Heuristic Token Counting Instead of tiktoken

Python uses `tiktoken` for accurate BPE token counting. The Rust version uses `text.len() / 4` as a heuristic. This avoids pulling in a large tokenizer dependency (tiktoken's Rust bindings or a BPE library) while being sufficiently accurate for threshold-based decisions. The compaction thresholds (70%/80%/85%/90%/99%) have wide margins, so a rough estimate does not cause premature or delayed compaction. API calibration via `update_from_api_usage()` provides accurate counts when available.

### 4. Enum Instead of String Constants for OptimizationLevel

Python uses string constants (`"none"`, `"warning"`, `"mask"`, etc.) on a class. Rust uses a proper enum, enabling exhaustive `match` and compile-time checks. The `as_str()` method provides backward-compatible string output for logging.

### 5. Serde Derives Replace Manual Serialization

Python's `ArtifactIndex.to_dict()`/`from_dict()` and `ContextTracer.export_trace()` build dicts manually. Rust derives `Serialize`/`Deserialize` on all data types, getting JSON (de)serialization for free. This eliminates a category of bugs where `to_dict()` and `from_dict()` fall out of sync.

### 6. ContextPicker Split: Data Models vs Orchestration

The Python `ContextPicker` is a monolithic class that imports `FileContentInjector`, `Playbook`, and `SessionManager` and orchestrates context assembly in one place. In Rust, `context_picker.rs` provides only the data models (`ContextCategory`, `ContextReason`, `ContextPiece`, `AssembledContext`, `ContextTracer`). The actual orchestration is wired up at the application layer in higher-level crates. This prevents circular dependencies and allows each data model to be used independently.

### 7. WorktreeManager as a Rust-Only Addition

The `WorktreeManager` in `worktree.rs` is new to the Rust codebase. It manages git worktrees for parallel subagent execution -- each subagent gets an isolated workspace. This was not needed in Python (which used different isolation mechanisms) but is essential for the Rust architecture's parallel agent model.

## Code Examples

### OptimizationLevel: String Constants to Enum

**Python:**
```python
class OptimizationLevel:
    NONE = "none"
    WARNING = "warning"
    MASK = "mask"
    PRUNE = "prune"
    AGGRESSIVE = "aggressive"
    COMPACT = "compact"
```

**Rust:**
```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OptimizationLevel {
    None,
    Warning,
    Mask,
    Prune,
    Aggressive,
    Compact,
}
```

### ValidatedMessageList: Inheritance to Composition

**Python:**
```python
class ValidatedMessageList(list):
    def __init__(self, initial=None, strict=False):
        super().__init__()
        self._strict = strict
        self._pending_tool_ids: set[str] = set()
        self._lock = threading.Lock()
        if initial:
            super().extend(initial)
            self._rebuild_pending_state()

    def append(self, msg):
        # Intercept and validate...
        super().append(msg)
```

**Rust:**
```rust
pub struct ValidatedMessageList {
    messages: Vec<ApiMessage>,
    pending_tool_ids: Mutex<HashSet<String>>,
    strict: bool,
}

impl ValidatedMessageList {
    pub fn messages(&self) -> &[ApiMessage] {
        &self.messages
    }

    pub fn add_tool_result(&mut self, tool_call_id: &str, content: &str) -> Result<(), String> {
        // Validate, then push...
        self.messages.push(msg);
        Ok(())
    }
}
```

### Token Counting: tiktoken to Heuristic

**Python:**
```python
class ContextTokenMonitor:
    def __init__(self, model="gpt-4"):
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
```

**Rust:**
```rust
#[derive(Debug, Clone, Default)]
pub struct ContextTokenMonitor;

impl ContextTokenMonitor {
    pub fn count_tokens(&self, text: &str) -> usize {
        text.len() / 4
    }
}
```

### ArtifactIndex: Manual Serialization to Serde Derive

**Python:**
```python
class ArtifactIndex:
    def to_dict(self):
        return {"entries": dict(self._entries)}

    @classmethod
    def from_dict(cls, data):
        idx = cls()
        idx._entries = dict(data.get("entries", {}))
        return idx
```

**Rust:**
```rust
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ArtifactIndex {
    entries: HashMap<String, ArtifactEntry>,
}
// Serialization is automatic via serde -- no manual to_dict/from_dict needed.
```

## Remaining Gaps

1. **LLM-powered summarization** -- `_summarize()` and `_sanitize_for_summarization()` are not ported. The Rust compactor only provides `fallback_summary()`. Full summarization requires wiring up the HTTP client at the agents layer.

2. **`compact_with_retry()`** -- The retry/replay loop that re-compacts if still over the limit after the first pass is not yet ported.

3. **History archival** -- `archive_history()` (writes full conversation to a scratch file before compaction) is not yet ported.

4. **Hook manager integration** -- `set_hook_manager()` and `PreCompact` event firing are not yet wired up in the Rust compactor.

5. **ContextPicker orchestration** -- The Rust crate provides data models only. The actual `pick_context()` method (file injection, playbook selection, history windowing, system prompt assembly) is not yet ported as a unified entry point.

6. **Accurate token counting** -- The `len() / 4` heuristic may need to be replaced with a proper tokenizer (e.g., `tiktoken-rs`) if compaction timing becomes an issue in practice.

## References

### Python
- `opendev-py/opendev/core/context_engineering/compaction.py` -- ContextCompactor, ArtifactIndex, OptimizationLevel
- `opendev-py/opendev/core/context_engineering/validated_message_list.py` -- ValidatedMessageList
- `opendev-py/opendev/core/context_engineering/message_pair_validator.py` -- MessagePairValidator
- `opendev-py/opendev/core/context_engineering/context_picker/picker.py` -- ContextPicker
- `opendev-py/opendev/core/context_engineering/context_picker/models.py` -- ContextCategory, ContextReason, ContextPiece, AssembledContext
- `opendev-py/opendev/core/context_engineering/context_picker/tracer.py` -- ContextTracer
- `opendev-py/opendev/core/context_engineering/retrieval/indexer.py` -- CodebaseIndexer
- `opendev-py/opendev/core/context_engineering/retrieval/retriever.py` -- ContextRetriever, EntityExtractor
- `opendev-py/opendev/core/context_engineering/retrieval/token_monitor.py` -- ContextTokenMonitor

### Rust
- `crates/opendev-context/src/lib.rs` -- Module declarations and re-exports
- `crates/opendev-context/src/compaction.rs` -- ContextCompactor, ArtifactIndex, ArtifactEntry, OptimizationLevel
- `crates/opendev-context/src/validated_list.rs` -- ValidatedMessageList
- `crates/opendev-context/src/pair_validator.rs` -- MessagePairValidator, ViolationType, ValidationResult
- `crates/opendev-context/src/context_picker.rs` -- ContextCategory, ContextReason, ContextPiece, AssembledContext, ContextTracer
- `crates/opendev-context/src/retrieval/mod.rs` -- Re-exports
- `crates/opendev-context/src/retrieval/indexer.rs` -- CodebaseIndexer
- `crates/opendev-context/src/retrieval/retriever.rs` -- ContextRetriever, EntityExtractor, Entities
- `crates/opendev-context/src/retrieval/token_monitor.rs` -- ContextTokenMonitor
- `crates/opendev-context/src/worktree.rs` -- WorktreeManager, WorktreeInfo
