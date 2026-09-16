# Subagent Execution Model

This document explains how subagents work in OpenDev at runtime.

The short version:

- A subagent is not a separate `opendev` OS process.
- A subagent is not a dedicated OS thread.
- A subagent is an isolated logical agent state executed as an async task/future inside the main `opendev` process.
- Concurrency is managed by Tokio.

## One-Sentence Mental Model

OpenDev runs as one Rust process. Inside that process, the parent agent and any subagents are separate in-memory execution states that Tokio schedules as asynchronous work.

If you need a simpler phrase, use this:

> A subagent is a logical child agent, not a child process.

## What the Computer Actually Sees

When you run OpenDev today, the operating system typically sees:

- one `opendev` process
- a Tokio runtime with a pool of worker threads
- file descriptors, sockets, child processes launched by tools such as `run_command`

What the operating system does **not** see for each subagent:

- a new `opendev` process per subagent
- a guaranteed dedicated OS thread per subagent

So if the model spawns 5 subagents, the machine does **not** usually look like:

```text
opendev
opendev-subagent-1
opendev-subagent-2
opendev-subagent-3
opendev-subagent-4
opendev-subagent-5
```

Instead, it looks more like:

```text
process: opendev
  runtime: tokio
  worker threads: a small shared pool
  tasks/futures:
    - parent agent loop
    - subagent A
    - subagent B
    - subagent C
    - TUI event bridge
    - HTTP requests
    - tool executions
```

The important distinction is that the subagents exist as Rust state and async execution units inside one process.

## What "Logical Agent State" Means

When we say a subagent is a "logical agent state", we mean that each subagent gets its own independent agent data, even though it lives in the same process as the parent.

Each subagent has its own:

- system prompt
- user task
- message history
- tool allowlist
- permission rules
- working directory context
- cancellation token
- progress stream back to TUI
- final result

