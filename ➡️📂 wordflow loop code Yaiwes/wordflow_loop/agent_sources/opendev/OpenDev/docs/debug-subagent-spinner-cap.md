# Debug: Subagent Spinner / Grouped Display Failures in TUI

## Problem

The original problem was that the TUI capped visible subagents at 3 and showed a `+N more agents running...` summary for the rest. That led to a follow-up grouped-display attempt, but the real user-facing bug is worse:

- after reasoning/thinking content appears,
- and the assistant says it will spawn subagents,
- the conversation context in the TUI can disappear or collapse when the `spawn_subagent` tools start.

So this doc now tracks both the original cap issue and the later failed fixes.

## What Was Tried

### Attempt 1: Remove cap logic in `spinner.rs`

**File:** `crates/opendev-tui/src/widgets/conversation/spinner.rs`

Changes made:
1. Removed `const MAX_SPINNER_SUBAGENTS: usize = 3;`
2. Removed `subagent_count`, `subagents_to_skip`, `subagent_idx` tracking variables
3. Removed the "+N more agents running…" summary block that rendered when `subagents_to_skip > 0`
4. Removed the `subagent_idx` increment and `continue` guard inside the `spawn_subagent` branch
5. Updated doc comment to remove mention of capping

**Result:** Compiles clean, clippy passes, smoke test (`echo "hello" | opendev -p "hello"`) works, but the user reports it still does not fix the visible TUI behavior.

Why it did not work:
- The cap was only one symptom.
- Changing spinner line generation alone does not help if the render path or cache/scroll math is still wrong.

### Attempt 2: Move spinner lines into scrollable conversation content

Changes made:
- `conversation/mod.rs` was changed so spinner lines are appended to the same render stream as conversation lines instead of being painted as a detached bottom overlay.
- `app/render.rs` was updated so selection and total-line math account for live spinner lines.
- `spinner.rs` was changed to group multiple active `spawn_subagent` tools into one block like `N subagents`.
- Regression tests were added to verify grouped rows appear in the rendered buffer for multiple subagents.

**Result:** The grouped spinner block does render in widget-level tests, but the user still reports the TUI can effectively blank out right after reasoning content and the `spawn_subagent` handoff.

Why it still did not fully work:
- The cache rebuild/culling logic still reasons about a message-only viewport using rough terminal-height estimates.
- During the reasoning -> tool-start transition, recent reasoning/assistant lines can be culled or pushed out incorrectly while live spinner rows are appended.
- That makes the bug look like “the TUI disappeared” even though active state still exists.

### Attempt 3: Event-sequence and cache investigation

Current hypothesis:
- The root bug is cache/render inconsistency, not just spinner formatting.
- `rebuild_cached_lines()` uses viewport culling based on terminal height, while the actual conversation viewport is smaller and also has live spinner rows appended after cached lines.
- When the agent is actively reasoning or spawning subagents, the culling policy is too aggressive for the near-bottom conversation context.

### Attempt 4: Make cache culling viewport-aware and keep more recent lines during active subagent work

Changes made:
- `app/cache.rs` was updated to compute the actual conversation viewport height instead of using raw terminal height.
- Cache culling was made more conservative while `agent_active`, `task_progress`, `active_tools`, or `active_subagents` are present.
- New regressions were added for:
  - reasoning content remaining cached when subagent tools are active,
  - short-terminal rendering of the reasoning -> "spawn 2 agents" -> active subagents transition,
  - event-driven `ReasoningContent` + `AgentChunk` + `ToolStarted` ordering.

**Result:** The new cache and render regressions pass, but the user still reports the live grouped subagent display is not showing correctly in the real session.

Why it still did not fully work:
- This helped protect recent reasoning/assistant content from being culled.
- It did not explain why the grouped active subagent block could still fail to appear at all.
- That means the issue is not only cache visibility; there is also likely a timing/render scheduling problem.

### Attempt 5: Group completed `spawn_subagent` transcript entries

