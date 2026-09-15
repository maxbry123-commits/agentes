# Tool Implementation Guide

## Overview

The tool system is the execution backbone of OpenDev's ReAct loop. It translates LLM-generated tool calls into concrete actions — reading files, running commands, spawning subagents, and more. The system spans two crates (`opendev-tools-core` for the framework and `opendev-tools-impl` for the 27 tool implementations) and provides parameter normalization, result sanitization, group-based access control, and parallel execution scheduling.

In the dependency graph, `opendev-tools-core` is a leaf crate with no OpenDev dependencies. `opendev-tools-impl` depends on `opendev-tools-core` and implements every tool against the `BaseTool` trait. The agent crate (`opendev-agents`) owns the `ToolRegistry` instance, registers tools at startup, and calls `registry.execute()` inside the ReAct loop.

## Python Architecture

### Module Structure

```
opendev/core/context_engineering/tools/
  registry.py             # ToolRegistry — central dispatch hub
  param_normalizer.py     # normalize_params() — key/path/whitespace fixing
  result_sanitizer.py     # ToolResultSanitizer — truncation before context entry
  parallel_policy.py      # ParallelPolicy — read/write partitioning
  tool_policy.py          # ToolPolicy — profile/group permission system
  context.py              # ToolExecutionContext dataclass
  file_time.py            # FileTimeTracker for stale-read detection
  implementations/
    base.py               # BaseTool ABC
    bash_tool/            # Bash execution (directory)
    edit_tool/            # File editing (directory)
    file_ops.py           # FileOps (read, list, search)
    write_tool.py         # WriteTool
    agents_tool.py        # AgentsTool (subagent listing)
    patch_tool.py         # PatchTool (unified diff)
    pdf_tool.py           # PDFTool
    task_complete_tool.py # TaskCompleteTool
    present_plan_tool.py  # PresentPlanTool
    ...26 files total
  handlers/
    file_handlers.py      # FileToolHandler (delegates to file_ops, write, edit)
    process_handlers.py   # ProcessToolHandler (delegates to bash)
    web_handlers.py       # WebToolHandler
    ...19 files total
```

### Key Abstractions

- **`BaseTool` (ABC):** Abstract base with `name` (property), `description` (property), `execute(**kwargs)` (method). Concrete tools inherit and implement all three.
- **Handler classes:** Intermediate layer between registry and tool implementations. `FileToolHandler` wraps `FileOps`, `WriteTool`, and `EditTool` behind a single interface. Handlers receive raw argument dicts and a `ToolExecutionContext`.
- **`ToolRegistry`:** God-class that owns all handlers and tools, holds a `_handlers: dict[str, Callable]` mapping tool names to callables, and provides `execute_tool()` as the single entry point. It also manages MCP tool discovery, hook integration, subagent sessions, and batch execution.
- **`ToolExecutionContext`:** Dataclass carrying `mode_manager`, `approval_manager`, `undo_manager`, `task_monitor`, `session_manager`, `ui_callback`, `is_subagent`, and `file_time_tracker`.

### Design Patterns

- **Facade:** `ToolRegistry` presents a single `execute_tool()` method, hiding the routing to 40+ handlers.
- **Strategy:** `ToolResultSanitizer` uses `TruncationRule` with pluggable strategies (head, tail, head_tail).
- **Chain of Responsibility:** `execute_tool()` chains PreToolUse hooks -> normalization -> dispatch -> PostToolUse hooks.
- **Template Method:** Handlers follow a common pattern (extract args, validate, delegate to implementation, format result) but there is no formal base handler class.

### SOLID Analysis

| Principle | Adherence | Notes |
|---|---|---|
| **S** (Single Responsibility) | Weak | `ToolRegistry` handles dispatch, hooks, MCP discovery, subagent sessions, batch execution, and skill loading — all in one 960-line class. |
| **O** (Open/Closed) | Moderate | Adding a tool requires editing `__init__` to register the handler and adding a new entry to `_handlers`. |
| **L** (Liskov Substitution) | Good | All tools conform to `BaseTool` ABC. |
| **I** (Interface Segregation) | Weak | `ToolExecutionContext` carries 8 optional fields; most tools use 0-2 of them. |
| **D** (Dependency Inversion) | Weak | `ToolRegistry.__init__` takes concrete tool instances as constructor parameters. |

