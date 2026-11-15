# Rust Architecture

## Workspace Layout

```
opendev-rust/
├── Cargo.toml                          # [workspace] root
├── crates/
│   ├── opendev-models/                 # Phase 1 — Data types
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── message.rs              # ChatMessage, ToolCall, Role, InputProvenance
│   │       ├── session.rs              # Session, SessionMetadata, Channel
│   │       ├── config.rs               # AppConfig, PermissionConfig, PlaybookConfig
│   │       ├── file_change.rs          # FileChange, FileChangeType
│   │       ├── operation.rs            # WriteResult, EditResult
│   │       ├── user.rs                 # User model
│   │       ├── api.rs                  # API request/response models
│   │       └── validator.rs            # Message validation rules
│   │
│   ├── opendev-config/                 # Phase 1 — Configuration
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── loader.rs               # Hierarchical config merge (project > user > env > defaults)
│   │       ├── models_dev.rs           # models.dev API cache (24h TTL)
│   │       └── paths.rs               # ~/.opendev/, session dirs, project encoding
│   │
│   ├── opendev-http/                   # Phase 2 — HTTP & Auth
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── client.rs              # reqwest wrapper with retry + interrupt (CancellationToken)
│   │       ├── auth.rs                # CredentialStore (~/.opendev/auth.json, mode 0600)
│   │       ├── rotation.rs            # API key rotation across providers
│   │       ├── adapters/
│   │       │   ├── mod.rs
│   │       │   ├── base.rs            # ProviderAdapter trait
│   │       │   ├── anthropic.rs       # Anthropic-specific (prompt caching, cache_control)
│   │       │   └── openai.rs          # OpenAI-specific (o1/o3 reasoning models)
│   │       └── models.rs             # HttpResult, RetryConfig
│   │
│   ├── opendev-context/                # Phase 3 — Context Engineering
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── compaction.rs          # Staged compaction (70%/80%/85%/90%/99% thresholds)
│   │       ├── token_monitor.rs       # Token counting via tiktoken-rs
│   │       ├── validated_list.rs      # ValidatedMessageList
│   │       ├── pair_validator.rs      # Message pair repair
│   │       └── context_picker.rs      # Dynamic context selection
│   │
│   ├── opendev-history/                # Phase 3 — Session Persistence
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── session_manager.rs     # JSON read/write to ~/.opendev/sessions/
│   │       ├── index.rs              # Fast metadata lookups via cached index
│   │       ├── listing.rs            # Session listing and search
│   │       ├── file_locks.rs         # Exclusive file locks (fd-lock)
│   │       ├── undo.rs              # Undo manager
│   │       └── snapshot.rs          # Session snapshots
│   │
│   ├── opendev-memory/                 # Phase 3 — ACE Memory
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── playbook.rs           # ACE playbook (sections, bullets, scoring)
│   │       ├── delta.rs              # Delta batch operations
│   │       ├── embeddings.rs         # Embedding cache + similarity search
│   │       ├── selector.rs           # Relevant bullet retrieval per turn
│   │       ├── reflector.rs          # Post-turn reflection
│   │       └── roles.rs             # Role-based memory access
│   │
│   ├── opendev-tools-core/             # Phase 4 — Tool Framework
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── traits.rs            # BaseTool trait, ToolResult, ToolContext
│   │       ├── registry.rs          # ToolRegistry: discovery + dispatch
│   │       ├── normalizer.rs        # Parameter normalization (relative→absolute paths)
│   │       ├── sanitizer.rs         # Result truncation, context bloat prevention
│   │       ├── policy.rs            # Tool policy (allow/deny patterns)
│   │       └── parallel.rs          # Parallel execution policy (read-only tools)
│   │
│   ├── opendev-tools-impl/             # Phase 4 — Tool Implementations
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── bash.rs              # Bash tool (tokio::process::Command)
│   │       ├── file_read.rs         # Read file tool
│   │       ├── file_write.rs        # Write file tool
│   │       ├── file_edit.rs         # Edit tool (string replacement)
│   │       ├── file_list.rs         # List files (glob patterns)
│   │       ├── file_search.rs       # Search file contents (ripgrep)
│   │       ├── git.rs              # Git operations (git2)
│   │       ├── web_fetch.rs        # URL fetch (reqwest + scraper)
│   │       ├── web_search.rs       # Web search (DuckDuckGo)
│   │       ├── web_screenshot.rs   # Web screenshot (headless_chrome)
│   │       ├── browser.rs          # Browser automation
│   │       ├── pdf.rs              # PDF extraction (lopdf)
│   │       ├── memory.rs           # Memory search/write tools
│   │       ├── session.rs          # Session management tools
│   │       ├── agents.rs           # Subagent spawn/output tools
│   │       ├── schedule.rs         # Scheduled task tool
│   │       ├── ask_user.rs         # Ask user tool (UI callback)
│   │       ├── patch.rs            # Patch tool
│   │       ├── notebook.rs         # Jupyter notebook tool
│   │       └── open_browser.rs     # Open browser tool
│   │
│   ├── opendev-tools-lsp/              # Phase 4 — LSP Integration
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── wrapper.rs           # LSP client wrapper
│   │       ├── handler.rs           # Request/response coordination
│   │       ├── protocol.rs          # LSP protocol types (lsp-types crate)
│   │       ├── utils.rs             # Range calculations, position normalization
│   │       ├── cache.rs             # Symbol cache
│   │       └── servers/             # 39 language server configurations
│   │           ├── mod.rs
│   │           ├── pyright.rs
│   │           ├── typescript.rs
│   │           ├── rust_analyzer.rs
│   │           ├── gopls.rs
│   │           ├── clangd.rs
│   │           └── ... (34 more)
│   │
│   ├── opendev-tools-symbol/           # Phase 4 — Symbol Operations
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── find_symbol.rs       # AST-based symbol search
│   │       ├── find_references.rs   # Find referencing symbols
│   │       ├── rename.rs           # Rename symbol
│   │       └── replace_body.rs     # Replace symbol body
│   │
│   ├── opendev-agents/                 # Phase 5 — Agent System
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── traits.rs           # BaseAgent trait
│   │       ├── main_agent.rs       # MainAgent (composition: HttpClient + LlmCaller + RunLoop)
│   │       ├── llm_calls.rs        # LLM call logic (thinking, critique, normal)
│   │       ├── react_loop.rs       # ReAct loop (reason → tool → execute → loop)
│   │       ├── prompts/
│   │       │   ├── mod.rs
│   │       │   ├── composer.rs     # PromptComposer (priority-ordered sections)
│   │       │   ├── loader.rs       # Template loading (include_str! + runtime)
│   │       │   ├── renderer.rs     # Variable substitution
│   │       │   └── templates/      # Embedded markdown templates
│   │       ├── subagents/
│   │       │   ├── mod.rs
│   │       │   ├── manager.rs      # SubagentManager (registry + execution)
│   │       │   ├── code_explorer.rs
│   │       │   ├── planner.rs
│   │       │   ├── ask_user.rs
│   │       │   ├── web_clone.rs
│   │       │   ├── web_generator.rs
│   │       │   ├── pr_reviewer.rs
│   │       │   └── security_reviewer.rs
│   │       └── response/
│   │           ├── mod.rs
│   │           └── cleaner.rs      # Response cleaning + normalization
│   │
│   ├── opendev-mcp/                    # Phase 6 — MCP Client
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── manager.rs          # MCPManager (connection pooling)
│   │       ├── config.rs           # MCP server configuration
│   │       ├── models.rs           # MCP protocol models
│   │       └── transport/
│   │           ├── mod.rs
│   │           ├── stdio.rs        # Stdio transport (tokio::process)
│   │           ├── sse.rs          # SSE transport (reqwest + eventsource)
│   │           └── http.rs         # HTTP transport
│   │
│   ├── opendev-web/                    # Phase 6 — Web Backend
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── server.rs           # Axum app creation, middleware, static files
│   │       ├── state.rs            # Shared state (Arc<RwLock<WebState>>)
│   │       ├── websocket.rs        # WebSocket manager (broadcast, handle_message)
│   │       ├── routes/
│   │       │   ├── mod.rs
│   │       │   ├── auth.rs         # Authentication routes
│   │       │   ├── chat.rs         # POST /api/chat/query, GET /api/chat/messages
│   │       │   ├── sessions.rs     # Session CRUD
│   │       │   ├── config.rs       # Configuration endpoints
│   │       │   └── mcp.rs          # MCP server management
│   │       └── callback.rs         # WebUICallback (broadcasts via WebSocket)
│   │
│   ├── opendev-channels/               # Phase 6 — Multi-Channel
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       └── router.rs          # Channel router (CLI, Web, Telegram, WhatsApp)
│   │
│   ├── opendev-tui/                    # Phase 7 — Terminal UI
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── app.rs              # Main ratatui app loop
│   │       ├── state.rs            # App state
│   │       ├── widgets/
│   │       │   ├── mod.rs
│   │       │   ├── conversation.rs # Conversation log (scrollable, markdown)
│   │       │   ├── input.rs        # Text input with autocomplete
│   │       │   ├── status_bar.rs   # Mode, model, cost display
│   │       │   ├── progress.rs     # Progress/spinner
│   │       │   ├── todo_panel.rs   # Todo list
│   │       │   └── welcome.rs      # Welcome screen
│   │       ├── controllers/
│   │       │   ├── mod.rs
│   │       │   ├── approval.rs     # Approval prompts
│   │       │   ├── ask_user.rs     # Ask-user prompts
│   │       │   ├── autocomplete.rs # Autocomplete popup
│   │       │   ├── commands.rs     # Slash command routing
│   │       │   └── model_picker.rs # Model selection
│   │       ├── formatters/
│   │       │   ├── mod.rs
│   │       │   ├── bash.rs         # Bash output formatting
│   │       │   ├── file.rs         # File operation formatting
│   │       │   ├── markdown.rs     # Markdown rendering (termimad)
│   │       │   └── tool.rs         # Generic tool result formatting
│   │       └── callback.rs         # TUICallback (implements UICallback trait)
│   │
│   ├── opendev-repl/                   # Phase 7 — REPL
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── repl.rs             # Main REPL loop
│   │       ├── query_processor.rs  # Query enhancement + execution
│   │       ├── tool_executor.rs    # Tool call execution with approval
│   │       ├── react_controller.rs # ReAct loop flow control
│   │       └── commands/
│   │           ├── mod.rs
│   │           ├── session.rs      # Session commands
│   │           ├── mode.rs         # Mode switching
│   │           ├── config.rs       # Config commands
│   │           ├── mcp.rs          # MCP commands
│   │           ├── help.rs         # Help display
│   │           └── tools.rs        # Tool management
│   │
│   ├── opendev-cli/                    # Phase 7 — Binary Entry Point
│   │   ├── Cargo.toml
│   │   └── src/
│   │       └── main.rs            # clap CLI, dispatch to TUI/Web/REPL
│   │
│   └── opendev-pyo3/                   # Cross-phase — PyO3 Bridge
│       ├── Cargo.toml
│       └── src/
│           ├── lib.rs             # #[pymodule] combining all sub-modules
│           ├── models.rs          # Python-facing model wrappers
│           ├── http.rs            # Python-facing HTTP client
│           ├── context.rs         # Python-facing context engineering
│           └── tools.rs           # Python-facing tool registry
```

