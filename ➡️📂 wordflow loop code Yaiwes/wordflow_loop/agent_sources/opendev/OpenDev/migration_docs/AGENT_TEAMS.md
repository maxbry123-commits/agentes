# Agent Team Structure

## Overview

The migration is parallelized across 5 teams with 13 total agents. Each agent is a Claude Code subagent with a specific focus area, working in its own git worktree to avoid conflicts.

## Team A: Foundation (Phases 1-2)

Starts immediately. No dependencies on other teams.

### Agent A1: Models Agent
**Focus**: All Pydantic data models → serde structs + PyO3 wrappers
**Files to read**:
- `opendev/models/message.py`
- `opendev/models/session.py`
- `opendev/models/config.py`
- `opendev/models/file_change.py`
- `opendev/models/operation.py`
- `opendev/models/user.py`
- `opendev/models/api.py`
- `opendev/models/message_validator.py`
**Creates**:
- `opendev-rust/crates/opendev-models/` (full crate)
- `opendev-rust/crates/opendev-config/` (full crate)
**Tests**:
- Serialize/deserialize round-trips for every model
- Load existing `~/.opendev/sessions/*.json` files
- PyO3 interop tests

### Agent A2: HTTP Agent
**Focus**: HTTP client, auth, provider adapters → reqwest
**Files to read**:
- `opendev/core/agents/components/api/http_client.py`
- `opendev/core/agents/components/api/auth_rotation.py`
- `opendev/core/agents/components/api/base_adapter.py`
- `opendev/core/agents/components/api/anthropic_adapter.py`
- `opendev/core/agents/components/api/openai_responses_adapter.py`
- `opendev/core/auth/credentials.py`
- `opendev/core/auth/user_store.py`
**Creates**:
- `opendev-rust/crates/opendev-http/` (full crate)
**Tests**:
- Mock server tests (wiremock)
- Retry logic tests
- Auth rotation tests
- Credential file security tests (permissions)

---

## Team B: Context Engineering (Phase 3)

Starts after Agent A1 delivers `opendev-models`. Can run in parallel with Agent A2.

### Agent B1: History Agent
**Focus**: Session persistence, file locks, undo, snapshots
**Files to read**:
- `opendev/core/context_engineering/history/session_manager/index.py`
- `opendev/core/context_engineering/history/session_manager/listing.py`
- `opendev/core/context_engineering/history/file_locks.py`
- `opendev/core/context_engineering/history/snapshot.py`
**Creates**:
- `opendev-rust/crates/opendev-history/` (full crate)
**Tests**:
- Load/save real session JSON files
- File locking stress tests (multi-threaded)
- Undo/redo round-trips

### Agent B2: Compaction Agent
**Focus**: Token monitoring, staged compaction, message validation
**Files to read**:
- `opendev/core/context_engineering/compaction.py`
- `opendev/core/context_engineering/validated_message_list.py`
- `opendev/core/context_engineering/message_pair_validator.py`
- `opendev/core/context_engineering/context_picker/`
**Creates**:
- `opendev-rust/crates/opendev-context/` (full crate)
**Tests**:
- Token counting accuracy (compare with tiktoken Python)
- Compaction at various thresholds
- Message pair validation edge cases

### Agent B3: Memory Agent
**Focus**: ACE playbook, embeddings, semantic search
**Files to read**:
- `opendev/core/context_engineering/memory/playbook.py`
- `opendev/core/context_engineering/memory/delta.py`
- `opendev/core/context_engineering/memory/embeddings.py`
- `opendev/core/context_engineering/memory/selector.py`
- `opendev/core/context_engineering/memory/reflection/reflector.py`
- `opendev/core/context_engineering/memory/roles.py`
**Creates**:
- `opendev-rust/crates/opendev-memory/` (full crate)
**Tests**:
- Playbook serialize/deserialize round-trips
- Embedding similarity search accuracy
- Delta batch operations

---

## Team C: Tools (Phase 4)

Starts after Teams A and B complete. This is the largest team (4 agents) because tools are independent and can be developed in parallel.

