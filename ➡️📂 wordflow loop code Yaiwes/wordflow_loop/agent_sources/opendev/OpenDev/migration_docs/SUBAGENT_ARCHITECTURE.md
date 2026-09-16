# Subagent Architecture

## Overview

The subagent system enables the main agent to delegate complex, multi-step tasks to ephemeral child agents, each running its own isolated ReAct loop with a restricted tool set and specialized system prompt. Subagents are the primary mechanism for parallelism and task decomposition in OpenDev -- the parent agent spawns one or more subagents via the `spawn_subagent` tool, and each subagent operates with fresh message history, no access to the parent's conversation context, and a bounded iteration budget.

In the overall architecture, the subagent system spans three crates: `opendev-agents` (spec and manager), `opendev-tools-impl` (the `SpawnSubagentTool` bridge that the LLM invokes), and `opendev-docker` (container lifecycle for sandboxed execution). The Python counterpart lives in `opendev/core/agents/subagents/`.

## Python Architecture

### Module Structure

```
opendev/core/agents/subagents/
  __init__.py              # Public API: SubAgentSpec, CompiledSubAgent, SubAgentManager, ALL_SUBAGENTS
  specs.py                 # SubAgentSpec (TypedDict), CompiledSubAgent (TypedDict)
  task_tool.py             # create_task_tool_schema(), format_task_result(), TASK_TOOL_NAME
  tool_metadata.py         # ToolInfo dataclass, display name mappings for UI
  agents/
    __init__.py            # ALL_SUBAGENTS list aggregating all built-in specs
    ask_user.py            # ASK_USER_SUBAGENT spec
    code_explorer.py       # CODE_EXPLORER_SUBAGENT spec
    planner.py             # PLANNER_SUBAGENT spec
    pr_reviewer.py         # PR_REVIEWER_SUBAGENT spec
    project_init.py        # PROJECT_INIT_SUBAGENT spec
    security_reviewer.py   # SECURITY_REVIEWER_SUBAGENT spec
    web_clone.py           # WEB_CLONE_SUBAGENT spec
    web_generator.py       # WEB_GENERATOR_SUBAGENT spec
  manager/
    __init__.py            # Re-exports SubAgentManager, AgentConfig, SubAgentDeps, AgentSource
    manager.py             # SubAgentManager class (diamond mixin), AgentConfig, SubAgentDeps, AgentSource
    registration.py        # RegistrationMixin: register_subagent, register_defaults, register_custom_agents
    execution.py           # ExecutionMixin: execute_subagent, execute_subagent_async, execute_parallel, _execute_ask_user
    docker.py              # DockerMixin: _execute_with_docker, _copy_files_to_docker, _copy_files_from_docker, path sanitization
```

### Key Abstractions

- **`SubAgentSpec`** (TypedDict): Declarative specification for a subagent -- name, description, system_prompt, optional tool list, optional model override, optional docker_config.
- **`CompiledSubAgent`** (TypedDict): A spec that has been resolved into a live `MainAgent` instance ready for execution, with tool names baked in.
- **`SubAgentManager`**: Central orchestrator composed via three mixins (`RegistrationMixin`, `ExecutionMixin`, `DockerMixin`). Owns the `_agents` dict mapping names to `CompiledSubAgent`.
- **`AgentConfig`**: Intermediate representation used for building tool descriptions and supporting custom agent loading from JSON/markdown files.
- **`AgentSource`** (Enum): Tracks whether an agent is `BUILTIN`, `USER_GLOBAL`, or `PROJECT`-scoped.
- **`SubAgentDeps`**: Dependency injection container holding mode_manager, approval_manager, undo_manager, session_manager.

### Design Patterns

1. **Mixin-based composition**: `SubAgentManager` inherits from three mixins (`RegistrationMixin`, `ExecutionMixin`, `DockerMixin`) to separate registration, execution, and Docker concerns. Each mixin declares the instance attributes it expects but does not own `__init__`.
2. **TypedDict specs**: Agent definitions are plain dictionaries with type annotations, not classes. This keeps them serializable and easy to define declaratively.
3. **Lazy compilation**: Specs are registered as TypedDicts; actual `MainAgent` instances are created during `register_subagent()`, not at import time.
4. **Nested UI callbacks**: `NestedUICallback` wraps the parent callback to provide depth-aware display with optional Docker path sanitization.
5. **Docker-transparent execution**: When a spec includes `docker_config`, execution seamlessly switches to Docker mode (container start, file copy in, task rewrite, Docker tool registry, file copy out, container stop) -- all invisible to the subagent's ReAct loop.

