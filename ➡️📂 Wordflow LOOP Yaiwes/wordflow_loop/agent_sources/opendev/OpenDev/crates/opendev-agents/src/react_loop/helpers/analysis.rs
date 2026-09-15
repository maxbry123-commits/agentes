//! Subagent analysis helpers.

use serde_json::Value;

use super::super::ReactLoop;

impl ReactLoop {
    /// Count the total number of individual tool calls in a subagent result.
    ///
    /// Each assistant message may contain multiple parallel tool calls (e.g., 5
    /// file reads in one turn). This counts every individual tool call, not just
    /// the number of assistant turns that have tool calls.
    pub fn count_subagent_tool_calls(messages: &[Value]) -> usize {
        messages
            .iter()
            .filter(|msg| msg.get("role").and_then(|r| r.as_str()) == Some("assistant"))
            .filter_map(|msg| msg.get("tool_calls").and_then(|tc| tc.as_array()))
            .map(|arr| arr.len())
            .sum()
    }

    /// Count the number of assistant turns that contain tool calls.
    ///
    /// Used for shallow subagent detection: if a subagent only made <=1 tool
    /// turn, the parent could have done it directly.
    pub fn count_subagent_tool_turns(messages: &[Value]) -> usize {
        messages
            .iter()
            .filter(|msg| {
                msg.get("role").and_then(|r| r.as_str()) == Some("assistant")
                    && msg
                        .get("tool_calls")
                        .and_then(|tc| tc.as_array())
                        .map(|a| !a.is_empty())
                        .unwrap_or(false)
            })
            .count()
    }

    /// Generate a shallow subagent warning suffix if applicable.
    ///
    /// Returns `Some(warning)` if the subagent made <=1 tool turns, `None` otherwise.
    pub fn shallow_subagent_warning(result_messages: &[Value], success: bool) -> Option<String> {
        if !success {
            return None;
        }
        let tool_turn_count = Self::count_subagent_tool_turns(result_messages);
        if tool_turn_count <= 1 {
            Some(format!(
                "\n\n[SHALLOW SUBAGENT WARNING] This subagent only made \
                 {tool_turn_count} tool call(s). Spawning a subagent for a task \
                 that requires ≤1 tool call is wasteful — you should have used a \
                 direct tool call instead. For future similar tasks, use read_file, \
                 search, or list_files directly rather than spawning a subagent."
            ))
        } else {
            None
        }
    }
}