## Rust Architecture

### Module Structure

```
crates/opendev-tools-core/src/
  lib.rs          # Re-exports
  traits.rs       # BaseTool trait, ToolResult, ToolContext, ToolError
  registry.rs     # ToolRegistry (HashMap<String, Arc<dyn BaseTool>>)
  normalizer.rs   # normalize_params() — camelCase, whitespace, path resolution
  sanitizer.rs    # ToolResultSanitizer — per-tool truncation rules
  policy.rs       # ToolPolicy — group/profile permission system
  parallel.rs     # ParallelPolicy — read/write/other partitioning

crates/opendev-tools-impl/src/
  lib.rs          # Module declarations + re-exports of all tool structs
  file_read.rs    # FileReadTool
  file_write.rs   # FileWriteTool
  file_edit.rs    # FileEditTool
  file_list.rs    # FileListTool
  file_search.rs  # FileSearchTool
  bash.rs         # BashTool
  git.rs          # GitTool
  web_fetch.rs    # WebFetchTool
  web_search.rs   # WebSearchTool
  web_screenshot.rs # WebScreenshotTool
  browser.rs      # BrowserTool
  ask_user.rs     # AskUserTool
  memory.rs       # MemoryTool
  session.rs      # SessionTool
  agents.rs       # AgentsTool, SpawnSubagentTool
  batch.rs        # BatchTool
  patch.rs        # PatchTool
  pdf.rs          # PdfTool
  schedule.rs     # ScheduleTool
  message.rs      # MessageTool
  notebook_edit.rs# NotebookEditTool
  open_browser.rs # OpenBrowserTool
  task_complete.rs# TaskCompleteTool
  present_plan.rs # PresentPlanTool
  todo.rs         # TodoTool
  vlm.rs          # VlmTool
  diff_preview.rs # DiffPreviewTool
  worktree.rs     # WorktreeManager
  edit_replacers.rs # Edit replacement algorithms (internal)
```

### Key Abstractions

- **`BaseTool` (async trait):** `fn name(&self) -> &str`, `fn description(&self) -> &str`, `fn parameter_schema(&self) -> serde_json::Value`, `async fn execute(&self, args: HashMap<String, Value>, ctx: &ToolContext) -> ToolResult`. Requires `Send + Sync + Debug`.
- **`ToolResult`:** Struct with `success: bool`, `output: Option<String>`, `error: Option<String>`, `metadata: HashMap<String, Value>`. Factory methods: `ok()`, `ok_with_metadata()`, `fail()`, `from_error()`.
- **`ToolContext`:** Struct with `working_dir: PathBuf`, `is_subagent: bool`, `session_id: Option<String>`, `values: HashMap<String, Value>`. Builder pattern via `with_subagent()`, `with_session_id()`, `with_value()`.
- **`ToolError`:** Enum with variants `Execution`, `InvalidParams`, `NotFound`, `PermissionDenied`, `Interrupted`, `Io`, `Other`. Implements `thiserror::Error`.
- **`ToolRegistry`:** Thin wrapper around `HashMap<String, Arc<dyn BaseTool>>`. Methods: `register()`, `unregister()`, `get()`, `contains()`, `tool_names()`, `get_schemas()`, `execute()`. The `execute()` method applies parameter normalization, then delegates to the tool.

### Design Patterns (and Python Mappings)

| Pattern | Python | Rust | Change |
|---|---|---|---|
| Tool abstraction | `BaseTool` ABC with `**kwargs` | `BaseTool` async trait with typed `HashMap` args | Static dispatch possible; schema is a trait method, not separate |
| Registry | God-class with 960 lines, inline routing | 106-line struct with `HashMap<String, Arc<dyn BaseTool>>` | Responsibilities split out into separate modules |
| Handler layer | Separate handler classes wrapping tools | Eliminated; each tool implements `BaseTool` directly | Reduced indirection |
| Parameter normalization | Standalone function, called in `execute_tool()` | Standalone function, called in `ToolRegistry::execute()` | Same location, same logic |
| Result sanitization | Class with `sanitize(tool_name, result_dict)` | Struct with `sanitize(tool_name, success, output, error)` | Decomposed dict into explicit params |
| Parallel policy | Class with `partition(tool_calls)` returning dicts | Struct with `partition(&[ToolCall])` returning index groups | Returns indices instead of cloned data |