## Crate Dependency Graph

```
opendev-cli
├── opendev-tui
│   ├── opendev-agents
│   ├── opendev-repl
│   └── opendev-tools-core
├── opendev-web
│   ├── opendev-agents
│   ├── opendev-mcp
│   └── opendev-channels
├── opendev-repl
│   ├── opendev-agents
│   └── opendev-tools-core
├── opendev-agents
│   ├── opendev-http
│   ├── opendev-tools-core
│   ├── opendev-tools-impl
│   ├── opendev-context
│   └── opendev-memory
├── opendev-tools-core
│   └── opendev-models
├── opendev-tools-impl
│   ├── opendev-tools-core
│   ├── opendev-tools-lsp
│   ├── opendev-tools-symbol
│   ├── opendev-http
│   └── opendev-history
├── opendev-context
│   ├── opendev-models
│   └── opendev-http
├── opendev-history
│   └── opendev-models
├── opendev-memory
│   ├── opendev-models
│   └── opendev-http
├── opendev-http
│   ├── opendev-models
│   └── opendev-config
├── opendev-config
│   └── opendev-models
└── opendev-models (leaf — no internal deps)
```

## Key Trait Definitions

### BaseTool (replaces Python ABC)
```rust
#[async_trait]
pub trait Tool: Send + Sync {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn schema(&self) -> serde_json::Value;
    async fn execute(&self, args: serde_json::Value, ctx: &ToolContext) -> Result<ToolResult>;
}
```

