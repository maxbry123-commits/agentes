# Testing and Verification Strategy

## Testing Principles

1. **Every Rust crate has its own unit tests** (`#[cfg(test)]` modules)
2. **Integration tests validate cross-crate behavior** (`tests/` directory in workspace root)
3. **PyO3 bridge tests verify Python↔Rust interop** during the transition period
4. **Compatibility tests ensure no regression** by loading real data files
5. **End-to-end tests run the full system** after each phase

## Phase 1: Models and Config

### Unit Tests
```rust
// Round-trip serialization for every model
#[test]
fn test_chat_message_roundtrip() {
    let msg = ChatMessage { role: Role::User, content: "hello".into(), .. };
    let json = serde_json::to_string(&msg).unwrap();
    let parsed: ChatMessage = serde_json::from_str(&json).unwrap();
    assert_eq!(msg, parsed);
}

// Enum string values match Python
#[test]
fn test_role_serialization() {
    assert_eq!(serde_json::to_string(&Role::User).unwrap(), "\"user\"");
    assert_eq!(serde_json::to_string(&Role::Assistant).unwrap(), "\"assistant\"");
}
```

### Compatibility Tests
- Load every JSON file in `~/.opendev/sessions/` with both Python and Rust
- Assert identical field values after parsing
- Test edge cases: empty sessions, sessions with nested tool calls, sessions with thinking traces

### PyO3 Tests
```python
# Python test calling Rust
from opendev_rust.models import ChatMessage, Role
msg = ChatMessage(role=Role.USER, content="hello")
assert msg.role == Role.USER
json_str = msg.to_json()
msg2 = ChatMessage.from_json(json_str)
assert msg2.content == "hello"
```

### Verification Command
```bash
cd opendev-rust && cargo test -p opendev-models -p opendev-config
# Then from Python:
cd .. && uv run pytest tests/test_session_model.py tests/test_message_validator.py tests/test_validated_message_list.py
```

---

## Phase 2: HTTP Client and Auth

### Unit Tests
- Retry logic: mock server returns 429, verify exponential backoff and eventual success
- Retry exhaustion: mock server always fails, verify error after MAX_RETRIES
- Interrupt: start request, cancel via CancellationToken, verify Interrupted error
- Auth rotation: configure multiple keys, verify rotation on 401
- Credential store: write/read auth.json, verify file permissions (0600)

### Mock Server Tests (wiremock)
```rust
#[tokio::test]
async fn test_retry_on_429() {
    let mock_server = MockServer::start().await;
    Mock::given(method("POST"))
        .respond_with(ResponseTemplate::new(429)
            .set_body_string("rate limited")
            .insert_header("Retry-After", "1"))
        .up_to_n_times(2)
        .mount(&mock_server).await;
    Mock::given(method("POST"))
        .respond_with(ResponseTemplate::new(200).set_body_string("ok"))
        .mount(&mock_server).await;

    let client = AgentHttpClient::new(mock_server.uri());
    let result = client.post("/v1/chat/completions", body).await.unwrap();
    assert_eq!(result.status, 200);
}
```

### Integration Test (gated)
```rust
#[tokio::test]
#[ignore] // Run with: cargo test -- --ignored
async fn test_live_openai_call() {
    let api_key = std::env::var("OPENAI_API_KEY").expect("OPENAI_API_KEY required");
    let client = AgentHttpClient::new_with_key("https://api.openai.com", &api_key);
    let response = client.post("/v1/chat/completions", sample_request()).await.unwrap();
    assert_eq!(response.status, 200);
}
```

### Verification Command
```bash
cargo test -p opendev-http
cargo test -p opendev-http -- --ignored  # live API test (needs OPENAI_API_KEY)
```

---

## Phase 3: Context Engineering

### Compaction Tests
- Create message list at 70% token usage → verify masking stage triggers
- Create message list at 90% token usage → verify summarization triggers
- Verify token count matches `tiktoken-rs` output exactly
- Compare compaction output with Python implementation on same input

### History Tests
- Load/save session to temp directory
- Concurrent file lock test (10 threads, same file)
- Undo: make change, undo, verify original state
- Session index: create 100 sessions, verify index lookup speed

