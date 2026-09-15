---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
workflowType: prd
classification:
  projectType: full-stack-developer-tool
  domain: developer-tooling
  complexity: high
  projectContext: brownfield
inputDocuments:
  - docs/architecture.md
  - docs/providers.md
  - docs/debug-subagent-spinner-cap.md
  - docs/subagent-execution-model.md
---

# Product Requirements Document — OpenDev Web UI Synchronization

**Author:** nghibui
**Date:** 2026-03-27

## Executive Summary

OpenDev is an open-source AI coding agent with two frontends: a terminal UI (TUI) built with ratatui and a Web UI built with React/Vite/Tailwind. The TUI has been the primary development focus and is feature-rich — subagent tree display, thinking block streaming, bash preview, todo/plan tracking, diff rendering, background task management, and comprehensive status monitoring. The Web UI has a solid foundation (WebSocket protocol with 35+ message types, multi-session support, chat, approval dialogs) but has fallen significantly behind the TUI in feature coverage.

**Goal:** Bring the Web UI to feature parity with the TUI through a shared frontend interface layer that prevents future drift between the two frontends.

**Differentiator:** A unified event protocol consumed by both TUI and Web UI, ensuring that agent capabilities are exposed identically regardless of frontend — changes to agent behavior propagate to both UIs through a single integration point.

**Target Users:** Developers who prefer a browser-based interface for running AI coding agents, with the same feedback richness as the terminal experience.

## Success Criteria

### User Success

- Developer runs a full agent session through the Web UI with the same feedback richness as the TUI
- Subagent execution is visible in real-time: tree structure, active tools, completion summaries
- Tool results are collapsible with smart previews (bash preview for >4 lines, diff rendering)
- Plan/todo progress is visible during multi-step execution

### Business Success

- Single codebase serves both TUI and Web UI users without feature drift
- Web UI becomes a viable alternative to the TUI, not a second-class citizen
- Reduced maintenance burden through shared event protocol

### Technical Success

- All WebSocket message types defined in `protocol.rs` are fully handled by the frontend
- Frontend Zustand store handles all 35+ event types with correct state management
- No new backend changes needed where existing protocol already covers the feature

### Measurable Outcomes

- 100% of TUI display features have Web UI equivalents
- All existing WebSocket message types rendered in the UI
- Zero "dead" protocol messages (defined but unhandled)
- Adding a new event type requires changes in exactly one Rust module

## Product Scope

### Phase 0 — Shared Frontend Interface Layer

Before any feature work, establish a unified event/state interface that both TUI and Web UI consume.

**Problem:** TUI receives events via `AgentEventCallback` trait converted to `AppEvent` in `tui_runner.rs`. Web UI receives events via `broadcast::Sender<WsBroadcast>` serialized as JSON over WebSocket. These are two separate translation layers from the same agent core — changes require updates in both places, and they drift.

**Solution:** A `FrontendEvent` enum in a shared Rust module (likely `opendev-models` or new `opendev-frontend` crate) that defines the canonical set of events both UIs consume. One adapter from agent internals to `FrontendEvent`. TUI consumes directly. Web UI serializes to JSON over WebSocket. TypeScript types derived from Rust definitions.

### Phase 1 — MVP Feature Set

| Priority | Feature | Traces to |
|----------|---------|-----------|
| P0 | Subagent tree display | FR13-FR18 |
| P0 | Thinking block streaming + toggle | FR6-FR7 |
| P0 | Tool result expand/collapse | FR8-FR9 |
| P0 | Bash preview (collapsed >4 lines) | FR10 |
| P1 | Status bar (model, tokens, cost, context %) | FR23-FR28 |
| P1 | Todo/plan panel | FR19-FR22 |
| P1 | Diff rendering | FR11 |
| P1 | Subagent completion summaries | FR17 |

### Phase 2 — Growth

- Background task panel and indicators (FR43-FR44)
- Keyboard shortcuts
- File change tracking display
- Command autocomplete (`/` commands, `@` file mentions)
- Toast notification improvements

### Phase 3 — Expansion

- Welcome screen / onboarding
- CodeWiki integration
- Trace/DAG visualization
- Bridge mode (TUI + Web UI co-existing on same session)
- Mobile-responsive layout

## User Journeys

### Journey 1: Developer Running an Agent Session

Alex, a backend developer, opens the Web UI to refactor a service. They type a query and hit send. The assistant starts streaming — the thinking block pulses as the agent reasons. A subagent spawns and a tree appears: "Explore: searching for patterns" with live tool count and elapsed timer. Active tool calls nest below — `Grep: "handler"`, `Read: src/api/routes.rs`. The subagent completes: "Done (12 tool uses, 2.1k tokens, 8s)". The main agent calls `Edit` — a diff renders inline with green/red highlighting. A bash command runs, the result collapses to first 2 + last 2 lines with "+47 lines" between. The todo panel tracks: "Refactor handler done", "Update tests in-progress", "Run clippy pending". The status bar shows token usage, session cost, and context fill.

