# TUI Migration -- Textual to Ratatui

## Overview

The TUI layer was rewritten from Python's Textual framework (event-driven, CSS-styled, retained widget tree) to Rust's ratatui (immediate-mode, constraint-based, stateless render functions). The Python implementation comprised ~32K LOC across 90+ files in `opendev/ui_textual/`; the Rust replacement is ~11K LOC across 35 files in `crates/opendev-tui/src/`. This 3:1 compression is the result of eliminating Textual's widget lifecycle overhead, collapsing CSS-driven layout into inline constraint expressions, and replacing the callback-based agent bridge with a typed `AppEvent` enum delivered over `tokio::mpsc` channels.

Within the overall architecture, `opendev-tui` is the terminal frontend. It consumes events produced by the agent runtime (`opendev-agents`, `opendev-runtime`) and renders them to the terminal via `crossterm` + `ratatui`. The binary entrypoint (`opendev-cli`) wires the TUI to the runtime by sharing an `mpsc::UnboundedSender<AppEvent>` that the agent loop uses to push events into the UI.

## Python Architecture

### Textual Framework Patterns

Textual is a Python TUI framework built on Rich. It uses a **retained-mode** widget tree: widgets are instantiated once in a `compose()` method, mounted into a DOM, styled by TCSS (Textual CSS), and updated via reactive attributes and message passing. Key patterns:

- **`App.compose()`** -- Declarative widget tree construction. `SWECLIChatApp.compose()` yields `Header`, `Container`, `ConversationLog`, `Rule`, `TodoPanel`, `ChatTextArea`, `ProgressBar`, `DebugPanel`, and `StatusBar`. Once composed, these widgets persist for the lifetime of the app.
- **TCSS Styling** -- Layout and color are defined in `styles/chat.tcss` (250 lines). Selectors like `#conversation { height: 1fr; padding: 1 2; }` and pseudo-classes like `TextArea:focus { border-left: thick $accent; }` control appearance. Textual resolves these at mount time and when classes are toggled.
- **Widget Lifecycle** -- Each widget has `on_mount()`, `on_unmount()`, `on_resize()` hooks. `ConversationLog.on_mount()` wires up sub-managers (SpinnerManager, MessageRenderer, ToolRenderer, ScrollController). `on_unmount()` tears down timers and animation loops.
- **Message/Event Bubbling** -- Textual uses a message-based event system. `ChatTextArea.Submitted` is a `Message` subclass that bubbles up from the input widget. Key events propagate through `_on_key()` where controllers intercept them based on active mode (approval, model picker, wizard, etc.).
- **Thread Safety** -- Agent callbacks arrive on background threads. `call_from_thread()` and `call_from_thread_nonblocking()` marshal updates onto the Textual event loop. The `BridgeUICallback` forwards all agent events to both the TUI callback and an optional WebSocket callback.

### Class Hierarchy / Module Structure

```
chat_app.py              SWECLIChatApp(App)       -- Root application
  callback_interface.py    UICallbackProtocol       -- ~30 method protocol
  bridge_callback.py       BridgeUICallback         -- Dual TUI+Web forwarding
  runner.py                TextualRunner            -- Agent lifecycle orchestrator
widgets/
  conversation_log.py      ConversationLog(RichLog) -- Retained line buffer, block registry
  chat_text_area.py        ChatTextArea(TextArea)   -- Input with autocomplete, paste handling
  status_bar.py            StatusBar(Static)        -- Rich Text rendering
  welcome_panel.py         AnimatedWelcomePanel     -- ASCII art animation
  todo_panel.py            TodoPanel                -- Plan progress display
  conversation/
    block_registry.py      BlockRegistry            -- Track content blocks for resize reflow
    message_renderer.py    DefaultMessageRenderer   -- Role-prefixed message rendering
    scroll_controller.py   DefaultScrollController  -- User scroll state tracking
    spinner_manager.py     DefaultSpinnerManager    -- Inline spinner animation
    tool_renderer/         DefaultToolRenderer      -- Tool call/result/nested rendering
controllers/
  approval_prompt_controller.py   ApprovalPromptController
  ask_user_prompt_controller.py   AskUserPromptController
  plan_approval_controller.py     PlanApprovalController
  autocomplete_popup_controller.py AutocompletePopupController
  command_router.py               CommandRouter
  message_controller.py           MessageController
  model_picker_controller.py      ModelPickerController
  agent_creator_controller.py     AgentCreatorController
  skill_creator_controller.py     SkillCreatorController
  spinner_controller.py           SpinnerController
managers/
  approval_manager.py     ChatApprovalManager
  console_buffer_manager.py ConsoleBufferManager
  console_output_manager.py ConsoleOutputManager
  display_ledger.py       DisplayLedger
  frecency_manager.py     FrecencyManager
  interrupt_manager.py    InterruptManager
  message_history.py      MessageHistory
  spinner_service/        SpinnerService (multi-file)
  tool_summary_manager.py ToolSummaryManager
```