What was observed:
- Some screenshots were not showing the live spinner area.
- They were showing the completed conversation transcript after many `spawn_subagent` calls had already finished.
- That path bypasses `spinner.rs` entirely.

Changes made:
- `app/event_dispatch.rs` was updated so consecutive finished `spawn_subagent` `ToolResult`s aggregate into one synthetic grouped transcript entry instead of one `DisplayMessage` per subagent.
- `formatters/tool_registry.rs` was updated to render the synthetic grouped entry header as `N subagents`.
- `widgets/conversation/mod.rs` got a render regression to verify the grouped completed transcript path.

**Result:** Completed subagent tool results can now be grouped in tests, but the user still reports the live TUI state can be empty or not show the expected active grouped display.

Why it still did not fully work:
- This only addresses the finished transcript path.
- It does not guarantee the live active state is ever rendered before the tools finish.

### Attempt 6: Render sooner instead of draining the whole event burst first

New hypothesis:
- The app loop may be swallowing the entire burst of `ToolStarted`, `SubagentStarted`, `ToolResult`, and `ToolFinished` events before the next draw.
- If that happens, the live grouped state can be skipped completely even if the spinner-grouping logic is correct.

Changes made:
- `app/mod.rs` was changed so the main loop stops draining queued events early when it hits render-relevant transitions:
  - `ReasoningContent`
  - `AgentChunk` / `AgentMessage`
  - `ToolStarted` / `ToolResult` / `ToolFinished`
  - `SubagentStarted` / `SubagentToolCall` / `SubagentToolComplete` / `SubagentFinished`
- App-level tests were added to verify those events force a render opportunity before the queue is fully drained.

**Result:** The new app tests pass, and this is the strongest explanation so far for why the active grouped display may never appear in the TUI. However, the user still reports that the real-world session does not show the expected grouped live state.

Why it still did not fully work:
- The test only verifies the decision policy in the event loop, not a full end-to-end replay of the actual production event burst.
- The underlying producer may still be sending events in an order or at a cadence that bypasses the intended visible intermediate state.
- There may still be another live-state render path that does not go through the assumptions captured in the current tests.

## What Is Confirmed Not To Be Enough

- Removing the `3`-subagent cap in `spinner.rs` alone.
- Grouping subagent rows in `spinner.rs` alone.
- Making spinner lines scrollable without also fixing cache culling and total-content assumptions.
- Making cache culling more conservative, by itself.
- Grouping only the completed transcript path.
- Rendering earlier in the app loop, by itself, based on the current test coverage.

## Current Direction

The current status is:

- active spinner grouping exists in code,
- completed transcript grouping exists in code,
- cache culling is more conservative,
- the app loop now tries to render before draining visible tool/subagent bursts,
- but the real user session still does not show the expected grouped live state.

The next debugging step should focus on reproducing the exact real event stream, not adding more speculative grouping logic.

Specifically:

- Record or replay the exact event sequence for a failing run with multiple `spawn_subagent` calls.
- Confirm whether the live phase actually produces:
  - multiple concurrent `ToolStarted(spawn_subagent)` events,
  - matching `SubagentStarted` events before completion,
  - at least one draw opportunity before all tools finish.
- If the real event stream never exposes multiple concurrent active subagents to the TUI, then the grouping bug is upstream of `spinner.rs`.
- If the event stream does expose them, then the next fix should target the exact mismatch between recorded events and rendered state, not broad render heuristics.

## Key Code Paths

- **Spinner build / grouping:** `crates/opendev-tui/src/widgets/conversation/spinner.rs`
- **Conversation render path:** `crates/opendev-tui/src/widgets/conversation/mod.rs`
- **Selection / total-line math:** `crates/opendev-tui/src/app/render.rs`
- **Cache rebuild / viewport culling:** `crates/opendev-tui/src/app/cache.rs`
- **Reasoning + tool event order:** `crates/opendev-tui/src/app/event_dispatch.rs`
- **Event loop drain/render policy:** `crates/opendev-tui/src/app/mod.rs`
