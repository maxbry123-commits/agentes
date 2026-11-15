# Migration Phases

## Phase 1: Core Data Models and Configuration

**Status**: Not started
**Estimated effort**: ~2.5K LOC Python → ~3K LOC Rust
**Dependencies**: None (leaf of dependency graph)

### What to migrate

| Python Source | Rust Target | Description |
|---------------|-------------|-------------|
| `opendev/models/message.py` | `opendev-models/src/message.rs` | ChatMessage, ToolCall, Role, InputProvenance |
| `opendev/models/session.py` | `opendev-models/src/session.rs` | Session, SessionMetadata, Channel enum |
| `opendev/models/config.py` | `opendev-models/src/config.rs` | AppConfig, PermissionConfig, PlaybookConfig |
| `opendev/models/file_change.py` | `opendev-models/src/file_change.rs` | FileChange, FileChangeType enum |
| `opendev/models/operation.py` | `opendev-models/src/operation.rs` | WriteResult, EditResult |
| `opendev/models/user.py` | `opendev-models/src/user.rs` | User model |
| `opendev/models/api.py` | `opendev-models/src/api.rs` | API request/response types |
| `opendev/models/message_validator.py` | `opendev-models/src/validator.rs` | Validation rules |
| `opendev/core/paths.py` | `opendev-config/src/paths.rs` | Path constants |
| `opendev/config/models.py` | `opendev-config/src/lib.rs` | ModelInfo, ProviderInfo |
| `opendev/config/models_dev_loader.py` | `opendev-config/src/models_dev.rs` | models.dev API cache |

### Key decisions
- All model structs derive `serde::Serialize, serde::Deserialize`
- Enums use `strum` for string conversion (matching Python enum string values)
- `chrono::DateTime<Utc>` replaces Python `datetime`
- `uuid::Uuid` replaces Python `uuid4()`
- PyO3 `#[pyclass]` annotations on all public types for bridge

### Deliverables
- `opendev-models` crate with all data types
- `opendev-config` crate with hierarchical config loading
- PyO3 module exposing both crates to Python
- Round-trip serialization tests for all types
- Compatibility test: load existing session JSON files

---

## Phase 2: HTTP Client, Auth, and API Adapters

**Status**: Not started
**Estimated effort**: ~3K LOC Python → ~2.5K LOC Rust
**Dependencies**: Phase 1 (models)

### What to migrate

| Python Source | Rust Target | Description |
|---------------|-------------|-------------|
| `opendev/core/agents/components/api/http_client.py` | `opendev-http/src/client.rs` | reqwest wrapper, retry, interrupt |
| `opendev/core/agents/components/api/auth_rotation.py` | `opendev-http/src/rotation.rs` | API key rotation |
| `opendev/core/agents/components/api/base_adapter.py` | `opendev-http/src/adapters/base.rs` | ProviderAdapter trait |
| `opendev/core/agents/components/api/anthropic_adapter.py` | `opendev-http/src/adapters/anthropic.rs` | Anthropic adapter |
| `opendev/core/agents/components/api/openai_responses_adapter.py` | `opendev-http/src/adapters/openai.rs` | OpenAI adapter |
| `opendev/core/auth/credentials.py` | `opendev-http/src/auth.rs` | CredentialStore |
| `opendev/core/auth/user_store.py` | `opendev-http/src/auth.rs` | User storage |