### SOLID Analysis

- **S (Single Responsibility)**: Generally respected. Each controller owns one UI flow (approval, model picking, etc.). However, `ConversationLog` is a God Object -- 927 lines delegating to 4 sub-managers, managing block registries, protected lines, resize re-rendering, and 40+ public methods.
- **O (Open/Closed)**: `UICallbackProtocol` is extensible (add new `on_*` methods) but every implementation must be updated. `ForwardingUICallback` mitigates this.
- **L (Liskov)**: `ConversationLog(RichLog)` respects the RichLog contract but overrides `write()` in a way that changes the block-tracking semantics.
- **I (Interface Segregation)**: `UICallbackProtocol` bundles ~30 methods. Most implementations only care about a subset.
- **D (Dependency Inversion)**: Controllers depend on the concrete `SWECLIChatApp` class via direct `self.app` references, not abstractions.

## Rust Architecture

### Ratatui Immediate-Mode Patterns

Ratatui is a Rust TUI library using **immediate-mode rendering**: the entire screen is rebuilt from state on every frame. There is no retained widget tree, no mount/unmount lifecycle, and no CSS. Key patterns:

- **`App::render()`** -- Called once per frame inside `terminal.draw(|frame| self.render(frame))`. Constructs `ConversationWidget`, `InputWidget`, `TodoPanelWidget`, `NestedToolWidget`, `StatusBarWidget` as ephemeral structs, passes `&AppState` slices, and calls `frame.render_widget()`. Widgets are created and destroyed every frame.
- **Constraint Layout** -- Layout is computed inline with `layout::Layout::default().direction(Vertical).constraints([Min(5), Length(todo_height), Length(subagent_height), Length(input_lines), Length(2)])`. No external stylesheet. Layout adapts dynamically based on state (e.g., `todo_height` is 0 when no todos exist).
- **Stateless Widgets** -- Each widget implements `impl Widget for WidgetType` with a single `fn render(self, area: Rect, buf: &mut Buffer)` method. Widgets hold `&'a` references to state slices, not owned data. No `on_mount`, no timers, no internal state.
- **`AppEvent` Enum Dispatch** -- All events (terminal, agent, tool, thinking, UI) are variants of a single `AppEvent` enum. The `handle_event()` method pattern-matches exhaustively. No event bubbling, no message propagation.
- **Async Channel Bridge** -- The agent runtime sends events via `mpsc::UnboundedSender<AppEvent>`. The event loop (`EventHandler`) merges crossterm terminal events with agent events and tick timers using `tokio::select!`. No thread marshaling needed -- everything runs on the tokio runtime.

### Struct Hierarchy / Module Structure

```
app.rs                   App, AppState, DisplayMessage, ToolExecution
event.rs                 AppEvent (37 variants), EventHandler
widgets/
  conversation.rs        ConversationWidget<'a>   -- Immediate-mode message renderer
  input.rs               InputWidget<'a>          -- Cursor rendering, multiline
  status_bar.rs          StatusBarWidget<'a>      -- Single-line status
  spinner.rs             SpinnerState             -- Frame counter, char lookup
  thinking.rs            ThinkingBlock, ThinkingPhase
  progress.rs            TaskProgress
  nested_tool.rs         NestedToolWidget, SubagentDisplayState
  todo_panel.rs          TodoPanelWidget, TodoDisplayItem
  tool_display.rs        Tool result rendering helpers
  welcome_panel.rs       WelcomePanelWidget, WelcomePanelState
controllers/
  approval.rs            ApprovalController
  ask_user.rs            AskUserController
  autocomplete_popup.rs  AutocompletePopupController, CompletionItem
  mcp_command.rs         McpCommandController, McpServerInfo
  message.rs             MessageController
  model_picker.rs        ModelPickerController, ModelOption
  plan_approval.rs       PlanApprovalController, PlanDecision
  agent_creator.rs       AgentCreatorController, AgentSpec
  skill_creator.rs       SkillCreatorController, SkillSpec
  slash_commands.rs       BUILTIN_COMMANDS, SlashCommand
  spinner.rs             SpinnerController
managers/
  background_tasks.rs    BackgroundTaskManager, TaskStatus
  display_ledger.rs      DisplayLedger
  frecency.rs            FrecencyTracker, FrecencyEntry
  interrupt.rs           InterruptManager
  message_history.rs     MessageHistory
  spinner.rs             SpinnerService
autocomplete/
  completers.rs          Slash command + file completers
  file_finder.rs         Filesystem walker
  formatters.rs          Completion display formatting
  strategies.rs          Matching strategies (prefix, fuzzy)
formatters/
  base.rs, bash_formatter.rs, directory_formatter.rs, display.rs,
  factory.rs, file_formatter.rs, generic_formatter.rs, markdown.rs,
  style_tokens.rs, tool_colors.rs
```

