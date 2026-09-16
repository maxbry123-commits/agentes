//! Types and constants for the ReAct loop.

use serde_json::Value;

use crate::traits::{AgentError, AgentResult};

/// Metrics for a single tool call execution.
#[derive(Debug, Clone)]
pub struct ToolCallMetric {
    /// Name of the tool that was called.
    pub tool_name: String,
    /// Wall-clock duration of the tool execution in milliseconds.
    pub duration_ms: u64,
    /// Whether the tool call succeeded.
    pub success: bool,
}

/// Per-iteration metrics collected during the ReAct loop.
#[derive(Debug, Clone, Default)]
pub struct IterationMetrics {
    /// 1-based iteration number.
    pub iteration: usize,
    /// Wall-clock latency of the LLM API call in milliseconds.
    pub llm_latency_ms: u64,
    /// Number of input (prompt) tokens consumed.
    pub input_tokens: u64,
    /// Number of output (completion) tokens generated.
    pub output_tokens: u64,
    /// Metrics for each tool call executed in this iteration.
    pub tool_calls: Vec<ToolCallMetric>,
    /// Total wall-clock duration of the iteration in milliseconds.
    pub total_duration_ms: u64,
}

/// Tools that are safe for parallel execution (read-only, no side effects).
pub static PARALLELIZABLE_TOOLS: &[&str] = &[
    "Read",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
    "capture_web_screenshot",
    "analyze_image",
    "TaskList",
    "search_tools",
    "find_symbol",
    "find_referencing_symbols",
];

/// Read-only tool names for consecutive-reads detection.
/// When all tool calls in an iteration are from this set, the consecutive reads
/// counter increments. After 5 consecutive read-only iterations, a nudge is injected.
pub(super) static READ_OPS: &[&str] = &[
    "Read",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
    "find_symbol",
    "TaskList",
    "read_pdf",
    "analyze_image",
];

/// Result of processing a single turn in the ReAct loop.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TurnResult {
    /// The loop should continue with the next iteration.
    Continue,
    /// The agent wants to execute tool calls.
    ToolCall {
        /// Tool call objects from the LLM response.
        tool_calls: Vec<Value>,
    },
    /// The agent has completed its task.
    Complete {
        /// Final content from the agent.
        content: String,
        /// Completion status (e.g. "success", "failed").
        status: Option<String>,
    },
    /// Maximum iterations reached.
    MaxIterations,
    /// The run was interrupted by the user.
    Interrupted,
}

/// Control flow signal returned by extracted phase functions.
///
/// Used to propagate `continue` and `return` semantics from extracted
/// functions back to the orchestrator loop in `run_inner`.
pub(super) enum LoopAction {
    /// Continue to the next iteration of the main loop.
    Continue,
    /// Return this result from `run_inner`.
    Return(Result<AgentResult, AgentError>),
}
