# Migration Strategy

## Goals

1. **Performance**: Eliminate Python GIL bottleneck, achieve native-speed token counting, file I/O, JSON serialization, and HTTP request handling
2. **Single binary distribution**: Ship a single `opendev` binary with no Python runtime dependency
3. **Memory safety**: Leverage Rust's ownership model to eliminate runtime crashes from null references, data races, and memory leaks
4. **Type safety**: Replace runtime Pydantic validation with compile-time type checking
5. **Startup time**: Sub-100ms cold start vs current ~2-3s Python import chain

## Principles

### Incremental Migration via PyO3
Every Rust crate exposes a `#[pymodule]` so Python can import and use Rust types during the transition. This means:
- The system is always functional — never broken between phases
- Each phase can be tested against the existing Python test suite
- Rollback is trivial: revert to Python implementation by removing the PyO3 import

### Bottom-Up Dependency Order
Migration follows the dependency graph from leaves to root:
```
Models (leaf) → Config → HTTP → Context → Tools → Agents → Web/MCP → TUI/CLI (root)
```
Each phase only depends on previously migrated crates, never on Python code.

### API Contract Preservation
- The React frontend must work unchanged against the Rust web backend
- Session JSON files must be readable by both Python and Rust during transition
- CLI flags and behavior must remain identical

### Composition Over Inheritance
Python's mixin inheritance pattern (e.g., `MainAgent = HttpClientMixin + LlmCallsMixin + RunLoopMixin + BaseAgent`) is replaced with Rust's composition pattern: structs hold trait objects as fields.

## Current Architecture (Python)

```
CLI Entry (cli/main.py)
    │
    ├── TUI (ui_textual/) ─── 32.5K LOC, Textual framework
    ├── Web (web/) ─────────── 5.5K LOC, FastAPI + WebSocket
    │
    ├── REPL (repl/) ───────── 9K LOC, command processing
    │
    ├── Agents (core/agents/) ── 8.7K LOC, ReAct loop + subagents
    │   ├── Prompts (prompts/) ── modular markdown composition
    │   └── Components (api/) ─── HTTP client, auth, adapters
    │
    ├── Context Engineering (core/context_engineering/) ── 47K LOC
    │   ├── Tools (tools/) ─── 40+ implementations, registry, LSP, symbols
    │   ├── MCP (mcp/) ────── Model Context Protocol client
    │   ├── Memory (memory/) ── ACE playbook, embeddings
    │   ├── History (history/) ── session persistence, undo
    │   └── Compaction ──────── staged context compression
    │
    ├── Runtime (core/runtime/) ── mode manager, approval, cost tracking
    ├── Auth (core/auth/) ──── credential store
    └── Models (models/) ───── Pydantic data models
```

## Target Architecture (Rust)

```
opendev-cli (binary crate, clap)
    │
    ├── opendev-tui ──────── ratatui + crossterm
    ├── opendev-web ──────── axum + WebSocket + tower-http
    │
    ├── opendev-repl ─────── command processing
    │
    ├── opendev-agents ───── ReAct loop + subagents
    │   └── uses: opendev-http, opendev-tools-core, opendev-context
    │
    ├── opendev-tools-core ── BaseTool trait, registry
    ├── opendev-tools-impl ── 40+ tool implementations
    ├── opendev-tools-lsp ─── LSP client + 39 language servers
    ├── opendev-tools-symbol ─ AST-based symbol operations
    │
    ├── opendev-mcp ──────── MCP client (stdio/SSE/HTTP)
    ├── opendev-channels ─── multi-channel router
    │
    ├── opendev-context ──── compaction, validated message list
    ├── opendev-history ──── session persistence, file locks
    ├── opendev-memory ───── ACE playbook, embeddings
    │
    ├── opendev-http ─────── reqwest client, auth rotation
    ├── opendev-config ───── hierarchical config loading
    └── opendev-models ───── serde data models (foundation)
```

## Risk Assessment

### High Risk
- **Textual → ratatui**: Completely different paradigm (reactive CSS widgets vs immediate-mode rendering). Accept visual differences; prioritize feature parity over pixel-perfect match.
- **crawl4ai replacement**: No direct Rust equivalent for AI-powered web extraction. Mitigation: Use `headless_chrome` + `scraper` crate, implement extraction natively.

### Medium Risk
- **MCP client**: Rust MCP ecosystem is young. Mitigation: Implement minimal client against the MCP spec directly using reqwest (HTTP/SSE) and tokio::process (stdio).
- **PyO3 bridge complexity**: Bidirectional Python↔Rust calls during transition add overhead. Mitigation: Keep bridge thin, remove bridge code as each phase completes.

### Low Risk
- **tiktoken → tiktoken-rs**: Direct Rust port exists and is maintained.
- **httpx → reqwest**: Well-established, feature-complete HTTP client.
- **FastAPI → axum**: Both are modern, async-first frameworks with similar patterns.
- **Pydantic → serde**: serde is the gold standard for Rust serialization.
- **gitpython → git2**: Mature libgit2 bindings for Rust.

## Success Criteria

Phase is complete when:
1. All Rust tests pass (unit + integration)
2. Existing Python tests pass through PyO3 bridge (during transition)
3. No regression in functionality
4. Performance is equal to or better than Python

Full migration is complete when:
1. `opendev-cli` binary runs all features without Python runtime
2. React frontend works unchanged against Rust web backend
3. All existing session files load correctly
4. All 40+ tools work correctly
5. MCP and LSP integrations function