### UICallback (replaces Python UICallbackProtocol)
```rust
#[async_trait]
pub trait UICallback: Send + Sync {
    async fn on_thinking_start(&self);
    async fn on_thinking_complete(&self, content: &str);
    async fn on_assistant_message(&self, content: &str);
    async fn on_tool_call(&self, name: &str, args: &serde_json::Value, id: &str);
    async fn on_tool_result(&self, name: &str, result: &ToolResult, id: &str);
    async fn on_progress_start(&self, message: &str);
    async fn on_progress_update(&self, message: &str);
    async fn on_progress_complete(&self);
    async fn on_interrupt(&self);
    async fn on_cost_update(&self, total_cost_usd: f64);
    async fn on_bash_output_line(&self, line: &str);
    async fn on_nested_tool_call(&self, name: &str, args: &serde_json::Value, depth: u32);
    async fn on_nested_tool_result(&self, name: &str, result: &ToolResult, depth: u32);
    // ... additional methods
}
```

### BaseAgent (replaces Python mixin inheritance)
```rust
pub struct MainAgent {
    pub http_client: AgentHttpClient,      // was HttpClientMixin
    pub llm_caller: LlmCaller,            // was LlmCallsMixin
    pub tool_registry: Arc<ToolRegistry>,  // injected
    pub config: AgentConfig,               // from opendev-config
    pub ui_callback: Arc<dyn UICallback>,  // injected
    pub cancel_token: CancellationToken,   // was task_monitor.should_interrupt()
}
```