**Capabilities revealed:** Subagent tree, thinking blocks, tool result collapse, bash preview, diff rendering, todo panel, status bar.

### Journey 2: Developer Debugging a Failure

A tool approval dialog appears for a destructive bash command — Alex reviews and denies it. The agent adapts. A subagent fails, showing failure status with error summary. Alex expands collapsed tool results to inspect output. They interrupt the agent, see "interrupted" feedback, then send a corrected instruction. The agent resumes with context intact.

**Capabilities revealed:** Approval dialogs, error states, tool result toggle, interrupt flow, failure indicators.

### Journey 3: Team Lead Monitoring Agent Work

Jordan opens the Web UI to check a running agent session. The status bar shows model, cost ($0.42), tokens (45k/200k), git branch. Background tasks show in a panel. The todo panel shows 70% completion. Jordan switches between sessions in the sidebar.

**Capabilities revealed:** Status bar, background tasks, session switching, read-only monitoring, cost visibility.

### Journey 4: Developer Configuring the Agent

Sam switches from Claude to Ollama, adjusts temperature, sets autonomy to Semi-Auto. They configure an MCP server and see it connect. They toggle thinking level to High. Changes reflect immediately in the status bar.

**Capabilities revealed:** Settings panel, model config, MCP management, autonomy/thinking controls, real-time status updates.

### Journey Requirements Summary

| Journey | Key Capabilities |
|---------|-----------------|
| Agent Session | Subagent tree, thinking stream, bash preview, diff render, todo panel, status bar |
| Debugging | Approval dialog, error states, tool toggle, interrupt, failure display |
| Monitoring | Status bar, background tasks, session switching, cost/token display |
| Configuration | Settings panel, model config, MCP management, autonomy controls |

## Domain-Specific Requirements

### Technical Constraints

- **Real-time streaming:** WebSocket handles high-frequency message bursts (rapid tool calls, subagent events, thinking chunks) without dropping or reordering
- **State consistency:** Zustand store maintains consistent state across concurrent subagent events — multiple subagents emit tool calls simultaneously
- **Protocol completeness:** All 35+ `WsMessageType` variants in `protocol.rs` handled — unhandled message types are silent failures
- **Frontend-first:** No backend changes for features already covered by the existing WebSocket protocol

### Integration Requirements

- Web UI consumes the same `broadcast::Sender<WsBroadcast>` infrastructure
- Settings persist to the same config files the TUI reads
- Sessions are interchangeable between TUI and Web UI (same history format)

### Risk Mitigations

- **Event ordering:** Buffer and sequence subagent events by ID to prevent race conditions
- **Memory leaks:** Prune completed subagent state from Zustand store after threshold (TUI caps at 100 completed tools)
- **Reconnection:** On WebSocket reconnect, re-fetch session state via REST to avoid stale UI

## Developer Tool — Web UI Specific Requirements

### Architecture

**Frontend-only where possible.** The WebSocket protocol already defines `subagent_start`, `subagent_complete`, `nested_tool_call`, `nested_tool_result`, `thinking_block`, `progress`, `message_chunk/start/complete`. The Zustand store (~785 lines) handles many events but is missing handlers for subagent tree state, todo tracking, and status bar data.

**Backend gaps (minimal):** Verify subagent events are wired to broadcast. Verify progress events carry todo/plan data. Status bar data (tokens, cost, context %) may need a periodic WebSocket push or REST endpoint.

### New Components

- `SubagentTree` — receives subagent events, renders nested tool calls with status/stats
- `TodoPanel` — tracks plan items with pending/in-progress/completed status
- `StatusBar` — model, tokens, cost, context %, branch, autonomy, MCP status
- Enhanced `ToolCallMessage` — bash preview logic, diff rendering
- Enhanced `ThinkingBlock` — streaming animation, expand/collapse toggle

### State Management Additions

Zustand store extensions:
- `subagents: Map<string, SubagentState>` — active subagent tracking
- `todos: TodoItem[]` — plan/todo items with status
- `statusBar: { tokens, cost, contextPct, model, branch, autonomy }` — status data
- `backgroundTasks: BackgroundTask[]` — background agent tracking

## Functional Requirements

### Shared Frontend Interface

- **FR1:** System provides a unified event protocol consumed by both TUI and Web UI from a single source
- **FR2:** System translates agent-internal events into frontend events through one adapter layer
- **FR3:** System defines a canonical state shape that both frontends render from
- **FR4:** System enables TypeScript type generation from Rust event definitions

### Conversation Display

- **FR5:** User can view streaming conversation with role-differentiated styling (user, assistant, system)
- **FR6:** User can view real-time thinking/reasoning blocks during agent processing
- **FR7:** User can toggle thinking block visibility (expand/collapse)
- **FR8:** User can view tool call results with name, arguments summary, and output
- **FR9:** User can toggle tool result visibility (expand/collapse)
- **FR10:** User can view collapsed bash results as preview (first 2 + last 2 lines for >4 line results)
- **FR11:** User can view diff-formatted output for edit tool results with add/remove highlighting
- **FR12:** User can view markdown-rendered assistant messages (code blocks, bold, italic, links)