### SOLID Analysis

| Principle | Adherence | Notes |
|---|---|---|
| **S** (Single Responsibility) | Strong | Registry does only registration and dispatch. Normalization, sanitization, policy, and parallelism are separate modules. |
| **O** (Open/Closed) | Strong | Adding a tool requires only implementing `BaseTool` and calling `registry.register()`. No existing code changes. |
| **L** (Liskov Substitution) | Strong | All tools behind `Arc<dyn BaseTool>` are interchangeable. |
| **I** (Interface Segregation) | Improved | `ToolContext` carries only 4 fields; tool-specific data goes in `values` HashMap. |
| **D** (Dependency Inversion) | Strong | Registry depends on `Arc<dyn BaseTool>` trait objects, not concrete types. |

## Migration Mapping

| Python Class/Module | Rust Struct/Trait | Pattern Change | Notes |
|---|---|---|---|
| `BaseTool` (ABC) | `BaseTool` (async trait) | ABC -> trait; `execute(**kwargs)` -> `execute(HashMap, &ToolContext)` | `parameter_schema()` moved into trait from separate schema files |
| `ToolRegistry` (class, 960 LOC) | `ToolRegistry` (struct, 106 LOC) | God-class split into registry + 5 modules | Hooks, MCP discovery, subagent management live in calling code |
| `ToolExecutionContext` (dataclass, 8 fields) | `ToolContext` (struct, 4 fields) | Flattened; optional managers removed | Tool-specific context goes in `values` HashMap |
| `TruncationRule` (dataclass) | `TruncationRule` (struct) + `TruncationStrategy` (enum) | String-based strategy -> enum | Type-safe strategy selection |
| `ToolResultSanitizer` (class) | `ToolResultSanitizer` (struct) | `sanitize(name, dict)` -> `sanitize(name, bool, Option<&str>, Option<&str>)` | Explicit params instead of dict unpacking |
| `ParallelPolicy` (class) | `ParallelPolicy` (struct) | Returns `list[list[dict]]` -> `Vec<Vec<usize>>` | Index-based to avoid cloning tool call data |
| `ToolPolicy` (class) | `ToolPolicy` (struct) | `ValueError` -> `Result<_, String>` | Error handling via Result type |
| `param_normalizer.normalize_params()` | `normalizer::normalize_params()` | Identical signature and behavior | Same camelCase map, same path params list |
| `FileToolHandler` + `FileOps` + `WriteTool` + `EditTool` | `FileReadTool`, `FileWriteTool`, `FileEditTool`, `FileListTool`, `FileSearchTool` | Handler layer eliminated; 1 class -> 5 structs | Each file operation is a standalone `BaseTool` implementor |
| `ProcessToolHandler` + `BashTool` | `BashTool` | Handler eliminated | Direct trait implementation |
| `BatchToolHandler` | `BatchTool` | Handler -> tool | Implements `BaseTool` directly |
| `handlers/*.py` (19 files) | No equivalent | Eliminated entirely | Tools self-contained; no intermediate routing |

## Tool Reference Table