### Agent C1: Tool Core Agent
**Focus**: Tool framework — trait, registry, normalization, sanitization, policy
**Files to read**:
- `opendev/core/context_engineering/tools/implementations/base.py` (or equivalent)
- `opendev/core/context_engineering/tools/registry.py`
- `opendev/core/context_engineering/tools/param_normalizer.py`
- `opendev/core/context_engineering/tools/result_sanitizer.py`
- `opendev/core/context_engineering/tools/tool_policy.py`
- `opendev/core/context_engineering/tools/parallel_policy.py`
**Creates**:
- `opendev-rust/crates/opendev-tools-core/` (full crate)
**Tests**:
- Tool registration and dispatch
- Parameter normalization (paths, types)
- Result truncation at various sizes
- Policy evaluation (allow/deny patterns)

### Agent C2: File & System Tools Agent
**Focus**: bash, file read/write/edit/list/search, git, patch
**Files to read**:
- `opendev/core/context_engineering/tools/implementations/bash_tool/`
- `opendev/core/context_engineering/tools/implementations/edit_tool/`
- `opendev/core/context_engineering/tools/implementations/git_tool.py`
- `opendev/core/context_engineering/tools/implementations/patch_tool.py`
- `opendev/core/context_engineering/tools/handlers/process_handlers.py`
- `opendev/core/context_engineering/tools/handlers/search_tools_handler.py`
**Creates**:
- Bash, file ops, git, patch tools in `opendev-tools-impl`
**Tests**:
- Bash tool with real subprocess (temp dir)
- File operations on temp files
- Git operations on temp repo
- Edit tool string replacement edge cases

### Agent C3: Web & External Tools Agent
**Focus**: web_fetch, web_search, web_screenshot, browser, pdf, memory tools, session tools
**Files to read**:
- `opendev/core/context_engineering/tools/implementations/web_fetch_tool.py`
- `opendev/core/context_engineering/tools/implementations/web_search_tool.py`
- `opendev/core/context_engineering/tools/implementations/web_screenshot_tool.py`
- `opendev/core/context_engineering/tools/implementations/browser_tool.py`
- `opendev/core/context_engineering/tools/implementations/pdf_tool.py`
- `opendev/core/context_engineering/tools/implementations/memory_tools.py`
- `opendev/core/context_engineering/tools/implementations/session_tools.py`
- `opendev/core/context_engineering/tools/implementations/ask_user_tool.py`
- `opendev/core/context_engineering/tools/implementations/schedule_tool.py`
- `opendev/core/context_engineering/tools/implementations/open_browser_tool.py`
**Creates**:
- Web and external tools in `opendev-tools-impl`
**Tests**:
- Web fetch with mock HTTP server
- PDF extraction from test files
- Memory tool operations

### Agent C4: LSP & Symbol Agent
**Focus**: All 39 language server configs, LSP protocol handler, symbol operations
**Files to read**:
- `opendev/core/context_engineering/tools/lsp/wrapper.py`
- `opendev/core/context_engineering/tools/lsp/ls_handler.py`
- `opendev/core/context_engineering/tools/lsp/ls_request.py`
- `opendev/core/context_engineering/tools/lsp/ls_types.py`
- `opendev/core/context_engineering/tools/lsp/language_servers/` (all 39 files)
- `opendev/core/context_engineering/tools/symbol_tools/` (all 4 files)
**Creates**:
- `opendev-rust/crates/opendev-tools-lsp/` (full crate)
- `opendev-rust/crates/opendev-tools-symbol/` (full crate)
**Tests**:
- LSP protocol message serialization
- Symbol search on test projects (Python, TypeScript)
- Language server config validation

---

## Team D: Orchestration (Phases 5-6)

Starts after Teams A-C complete (needs HTTP, tools, context).

### Agent D1: Agent Core
**Focus**: BaseAgent trait, MainAgent, LLM calls, ReAct loop, prompt composition, subagents
**Files to read**:
- `opendev/core/base/abstract/base_agent.py`
- `opendev/core/base/interfaces/agent_interface.py`
- `opendev/core/agents/main_agent/` (all files)
- `opendev/core/agents/subagents/` (all files)
- `opendev/core/agents/prompts/` (all files)
- `opendev/core/agents/components/response/cleaner.py`
**Creates**:
- `opendev-rust/crates/opendev-agents/` (full crate)
**Tests**:
- Prompt composition snapshot tests
- Mock LLM response tests for ReAct iterations
- Subagent spawn and result collection
- Integration test with live API (gated)

