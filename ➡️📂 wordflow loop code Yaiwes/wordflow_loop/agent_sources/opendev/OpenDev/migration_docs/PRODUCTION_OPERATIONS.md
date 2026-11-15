# Production Operations

## Overview

This document covers the production-critical runtime subsystems that keep OpenDev reliable under real-world conditions: interrupt handling, error classification and retry, session persistence with crash recovery, file locking, configuration migration, the snapshot system for per-step undo, and the EventBus for decoupled inter-component communication. Together these subsystems form the operational backbone that sits between the agent logic (`opendev-agents`) and the user-facing frontends (`opendev-tui`, `opendev-web`).

In the overall architecture, most of these subsystems live in two crates:
- **`opendev-runtime`** -- interrupt tokens, error classification, error handling, snapshot manager, event bus
- **`opendev-history`** -- session manager, file locks, session index, a second snapshot manager for per-step undo

## Python Architecture

### Module Structure

```
opendev/core/
  runtime/
    interrupt_token.py          # InterruptToken (threading.Event + ctypes async exception injection)
    monitoring/
      error_handler.py          # ErrorHandler (interactive Rich console prompts)
      task_monitor.py           # TaskMonitor (timer, token tracking, interrupt delegation)
    config.py                   # ConfigManager (hierarchical JSON loading, fireworks normalization)
    session_model.py            # Per-session model overlay
  errors.py                     # ErrorCategory enum, StructuredError dataclass hierarchy, classify_api_error()
  events/
    bus.py                      # EventBus (threading.Lock, dict[EventType, list[handler]])
    types.py                    # EventType enum (30+ variants), Event dataclass
  snapshot/
    manager.py                  # SnapshotManager (shadow git repo, take/diff/revert/cleanup)
  context_engineering/
    history/
      file_locks.py             # exclusive_session_lock() context manager (fcntl.flock)
      session_manager/
        manager.py              # SessionManager (mixin composition: Index + Persistence + Listing)
        persistence.py          # PersistenceMixin (JSON + JSONL split, auto-save every N turns)
```

### Key Abstractions

- **InterruptToken**: A `threading.Event` wrapper with a three-layer force-interrupt mechanism: (1) set polling flag, (2) cancel in-flight HTTP via callback, (3) inject `InterruptedError` into the agent thread via `PyThreadState_SetAsyncExc` with retry.
- **StructuredError hierarchy**: A base `StructuredError` dataclass with specialized subclasses (`ContextOverflowError`, `RateLimitError`, `AuthError`, `GatewayError`, `OutputLengthError`) using `field(init=False)` defaults.
- **ErrorHandler**: Interactive error recovery via Rich console prompts. Presents retry/skip/cancel/edit choices.
- **TaskMonitor**: Combines timer, token delta tracking, and interrupt delegation. Holds an optional `InterruptToken` reference.
- **SessionManager**: Composed via Python mixins (`IndexMixin`, `PersistenceMixin`, `ListingMixin`). Supports auto-save every N turns, project-scoped storage, JSONL transcript format, and session forking.
- **exclusive_session_lock**: Context manager using `fcntl.flock()` with 50ms retry polling and configurable timeout.
- **EventBus**: Synchronous pub/sub with topic-based subscriptions and wildcard handlers. Thread-safe via `threading.Lock`.
- **SnapshotManager**: Shadow git repository per project. Creates commits containing copies of files, supports diff and revert.
- **ConfigManager**: Hierarchical loading (global > project), JSON comment stripping, `{env:VAR}` and `{file:path}` substitution, Fireworks model normalization, legacy `api_key` removal.

### Design Patterns

- **Mixin composition** for SessionManager (IndexMixin, PersistenceMixin, ListingMixin)
- **Observer pattern** for EventBus (subscribe/publish with wildcard support)
- **Context manager pattern** for file locking (`exclusive_session_lock`)
- **Strategy pattern** for error classification (regex pattern lists per error category)
- **Three-layer cancellation** in InterruptToken (flag, HTTP callback, async exception injection)

### SOLID Analysis

