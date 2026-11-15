//! Per-iteration event emitter with display-suppression logic.

use std::sync::atomic::{AtomicBool, Ordering};

use opendev_tools_core::ToolResult;

/// Per-iteration event emitter that centralizes display-suppression logic.
///
/// During normal iterations, all events pass through to the callback.
/// During completion-nudge verification iterations, text and reasoning
/// events are silently dropped while tool events still pass through.
///
/// This struct is the ONLY way text/reasoning should be emitted to the
/// callback from the react loop. Do NOT call event_callback directly
/// for text/reasoning — always go through the emitter.
pub(super) struct IterationEmitter<'a> {
    cb: Option<&'a dyn crate::traits::AgentEventCallback>,
    suppress_content: bool,
    text_emitted: AtomicBool,
    reasoning_emitted: AtomicBool,
}

impl<'a> IterationEmitter<'a> {
    pub(super) fn new(
        cb: Option<&'a dyn crate::traits::AgentEventCallback>,
        suppress_content: bool,
    ) -> Self {
        Self {
            cb,
            suppress_content,
            text_emitted: AtomicBool::new(false),
            reasoning_emitted: AtomicBool::new(false),
        }
    }

    /// Emit a streaming text chunk. Suppressed during nudge iterations.
    pub(super) fn emit_text(&self, text: &str) {
        if !self.suppress_content
            && let Some(cb) = self.cb
        {
            cb.on_agent_chunk(text);
            self.text_emitted.store(true, Ordering::Relaxed);
        }
    }

    /// Emit reasoning content. Suppressed during nudge iterations.
    pub(super) fn emit_reasoning(&self, text: &str) {
        if !self.suppress_content
            && let Some(cb) = self.cb
        {
            cb.on_reasoning(text);
            self.reasoning_emitted.store(true, Ordering::Relaxed);
        }
    }

    /// Emit reasoning block start (separator between interleaved blocks).
    pub(super) fn emit_reasoning_block_start(&self) {
        if !self.suppress_content
            && let Some(cb) = self.cb
        {
            cb.on_reasoning_block_start();
        }
    }

    /// Emit text if streaming didn't deliver it (non-streaming fallback).
    pub(super) fn emit_text_if_not_streamed(&self, content: &str) {
        if !self.suppress_content
            && !content.is_empty()
            && !self.text_emitted.load(Ordering::Relaxed)
            && let Some(cb) = self.cb
        {
            cb.on_agent_chunk(content);
            self.text_emitted.store(true, Ordering::Relaxed);
        }
    }

    /// Emit reasoning from response body if streaming didn't already deliver it.
    pub(super) fn emit_reasoning_if_not_streamed(&self, reasoning: &str) {
        if !self.suppress_content
            && !reasoning.is_empty()
            && !self.reasoning_emitted.load(Ordering::Relaxed)
            && let Some(cb) = self.cb
        {
            cb.on_reasoning(reasoning);
            self.reasoning_emitted.store(true, Ordering::Relaxed);
        }
    }

    // --- Tool events: NEVER suppressed ---

    pub(super) fn emit_tool_started(
        &self,
        id: &str,
        name: &str,
        args: &std::collections::HashMap<String, serde_json::Value>,
    ) {
        if let Some(cb) = self.cb {
            cb.on_tool_started(id, name, args);
        }
    }

    pub(super) fn emit_tool_finished(&self, id: &str, success: bool) {
        if let Some(cb) = self.cb {
            cb.on_tool_finished(id, success);
        }
    }

    pub(super) fn emit_tool_result(&self, id: &str, name: &str, output: &str, success: bool) {
        if let Some(cb) = self.cb {
            cb.on_tool_result(id, name, output, success);
        }
    }

    pub(super) fn emit_token_usage(&self, input: u64, output: u64) {
        if let Some(cb) = self.cb {
            cb.on_token_usage(input, output);
        }
    }

    pub(super) fn emit_context_usage(&self, pct: f64) {
        if let Some(cb) = self.cb {
            cb.on_context_usage(pct);
        }
    }
}

/// Build the display string for a tool result sent to the TUI.
///
/// On success: return the output text.
/// On failure: return the error message followed by the output (stdout/stderr)
/// so the user can see *why* the command failed, not just the exit code.
pub(super) fn tool_result_display_output(result: &ToolResult) -> String {
    if result.success {
        return result.output.as_deref().unwrap_or("").to_string();
    }
    let error = result.error.as_deref().unwrap_or("Tool execution failed");
    match result.output.as_deref() {
        Some(output) if !output.is_empty() => format!("{error}\n{output}"),
        _ => error.to_string(),
    }
}
