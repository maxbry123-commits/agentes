//! Tool classification, formatting, and error categorization utilities.

use serde_json::Value;

use super::super::ReactLoop;

impl ReactLoop {
    /// Check if a set of tool calls are all parallelizable.
    pub fn all_parallelizable(&self, tool_calls: &[Value]) -> bool {
        if tool_calls.len() <= 1 {
            return false;
        }

        tool_calls.iter().all(|tc| {
            let name = tc
                .get("function")
                .and_then(|f| f.get("name"))
                .and_then(|n| n.as_str())
                .unwrap_or("");
            self.parallelizable.contains(name) && !matches!(name, "TaskStop" | "task_complete")
        })
    }

    /// Check if a tool call is for task completion.
    pub fn is_task_complete(tool_call: &Value) -> bool {
        tool_call
            .get("function")
            .and_then(|f| f.get("name"))
            .and_then(|n| n.as_str())
            .is_some_and(|n| matches!(n, "TaskStop" | "task_complete"))
    }

    /// Extract the summary and status from a task_complete tool call.
    pub fn extract_task_complete_args(tool_call: &Value) -> (String, String) {
        let args_str = tool_call
            .get("function")
            .and_then(|f| f.get("arguments"))
            .and_then(|a| a.as_str())
            .unwrap_or("{}");

        let args: Value = serde_json::from_str(args_str).unwrap_or_default();
        let summary = args
            .get("result")
            .or_else(|| args.get("summary"))
            .and_then(|s| s.as_str())
            .unwrap_or("Task completed")
            .to_string();
        let status = args
            .get("status")
            .and_then(|s| s.as_str())
            .unwrap_or("success")
            .to_string();

        (summary, status)
    }

    /// Format a tool execution result into a string for the message history.
    pub fn format_tool_result(_tool_name: &str, result: &Value) -> String {
        let success = result
            .get("success")
            .and_then(|s| s.as_bool())
            .unwrap_or(false);

        let base = if success {
            let output = result
                .get("separate_response")
                .or_else(|| result.get("output"))
                .and_then(|o| o.as_str())
                .unwrap_or("");

            let completion_status = result.get("completion_status").and_then(|s| s.as_str());

            if let Some(status) = completion_status {
                format!("[completion_status={status}]\n{output}")
            } else {
                output.to_string()
            }
        } else {
            let error = result
                .get("error")
                .and_then(|e| e.as_str())
                .unwrap_or("Tool execution failed");
            format!("Error: {error}")
        };

        // Append LLM-only suffix if present (hidden from UI, visible to LLM)
        if let Some(suffix) = result.get("llm_suffix").and_then(|s| s.as_str()) {
            format!("{base}\n\n{suffix}")
        } else {
            base
        }
    }

    /// Classify an error for targeted nudge selection.
    pub fn classify_error(error_text: &str) -> &'static str {
        let lower = error_text.to_lowercase();
        if lower.contains("permission denied") {
            "permission_error"
        } else if lower.contains("old_content") || lower.contains("old content") {
            "edit_mismatch"
        } else if lower.contains("no such file") || lower.contains("not found") {
            "file_not_found"
        } else if lower.contains("syntax") {
            "syntax_error"
        } else if lower.contains("429") || lower.contains("rate limit") {
            "rate_limit"
        } else if lower.contains("timeout") || lower.contains("timed out") {
            "timeout"
        } else {
            "generic"
        }
    }
}