## Async Model

Python uses a sync/async hybrid (sync ReAct main thread + async MCP event loop in background thread). Rust unifies on tokio:

- ReAct loop runs as a tokio task
- Tool executions are `async fn`
- Blocking operations (bash subprocess, file I/O) use `tokio::task::spawn_blocking`
- MCP client uses native tokio async (no separate event loop needed)
- Interrupts use `tokio_util::sync::CancellationToken` with `tokio::select!`

```rust
// ReAct loop with interrupt support
loop {
    let response = tokio::select! {
        resp = self.llm_caller.call(&messages, &schemas) => resp?,
        _ = self.cancel_token.cancelled() => return Err(AgentError::Interrupted),
    };

    match response.tool_calls {
        Some(calls) => {
            let results = execute_tools_parallel(&calls, &self.tool_registry).await?;
            messages.extend(results);
        }
        None => break response,
    }
}
```

## Error Handling

- Library crates use `thiserror` for typed errors
- Application crate (`opendev-cli`) uses `anyhow` for ergonomic error propagation
- All errors implement `std::fmt::Display` for user-friendly messages

```rust
// In opendev-http
#[derive(Debug, thiserror::Error)]
pub enum HttpError {
    #[error("request failed after {retries} retries: {source}")]
    RetryExhausted { retries: u32, source: reqwest::Error },
    #[error("request interrupted by user")]
    Interrupted,
    #[error("authentication failed for provider {provider}")]
    AuthFailed { provider: String },
}
```

## Logging

Replace Python `logging` with the `tracing` crate:
- Structured logging with spans
- Per-crate log filtering via `RUST_LOG` env var
- JSON output for production, pretty output for development