This isolation is visible in the subagent manager where a fresh system prompt, tool schemas, `ToolContext`, and message list are built for each child run ([spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-agents/src/subagents/manager/spawn.rs#L116), [spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-agents/src/subagents/manager/spawn.rs#L182), [spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-agents/src/subagents/manager/spawn.rs#L188), [spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-agents/src/subagents/manager/spawn.rs#L208)).

Conceptually, memory might contain something like:

```text
Subagent A:
  messages = [...]
  tools = ["read_file", "grep", "list_files"]
  status = waiting_on_llm

Subagent B:
  messages = [...]
  tools = ["read_file", "edit_file", "run_command"]
  status = executing_tool

Subagent C:
  messages = [...]
  tools = ["read_file", "grep"]
  status = finished
```

They are separate as program state, not as operating-system processes.

## What an Async Future Is

An async future is a resumable computation.

Instead of reserving a full thread and blocking it while waiting, Rust stores the task's state in an object that can be paused and resumed.

That object contains, roughly:

- where execution should continue
- local variables that must be preserved
- what operation it is currently waiting on
- whether it is ready to make progress again

For subagents, that usually means:

1. build prompt and tool schemas
2. send LLM request
3. pause while waiting for HTTP response
4. resume when response arrives
5. execute tools
6. pause if a tool is waiting on I/O
7. resume again
8. continue until completion

So a subagent is not "continuously burning CPU". Most of its lifetime is spent waiting on:

- model API responses
- file I/O
- command output
- timers or cancellation

Async execution is a good fit for that pattern.

## Tokio's Role

Tokio is the async runtime that schedules these tasks.

In OpenDev's current design, Tokio is responsible for:

- polling async agent futures
- waking them when network or tool I/O completes
- multiplexing many tasks over a shared thread pool
- handling cancellation and event delivery

This means:

- a subagent does not own a thread
- a thread may run many subagents over time
- the same subagent may resume on different worker threads across its lifetime

That is why the correct statement is:

- `subagent != thread`
- `subagent = isolated agent state + async execution`

## Current Call Path

At a high level, the current path is:

1. The parent agent decides to call `spawn_subagent`.
2. `SpawnSubagentTool` validates arguments and creates child IDs and cancellation state.
3. The tool calls `SubagentManager::spawn(...)`.
4. The manager constructs a fresh subagent prompt, tool context, and runner.
5. The runner executes its own ReAct loop.
6. The result is returned to the parent agent as the tool result.

Relevant code:

- tool entry point: [spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-tools-impl/src/agents/spawn.rs#L139)
- synchronous await of child run: [spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-tools-impl/src/agents/spawn.rs#L260)
- subagent execution entry: [spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-agents/src/subagents/manager/spawn.rs#L53)
- runner context and child loop: [spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-agents/src/subagents/manager/spawn.rs#L216)

## Is a Single `spawn_subagent` Call Parallel?

No.

A single `spawn_subagent` tool call blocks the parent tool execution until the child finishes. This is explicit in the tool implementation where it directly awaits the manager's `spawn()` call ([spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-tools-impl/src/agents/spawn.rs#L260)).

That means this pattern is sequential:

```text
parent
  -> spawn_subagent(A)
  -> wait
  -> get result
  -> continue
```

## When Do Subagents Run Concurrently?

Subagents run concurrently when the parent agent emits multiple `spawn_subagent` tool calls in the same model response.

The ReAct loop has a special path for "all tool calls are `spawn_subagent`". In that case it executes them together with `futures::join_all`, bounded by a semaphore ([execution.rs](/Users/nghibui/codes/opendev/crates/opendev-agents/src/react_loop/execution.rs#L657), [execution.rs](/Users/nghibui/codes/opendev/crates/opendev-agents/src/react_loop/execution.rs#L667), [execution.rs](/Users/nghibui/codes/opendev/crates/opendev-agents/src/react_loop/execution.rs#L731)).

So this pattern is parallel:

```text
parent
  -> tool calls: spawn_subagent(A), spawn_subagent(B), spawn_subagent(C)
  -> all three futures are started
  -> tokio schedules them concurrently
  -> parent receives all results
```

This is still in-process concurrency, not subprocess-based parallelism.

## Why a Subagent Is Not a Thread

It is tempting to think "if it runs at the same time, it must be a thread". That is not how async Rust works.

What is actually true:

- Tokio has a worker-thread pool.
- Async tasks are scheduled onto those worker threads.
- A subagent is one of those async tasks.

So:

- one thread can execute many subagents over time
- one subagent does not reserve one thread for its whole lifetime
- one subagent can be paused while another runs

This is especially efficient when most work is I/O-bound.

## Why This Design Fits OpenDev

OpenDev subagents are mostly orchestrators around I/O-heavy operations:

- LLM HTTP calls
- file reads
- code search
- command execution
- event streaming to the TUI

Those operations spend a lot of time waiting. Async scheduling avoids wasting a whole thread per waiting agent.

Benefits of the current model:

- lower memory overhead per subagent
- faster fan-out to many subagents
- simpler state sharing
- easy streaming of progress events
- easy shared configuration and tool registry access
- cheap cancellation trees using child tokens

The code already reflects this by sharing the tool registry and HTTP client and giving each child its own logical execution context ([mod.rs](/Users/nghibui/codes/opendev/crates/opendev-cli/src/runtime/mod.rs#L333), [spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-tools-impl/src/agents/spawn.rs#L263), [spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-agents/src/subagents/manager/spawn.rs#L188)).

## What Isolation Exists Today

Current isolation is logical, not OS-enforced.

That means subagents are isolated by program structure:

- separate prompts
- separate message histories
- restricted tools
- permission filters
- independent cancellation
- separate child session IDs for saved history

But they still share:

- one process
- one address space
- one runtime
- shared libraries
- shared registry objects

Completed child sessions are persisted with a child `task_id` and `parent_id`, but that session separation is not the same thing as process separation ([spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-tools-impl/src/agents/spawn.rs#L233), [spawn.rs](/Users/nghibui/codes/opendev/crates/opendev-tools-impl/src/agents/spawn.rs#L281)).

## What Would Change With a Thread-Per-Agent Design

If each subagent had its own dedicated OS thread:

- the process count would still usually be one
- memory usage would go up
- idle waiting agents would still consume more scheduler/runtime overhead
- implementation would become more complex around synchronization

Thread-per-agent helps more when work is CPU-heavy and long-running.

OpenDev subagents are generally not CPU-heavy. They are mostly waiting on remote calls and tool I/O. That is why async tasks are usually a better fit here than dedicated threads.

## What Would Change With a Subprocess-Per-Agent Design

If each subagent were a child process, the machine would actually show separate processes for each agent.

Benefits:

- crash isolation
- stronger sandbox boundaries
- independent memory spaces
- easier per-agent resource limits
- better isolation for untrusted code or unstable plugins

Costs:

- process startup overhead
- IPC complexity
- more serialization/deserialization
- more complicated progress/event routing
- harder shared-state access
- higher memory use

So a subprocess model is not automatically "better". It is better when hard isolation matters more than lightweight orchestration.

## Current Backgrounding Is Separate From Subagents

There is one related concept that can cause confusion: background agents in the TUI.

Foreground subagents are still in-process child agent runs. Separately, the TUI can move agent work into a background Tokio task using `tokio::spawn(...)` ([tui_runner.rs](/Users/nghibui/codes/opendev/crates/opendev-cli/src/tui_runner.rs#L694)).

That still does not mean "new OS process". It means "another async task scheduled by Tokio".

## Common Misunderstandings

### "If it runs at the same time, it must be a thread"

Not in an async runtime. It may simply be another future being polled on the same shared worker pool.

### "If the subagent has its own session ID, it is a separate process"

No. Session identity is logical persistence. Process identity is an OS-level runtime boundary.

### "If the subagent runs a shell command, then the subagent is a subprocess"

Not exactly. The subagent itself is still in-process. One of its tools may launch a child subprocess.

### "Async means single-threaded"

Not necessarily. Tokio commonly uses a multi-threaded runtime. Async means the work is represented as resumable tasks rather than as dedicated blocking threads.

## Practical Rule of Thumb

Use this shorthand when thinking about the current architecture:

- parent agent: async task with its own state
- subagent: another async task with its own state
- process boundary: shared
- thread boundary: shared pool, not dedicated
- session boundary: separate logical conversation/history

## Summary

Today, OpenDev subagents are:

- isolated as agent state
- executed as async futures
- scheduled by Tokio
- usually concurrent only when emitted in the same tool batch
- not dedicated threads
- not separate `opendev` child processes

The best mental model is:

> One `opendev` process contains many independent agent states, and Tokio drives them forward as async work.