### Agent D2: Web & MCP Agent
**Focus**: Axum server, WebSocket, REST routes, MCP client, channel router
**Files to read**:
- `opendev/web/server.py`
- `opendev/web/websocket.py`
- `opendev/web/state.py`
- `opendev/web/routes/` (all files)
- `opendev/core/context_engineering/mcp/` (all files)
- `opendev/core/channels/router.py`
**Creates**:
- `opendev-rust/crates/opendev-web/` (full crate)
- `opendev-rust/crates/opendev-mcp/` (full crate)
- `opendev-rust/crates/opendev-channels/` (full crate)
**Tests**:
- API endpoint compatibility tests (same requests/responses as FastAPI)
- WebSocket message flow tests
- MCP client test against sqlite server
- React frontend integration test

---

## Team E: UI (Phase 7)

Starts after Teams D completes. This is the final phase.

### Agent E1: TUI Agent
**Focus**: ratatui app, widgets, controllers, formatters, callbacks
**Files to read**:
- `opendev/ui_textual/chat_app.py`
- `opendev/ui_textual/runner.py`
- `opendev/ui_textual/callback_interface.py`
- `opendev/ui_textual/widgets/` (all files)
- `opendev/ui_textual/controllers/` (all files)
- `opendev/ui_textual/formatters_internal/` (all files)
- `opendev/ui_textual/managers/` (all files)
**Creates**:
- `opendev-rust/crates/opendev-tui/` (full crate)
**Tests**:
- Ratatui buffer snapshot tests
- Keybinding tests
- Widget rendering tests

### Agent E2: REPL & CLI Agent
**Focus**: REPL loop, command processing, clap CLI entry point
**Files to read**:
- `opendev/repl/repl.py`
- `opendev/repl/query_processor.py`
- `opendev/repl/tool_executor.py`
- `opendev/repl/react_executor/`
- `opendev/repl/commands/` (all files)
- `opendev/cli/main.py`
- `opendev/input/` (all files)
**Creates**:
- `opendev-rust/crates/opendev-repl/` (full crate)
- `opendev-rust/crates/opendev-cli/` (binary crate)
**Tests**:
- Command parsing tests (clap)
- REPL command dispatch tests
- End-to-end: run binary, send query, verify output

---

## Parallelism Timeline

```
Phase 1 (Foundation):
  [Week 1-2] ██ Agent A1 (Models)
  [Week 1-3] ███ Agent A2 (HTTP)

Phase 3 (Context):
  [Week 2-4] ███ Agent B1 (History)      ← starts after A1
  [Week 2-4] ███ Agent B2 (Compaction)   ← starts after A1
  [Week 2-4] ███ Agent B3 (Memory)       ← starts after A1

Phase 4 (Tools):
  [Week 4-6] ███ Agent C1 (Tool Core)    ← starts after A1
  [Week 5-7] ███ Agent C2 (File Tools)   ← starts after C1
  [Week 5-7] ███ Agent C3 (Web Tools)    ← starts after C1
  [Week 5-8] ████ Agent C4 (LSP)         ← starts after C1

Phase 5-6 (Orchestration):
  [Week 7-10] ████ Agent D1 (Agents)     ← starts after C1-C3
  [Week 7-10] ████ Agent D2 (Web/MCP)    ← starts after D1 scaffolding

Phase 7 (UI):
  [Week 10-14] █████ Agent E1 (TUI)      ← starts after D1
  [Week 10-13] ████ Agent E2 (REPL/CLI)  ← starts after D1
```

## Agent Spawn Commands

Each agent should be spawned with `isolation: "worktree"` and detailed prompts referencing the specific files listed above. Example:

```
Agent A1: "Migrate all Pydantic models from opendev/models/ to Rust serde structs in opendev-rust/crates/opendev-models/. Read each Python source file, create equivalent Rust structs with serde derive macros. Ensure JSON serialization is compatible with existing session files. Add PyO3 #[pyclass] annotations. Write comprehensive tests."
```

## Coordination Rules

1. **No cross-agent file edits**: Each agent owns its crate(s) exclusively
2. **Shared workspace Cargo.toml**: Agent A1 creates the workspace root; other agents add their crate to [workspace.members]
3. **Interface contracts**: Teams define trait signatures before implementation (e.g., Team C waits for Team A's model types before writing tool code)
4. **Integration checkpoints**: After each phase completes, run the full test suite before starting the next phase