- **SRP**: Generally well-separated. `InterruptToken` handles only cancellation; `StructuredError` handles only classification. However, `ErrorHandler` mixes error display with interactive prompting (violates SRP).
- **OCP**: The `StructuredError` subclass hierarchy is open for extension (add new error types) without modifying `classify_api_error()`. Pattern lists are closed arrays.
- **LSP**: Subclasses of `StructuredError` are substitutable. `InterruptToken` provides `TaskMonitor`-compatible duck-typing methods.
- **ISP**: `TaskMonitor` is a fairly large interface (timer + tokens + interrupt). Could be split.
- **DIP**: `ErrorHandler` depends directly on Rich `Console` and `prompt_toolkit`. `SessionManager` directly accesses filesystem. No dependency injection.

## Rust Architecture

### Module Structure

```
crates/opendev-runtime/src/
  interrupt.rs        # InterruptToken (AtomicBool + CancellationToken)
  errors.rs           # ErrorCategory enum, StructuredError struct, classify_api_error()
  error_handler.rs    # ErrorAction enum, ErrorResult, OperationError, is_transient_error()
  event_bus.rs        # EventBus (tokio::sync::broadcast), FilteredSubscriber
  snapshot.rs         # SnapshotManager (shadow git, take/diff/revert/cleanup)
  lib.rs              # Module declarations and re-exports

crates/opendev-history/src/
  session_manager.rs  # SessionManager (JSON + JSONL split format)
  file_locks.rs       # FileLock (fd-lock RwLock), with_file_lock()
  snapshot.rs         # SnapshotManager (bare shadow git, tree-hash based, track/patch/revert/restore)
  index.rs            # SessionIndex
  listing.rs          # SessionListing
  lib.rs              # Module declarations and re-exports

crates/opendev-config/src/
  loader.rs           # ConfigLoader (hierarchical merge, atomic save, env overrides)
  paths.rs            # Path resolution
```

### Key Abstractions

- **InterruptToken** (`interrupt.rs`): Wraps `Arc<InterruptInner>` containing an `AtomicBool` (for synchronous polling) and a `tokio_util::sync::CancellationToken` (for async `select!` integration). `Clone` is cheap (Arc). `force_interrupt()` is identical to `request()` since Rust uses cooperative cancellation rather than CPython's async exception injection.
- **StructuredError** (`errors.rs`): Single flat struct with optional fields (`token_count`, `token_limit`, `retry_after`) instead of Python's subclass hierarchy. Implements `Display`, `Error`, `Serialize`, `Deserialize`. Pattern matching uses `LazyLock<PatternSet>` with pre-compiled `Regex` vectors.
- **ErrorAction / ErrorResult / OperationError** (`error_handler.rs`): Pure data types with no UI coupling. The `resolve_choice()` and `available_actions()` functions are pure logic; the TUI handles presentation separately.
- **EventBus** (`event_bus.rs`): Built on `tokio::sync::broadcast` with a configurable capacity (default 256). Events are `Clone` (required by broadcast). `FilteredSubscriber` wraps a receiver with event-type filtering. No global singleton; instances are passed via dependency injection.
- **FileLock** (`file_locks.rs`): Uses `fd-lock::RwLock` for cross-platform exclusive locks. Creates `.lock` sidecar files, retries every 50ms up to timeout. RAII-based: lock released on `Drop`, sidecar file cleaned up.
- **SessionManager** (`session_manager.rs`): Single struct (no mixin composition). JSON metadata + JSONL transcript split. Atomic writes via temp-file-then-rename. Session index updated on save.
- **SnapshotManager** (two implementations):
  - `opendev-runtime::snapshot` -- commit-based: copies files into a shadow git repo and creates commits. Supports `take_snapshot`, `get_diff`, `revert_to_snapshot`.
  - `opendev-history::snapshot` -- tree-hash-based: uses `--bare` init and `git write-tree` for lightweight snapshots without commits. Supports `track`, `patch`, `revert`, `restore`, `undo_last`.
- **ConfigLoader** (`loader.rs`): Hierarchical merge via `serde_json::Value` overlay. Atomic save (write to `.tmp` then rename). Environment variable overrides for provider, model, max_tokens, temperature, verbose, debug.

### Design Patterns and Python Mapping