| Tool Name | Rust Module | Description | Tool Group |
|---|---|---|---|
| `read_file` | `file_read.rs` | Read file contents with line ranges, binary detection | group:read |
| `list_files` | `file_list.rs` | List directory contents with glob patterns | group:read |
| `search` | `file_search.rs` | Regex/text search across files (ripgrep-based) | group:read |
| `find_symbol` | (opendev-tools-symbol) | AST-based symbol lookup | group:read |
| `find_referencing_symbols` | (opendev-tools-symbol) | Find references to a symbol | group:read |
| `read_pdf` | `pdf.rs` | Extract text and metadata from PDF files | group:read |
| `analyze_image` | `vlm.rs` | Vision LM image analysis | group:read |
| `write_file` | `file_write.rs` | Create or overwrite files | group:write |
| `edit_file` | `file_edit.rs` | Surgical string replacement in files | group:write |
| `insert_before_symbol` | (opendev-tools-symbol) | Insert code before an AST symbol | group:write |
| `insert_after_symbol` | (opendev-tools-symbol) | Insert code after an AST symbol | group:write |
| `replace_symbol_body` | (opendev-tools-symbol) | Replace an AST symbol's body | group:write |
| `rename_symbol` | (opendev-tools-symbol) | Rename an AST symbol across files | group:write |
| `notebook_edit` | `notebook_edit.rs` | Edit Jupyter notebook cells | group:write |
| `apply_patch` | `patch.rs` | Apply unified diff patches | group:write |
| `run_command` | `bash.rs` | Execute shell commands with timeout | group:process |
| `list_processes` | `bash.rs` | List running background processes | group:process |
| `get_process_output` | `bash.rs` | Get output from a background process | group:process |
| `kill_process` | `bash.rs` | Terminate a background process | group:process |
| `fetch_url` | `web_fetch.rs` | Fetch and extract content from URLs | group:web |
| `web_search` | `web_search.rs` | Search the web via search APIs | group:web |
| `capture_web_screenshot` | `web_screenshot.rs` | Capture webpage screenshots | group:web |
| `capture_screenshot` | `web_screenshot.rs` | Capture local screenshots | group:web |
| `browser` | `browser.rs` | Browser automation (navigate, click, etc.) | group:web |
| `open_browser` | `open_browser.rs` | Open a URL in the system browser | group:web |
| `git` | `git.rs` | Git operations (status, diff, commit, etc.) | group:git |
| `list_sessions` | `session.rs` | List conversation sessions | group:session |
| `get_session_history` | `session.rs` | Retrieve session message history | group:session |
| `spawn_subagent` | `agents.rs` | Spawn a parallel subagent | group:session |
| `get_subagent_output` | `agents.rs` | Get output from background subagent | group:session |
| `list_subagents` | `session.rs` | List active subagents | group:session |
| `memory_search` | `memory.rs` | Search memory embeddings | group:memory |
| `memory_write` | `memory.rs` | Write to memory store | group:memory |
| `task_complete` | `task_complete.rs` | Signal task completion to terminate ReAct loop | group:meta |
| `ask_user` | `ask_user.rs` | Prompt user for input/clarification | group:meta |
| `present_plan` | `present_plan.rs` | Present implementation plan for approval | group:meta |
| `write_todos` | `todo.rs` | Create todo items from plan | group:meta |
| `update_todo` | `todo.rs` | Update a todo item's status | group:meta |
| `complete_todo` | `todo.rs` | Mark a todo as complete | group:meta |
| `list_todos` | `todo.rs` | List current todos | group:meta |
| `clear_todos` | `todo.rs` | Clear all todos | group:meta |
| `search_tools` | (opendev-tools-core) | Discover MCP tools by keyword | group:meta |
| `invoke_skill` | (opendev-agents) | Load a skill into conversation context | group:meta |
| `batch_tool` | `batch.rs` | Execute multiple tools in parallel/serial | group:meta |
| `list_agents` | `agents.rs` | List available subagent types | group:meta |
| `send_message` | `message.rs` | Send a message to another channel | group:messaging |
| `schedule` | `schedule.rs` | Schedule a future task | group:automation |
| `diff_preview` | `diff_preview.rs` | Preview file diffs before editing | (internal) |

## How to Add a New Tool

### Step 1: Create the Tool Module

Create a new file in `crates/opendev-tools-impl/src/`, e.g., `my_tool.rs`:

```rust
//! My custom tool — does something useful.

use std::collections::HashMap;
use opendev_tools_core::{BaseTool, ToolContext, ToolResult};

/// Tool for doing something useful.
#[derive(Debug)]
pub struct MyTool;

#[async_trait::async_trait]
impl BaseTool for MyTool {
    fn name(&self) -> &str {
        "my_tool"
    }

    fn description(&self) -> &str {
        "Does something useful. Provide a 'target' parameter."
    }

    fn parameter_schema(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "The target to operate on"
                }
            },
            "required": ["target"]
        })
    }

    async fn execute(
        &self,
        args: HashMap<String, serde_json::Value>,
        ctx: &ToolContext,
    ) -> ToolResult {
        let target = match args.get("target").and_then(|v| v.as_str()) {
            Some(t) => t,
            None => return ToolResult::fail("target is required"),
        };

        // Use ctx.working_dir for path resolution if needed
        let _working_dir = &ctx.working_dir;

        // Do the work...
        ToolResult::ok(format!("Processed: {target}"))
    }
}
```