### SOLID Analysis

- **S (Single Responsibility)**: `AppState` is a single struct holding all mutable state (~30 fields), but this is idiomatic for immediate-mode UIs. Each widget has exactly one job: turn a state slice into `Buffer` writes. Controllers are thin state machines.
- **O (Open/Closed)**: Adding a new event means adding an `AppEvent` variant and a match arm -- the compiler enforces exhaustiveness.
- **L (Liskov)**: The `Widget` trait contract is simple (`fn render(self, Rect, &mut Buffer)`) and all implementations respect it.
- **I (Interface Segregation)**: No fat callback protocols. Each widget takes only the state slices it needs via builder methods.
- **D (Dependency Inversion)**: Widgets depend on `&AppState` fields (data), not on the `App` struct itself. The agent runtime depends only on `mpsc::UnboundedSender<AppEvent>`, not on the TUI.

## Migration Mapping

| Python Class/Module | Rust Struct/Trait | Pattern Change | Notes |
|---|---|---|---|
| `SWECLIChatApp(App)` | `App` + `AppState` | Retained tree -> immediate-mode loop | State split from behavior; `AppState` is pure data |
| `SWECLIChatApp.compose()` | `App::render()` | One-time composition -> per-frame construction | Widgets are ephemeral `'a`-lifetime structs |
| `styles/chat.tcss` (250 LOC) | Inline `layout::Constraint` + `style_tokens.rs` | External CSS -> programmatic constraints | Colors in `style_tokens.rs` constants |
| `ConversationLog(RichLog)` | `ConversationWidget<'a>` | Retained line buffer with block registry -> stateless render from `Vec<DisplayMessage>` | Eliminates resize reflow, block tracking, protected lines |
| `ChatTextArea(TextArea)` | `InputWidget<'a>` + key handling in `App::handle_key()` | Widget-internal key dispatch -> centralized match | No more mode-checking cascade in `_on_key()` |
| `StatusBar(Static)` | `StatusBarWidget<'a>` | Reactive Rich Text -> immediate Span construction | Same visual output, no `reactive` machinery |
| `UICallbackProtocol` (30 methods) | `AppEvent` enum (37 variants) | Trait-based callbacks -> typed enum dispatch | Compiler-enforced exhaustive matching |
| `BridgeUICallback` | `mpsc::UnboundedSender<AppEvent>` | Dual-forwarding callback object -> channel clone | Web UI gets its own channel subscriber |
| `TextualRunner` | `opendev-cli` main + `App::with_message_channel()` | Orchestrator class -> channel wiring at startup | No more `call_from_thread` marshaling |
| `BlockRegistry` + `ContentBlock` | Not needed | Resize reflow bookkeeping eliminated | Immediate-mode re-renders everything each frame |
| `DefaultScrollController` | `AppState::scroll_offset` + `user_scrolled` | Object with timer callbacks -> two fields | Scroll logic in `handle_key()` match arms |
| `DefaultSpinnerManager` | `SpinnerState` + `SpinnerController` | Timer-driven animation -> tick-driven frame counter | `Tick` event advances frame every 80ms |
| `DefaultMessageRenderer` | `ConversationWidget::build_lines()` | Method calls on retained widget -> pure function | `MarkdownRenderer::render()` for assistant messages |
| `DefaultToolRenderer` (800+ LOC) | `ConversationWidget` tool rendering + `ToolExecution` | Stateful renderer with index tracking -> stateless render from tool state | No `adjust_indices()` needed |
| `InterruptManager` | `InterruptManager` | Same pattern, simpler | No controller registry; direct `AtomicBool` flag |
| `MessageHistory` | `MessageHistory` | Same pattern | Vec-based up/down navigation |
| `DisplayLedger` | `DisplayLedger` | Same pattern | Deduplication for message display |
| `FrecencyManager` | `FrecencyTracker` | Same pattern | Score-based suggestion ranking |
| `SpinnerService` (multi-file) | `SpinnerService` (single file) | 4-file module -> single struct | Animation state simplified |
| `ApprovalPromptController` | `ApprovalController` | Same pattern, thinner | No `adjust_indices()`, no line manipulation |
| `AskUserPromptController` | `AskUserController` | Same pattern | Inline rendering instead of log mutation |
| `ModelPickerController` | `ModelPickerController` | Same pattern | Selection state in controller, rendered inline |
| `AgentCreatorController` | `AgentCreatorController` | Same pattern | Wizard state machine |
| `SkillCreatorController` | `SkillCreatorController` | Same pattern | Wizard state machine |
| `CommandRouter` | `slash_commands.rs` | Class -> module-level functions | `BUILTIN_COMMANDS` static array |
| `AutocompletePopupController` | `AutocompletePopupController` + `AutocompleteEngine` | Widget mutation -> state + inline render | Popup rendered in `App::render_autocomplete()` |
| `ConsoleBufferManager` | Not needed | Console output bridging eliminated | Agent output arrives as `AppEvent` variants |
| `ToolSummaryManager` | Not needed | Tool summary tracking eliminated | Summary computed inline from `DisplayToolCall` |
| `SpinnerController` | `SpinnerController` | Same core logic | Braille frames, tick-driven |