### SOLID Analysis

- **S (Single Responsibility)**: Partially -- the three mixins separate concerns, but `DockerMixin` handles both container lifecycle and file operations.
- **O (Open/Closed)**: Custom agents can be added via `register_custom_agents()` without modifying built-in specs.
- **L (Liskov)**: N/A -- no inheritance hierarchy for agent types; they are all data (TypedDicts).
- **I (Interface Segregation)**: The mixin pattern provides some segregation, though all mixins share instance state.
- **D (Dependency Inversion)**: `SubAgentManager` depends on abstract `tool_registry` and `mode_manager` (Any-typed), not concrete implementations.

## Rust Architecture

### Module Structure

```
crates/opendev-agents/src/subagents/
  mod.rs                   # Re-exports: SubAgentSpec, builtins, SubagentManager, SubagentType, etc.
  spec.rs                  # SubAgentSpec struct, builder methods, builtins module (factory functions)
  manager.rs               # SubagentManager, SubagentType enum, SubagentProgressCallback trait,
                           #   SubagentRunResult, NoopProgressCallback, spawn()

crates/opendev-tools-impl/src/
  agents.rs                # AgentsTool (list tool), SpawnSubagentTool (spawn tool),
                           #   SubagentEvent enum, ChannelProgressCallback

crates/opendev-docker/src/
  lib.rs                   # Re-exports
  models.rs                # DockerConfig, ContainerSpec, VolumeMount, PortMapping, ContainerStatus, etc.
  deployment.rs            # DockerDeployment: pull_image, start_container, start, stop, inspect, remove
  session.rs               # DockerSession: exec_command, copy_file_in, copy_file_out, interrupt
  tool_handler.rs          # DockerToolHandler: run_command, read_file, write_file, list_files, search, translate_path
  errors.rs                # DockerError enum
  local_runtime.rs         # LocalRuntime
  remote_runtime.rs        # RemoteRuntime
```

### Key Abstractions

- **`SubAgentSpec`** (struct, `Serialize`/`Deserialize`): Mirrors the Python TypedDict. Builder pattern via `with_tools()`, `with_model()`. Contains name, description, system_prompt, tools (Vec<String>), model (Option<String>).
- **`builtins`** module: Factory functions (`code_explorer()`, `planner()`, `ask_user()`, etc.) that construct `SubAgentSpec` instances with hardcoded tool lists. Takes system_prompt as parameter since prompts are loaded at a higher level.
- **`SubagentManager`**: Owns `HashMap<String, SubAgentSpec>`. Provides `register()`, `get()`, `get_by_type()`, `names()`, `build_enum_description()`, and `spawn()`.
- **`SubagentType`** (enum): Type-safe enum (`CodeExplorer`, `Planner`, `AskUser`, `PrReviewer`, `SecurityReviewer`, `WebClone`, `WebGenerator`, `Custom`) with `from_name()` and `canonical_name()` for bidirectional mapping.
- **`SubagentProgressCallback`** (trait): Defines `on_started`, `on_tool_call`, `on_tool_complete`, `on_finished`. Implementors: `NoopProgressCallback`, `ChannelProgressCallback`.
- **`SubagentRunResult`**: Bundles `AgentResult`, `tool_call_count`, and optional `shallow_warning`.
- **`SpawnSubagentTool`**: Implements `BaseTool`. Holds `Arc<SubagentManager>`, `Arc<ToolRegistry>`, `Arc<AdaptedClient>`, parent model, working dir, and optional event sender.
- **`SubagentEvent`** (enum): Typed events (`Started`, `ToolCall`, `ToolComplete`, `Finished`) sent from subagent to TUI via `mpsc::UnboundedSender`.
- **`DockerDeployment`**: Container lifecycle (pull, start, stop, inspect, remove) with `Drop`-based cleanup.
- **`DockerSession`**: Command execution via `docker exec`, file transfer via `docker cp`.
- **`DockerToolHandler`**: Routes tool calls (run_command, read_file, write_file, list_files, search) into a Docker container with path translation.

### Design Patterns and Python Mapping