### Step 2: Register the Module

In `crates/opendev-tools-impl/src/lib.rs`, add:

```rust
pub mod my_tool;
pub use my_tool::MyTool;
```

### Step 3: Add to Tool Group

In `crates/opendev-tools-core/src/policy.rs`, add the tool to the appropriate group:

```rust
groups.insert(
    "group:meta",  // or whichever group fits
    HashSet::from([
        // ...existing tools...
        "my_tool",
    ]),
);
```

### Step 4: Add to Parallel Policy (if applicable)

If the tool is read-only, add it to `read_only_tools()` in `crates/opendev-tools-core/src/parallel.rs`. If it modifies state, add it to `write_tools()`.

### Step 5: Add Sanitization Rule (if needed)

If the tool can produce large output, add a truncation rule in `crates/opendev-tools-core/src/sanitizer.rs`:

```rust
rules.insert("my_tool".into(), TruncationRule::head(10000));
```

### Step 6: Add Normalization Mappings (if needed)

If the LLM might send camelCase parameter names, add mappings in `crates/opendev-tools-core/src/normalizer.rs`:

```rust
"myTarget" => Some("my_target"),
```

If the tool has path parameters, add them to `PATH_PARAMS`.

### Step 7: Register at Startup

In the agent initialization code, register the tool with the registry:

```rust
registry.register(Arc::new(MyTool));
```

### Step 8: Write Tests

Add unit tests in the tool module itself and integration tests if the tool interacts with external systems.

## Key Design Decisions

### Elimination of the Handler Layer

**Python:** Tools were wrapped in handler classes (`FileToolHandler`, `ProcessToolHandler`, etc.) that sat between the registry and the implementations. This added indirection — a `read_file` call went through `ToolRegistry -> FileToolHandler -> FileOps.read_file()`.

**Rust:** Each tool implements `BaseTool` directly. The registry dispatches straight to the tool via `Arc<dyn BaseTool>`. This eliminates an entire layer of abstraction, reducing code and making the dispatch path obvious. The tradeoff is that tools that share state (e.g., the Python `FileOps` class that held `working_dir`) must get that state from `ToolContext` instead.

### Registry as Thin Dispatcher vs. God-Class

**Python:** `ToolRegistry` was 960 lines with inline handler routing, hook management, MCP discovery, subagent session saving, batch execution, skill loading, and todo management.

**Rust:** `ToolRegistry` is 106 lines. It does exactly two things: store tools and dispatch execution. Everything else — hooks, MCP discovery, subagent management — lives in the calling code (`opendev-agents`) or in the tools themselves (`BatchTool`, `SpawnSubagentTool`).

### Index-Based Parallel Partitioning

**Python:** `ParallelPolicy.partition()` returned `list[list[dict]]` — copies of the tool call dicts grouped by execution order.

**Rust:** `ParallelPolicy::partition()` returns `Vec<Vec<usize>>` — indices into the original slice. This avoids cloning tool call data, which matters when tool calls carry large argument payloads (e.g., `apply_patch` with multi-file diffs).

### Typed Truncation Strategy

**Python:** `TruncationRule.strategy` was a string (`"head"`, `"tail"`, `"head_tail"`), validated at runtime.

**Rust:** `TruncationStrategy` is an enum with `Head`, `Tail`, and `HeadTail { head_ratio: f64 }` variants. Invalid strategies are caught at compile time, and the `head_ratio` field is only present when relevant.

### Explicit ToolResult Fields

**Python:** Tool results were `dict[str, Any]` with no type guarantees. Success was `result.get("success", False)`, output was `result.get("output")`.

**Rust:** `ToolResult` is a struct with `success: bool`, `output: Option<String>`, `error: Option<String>`, `metadata: HashMap<String, Value>`. Factory methods (`ok()`, `fail()`) enforce correct field combinations.

## Code Examples