### Key decisions
- `reqwest` with `rustls-tls` (no OpenSSL dependency)
- Interrupt via `tokio_util::sync::CancellationToken` + `tokio::select!` (replaces polling `_should_interrupt`)
- Retry with exponential backoff via custom logic (simpler than Python's polling loop)
- Auth file at `~/.opendev/auth.json` with `std::fs::set_permissions` (mode 0600)

### Deliverables
- `opendev-http` crate with full HTTP client
- Provider adapters for Anthropic and OpenAI
- Credential store with atomic writes
- Mock server tests (wiremock crate)
- Integration test with live API call (gated by env var)

---

## Phase 3: Context Engineering Core

**Status**: Not started
**Estimated effort**: ~15K LOC Python → ~12K LOC Rust
**Dependencies**: Phase 1 (models), Phase 2 (HTTP for LLM-powered compaction)

### What to migrate

**opendev-context crate:**

| Python Source | Rust Target | Description |
|---------------|-------------|-------------|
| `opendev/core/context_engineering/compaction.py` | `opendev-context/src/compaction.rs` | Staged compaction |
| `opendev/core/context_engineering/validated_message_list.py` | `opendev-context/src/validated_list.rs` | ValidatedMessageList |
| `opendev/core/context_engineering/message_pair_validator.py` | `opendev-context/src/pair_validator.rs` | Message pair repair |
| `opendev/core/context_engineering/context_picker/` | `opendev-context/src/context_picker.rs` | Dynamic context selection |

**opendev-history crate:**

| Python Source | Rust Target | Description |
|---------------|-------------|-------------|
| `opendev/core/context_engineering/history/session_manager/index.py` | `opendev-history/src/index.rs` | Session index |
| `opendev/core/context_engineering/history/session_manager/listing.py` | `opendev-history/src/listing.rs` | Session listing |
| `opendev/core/context_engineering/history/file_locks.py` | `opendev-history/src/file_locks.rs` | File locks (fd-lock) |
| `opendev/core/context_engineering/history/snapshot.py` | `opendev-history/src/snapshot.rs` | Snapshots |

**opendev-memory crate:**

| Python Source | Rust Target | Description |
|---------------|-------------|-------------|
| `opendev/core/context_engineering/memory/playbook.py` | `opendev-memory/src/playbook.rs` | ACE playbook |
| `opendev/core/context_engineering/memory/delta.py` | `opendev-memory/src/delta.rs` | Delta operations |
| `opendev/core/context_engineering/memory/embeddings.py` | `opendev-memory/src/embeddings.rs` | Embedding cache |
| `opendev/core/context_engineering/memory/selector.py` | `opendev-memory/src/selector.rs` | Semantic selector |
| `opendev/core/context_engineering/memory/reflection/reflector.py` | `opendev-memory/src/reflector.rs` | Reflection |
| `opendev/core/context_engineering/memory/roles.py` | `opendev-memory/src/roles.rs` | Roles |

### Key decisions
- Token counting via `tiktoken-rs` crate
- File locking via `fd-lock` crate (cross-platform)
- Session JSON read/write via `serde_json` (must match Python format exactly)

### Deliverables
- Three crates: `opendev-context`, `opendev-history`, `opendev-memory`
- Session file compatibility tests (load real files from ~/.opendev/sessions/)
- Compaction tests at various token thresholds
- File locking stress tests

---

## Phase 4: Tool System and Implementations

**Status**: Not started
**Estimated effort**: ~20K LOC Python → ~18K LOC Rust
**Dependencies**: Phases 1-3

### What to migrate

**opendev-tools-core:**

| Python Source | Rust Target | Description |
|---------------|-------------|-------------|
| `opendev/core/context_engineering/tools/implementations/base.py` | `opendev-tools-core/src/traits.rs` | BaseTool trait |
| `opendev/core/context_engineering/tools/registry.py` | `opendev-tools-core/src/registry.rs` | ToolRegistry |
| `opendev/core/context_engineering/tools/param_normalizer.py` | `opendev-tools-core/src/normalizer.rs` | Param normalization |
| `opendev/core/context_engineering/tools/result_sanitizer.py` | `opendev-tools-core/src/sanitizer.rs` | Result truncation |
| `opendev/core/context_engineering/tools/tool_policy.py` | `opendev-tools-core/src/policy.rs` | Tool policy |
| `opendev/core/context_engineering/tools/parallel_policy.py` | `opendev-tools-core/src/parallel.rs` | Parallel policy |

**opendev-tools-impl:** All 20+ tool implementations from `tools/implementations/`

**opendev-tools-lsp:** All 39 language server configs from `tools/lsp/language_servers/`

**opendev-tools-symbol:** Symbol operations from `tools/symbol_tools/`

### Key decisions
- `BaseTool` becomes an `async_trait` in Rust
- Bash tool uses `tokio::process::Command` with output streaming
- Git operations via `git2` crate (libgit2 bindings)
- File search via `grep` crate or inline ripgrep integration
- Web fetch via `reqwest` + `scraper` for HTML parsing
- PDF via `lopdf` or `pdf-extract`

### Deliverables
- Four crates with all tools implemented
- Unit tests per tool with mocked dependencies
- Integration tests for bash, file ops, git (using temp dirs/repos)
- LSP tests against TypeScript and Python language servers

---

## Phase 5: Agent Layer and ReAct Loop

**Status**: Not started
**Estimated effort**: ~8.7K LOC Python → ~7K LOC Rust
**Dependencies**: Phases 1-4

### What to migrate

| Python Source | Rust Target | Description |
|---------------|-------------|-------------|
| `opendev/core/base/abstract/base_agent.py` | `opendev-agents/src/traits.rs` | BaseAgent trait |
| `opendev/core/agents/main_agent/agent.py` | `opendev-agents/src/main_agent.rs` | MainAgent struct |
| `opendev/core/agents/main_agent/llm_calls.py` | `opendev-agents/src/llm_calls.rs` | LLM call methods |
| `opendev/core/agents/main_agent/run_loop.py` | `opendev-agents/src/react_loop.rs` | ReAct loop |
| `opendev/core/agents/prompts/composition.py` | `opendev-agents/src/prompts/composer.rs` | PromptComposer |
| `opendev/core/agents/prompts/loader.py` | `opendev-agents/src/prompts/loader.rs` | Template loader |
| `opendev/core/agents/subagents/` | `opendev-agents/src/subagents/` | 8 subagent types |
| `opendev/core/agents/components/response/cleaner.py` | `opendev-agents/src/response/cleaner.rs` | Response cleaner |

### Key decisions
- Mixin inheritance → composition (MainAgent holds HttpClient, LlmCaller, ToolRegistry as fields)
- Prompt templates: `include_str!` for built-in, runtime file loading for user customizations
- Subagent execution via `tokio::task::spawn` with restricted tool sets

### Deliverables
- `opendev-agents` crate
- Prompt composition snapshot tests
- Mock LLM response tests for ReAct loop
- Integration test with real API call

---

## Phase 6: Web Backend and MCP

**Status**: Not started
**Estimated effort**: ~8K LOC Python → ~6K LOC Rust
**Dependencies**: Phase 5 (agents)

### What to migrate

| Python Source | Rust Target | Description |
|---------------|-------------|-------------|
| `opendev/web/server.py` | `opendev-web/src/server.rs` | Axum app + middleware |
| `opendev/web/websocket.py` | `opendev-web/src/websocket.rs` | WebSocket manager |
| `opendev/web/state.py` | `opendev-web/src/state.rs` | Shared state |
| `opendev/web/routes/*.py` | `opendev-web/src/routes/*.rs` | REST routes |
| `opendev/core/context_engineering/mcp/manager/manager.py` | `opendev-mcp/src/manager.rs` | MCP manager |
| `opendev/core/context_engineering/mcp/manager/transport.py` | `opendev-mcp/src/transport/` | MCP transports |
| `opendev/core/channels/router.py` | `opendev-channels/src/router.rs` | Channel router |

### Key decisions
- Axum must expose identical REST/WebSocket API as FastAPI (React frontend unchanged)
- State shared via `Arc<RwLock<WebState>>` (replaces Python's module-level state)
- Static files served via `tower-http::services::ServeDir`
- MCP client built on reqwest (HTTP/SSE) and tokio::process (stdio)

### Deliverables
- Three crates: `opendev-web`, `opendev-mcp`, `opendev-channels`
- API compatibility tests (same requests, same responses)
- React frontend integration test
- MCP test against sqlite MCP server

### API Endpoints to Match

```
GET  /api/health
POST /api/chat/query
GET  /api/chat/messages
POST /api/chat/clear
POST /api/chat/interrupt
GET  /api/sessions
GET  /api/sessions/{id}
POST /api/sessions/{id}/resume
GET  /api/config
PUT  /api/config
GET  /api/config/models
WS   /ws
```

---

## Phase 7: TUI and CLI

**Status**: Not started
**Estimated effort**: ~42K LOC Python → ~30K LOC Rust
**Dependencies**: Phases 5-6

### What to migrate

| Python Source | Rust Target | Description |
|---------------|-------------|-------------|
| `opendev/ui_textual/chat_app.py` | `opendev-tui/src/app.rs` | Main ratatui app |
| `opendev/ui_textual/widgets/` | `opendev-tui/src/widgets/` | All widgets |
| `opendev/ui_textual/controllers/` | `opendev-tui/src/controllers/` | All controllers |
| `opendev/ui_textual/formatters_internal/` | `opendev-tui/src/formatters/` | Output formatters |
| `opendev/ui_textual/callback_interface.py` | `opendev-tui/src/callback.rs` | UICallback trait |
| `opendev/repl/repl.py` | `opendev-repl/src/repl.rs` | REPL loop |
| `opendev/repl/query_processor.py` | `opendev-repl/src/query_processor.rs` | Query processing |
| `opendev/repl/tool_executor.py` | `opendev-repl/src/tool_executor.rs` | Tool execution |
| `opendev/repl/commands/` | `opendev-repl/src/commands/` | All commands |
| `opendev/cli/main.py` | `opendev-cli/src/main.rs` | CLI entry (clap) |
| `opendev/input/autocomplete/` | `opendev-tui/src/controllers/autocomplete.rs` | Autocomplete |

### Key decisions
- Textual (reactive CSS widgets) → ratatui (immediate-mode rendering) — different paradigm
- Rich markdown → termimad or pulldown-cmark with custom renderer
- prompt-toolkit → crossterm raw input handling
- Accept visual differences; prioritize feature parity

### Deliverables
- Three crates: `opendev-tui`, `opendev-repl`, `opendev-cli`
- The final `opendev` binary
- Ratatui snapshot tests
- Full manual QA of all TUI features
- End-to-end test: start binary, type query, verify response