| Pattern | Python | Rust |
|---|---|---|
| Cancellation | `threading.Event` + `ctypes.PyThreadState_SetAsyncExc` | `AtomicBool` + `CancellationToken` (cooperative) |
| Error hierarchy | Dataclass inheritance (`ContextOverflowError(StructuredError)`) | Single struct with `ErrorCategory` enum discriminant |
| Error classification | List of raw regex strings, compiled at call time | `LazyLock<PatternSet>` with pre-compiled `Regex` vectors |
| Session composition | Python mixins (`IndexMixin + PersistenceMixin + ListingMixin`) | Single struct, separate modules for index/listing |
| File locking | `fcntl.flock()` context manager | `fd-lock::RwLock` with RAII `Drop` |
| Event bus | `threading.Lock` + `dict[EventType, list[handler]]` | `tokio::sync::broadcast` channel |
| Config loading | JSON comment stripping, `{env:VAR}` substitution, Fireworks normalization | `serde_json::Value` merge, env var overrides |
| Snapshot storage | Shadow git repo with commits | Two variants: commit-based and bare tree-hash-based |

### SOLID Analysis

- **SRP**: Excellent separation. `InterruptToken` is purely cancellation. `error_handler.rs` provides only data types and pure logic (no UI). `errors.rs` handles only classification. Presentation is pushed to the TUI/CLI layer.
- **OCP**: `ErrorCategory` enum is extensible by adding variants. Pattern lists in `LazyLock` are fixed at compile time but the `classify_api_error()` function is straightforward to extend.
- **LSP**: Not directly applicable (no trait inheritance for these types), but `InterruptToken` provides TaskMonitor-compatible method aliases (`should_interrupt`, `request_interrupt`).
- **ISP**: Clean. `EventBus` exposes only `publish`, `emit`, `subscribe`. `FileLock` exposes only `acquire` and `release`. No bloated interfaces.
- **DIP**: `EventBus` is injected (no global singleton). `ErrorHandler` types carry no UI dependencies. `SessionManager` still directly accesses the filesystem (same as Python).

## Migration Mapping

| Python Class/Module | Rust Struct/Trait | Pattern Change | Notes |
|---|---|---|---|
| `InterruptToken` (threading.Event + ctypes) | `InterruptToken` (AtomicBool + CancellationToken) | Three-layer force-interrupt becomes cooperative cancellation | No async exception injection in Rust; `force_interrupt()` == `request()` |
| `TaskMonitor` | Eliminated (split across InterruptToken + CostTracker) | Decomposed | Timer and token tracking moved to `CostTracker`; interrupt to `InterruptToken` |
| `StructuredError` hierarchy (5 subclasses) | `StructuredError` flat struct | Inheritance to composition | Single struct with `ErrorCategory` discriminant + optional fields |
| `classify_api_error()` | `classify_api_error()` | Pattern compilation moved to `LazyLock` | Same regex patterns, pre-compiled at first use |
| `ErrorHandler` (interactive Rich prompts) | `ErrorAction` + `ErrorResult` + `OperationError` | UI coupling removed | Pure data types; TUI handles presentation |
| `EventBus` (threading.Lock + dict) | `EventBus` (tokio::sync::broadcast) | Synchronous to async-native | No global singleton; `FilteredSubscriber` replaces wildcard handlers |
| `EventType` enum (30+ variants) | `Event.event_type: String` | Enum to free-form strings | More flexible; less type safety |
| `exclusive_session_lock()` (fcntl.flock) | `FileLock` (fd-lock::RwLock) | Context manager to RAII guard | Cross-platform via `fd-lock` crate |
| `SessionManager` (3 mixins) | `SessionManager` (single struct) | Mixin composition to struct | Separate modules but single type |
| `PersistenceMixin.add_message()` auto-save | `SessionManager.save_session()` caller-driven | Auto-save moved to caller | No built-in turn-count auto-save; caller decides when to save |
| `SnapshotManager` (commit-based shadow git) | Two `SnapshotManager` implementations | Split into commit-based and tree-hash-based | `opendev-runtime` has commit-based; `opendev-history` has tree-hash-based |
| `ConfigManager` (comment stripping, `{env:VAR}`) | `ConfigLoader` (serde_json merge, env overrides) | Simplified | No JSON comment support; no `{env:VAR}` / `{file:path}` substitution; no Fireworks normalization |
| `ConfigManager.ensure_directories()` legacy migration | Not ported | Dropped | No old flat sessions directory migration in Rust |

## Subsystem Details

### Interrupt Handling

**InterruptToken design** (`crates/opendev-runtime/src/interrupt.rs`):

The token wraps `Arc<InterruptInner>` containing two cancellation primitives:

1. **`AtomicBool flag`** -- for cheap synchronous polling via `is_requested()` / `throw_if_requested()`. Uses `Ordering::Release` for stores and `Ordering::Acquire` for loads to ensure visibility across threads.

