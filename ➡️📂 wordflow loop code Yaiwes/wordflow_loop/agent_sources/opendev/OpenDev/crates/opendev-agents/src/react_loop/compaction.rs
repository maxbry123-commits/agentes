//! Context compaction and artifact recording helpers.

use std::sync::Mutex;

use serde_json::Value;
use tracing::{info, warn};

use crate::llm_calls::LlmCaller;
use opendev_context::{ArtifactIndex, ContextCompactor, OptimizationLevel};
use opendev_http::adapted_client::AdaptedClient;
use opendev_tools_core::ToolResult;

/// Convert `Vec<Value>` messages to `Vec<ApiMessage>` for the compactor.
///
/// Only includes `Value::Object` entries; non-object values are skipped.
pub(super) fn values_to_api_messages(
    values: &[Value],
) -> Vec<opendev_context::compaction::ApiMessage> {
    values
        .iter()
        .filter_map(|v| v.as_object().cloned())
        .collect()
}

/// Apply staged context compaction based on current usage level.
///
/// Mirrors Python's `_maybe_compact()` — checks context usage percentage
/// and applies the appropriate optimization strategy:
/// - 70%: Warning only
/// - 80%: Mask old tool results with compact refs
/// - 85%: Prune old tool outputs
/// - 90%: Aggressive masking (fewer recent results preserved)
/// - 99%: Full compaction (summarize middle messages)
///
/// Returns `true` if LLM-powered compaction is needed (99% stage).
#[allow(clippy::ptr_arg)] // needs Vec for clear()/extend() in Compact branch caller
pub(super) fn apply_staged_compaction(
    compactor: &Mutex<ContextCompactor>,
    messages: &mut Vec<Value>,
) -> bool {
    let api_msgs = values_to_api_messages(messages);
    let level = if let Ok(mut comp) = compactor.lock() {
        comp.check_usage(&api_msgs, "")
    } else {
        return false;
    };

    match level {
        OptimizationLevel::None | OptimizationLevel::Warning => false,
        OptimizationLevel::Mask | OptimizationLevel::Aggressive => {
            // Convert to ApiMessage, apply masking + early summarization, convert back
            let mut api_msgs = values_to_api_messages(messages);
            if let Ok(comp) = compactor.lock() {
                comp.summarize_verbose_tool_outputs(&mut api_msgs);
                comp.mask_old_observations(&mut api_msgs, level);
            }
            // Write masked messages back
            let mut api_idx = 0;
            for msg in messages.iter_mut() {
                if msg.is_object() && api_idx < api_msgs.len() {
                    *msg = Value::Object(api_msgs[api_idx].clone());
                    api_idx += 1;
                }
            }
            // Invalidate stale calibration after content modification so the next
            // update_token_count recalculates from the actual reduced messages.
            if let Ok(mut comp) = compactor.lock() {
                comp.invalidate_calibration();
            }
            false
        }
        OptimizationLevel::Prune => {
            let mut api_msgs = values_to_api_messages(messages);
            if let Ok(comp) = compactor.lock() {
                comp.summarize_verbose_tool_outputs(&mut api_msgs);
                comp.mask_old_observations(&mut api_msgs, OptimizationLevel::Mask);
                comp.prune_old_tool_outputs(&mut api_msgs);
            }
            let mut api_idx = 0;
            for msg in messages.iter_mut() {
                if msg.is_object() && api_idx < api_msgs.len() {
                    *msg = Value::Object(api_msgs[api_idx].clone());
                    api_idx += 1;
                }
            }
            // Invalidate stale calibration after content modification.
            if let Ok(mut comp) = compactor.lock() {
                comp.invalidate_calibration();
            }
            false
        }
        OptimizationLevel::Compact => true,
    }
}

/// Perform LLM-powered compaction: build payload, call the compact model,
/// and replace messages with the summarized version.
///
/// Falls back to `compact()` (basic string summarization) if the LLM call
/// fails or if no compact model is configured.
pub(super) async fn do_llm_compaction(
    compactor: &Mutex<ContextCompactor>,
    messages: &mut Vec<Value>,
    caller: &LlmCaller,
    http_client: &AdaptedClient,
) {
    use crate::prompts::embedded::SYSTEM_COMPACTION;

    let api_msgs = values_to_api_messages(messages);
    let compact_model = &caller.config.model;

    // Try to build the LLM compaction payload
    let build_result = if let Ok(comp) = compactor.lock() {
        comp.build_compaction_payload(&api_msgs, SYSTEM_COMPACTION, compact_model)
    } else {
        None
    };

    let Some((payload, _middle_count, keep_recent)) = build_result else {
        // Too few messages or lock failed — fallback to basic compact
        if let Ok(mut comp) = compactor.lock() {
            let compacted = comp.compact(api_msgs, "");
            messages.clear();
            messages.extend(compacted.into_iter().map(Value::Object));
        }
        return;
    };

    // Call the LLM via the adapted client (uses provider adapters, auth, retries)
    let summary_text: Option<String> = match http_client.post_json(&payload, None).await {
        Ok(result) => result
            .body
            .as_ref()
            .and_then(|body| body.pointer("/choices/0/message/content"))
            .and_then(|v| v.as_str())
            .map(|s| s.to_string()),
        Err(e) => {
            warn!("LLM compaction request failed: {e}, using fallback");
            None
        }
    };

    let summary = match summary_text {
        Some(text) if !text.is_empty() => {
            info!(
                model = compact_model,
                summary_len = text.len(),
                "LLM compaction succeeded"
            );
            text
        }
        _ => {
            warn!("LLM compaction returned empty or failed, using fallback");
            ContextCompactor::fallback_summary(
                &api_msgs[1..api_msgs.len().saturating_sub(keep_recent)],
            )
        }
    };

    // Apply the compaction
    if let Ok(mut comp) = compactor.lock() {
        let compacted = comp.apply_llm_compaction(api_msgs, &summary, keep_recent);
        messages.clear();
        messages.extend(compacted.into_iter().map(Value::Object));
    }
}

/// Record file operations in the artifact index after successful tool execution.
///
/// Mirrors Python's `_record_artifact()` — tracks read/write/edit operations
/// so the artifact index survives compaction and the agent retains file awareness.
pub(super) fn record_artifact(
    artifact_index: &Mutex<ArtifactIndex>,
    tool_name: &str,
    args: &Value,
    result: &ToolResult,
) {
    let file_path = match args.get("file_path").and_then(|v| v.as_str()) {
        Some(p) => p,
        None => return,
    };

    let (operation, details) = match tool_name {
        "Read" | "read_file" => {
            let line_count = result
                .output
                .as_deref()
                .map(|o| o.lines().count())
                .unwrap_or(0);
            ("read", format!("{line_count} lines"))
        }
        "Write" | "write_file" => {
            let line_count = args
                .get("content")
                .and_then(|v| v.as_str())
                .map(|c| c.lines().count())
                .unwrap_or(0);
            ("created", format!("{line_count} lines"))
        }
        "Edit" | "edit_file" => ("modified", "edit".to_string()),
        _ => return,
    };

    if let Ok(mut index) = artifact_index.lock() {
        index.record(file_path, operation, &details);
    }
}