### Subagent Display

- **FR13:** User can view active subagents in a tree showing name, task, and status
- **FR14:** User can view active tool calls within each subagent with tool name, arguments, and elapsed time
- **FR15:** User can view completed tool calls within each subagent with success/failure status
- **FR16:** User can view subagent statistics (tool count, token usage, elapsed time)
- **FR17:** User can view a persistent completion summary after subagent finishes
- **FR18:** User can view nested tool calls from subagent execution in hierarchical form

### Plan & Todo Tracking

- **FR19:** User can view a todo/plan panel with task items showing status (pending, in-progress, completed)
- **FR20:** User can view plan progress as completed vs total count
- **FR21:** User can toggle todo panel visibility
- **FR22:** User can view the currently active task description

### Status & Monitoring

- **FR23:** User can view current model name and provider
- **FR24:** User can view token usage (used vs limit) and context fill percentage
- **FR25:** User can view session cost in USD
- **FR26:** User can view current git branch
- **FR27:** User can view current autonomy level
- **FR28:** User can view MCP server connection status

### Agent Control

- **FR29:** User can send messages to the agent
- **FR30:** User can interrupt a running agent
- **FR31:** User can respond to tool approval requests (approve/deny)
- **FR32:** User can respond to ask-user prompts (free text or option selection)
- **FR33:** User can respond to plan approval requests (approve/reject/revise)
- **FR34:** User can toggle between Normal and Plan operation modes

### Session Management

- **FR35:** User can create, switch between, and delete agent sessions
- **FR36:** User can view session history with message count and workspace metadata
- **FR37:** User can resume a previous session with full conversation history

### Configuration

- **FR38:** User can select model provider and model
- **FR39:** User can adjust temperature and max token settings
- **FR40:** User can set autonomy level (Manual/Semi-Auto/Auto)
- **FR41:** User can set thinking level (Off/Low/Medium/High)
- **FR42:** User can manage MCP server configurations (add/edit/delete/connect/disconnect)

### Background Tasks

- **FR43:** User can view background task indicators showing active background agents
- **FR44:** User can view background task completion results

## Non-Functional Requirements

### Performance

- **NFR1:** WebSocket event delivery < 50ms latency for real-time streaming feel
- **NFR2:** UI renders message chunks, subagent tree updates, and thinking blocks without visible jank
- **NFR3:** Zustand store handles rapid concurrent events (multiple subagents) without dropped or reordered updates
- **NFR4:** Session history (up to 500 messages) renders within 3 seconds on initial load
- **NFR5:** Collapse/expand toggles respond within 100ms

### Reliability

- **NFR6:** WebSocket reconnection restores full UI state via REST re-fetch without user intervention
- **NFR7:** Frontend gracefully handles unknown/malformed WebSocket message types (log and ignore)
- **NFR8:** Extended sessions (hours) do not leak memory — completed subagent state and old tool results pruned

### Maintainability

- **NFR9:** Adding a new event type requires changes in exactly one Rust module, with both TUI and Web UI consuming downstream
- **NFR10:** TypeScript types for frontend events derivable from Rust definitions — no manual type drift
- **NFR11:** Each Web UI feature is an independent React component with isolated Zustand slice

### Integration

- **NFR12:** Web UI reads and writes the same configuration files as the TUI
- **NFR13:** Sessions use the same history format — a TUI session is resumable in Web UI and vice versa

## Key Files Reference

### Frontend (React)
- `web-ui/src/stores/chat.ts` — Zustand state management (785 lines)
- `web-ui/src/api/websocket.ts` — WebSocket client with auto-reconnect
- `web-ui/src/api/client.ts` — REST API client
- `web-ui/src/components/Chat/ChatInterface.tsx` — Main UI orchestrator
- `web-ui/src/types/` — TypeScript interfaces (needs expansion)

### Backend (Rust)
- `crates/opendev-web/src/websocket.rs` — WebSocket message handling
- `crates/opendev-web/src/protocol.rs` — 35+ message type definitions
- `crates/opendev-web/src/state/mod.rs` — AppState, approval resolution
- `crates/opendev-web/src/routes/chat.rs` — Query dispatch

### TUI Reference (behavior specification)
- `crates/opendev-tui/src/widgets/conversation/mod.rs` — Conversation rendering
- `crates/opendev-tui/src/widgets/nested_tool/mod.rs` — Subagent tree display
- `crates/opendev-tui/src/widgets/todo_panel.rs` — Todo panel
- `crates/opendev-tui/src/widgets/status_bar.rs` — Status bar
- `crates/opendev-tui/src/widgets/spinner.rs` — Animated thinking indicators

### Shared Models
- `crates/opendev-models/src/` — ChatMessage, ToolCall, Role types
- `crates/opendev-runtime/src/event_bus/` — RuntimeEvent, EventBus
- `crates/opendev-agents/src/traits.rs` — AgentEventCallback trait
- `crates/opendev-tools-impl/src/agents/events.rs` — SubagentEvent enum