2. **`CancellationToken cancel`** -- from `tokio_util::sync`. Provides the `cancelled()` async future for use in `tokio::select!` blocks, enabling cancellation-aware async code without polling.

Key behavioral differences from Python:
- **No force-interrupt distinction**: Python's `force_interrupt()` uses three layers (flag, HTTP cancel callback, CPython async exception injection). Rust's `force_interrupt()` is identical to `request()` because Rust relies on cooperative cancellation.
- **No HTTP cancel callback**: The Rust HTTP client (`reqwest`) respects the `CancellationToken` natively through `tokio::select!`.
- **No `reset()` for CancellationToken**: The `AtomicBool` can be reset, but `CancellationToken` cannot be un-cancelled. For multi-run reuse, callers create a new `InterruptToken`.
- **Child tokens**: `child_token()` creates a derived token that is cancelled when the parent is cancelled, enabling hierarchical cancellation for sub-agents.

```rust
// Typical usage in an async agent loop
tokio::select! {
    result = do_llm_call(&messages) => handle_result(result),
    _ = token.cancelled() => return Err(InterruptedError.into()),
}
```

### Error Classification & Retry

**Error types** (`crates/opendev-runtime/src/errors.rs`):

The Python subclass hierarchy (`ContextOverflowError`, `RateLimitError`, etc.) is flattened into a single `StructuredError` struct with an `ErrorCategory` enum discriminant. Category-specific fields (`token_count`, `token_limit`, `retry_after`) are `Option<T>` instead of subclass-specific fields.

Named constructors (`StructuredError::context_overflow()`, `::rate_limit()`, `::auth()`, `::gateway()`, `::api()`, `::output_length()`) provide the same ergonomics as Python subclass constructors.

**Pattern matching** uses `LazyLock<PatternSet>` to pre-compile regex patterns at first access. The same provider-specific patterns are preserved (Anthropic, OpenAI, Google, Azure) with identical classification priority: gateway > overflow > rate_limit > auth (by status code) > auth (by pattern) > generic.

**Error handling** (`crates/opendev-runtime/src/error_handler.rs`):

Decoupled from UI. Provides pure data types:
- `ErrorAction` enum: Retry, Skip, Cancel, Edit
- `OperationError` struct: error info with `allow_retry` / `allow_edit` flags
- `available_actions()`: returns valid actions for a given error
- `resolve_choice()`: maps a character to an `ErrorResult`
- `is_transient_error()`: pattern-based classification for auto-retry decisions

**Retry policies**:
- `ContextOverflow`: retryable via context compaction (`should_compact()` returns true)
- `RateLimit`: retryable with optional `retry_after` delay
- `Gateway` / `OutputLength`: retryable
- `Auth`: never retryable
- `Api` with 5xx status: retryable
- Transient errors (timeout, connection reset, etc.): identified by `is_transient_error()`

### Session Management

**SessionManager** (`crates/opendev-history/src/session_manager.rs`):

Single struct replacing Python's mixin-based composition. Storage format:
- `{id}.json` -- session metadata (no messages)
- `{id}.jsonl` -- message transcript (one JSON object per line)

**Atomic writes**: Both files are written via temp-file-then-rename pattern:
```rust
let tmp_json = session_dir.join(format!(".{}.json.tmp", session.id));
std::fs::write(&tmp_json, &json_content)?;
std::fs::rename(&tmp_json, &json_path)?;
```

**Crash recovery**: The atomic write pattern ensures that a crash during write leaves either the old complete file or the new complete file. The temp file (dot-prefixed) is never read on load. Legacy format (messages in JSON, no JSONL) is supported for backward compatibility.

**Auto-save**: Unlike Python's `add_message(auto_save_interval=5)`, Rust does not have built-in turn-count auto-save. The caller (TUI/REPL) is responsible for calling `save_current()` at appropriate points. This is a deliberate simplification.

**Session index**: Updated on every save via `SessionIndex::upsert_entry()`. Provides O(1) session listing without parsing all JSON files.

### File Locking

**FileLock** (`crates/opendev-history/src/file_locks.rs`):

Cross-platform exclusive locking via `fd-lock::RwLock`:
- Creates a `.lock` sidecar file adjacent to the target file
- Attempts `try_write()` in a polling loop with 50ms sleep intervals
- Times out with `io::ErrorKind::TimedOut` after the specified duration
- RAII-based: `Drop` implementation releases the OS lock and removes the sidecar file