1. **Mixin elimination**: Python's three mixins (`RegistrationMixin`, `ExecutionMixin`, `DockerMixin`) collapse into a single `SubagentManager` struct in Rust. The manager handles registration and lookup; execution is in `spawn()`. Docker is a separate crate.
2. **TypedDict to struct + builder**: Python's `SubAgentSpec` TypedDict becomes a Rust struct with `Serialize`/`Deserialize` and a builder pattern (`with_tools()`, `with_model()`).
3. **Factory functions instead of module-level constants**: Python defines specs as module-level constants (`CODE_EXPLORER_SUBAGENT = SubAgentSpec(...)`). Rust uses factory functions in a `builtins` module that take system_prompt as a parameter, since prompt loading is a separate concern.
4. **Trait-based progress callbacks**: Python uses duck-typed `ui_callback` with `hasattr()` checks. Rust formalizes this into the `SubagentProgressCallback` trait with four methods.
5. **Channel-based event bridge**: Python's `NestedUICallback` wrapper pattern becomes Rust's `ChannelProgressCallback` + `SubagentEvent` enum, using `mpsc::UnboundedSender` to decouple subagent execution from TUI rendering.
6. **Arc-based shared ownership**: Python passes dependencies as mutable instance attributes. Rust uses `Arc<SubagentManager>`, `Arc<ToolRegistry>`, `Arc<AdaptedClient>` for safe concurrent access.
7. **Drop-based cleanup**: `DockerDeployment` implements `Drop` to force-remove the container if not explicitly stopped, replacing Python's try/finally pattern.

### SOLID Analysis

- **S (Single Responsibility)**: Strong. `SubAgentSpec` is pure data, `SubagentManager` handles registration + spawning, `SpawnSubagentTool` handles the LLM bridge, Docker is an entirely separate crate.
- **O (Open/Closed)**: The `SubagentProgressCallback` trait allows new progress consumers without modifying the manager. Custom agents register via `manager.register()`.
- **L (Liskov)**: `NoopProgressCallback` and `ChannelProgressCallback` are fully substitutable for `SubagentProgressCallback`.
- **I (Interface Segregation)**: The `SubagentProgressCallback` trait is minimal (4 methods). `BaseTool` is the single interface for all tools.
- **D (Dependency Inversion)**: `SubagentManager::spawn()` takes `Arc<ToolRegistry>` and `dyn SubagentProgressCallback`, not concrete types. `SpawnSubagentTool` depends on the `BaseTool` trait abstraction.

## Migration Mapping

| Python Class/Module | Rust Struct/Trait | Pattern Change | Notes |
|---|---|---|---|
| `SubAgentSpec` (TypedDict) | `SubAgentSpec` (struct) | TypedDict to struct + builder | `docker_config` and `copy_back_recursive` not yet in Rust |
| `CompiledSubAgent` (TypedDict) | N/A (inlined in `spawn()`) | Eliminated | Rust creates `MainAgent` on-the-fly in `spawn()` instead of pre-compiling |
| `SubAgentManager` (3 mixins) | `SubagentManager` (single struct) | Mixin diamond to flat struct | Registration + lookup; `spawn()` handles execution |
| `AgentConfig` | N/A | Not yet migrated | Used for custom agent loading and tool description building |
| `AgentSource` (str Enum) | N/A | Not yet migrated | Needed for custom agent source tracking |
| `SubAgentDeps` | `AgentDeps` | Simplified | Rust uses a generic `AgentDeps` instead of subagent-specific deps |
| `ALL_SUBAGENTS` (list) | `builtins::*()` factory functions | Module constants to factory functions | System prompts passed as parameter |
| `create_task_tool_schema()` | `SpawnSubagentTool::parameter_schema()` | Free function to trait method | Schema built from manager's registered specs |
| `format_task_result()` | Inline in `SpawnSubagentTool::execute()` | Absorbed into tool execution | |
| `NestedUICallback` | `ChannelProgressCallback` + `SubagentEvent` | Callback wrapper to channel + enum | Decoupled via async channel |
| `DockerMixin` | `opendev-docker` crate | Mixin to separate crate | Full crate with deployment, session, tool handler |
| `_execute_with_docker()` | Not yet wired (crate exists) | Docker lifecycle separate from subagent manager | Crate ready but not integrated into `spawn()` |
| `_execute_ask_user()` | Not yet migrated | Special-case subagent | Requires TUI integration |
| `execute_parallel()` | Not yet migrated | `asyncio.gather` | Can use `tokio::join!` or `JoinSet` |
| `register_custom_agents()` | Not yet migrated | Custom agent loading from JSON/markdown | |

