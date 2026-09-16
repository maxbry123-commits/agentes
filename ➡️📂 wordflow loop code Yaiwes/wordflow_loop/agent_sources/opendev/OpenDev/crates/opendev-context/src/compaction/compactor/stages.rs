//! Staged optimization methods for the context compactor.
//!
//! Implements observation masking, tool output pruning, and verbose output
//! summarization — the incremental compaction stages that run before
//! full compaction is triggered.

use std::collections::{HashMap, HashSet};

use tracing::info;

use super::super::levels::OptimizationLevel;
use super::super::preview::summarize_tool_output;
use super::super::tokens::count_tokens;
use super::super::{
    ApiMessage, PROTECTED_TOOL_TYPES, PRUNE_MIN_LENGTH, PRUNE_PROTECTED_TOKENS,
    TOOL_OUTPUT_SUMMARIZE_THRESHOLD,
};
use super::ContextCompactor;

impl ContextCompactor {
    /// Build a mapping from tool_call_id to tool function name.
    pub fn build_tool_call_map(messages: &[ApiMessage]) -> HashMap<String, String> {
        let mut tc_map = HashMap::new();
        for msg in messages {
            if msg.get("role").and_then(|v| v.as_str()) != Some("assistant") {
                continue;
            }
            if let Some(tool_calls) = msg.get("tool_calls").and_then(|v| v.as_array()) {
                for tc in tool_calls {
                    let tc_id = tc.get("id").and_then(|v| v.as_str()).unwrap_or("");
                    let func_name = tc
                        .get("function")
                        .and_then(|f| f.get("name"))
                        .and_then(|n| n.as_str())
                        .unwrap_or("");
                    if !tc_id.is_empty() && !func_name.is_empty() {
                        tc_map.insert(tc_id.to_string(), func_name.to_string());
                    }
                }
            }
        }
        tc_map
    }

    /// Replace old tool result messages with compact references.
    pub fn mask_old_observations(&self, messages: &mut [ApiMessage], level: OptimizationLevel) {
        let recent_threshold = match level {
            OptimizationLevel::Mask => 6,
            OptimizationLevel::Aggressive => 3,
            _ => return,
        };

        // Find all tool result message indices
        let tool_indices: Vec<usize> = messages
            .iter()
            .enumerate()
            .filter(|(_, msg)| msg.get("role").and_then(|v| v.as_str()) == Some("tool"))
            .map(|(i, _)| i)
            .collect();

        if tool_indices.len() <= recent_threshold {
            return;
        }

        let tc_map = Self::build_tool_call_map(messages);
        let old_count = tool_indices.len() - recent_threshold;
        let old_indices: HashSet<usize> = tool_indices[..old_count].iter().copied().collect();
        let mut masked_count = 0u32;

        for &i in &old_indices {
            let content = messages[i]
                .get("content")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();
            if content.starts_with("[ref:") {
                continue;
            }
            let tool_call_id = messages[i]
                .get("tool_call_id")
                .and_then(|v| v.as_str())
                .unwrap_or("?")
                .to_string();
            let tool_name = tc_map.get(&tool_call_id).map(|s| s.as_str()).unwrap_or("");
            if PROTECTED_TOOL_TYPES.contains(&tool_name) {
                continue;
            }
            messages[i].insert(
                "content".into(),
                serde_json::Value::String(format!(
                    "[ref: tool result {tool_call_id} — see history]"
                )),
            );
            masked_count += 1;
        }

        if masked_count > 0 {
            info!(
                "Masked {} old tool results (level={}, kept recent {})",
                masked_count,
                level.as_str(),
                recent_threshold,
            );
        }
    }

    /// Strip old tool outputs while protecting the most recent ones.
    pub fn prune_old_tool_outputs(&self, messages: &mut [ApiMessage]) {
        // Collect tool result indices in reverse order
        let mut tool_indices: Vec<usize> = Vec::new();
        for i in (0..messages.len()).rev() {
            if messages[i].get("role").and_then(|v| v.as_str()) == Some("tool") {
                tool_indices.push(i);
            }
        }

        if tool_indices.is_empty() {
            return;
        }

        let tc_map = Self::build_tool_call_map(messages);
        let mut protected_tokens: u64 = 0;
        let mut protected_indices: HashSet<usize> = HashSet::new();

        for &idx in &tool_indices {
            let content = messages[idx]
                .get("content")
                .and_then(|v| v.as_str())
                .unwrap_or("");
            if content.starts_with("[ref:")
                || content == "[pruned]"
                || content.starts_with("[summary:")
            {
                continue;
            }
            let tool_call_id = messages[idx]
                .get("tool_call_id")
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let tool_name = tc_map.get(tool_call_id).map(|s| s.as_str()).unwrap_or("");
            if PROTECTED_TOOL_TYPES.contains(&tool_name) {
                protected_indices.insert(idx);
                continue;
            }
            // Small outputs aren't worth pruning — keep them
            if content.len() < PRUNE_MIN_LENGTH {
                protected_indices.insert(idx);
                continue;
            }
            let token_estimate = count_tokens(content) as u64;
            if protected_tokens + token_estimate <= PRUNE_PROTECTED_TOKENS {
                protected_tokens += token_estimate;
                protected_indices.insert(idx);
            }
        }

        let mut pruned_count = 0u32;
        for &idx in &tool_indices {
            if protected_indices.contains(&idx) {
                continue;
            }
            let content = messages[idx]
                .get("content")
                .and_then(|v| v.as_str())
                .unwrap_or("");
            if content.starts_with("[ref:")
                || content == "[pruned]"
                || content.starts_with("[summary:")
            {
                continue;
            }
            // Small outputs survive even without budget
            if content.len() < PRUNE_MIN_LENGTH {
                continue;
            }
            messages[idx].insert(
                "content".into(),
                serde_json::Value::String("[pruned]".into()),
            );
            pruned_count += 1;
        }

        if pruned_count > 0 {
            info!(
                "Pruned {} old tool outputs (protected {}, ~{}K tokens kept)",
                pruned_count,
                protected_indices.len(),
                protected_tokens / 1000,
            );
        }
    }

    /// Summarize verbose tool outputs (>500 chars) with 2-3 line summaries.
    ///
    /// Replaces long tool outputs with a compact summary preserving the tool
    /// name, success/failure status, and first/last lines. Protected tool
    /// types and already-processed outputs are skipped.
    pub fn summarize_verbose_tool_outputs(&self, messages: &mut [ApiMessage]) {
        let tc_map = Self::build_tool_call_map(messages);
        let mut summarized_count = 0u32;

        for msg in messages.iter_mut() {
            if msg.get("role").and_then(|v| v.as_str()) != Some("tool") {
                continue;
            }
            let content = msg
                .get("content")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();

            if content.len() <= TOOL_OUTPUT_SUMMARIZE_THRESHOLD {
                continue;
            }
            if content.starts_with("[ref:")
                || content == "[pruned]"
                || content.starts_with("[summary:")
            {
                continue;
            }

            let tool_call_id = msg
                .get("tool_call_id")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();
            let tool_name = tc_map
                .get(&tool_call_id)
                .map(|s| s.as_str())
                .unwrap_or("tool");

            if PROTECTED_TOOL_TYPES.contains(&tool_name) {
                continue;
            }

            let summary = summarize_tool_output(tool_name, &content);
            msg.insert("content".into(), serde_json::Value::String(summary));
            summarized_count += 1;
        }

        if summarized_count > 0 {
            info!(
                "Summarized {} verbose tool outputs (>{} chars)",
                summarized_count, TOOL_OUTPUT_SUMMARIZE_THRESHOLD,
            );
        }
    }
}