### Python: BaseTool and Execution

```python
# implementations/base.py
class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any: ...

# registry.py (simplified dispatch)
class ToolRegistry:
    def execute_tool(self, tool_name, arguments, *, mode_manager=None, ...):
        arguments = normalize_params(tool_name, arguments, working_dir)
        context = ToolExecutionContext(mode_manager=mode_manager, ...)
        handler = self._handlers[tool_name]
        result = handler(arguments, context)
        return result
```

### Rust: BaseTool and Execution

```rust
// traits.rs
#[async_trait::async_trait]
pub trait BaseTool: Send + Sync + std::fmt::Debug {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn parameter_schema(&self) -> serde_json::Value;
    async fn execute(
        &self,
        args: HashMap<String, serde_json::Value>,
        ctx: &ToolContext,
    ) -> ToolResult;
}

// registry.rs (simplified dispatch)
impl ToolRegistry {
    pub async fn execute(
        &self, tool_name: &str,
        args: HashMap<String, serde_json::Value>,
        ctx: &ToolContext,
    ) -> ToolResult {
        let tool = match self.tools.get(tool_name) {
            Some(t) => t,
            None => return ToolResult::fail(format!("Unknown tool: {tool_name}")),
        };
        let normalized = normalizer::normalize_params(tool_name, args, Some(&working_dir));
        tool.execute(normalized, ctx).await
    }
}
```

### Python: Result Sanitization

```python
sanitizer = ToolResultSanitizer()
result = sanitizer.sanitize("run_command", {"success": True, "output": long_text})
# Returns: {"success": True, "output": "...truncated tail...\n\n[truncated: ...]"}
```

### Rust: Result Sanitization

```rust
let sanitizer = ToolResultSanitizer::new();
let result = sanitizer.sanitize("run_command", true, Some(&long_text), None);
// result.output contains truncated text with tail strategy
// result.was_truncated == true
```

## Remaining Gaps

1. **Hook integration in registry:** Python's `ToolRegistry.execute_tool()` ran PreToolUse/PostToolUse hooks inline. In Rust, hook execution is handled by the caller (`opendev-agents`), not the registry itself. This is a deliberate design choice, but it means the calling code must remember to run hooks.

2. **MCP tool discovery:** Python's `ToolRegistry` tracked discovered MCP tools and lazily expanded their schemas. In Rust, MCP tool management is handled by `opendev-mcp` crate separately from the tool registry.

3. **FileTimeTracker:** Python had stale-read detection (`FileTimeTracker`) embedded in the registry. The Rust equivalent would need to live in the calling code or as a middleware wrapper.

4. **Skill loading:** Python's `invoke_skill` tool was handled inside the registry. In Rust, skill management is in `opendev-agents`.

## References

### Python Source Files
- `opendev/core/context_engineering/tools/implementations/base.py` — BaseTool ABC
- `opendev/core/context_engineering/tools/registry.py` — ToolRegistry (960 LOC)
- `opendev/core/context_engineering/tools/param_normalizer.py` — Parameter normalization
- `opendev/core/context_engineering/tools/result_sanitizer.py` — Result sanitization
- `opendev/core/context_engineering/tools/parallel_policy.py` — Parallel execution policy
- `opendev/core/context_engineering/tools/tool_policy.py` — Group/profile access control
- `opendev/core/context_engineering/tools/implementations/` — 26 tool implementation files
- `opendev/core/context_engineering/tools/handlers/` — 19 handler files

### Rust Source Files
- `crates/opendev-tools-core/src/traits.rs` — BaseTool trait, ToolResult, ToolContext, ToolError
- `crates/opendev-tools-core/src/registry.rs` — ToolRegistry
- `crates/opendev-tools-core/src/normalizer.rs` — Parameter normalization
- `crates/opendev-tools-core/src/sanitizer.rs` — ToolResultSanitizer
- `crates/opendev-tools-core/src/policy.rs` — ToolPolicy (groups and profiles)
- `crates/opendev-tools-core/src/parallel.rs` — ParallelPolicy
- `crates/opendev-tools-impl/src/lib.rs` — Module declarations and re-exports
- `crates/opendev-tools-impl/src/*.rs` — 27 tool implementation modules