### Memory Tests
- Playbook: create bullets, serialize, deserialize, verify scores
- Embedding similarity: compute embeddings for known phrases, verify cosine similarity ordering
- Selector: given a query and playbook, verify correct bullets are selected

### Verification Command
```bash
cargo test -p opendev-context -p opendev-history -p opendev-memory
# Python compatibility:
uv run pytest tests/test_context_compaction.py tests/test_staged_compaction.py tests/test_file_locks.py
```

---

## Phase 4: Tool System

### Tool Core Tests
- Register 5 tools, dispatch by name, verify correct handler called
- Parameter normalization: relative path → absolute path
- Result sanitization: 100KB result → truncated to limit
- Policy: tool "bash" denied by pattern, verify rejection

### Tool Implementation Tests

**Bash tool**:
```rust
#[tokio::test]
async fn test_bash_echo() {
    let tool = BashTool::new();
    let result = tool.execute(json!({"command": "echo hello"}), &ctx).await.unwrap();
    assert!(result.output.contains("hello"));
}

#[tokio::test]
async fn test_bash_timeout() {
    let tool = BashTool::new();
    let result = tool.execute(json!({"command": "sleep 30", "timeout": 1000}), &ctx).await;
    assert!(result.is_err()); // timeout
}
```

**File tools**: Use `tempfile::TempDir` for all file operation tests
**Git tool**: Use `git2::Repository::init` to create test repos
**Web fetch**: Use wiremock for mock HTTP responses

### LSP Tests
- Serialize/deserialize LSP protocol messages (initialize, textDocument/definition, etc.)
- Test language server config generation for Python (Pyright) and TypeScript
- Integration test: start Pyright, send definition request, verify response

### Verification Command
```bash
cargo test -p opendev-tools-core -p opendev-tools-impl -p opendev-tools-lsp -p opendev-tools-symbol
# Python compatibility:
uv run pytest tests/test_tool_registry.py tests/test_tool_system_overhaul.py tests/test_lsp_symbol.py
```

---

## Phase 5: Agent Layer

### Prompt Composition Tests
Use `insta` crate for snapshot testing:
```rust
#[test]
fn test_system_prompt_composition() {
    let composer = PromptComposer::new();
    composer.register("security-policy", 100, include_str!("templates/security-policy.md"));
    composer.register("tool-descriptions", 200, include_str!("templates/tool-descriptions.md"));
    let prompt = composer.compose(&context);
    insta::assert_snapshot!(prompt);
}
```

### ReAct Loop Tests
Mock LLM to return predefined tool calls:
```rust
#[tokio::test]
async fn test_react_loop_completes() {
    let mock_llm = MockLlmCaller::new()
        .on_call(0, response_with_tool_call("read_file", json!({"path": "test.rs"})))
        .on_call(1, response_with_text("File contents look good."));
    let agent = MainAgent::new(mock_llm, mock_tools, mock_callback);
    let result = agent.run("Read test.rs").await.unwrap();
    assert!(result.contains("File contents look good"));
}

#[tokio::test]
async fn test_react_loop_max_iterations() {
    let mock_llm = MockLlmCaller::new()
        .always_return(response_with_tool_call("read_file", json!({"path": "x"})));
    let agent = MainAgent::new(mock_llm, mock_tools, mock_callback);
    let result = agent.run("Loop forever").await;
    assert!(matches!(result, Err(AgentError::MaxIterationsReached)));
}
```

### Verification Command
```bash
cargo test -p opendev-agents
cargo test -p opendev-agents -- --ignored  # live API test
```

---

## Phase 6: Web Backend and MCP

### API Compatibility Tests
For every endpoint, send the same HTTP request to both Python (FastAPI) and Rust (axum), assert identical JSON responses:
```rust
#[tokio::test]
async fn test_health_endpoint() {
    let app = create_test_app().await;
    let response = app.oneshot(Request::get("/api/health").body(Body::empty()).unwrap()).await.unwrap();
    assert_eq!(response.status(), 200);
}

#[tokio::test]
async fn test_chat_query() {
    let app = create_test_app().await;
    let response = app.oneshot(
        Request::post("/api/chat/query")
            .header("content-type", "application/json")
            .body(Body::from(json!({"query": "hello"}).to_string()))
            .unwrap()
    ).await.unwrap();
    assert_eq!(response.status(), 202); // Accepted
}
```