## Paradigm Shift Analysis

### Event-Driven (Textual) vs Immediate-Mode (ratatui)

**Textual**: Widgets are long-lived objects that receive events via method calls (`on_mount`, `on_resize`, `on_key`, `_on_key`). State changes trigger reactive updates. The framework decides when to repaint dirty regions. The `ConversationLog` maintains a persistent line buffer (`self.lines`) that is mutated in-place -- adding messages appends strips, removing approval prompts deletes line ranges, and resize triggers a coordinated re-render that walks the block registry.

**Ratatui**: The application owns all state in `AppState`. Every frame, the `render()` method constructs fresh widget structs, passes them state references, and they write directly to a `Buffer`. There is no dirty tracking -- the entire screen is diffed by the backend. The conversation is rebuilt from `Vec<DisplayMessage>` every frame. This eliminates the entire class of bugs around stale line indices, orphaned spinners, and resize reflow glitches that plagued the Python implementation.

**Trade-off**: Immediate mode is simpler and more predictable, but it means complex animations (like the block-aware resize reflow in Python) are either unnecessary (the terminal handles reflow) or must be implemented differently (e.g., the welcome panel fade-out uses a `WelcomePanelState` struct with frame counters instead of CSS animation).

### CSS Theming vs Constraint-Based Layout

**Textual**: The 250-line `chat.tcss` file defines layout (`height: 1fr`, `max-height: 15`, `padding: 1 2`), colors (`$accent`, `$background`, `$text-muted`), pseudo-classes (`:focus`, `:hover`), and conditional visibility (`display: none` / `display: block`). Widget identity is CSS ID-based (`#conversation`, `#input`). Adding a new section means adding CSS rules plus ensuring the cascade does not break existing layout.

**Ratatui**: Layout is a single `Layout::default().constraints([...]).split(area)` call in `render()`. Constraints are computed dynamically from state:
```rust
layout::Constraint::Length({
    let input_lines = self.state.input_buffer.matches('\n').count() + 1;
    (input_lines as u16 + 1).min(8)
})
```
Colors are constants in `style_tokens.rs`. Conditional visibility is a Rust `if` statement (`if has_todos { ... }`). There is no cascade, no specificity, and no selector conflicts.

**Trade-off**: CSS provides a declarative separation of concerns and hot-reloadability during development. Rust's inline approach is more explicit and refactorable but requires recompilation for visual changes.

### Widget Lifecycle Differences

**Textual**: Widgets go through `compose -> mount -> (resize/key/message events) -> unmount`. They own internal state, set up timers (`set_timer(0.05, callback)`), and manage sub-components. `ConversationLog` has a `_resize_timer`, `_block_registry`, `_spinner_manager`, `_scroll_controller`, and `_tool_renderer` -- all initialized in `__init__` and cleaned up in `on_unmount()`.