**`with_file_lock()`** convenience function: acquire lock, run closure, release lock.

Compared to Python's `fcntl.flock()` context manager, the Rust implementation:
- Works cross-platform (macOS, Linux, Windows) via `fd-lock`
- Uses RAII instead of context manager (same semantic, different mechanism)
- Cleans up sidecar files on `Drop` (Python also cleans up in `finally`)

### Snapshot System

Two snapshot implementations exist, serving different use cases:

**Commit-based** (`crates/opendev-runtime/src/snapshot.rs`):
- Shadow git repo at `~/.opendev/data/snapshot/{project_id}/`
- Creates actual git commits containing copies of modified files
- Operations: `take_snapshot()`, `get_diff()`, `revert_to_snapshot()`, `cleanup()`
- Project ID computed via `DefaultHasher` (16-char hex)
- Used for tool-level snapshots (before/after a single tool execution)

**Tree-hash-based** (`crates/opendev-history/src/snapshot.rs`):
- Bare shadow git repo at `~/.opendev/snapshot/{project_id}/`
- Uses `git write-tree` to capture tree hashes without creating commits
- Operations: `track()`, `patch()`, `revert()`, `restore()`, `undo_last()`
- Maintains an in-memory `Vec<String>` of snapshot hashes for the session
- `undo_last()` pops the most recent snapshot and restores to the previous one
- Used for step-level undo (revert any agent step)

Both implementations:
- Initialize lazily on first use
- Use `std::process::Command` to shell out to git
- Support garbage collection (`gc --prune=7.days.ago`)
- Handle missing git gracefully (return `None` / empty `Vec`)

### EventBus

**EventBus** (`crates/opendev-runtime/src/event_bus.rs`):

Built on `tokio::sync::broadcast`:
- `publish()` / `emit()` send events to all subscribers
- `subscribe()` returns a `broadcast::Receiver<Event>`
- `FilteredSubscriber` wraps a receiver with event-type-based filtering
- Handles lag gracefully (logs and skips missed events)
- No global singleton -- instances are passed via dependency injection