### WebSocket Tests
```rust
#[tokio::test]
async fn test_websocket_connection() {
    let server = start_test_server().await;
    let (ws, _) = tokio_tungstenite::connect_async(format!("ws://{}/ws", server.addr())).await.unwrap();
    let (mut write, mut read) = ws.split();
    write.send(Message::Text(json!({"type": "ping"}).to_string())).await.unwrap();
    let msg = read.next().await.unwrap().unwrap();
    let parsed: Value = serde_json::from_str(&msg.to_text().unwrap()).unwrap();
    assert_eq!(parsed["type"], "pong");
}
```

### React Frontend Test
```bash
# Start Rust backend
cd opendev-rust && cargo run -p opendev-web &
# Start React frontend in dev mode
cd web-ui && npm run dev &
# Run Playwright tests against the frontend
npx playwright test
```

### MCP Tests
```rust
#[tokio::test]
async fn test_mcp_stdio_transport() {
    let server = McpServer::start_stdio("uvx", &["mcp-server-sqlite", "--db", ":memory:"]).await.unwrap();
    let tools = server.list_tools().await.unwrap();
    assert!(!tools.is_empty());
}
```

### Verification Command
```bash
cargo test -p opendev-web -p opendev-mcp -p opendev-channels
```

---

## Phase 7: TUI and CLI

### Ratatui Snapshot Tests
```rust
#[test]
fn test_conversation_widget_render() {
    let mut terminal = TestTerminal::new(80, 24);
    let widget = ConversationWidget::new(vec![
        Message::user("Hello"),
        Message::assistant("Hi there!"),
    ]);
    terminal.draw(|f| f.render_widget(widget, f.area())).unwrap();
    insta::assert_snapshot!(terminal.buffer_to_string());
}
```

### CLI Parsing Tests
```rust
#[test]
fn test_cli_default_tui() {
    let args = Cli::parse_from(["opendev"]);
    assert!(args.command.is_none()); // default = TUI mode
}

#[test]
fn test_cli_prompt_mode() {
    let args = Cli::parse_from(["opendev", "-p", "hello world"]);
    assert_eq!(args.prompt, Some("hello world".to_string()));
}

#[test]
fn test_cli_web_ui() {
    let args = Cli::parse_from(["opendev", "run", "ui"]);
    assert!(matches!(args.command, Some(Command::Run(RunCommand::Ui))));
}
```

### Manual QA Checklist
After all automated tests pass, manually verify:
- [ ] Start TUI: `cargo run -p opendev-cli`
- [ ] Type a query, verify LLM response streams correctly
- [ ] Verify tool calls display (bash, file read, etc.)
- [ ] Verify autocomplete works (/ commands, @ files)
- [ ] Verify Shift+Tab switches modes
- [ ] Verify Escape interrupts
- [ ] Verify `/mode` command
- [ ] Verify session resume (`--continue`)
- [ ] Start web UI: `cargo run -p opendev-cli -- run ui`
- [ ] Verify React frontend loads and works
- [ ] Verify WebSocket real-time updates

### Verification Command
```bash
cargo test -p opendev-tui -p opendev-repl -p opendev-cli
# Full binary test:
cargo run -p opendev-cli -- -p "what is 2+2"
```

---

## Continuous Integration

### Per-PR Checks
```yaml
# .github/workflows/rust.yml
- cargo fmt --all -- --check
- cargo clippy --all-targets -- -D warnings
- cargo test --all
```

### Nightly Integration
```yaml
# Run live API tests
- cargo test --all -- --ignored
# Run Python compatibility tests
- uv run pytest tests/
# Build release binary
- cargo build --release -p opendev-cli
```

## Coverage

Use `cargo-llvm-cov` for code coverage:
```bash
cargo install cargo-llvm-cov
cargo llvm-cov --all --html
# Open target/llvm-cov/html/index.html
```

Target: >80% coverage for all crates except `opendev-tui` (widget rendering is hard to test; target >60%).