**Ratatui**: Widgets have no lifecycle. They are created in `render()`, call `fn render(self, area, buf)`, and are dropped. All persistent state lives in `AppState`. The spinner does not need a timer -- the `EventHandler` emits `AppEvent::Tick` every 80ms, and `handle_tick()` advances `state.spinner.tick()`.

### Event Bubbling vs AppEvent Enum Dispatch

**Textual**: Events bubble from child widgets to parent containers. `ChatTextArea._on_key()` is 400+ lines of mode-checking (`if approval_mode ... if ask_user_mode ... if model_picker_active ... if agent_wizard_active ...`) because the input widget intercepts keys for every possible UI state. The `Submitted(Message)` dataclass bubbles up to the app, where `on_chat_text_area_submitted()` handles it.

**Ratatui**: All events flow through a single `AppEvent` enum and are dispatched in `handle_event()` via exhaustive `match`. Key handling in `handle_key()` checks controller states in a flat priority order. There is no bubbling, no `event.stop()` / `event.prevent_default()`, and no risk of a child widget swallowing an event meant for a parent.

### TUI-AgentRuntime Bridge

**Textual**: The bridge is a `UICallbackProtocol` with ~30 methods (`on_thinking_start`, `on_tool_call`, `on_assistant_message`, etc.). `BridgeUICallback` implements this protocol and forwards to both the TUI callback and an optional web callback. Agent code runs on background threads and must use `call_from_thread()` to marshal updates onto the Textual event loop. The `TextualRunner` class (in `runner.py`) orchestrates the agent lifecycle, history hydration, console bridging, and MCP auto-connect.

**Ratatui**: The bridge is an `mpsc::UnboundedSender<AppEvent>`. The agent runtime sends typed events (`AppEvent::ToolStarted { tool_id, tool_name }`, `AppEvent::AgentChunk(text)`, etc.) directly into the channel. The `EventHandler` merges these with terminal events using `tokio::select!`. No thread marshaling is needed because both the agent and the TUI run on the same tokio runtime. The web UI (in `opendev-web`) subscribes to the same event stream via a broadcast channel.

## Key Design Decisions

1. **Centralized `AppState` over distributed widget state.** Every piece of mutable UI state lives in one struct. This makes state transitions explicit, serializable (for debugging), and impossible to get out of sync between widgets.

2. **`AppEvent` enum over callback protocol.** The 37-variant enum replaces the 30-method `UICallbackProtocol`. The compiler enforces that every event is handled (exhaustive match). Adding a new event type is a compile error until all handlers are updated.

3. **Ephemeral widgets over retained widgets.** Widgets hold `&'a` references and are dropped every frame. This eliminates the entire class of lifetime management bugs: stale references, orphaned timers, and mount/unmount ordering issues.

4. **Inline layout over CSS.** Layout constraints are computed from state in the same `render()` function that constructs widgets. This makes it trivial to conditionally show/hide panels (a Rust `if` vs toggling CSS `display` classes) and dynamically size areas (input height grows with newlines).

5. **Channel bridge over callback bridge.** `mpsc::UnboundedSender<AppEvent>` is `Clone + Send`, so any number of agent threads or tasks can push events without coordination. The old `BridgeUICallback` had to forward to two targets and wrap web errors in try/except; the new design uses separate channel subscribers.

6. **Tick-driven animation over timer callbacks.** The `EventHandler` emits `Tick` events at 80ms intervals. The `handle_tick()` method advances all animations (spinner frames, elapsed time counters, welcome panel fade). This replaces Textual's `set_timer()` per-widget timers and eliminates timer lifecycle management.

7. **No block registry or resize reflow.** The Python `ConversationLog` maintained a `BlockRegistry` to track content blocks and re-render wrappable content on resize. The Rust implementation rebuilds the entire conversation from `Vec<DisplayMessage>` every frame, so resize handling is automatic. This eliminated ~200 lines of fragile index-tracking code.

## Code Examples

### Spinner: Python (Textual) vs Rust (Ratatui)

**Python** -- Timer-driven, widget-internal state, lifecycle hooks:

```python
# controllers/spinner_controller.py
class SpinnerController:
    def __init__(self, app, tips_manager, todo_handler=None):
        self.app = app
        self.tips_manager = tips_manager
        self._active = False
        self._message = "Thinking..."

    def start(self, message=None):
        if self._active:
            return
        conversation = getattr(self.app, "conversation", None)
        if conversation is None:
            return
        self._message = message or self._pick_thinking_verb()
        self._active = True
        conversation.start_spinner(Text(self._message, style=GREY))

# widgets/conversation/spinner_manager.py
class DefaultSpinnerManager:
    def start_spinner(self, message):
        self._spinner_timer = self.widget.set_timer(0.08, self._tick, pause=False)
        self._spinner_line = len(self.widget.lines)
        self.widget.write(...)  # Mutate retained line buffer

    def _tick(self):
        # Replace strip at self._spinner_line with next animation frame
        self.widget.lines[self._spinner_line] = new_strip
        self.widget.refresh_line(self._spinner_line)
```

**Rust** -- Tick-driven, state in `AppState`, stateless render:

```rust
// widgets/spinner.rs
pub struct SpinnerState {
    frame: usize,
}
impl SpinnerState {
    pub fn tick(&mut self) { self.frame = (self.frame + 1) % SPINNER_FRAMES.len(); }
    pub fn current(&self) -> char { SPINNER_FRAMES[self.frame] }
}

// app.rs -- handle_tick advances spinner
fn handle_tick(&mut self) { self.state.spinner.tick(); }

// widgets/conversation.rs -- render reads current frame
let spinner_char = self.spinner_char; // Passed from AppState
// ... renders spinner_char inline in the conversation output
```

### Widget Composition: Python vs Rust

**Python** -- Declarative tree, CSS layout:

```python
class SWECLIChatApp(App):
    CSS_PATH = "styles/chat.tcss"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            yield ConversationLog(id="conversation")
            yield Rule(line_style="solid")
            yield TodoPanel(id="todo-panel")
            with Vertical(id="input-container"):
                yield Static("...", id="input-label")
                yield ChatTextArea(id="input")
            yield StatusBar(id="status-bar")
```

**Rust** -- Imperative layout, constraint-based:

```rust
fn render(&self, frame: &mut ratatui::Frame) {
    let chunks = layout::Layout::default()
        .direction(layout::Direction::Vertical)
        .constraints([
            layout::Constraint::Min(5),              // conversation
            layout::Constraint::Length(todo_height),  // todo panel
            layout::Constraint::Length(input_height), // input
            layout::Constraint::Length(2),            // status bar
        ])
        .split(frame.area());

    let conversation = ConversationWidget::new(&self.state.messages, self.state.scroll_offset)
        .terminal_width(area.width)
        .spinner_char(self.state.spinner.current());
    frame.render_widget(conversation, chunks[0]);

    let input = InputWidget::new(&self.state.input_buffer, self.state.input_cursor, ...);
    frame.render_widget(input, chunks[2]);

    let status = StatusBarWidget::new(&self.state.model, ...);
    frame.render_widget(status, chunks[3]);
}
```

## Remaining Gaps

1. **Mouse support.** The Python implementation disabled mouse (`ENABLE_MOUSE = False`) due to escape sequence issues. The Rust implementation filters mouse events in `EventHandler` (`CrosstermEvent::Mouse(_) => continue`). Mouse scroll support was recently added for the conversation widget but full mouse interaction (click, selection) is not yet implemented.

2. **Console output bridging.** The Python `ConsoleBufferManager` captured stdout/stderr from subprocesses and injected them into the conversation log. The Rust implementation handles this via `AppEvent::ToolOutput` events from the tool executor but does not capture arbitrary stdout from the process.

3. **Debug panel.** The Python `DebugPanel` widget (toggled with Ctrl+D) for live execution tracing does not have a Rust equivalent yet.

4. **Resize reflow for long output.** The Python `BlockRegistry` could re-wrap markdown content on terminal resize. The Rust implementation re-renders from state every frame, which handles layout changes but does not re-wrap previously-rendered content blocks with width-dependent formatting.

## References

- Python source: `/Users/nghibui/codes/opendev-py/opendev/ui_textual/`
- Rust source: `/Users/nghibui/codes/opendev/crates/opendev-tui/src/`
- Textual framework: https://textual.textualize.io/
- Ratatui framework: https://ratatui.rs/
- crossterm terminal backend: https://docs.rs/crossterm/
- Related migration docs: `/Users/nghibui/codes/opendev/migration_docs/`