**Event struct**:
- `event_type: String` (free-form, vs. Python's `EventType` enum)
- `source: String` (component that published)
- `data: serde_json::Value` (arbitrary payload)
- `timestamp_ms: u64` (milliseconds since epoch)

Compared to Python's EventBus:
- Async-native (broadcast channel vs. synchronous handler calls)
- No wildcard handlers (use `subscribe()` which receives all events, then filter)
- No global singleton (`get_bus()` pattern dropped)
- Capacity-bounded (256 events default, older events dropped if subscriber is slow)

**Current status**: The EventBus is wired into the architecture but, as noted in the Python source, neither the TUI (which uses ratatui's own event system) nor the Web UI (which uses direct WebSocket broadcasts) fully utilizes it yet. It is reserved for future unified event handling.

## Key Design Decisions

1. **Cooperative cancellation over async exception injection**: Python's `InterruptToken` uses `PyThreadState_SetAsyncExc` to forcibly interrupt blocked threads. Rust replaces this with `CancellationToken` + `tokio::select!`, which is safer (no undefined behavior from interrupted destructors) and idiomatic for async Rust.

2. **Flat struct over inheritance for errors**: Python uses 5 `StructuredError` subclasses. Rust uses a single struct with an enum discriminant and optional fields. This avoids trait objects and dynamic dispatch while preserving the same classification logic.

3. **Pre-compiled regex patterns**: Python compiles regex patterns on every `classify_api_error()` call. Rust uses `LazyLock` to compile once at first use, improving performance for repeated classifications.

4. **Struct over mixins for SessionManager**: Python composes SessionManager from three mixins. Rust uses a single struct with methods organized across the module. This is more idiomatic Rust and avoids the complexity of trait-based composition.

5. **Caller-driven auto-save**: Python's `add_message(auto_save_interval=5)` auto-saves every 5 turns. Rust delegates save timing to the caller, providing more control and avoiding hidden I/O.

6. **Two snapshot implementations**: The commit-based snapshot (runtime crate) and tree-hash-based snapshot (history crate) serve different granularities. The tree-hash approach is more lightweight (no commit objects) and better suited for high-frequency per-step snapshots.

7. **No global EventBus singleton**: Python uses `get_bus()` to return a module-level singleton. Rust passes `EventBus` instances explicitly, improving testability and avoiding hidden global state.

8. **Simplified config loading**: Rust drops JSON comment stripping, `{env:VAR}` / `{file:path}` template substitution, and Fireworks model normalization. Environment overrides use direct `std::env::var()` checks.

## Code Examples

### InterruptToken with tokio::select!

```rust
use opendev_runtime::InterruptToken;

let token = InterruptToken::new();
let child = token.clone();

// Agent loop
tokio::select! {
    response = llm_client.chat(&messages) => {
        // Process response
    }
    _ = child.cancelled() => {
        // User pressed ESC
        return Err(InterruptedError.into());
    }
}

// Synchronous polling in a tool
token.throw_if_requested()?;
```

### Error Classification

```rust
use opendev_runtime::{classify_api_error, ErrorCategory};

let err = classify_api_error(
    "This model's maximum context length is 128000 tokens",
    None,
    Some("openai"),
);
assert_eq!(err.category, ErrorCategory::ContextOverflow);
assert!(err.is_retryable);
assert!(err.should_compact());
```

### Atomic Session Save

```rust
use opendev_history::SessionManager;

let mgr = SessionManager::new(session_dir)?;
// Writes .tmp file then renames atomically
mgr.save_session(&session)?;
```

### File Locking

```rust
use opendev_history::FileLock;
use std::time::Duration;

let lock = FileLock::acquire(path, Duration::from_secs(5))?;
// ... exclusive access ...
lock.release(); // or just let it drop
```

### EventBus

```rust
use opendev_runtime::{EventBus, FilteredSubscriber};

let bus = EventBus::new();
let mut sub = FilteredSubscriber::new(&bus, Some(vec!["tool.complete".into()]));

bus.emit("tool.complete", "bash", serde_json::json!({"exit_code": 0}));

if let Some(event) = sub.recv().await {
    println!("Tool completed: {:?}", event.data);
}
```

## Remaining Gaps

1. **No `{env:VAR}` / `{file:path}` config substitution**: Python supports template variables in config values. Rust only supports direct environment variable overrides for a fixed set of fields.

2. **No JSON comment stripping**: Python's `ConfigManager` strips `//` and `/* */` comments from JSON config files. Rust's `ConfigLoader` requires strict JSON.

3. **No Fireworks model normalization**: Python auto-corrects Fireworks model IDs to `accounts/fireworks/models/{slug}` format. Not ported.

4. **No auto-save interval in SessionManager**: Python auto-saves every N turns. Rust relies on callers to save explicitly.

5. **EventBus not fully wired**: Neither TUI nor Web UI uses the EventBus as the primary event dispatch mechanism. Both use their own event systems.

6. **No session forking in Rust**: Python's `fork_session()` creates a child session by cloning messages up to a point. Not yet ported.

7. **EventType is free-form string**: Python defines 30+ typed `EventType` enum variants. Rust uses `String`, losing compile-time event type checking.

8. **No legacy directory migration**: Python's `ConfigManager.ensure_directories()` migrates old flat session directories. Not ported (assumes fresh Rust installation).

## References

- Python interrupt token: `opendev-py/opendev/core/runtime/interrupt_token.py`
- Python errors: `opendev-py/opendev/core/errors.py`
- Python error handler: `opendev-py/opendev/core/runtime/monitoring/error_handler.py`
- Python task monitor: `opendev-py/opendev/core/runtime/monitoring/task_monitor.py`
- Python session manager: `opendev-py/opendev/core/context_engineering/history/session_manager/`
- Python file locks: `opendev-py/opendev/core/context_engineering/history/file_locks.py`
- Python snapshot manager: `opendev-py/opendev/core/snapshot/manager.py`
- Python event bus: `opendev-py/opendev/core/events/bus.py`
- Python config manager: `opendev-py/opendev/core/runtime/config.py`
- Rust interrupt: `crates/opendev-runtime/src/interrupt.rs`
- Rust errors: `crates/opendev-runtime/src/errors.rs`
- Rust error handler: `crates/opendev-runtime/src/error_handler.rs`
- Rust event bus: `crates/opendev-runtime/src/event_bus.rs`
- Rust snapshot (runtime): `crates/opendev-runtime/src/snapshot.rs`
- Rust snapshot (history): `crates/opendev-history/src/snapshot.rs`
- Rust session manager: `crates/opendev-history/src/session_manager.rs`
- Rust file locks: `crates/opendev-history/src/file_locks.rs`
- Rust config loader: `crates/opendev-config/src/loader.rs`