## Built-in Agent Types

| Agent Type | Python Name | Rust Name | Tools | Purpose |
|---|---|---|---|---|
| Code Explorer | `Code-Explorer` | `Code-Explorer` | `read_file`, `search`, `list_files`, `find_symbol`, `find_referencing_symbols` | Read-only codebase exploration, architecture analysis, pattern research |
| Planner | `Planner` | `Planner` | Code Explorer tools + `write_file`, `edit_file` | Analyze codebase and write implementation plans to a file |
| Ask User | `ask-user` | `ask-user` | (none) | UI-only interaction: structured multiple-choice questions via TUI panel |
| PR Reviewer | `PR-Reviewer` | `PR-Reviewer` | Code Explorer tools + `run_command` | Review pull requests for correctness, style, performance, security |
| Security Reviewer | `Security-Reviewer` | `Security-Reviewer` | Code Explorer tools + `run_command` | Security-focused code review with severity/confidence scoring |
| Web Clone | `Web-clone` | `Web-Clone` | `capture_web_screenshot`, `analyze_image`, `write_file`, `read_file`, `run_command`, `list_files` | Visually analyze websites and generate code replicating their UI |
| Web Generator | `Web-Generator` | `Web-Generator` | `write_file`, `edit_file`, `run_command`, `list_files`, `read_file` | Create new web applications from scratch |
| Project Init | `Project-Init` | `project_init` | Python: `read_file`, `search`, `list_files`, `run_command`, `write_file`; Rust: `Read`, `Glob`, `Grep`, `Bash` | Analyze codebase and generate OPENDEV.md project instructions |

Note: All subagents intentionally exclude todo tools (`write_todos`, `update_todo`, etc.) -- only the main agent manages task tracking. Subagents also cannot spawn other subagents (no recursive spawning).

## Key Design Decisions

### 1. Ephemeral Agents with Fresh Context
Subagents start with empty message history. The parent must include all necessary context in the task prompt. This prevents context bleed, keeps token usage predictable, and enables parallel execution without shared state.

### 2. Tool Restriction as Security Boundary
Each subagent spec declares its allowed tools. The Code Explorer can only read; it cannot write files or run commands. This prevents accidental side effects during exploration tasks and provides a lightweight permission model.

### 3. Iteration Budget
Rust subagents get a `max_iterations: 25` cap (via `ReactLoopConfig`), preventing runaway execution. Python subagents have no hardcoded cap but stop when their prompt tells them to.

### 4. Shallow Subagent Detection
The Rust implementation counts tool calls after execution and emits a `shallow_warning` if a subagent completed with suspiciously few tool calls. This helps the parent agent detect when a subagent gave a superficial answer without actually doing work.

### 5. Progress Callback as Trait
The Python codebase uses duck-typed callbacks with `hasattr()` checks for optional methods like `on_parallel_agents_start`. Rust replaces this with the `SubagentProgressCallback` trait, providing compile-time guarantees and enabling the `ChannelProgressCallback` implementation that bridges to the TUI event loop.

### 6. Docker as Optional, Transparent Layer
Docker sandboxing is triggered by the presence of `docker_config` in a `SubAgentSpec`. The subagent's ReAct loop is unaware of Docker -- the tool registry is swapped to route calls through the container. If Docker is unavailable, execution falls back to local mode. The Rust `opendev-docker` crate provides the primitives but is not yet wired into the subagent spawn path.

### 7. Custom Agent Extensibility
Python supports user-defined agents via `~/.opendev/agents.json`, `<project>/.opendev/agents.json`, or markdown files in `~/.opendev/agents/*.md`. These are loaded by `register_custom_agents()` and participate in the same spawn mechanism as built-ins. This is not yet migrated to Rust.

## Code Examples

### Defining a Built-in Subagent (Python)

```python
# opendev/core/agents/subagents/agents/code_explorer.py
CODE_EXPLORER_SUBAGENT = SubAgentSpec(
    name="Code-Explorer",
    description="Deep LOCAL codebase exploration and research...",
    system_prompt=load_prompt("subagents/subagent-code-explorer"),
    tools=["read_file", "search", "list_files", "find_symbol", "find_referencing_symbols"],
)
```

### Defining a Built-in Subagent (Rust)

```rust
// crates/opendev-agents/src/subagents/spec.rs
pub fn code_explorer(system_prompt: &str) -> SubAgentSpec {
    SubAgentSpec::new(
        "Code-Explorer",
        "Deep LOCAL codebase exploration and research...",
        system_prompt,
    )
    .with_tools(CODE_EXPLORER_TOOLS.iter().map(|s| s.to_string()).collect())
}
```

### Spawning a Subagent (Rust)

```rust
// crates/opendev-agents/src/subagents/manager.rs — SubagentManager::spawn()
let config = MainAgentConfig {
    model,
    temperature: Some(0.7),
    max_tokens: Some(4096),
    working_dir: Some(working_dir.to_string()),
    allowed_tools,
    ..Default::default()
};
let mut agent = MainAgent::new(config, tool_registry);
agent.set_http_client(http_client);
agent.set_system_prompt(&spec.system_prompt);
agent.set_react_config(ReactLoopConfig { max_iterations: Some(25), .. });
let result = agent.run(task, &deps, None, task_monitor).await;
```

### SpawnSubagentTool Bridge (Rust)

```rust
// crates/opendev-tools-impl/src/agents.rs
impl BaseTool for SpawnSubagentTool {
    async fn execute(&self, args: HashMap<String, Value>, ctx: &ToolContext) -> ToolResult {
        let agent_type = args.get("agent_type").and_then(|v| v.as_str()).unwrap();
        let task = args.get("task").and_then(|v| v.as_str()).unwrap();
        let result = self.manager.spawn(
            agent_type, task, &self.parent_model,
            Arc::clone(&self.tool_registry),
            Arc::clone(&self.http_client),
            &working_dir, progress.as_ref(), None,
        ).await;
        // ... format result into ToolResult
    }
}
```

### Docker Container Lifecycle (Rust)

```rust
// crates/opendev-docker/src/deployment.rs
let mut deploy = DockerDeployment::new(config)?;  // Allocates port, generates container name
deploy.start().await?;                             // Pulls image + starts container
// ... execute subagent tools via DockerSession ...
deploy.stop().await?;                              // Graceful stop + force remove
// Drop impl also force-removes as safety net
```

## Remaining Gaps

1. **Docker integration in spawn path**: The `opendev-docker` crate has full container lifecycle support, but `SubagentManager::spawn()` does not yet detect `docker_config` on a spec or route tools through `DockerToolHandler`. The Python `_execute_with_docker()` flow (container start, file copy, task rewrite, Docker tool registry, file copy back, container stop) needs to be wired in.

2. **Custom agent loading**: `register_custom_agents()` for JSON and markdown agent definitions is not yet migrated. This includes `AgentConfig`, `AgentSource`, and the skill path resolution logic.

3. **Ask-user special case**: The `ask-user` subagent bypasses the LLM entirely and shows a TUI panel. This requires TUI integration that is not yet implemented in the Rust spawn path.

4. **Parallel execution**: Python's `execute_parallel()` uses `asyncio.gather` to run multiple subagents concurrently. Rust could use `tokio::JoinSet` but this is not yet implemented.

5. **Background execution**: Python supports `run_in_background` with `get_subagent_output` for deferred result checking. Not yet migrated.

6. **Resume support**: Python supports resuming a previous subagent session via `agent_id`. Not yet migrated.

7. **Hook integration**: Python fires `SubagentStart`/`SubagentStop` hooks via `_hook_manager`. Not yet wired in Rust.

8. **`docker_config` on SubAgentSpec**: The Rust `SubAgentSpec` does not include `docker_config` or `copy_back_recursive` fields that the Python version supports.

9. **Tool name divergence**: Some Rust built-in specs (e.g., `project_init`) use different tool names (`Read`, `Glob`, `Grep`, `Bash`) than Python (`read_file`, `search`, `list_files`, `run_command`), reflecting the tool registry naming difference between the two implementations.

## References

- Python subagent specs: `opendev-py/opendev/core/agents/subagents/specs.py`
- Python subagent manager: `opendev-py/opendev/core/agents/subagents/manager/`
- Python built-in agents: `opendev-py/opendev/core/agents/subagents/agents/`
- Rust SubAgentSpec: `crates/opendev-agents/src/subagents/spec.rs`
- Rust SubagentManager: `crates/opendev-agents/src/subagents/manager.rs`
- Rust SpawnSubagentTool: `crates/opendev-tools-impl/src/agents.rs`
- Rust Docker crate: `crates/opendev-docker/src/`
