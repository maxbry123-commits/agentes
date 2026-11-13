//! JSONL reader for sidechain transcripts.

use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use serde_json::Value;
use tracing::warn;

use super::types::{EntryKind, TranscriptEntry};

/// Reader for sidechain agent transcripts.
///
/// Opens the JSONL file and provides lazy iteration. Malformed lines
/// are skipped with a warning (handles partial writes gracefully).
pub struct SidechainReader {
    path: PathBuf,
}

impl SidechainReader {
    /// Open a transcript for reading.
    ///
    /// Path: `{session_dir}/agents/{agent_id}.jsonl`
    pub fn open(session_dir: &Path, agent_id: &str) -> io::Result<Self> {
        let path = session_dir.join("agents").join(format!("{agent_id}.jsonl"));
        if !path.exists() {
            return Err(io::Error::new(
                io::ErrorKind::NotFound,
                format!("Sidechain transcript not found: {}", path.display()),
            ));
        }
        Ok(Self { path })
    }

    /// Iterate all valid entries, skipping malformed lines.
    pub fn entries(&self) -> io::Result<Vec<TranscriptEntry>> {
        let content = fs::read_to_string(&self.path)?;
        let mut entries = Vec::new();
        for (line_num, line) in content.lines().enumerate() {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }
            match serde_json::from_str::<TranscriptEntry>(trimmed) {
                Ok(entry) => entries.push(entry),
                Err(e) => {
                    warn!(
                        path = %self.path.display(),
                        line = line_num + 1,
                        error = %e,
                        "Skipping malformed sidechain line"
                    );
                }
            }
        }
        Ok(entries)
    }

    /// Return the last `n` entries.
    pub fn tail(&self, n: usize) -> io::Result<Vec<TranscriptEntry>> {
        let entries = self.entries()?;
        let start = entries.len().saturating_sub(n);
        Ok(entries.into_iter().skip(start).collect())
    }

    /// Reconstruct LLM-compatible message history from the transcript.
    ///
    /// Filters out:
    /// - Empty assistant messages (whitespace-only content)
    /// - Orphaned tool calls (tool_use without a matching tool_result)
    /// - System prompt entries (not part of message history)
    /// - Token usage entries
    /// - State change entries
    pub fn into_messages(&self) -> io::Result<Vec<Value>> {
        let entries = self.entries()?;
        let mut messages: Vec<Value> = Vec::new();
        let mut pending_tool_call_ids: Vec<String> = Vec::new();

        for entry in entries {
            match entry.entry {
                EntryKind::AssistantMsg {
                    ref content,
                    ref tool_calls,
                } => {
                    // Skip whitespace-only assistant messages
                    if content.trim().is_empty() && tool_calls.is_none() {
                        continue;
                    }

                    let mut msg = serde_json::json!({
                        "role": "assistant",
                        "content": content,
                    });

                    if let Some(calls) = tool_calls {
                        msg["tool_calls"] = serde_json::json!(calls);
                        // Track pending tool call IDs
                        for call in calls {
                            if let Some(id) = call.get("id").and_then(|v| v.as_str()) {
                                pending_tool_call_ids.push(id.to_string());
                            }
                        }
                    }
                    messages.push(msg);
                }
                EntryKind::ToolResult {
                    ref call_id,
                    ref name,
                    ref output,
                    ok,
                } => {
                    // Remove from pending (matched)
                    pending_tool_call_ids.retain(|id| id != call_id);

                    messages.push(serde_json::json!({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": name,
                        "content": output,
                        "_success": ok,
                    }));
                }
                // Skip non-message entries
                EntryKind::SystemPrompt { .. }
                | EntryKind::Tokens { .. }
                | EntryKind::StateChange { .. } => {}
            }
        }

        // Filter out orphaned tool calls (tool_use without matching tool_result)
        if !pending_tool_call_ids.is_empty() {
            messages.retain(|msg| {
                if msg.get("role").and_then(|r| r.as_str()) == Some("assistant")
                    && let Some(calls) = msg.get("tool_calls").and_then(|c| c.as_array())
                {
                    // Keep the message if it has resolved tool calls or non-empty content
                    let has_resolved = calls.iter().any(|c| {
                        c.get("id")
                            .and_then(|id| id.as_str())
                            .is_some_and(|id| !pending_tool_call_ids.contains(&id.to_string()))
                    });
                    let has_content = msg
                        .get("content")
                        .and_then(|c| c.as_str())
                        .is_some_and(|c| !c.trim().is_empty());
                    return has_resolved || has_content;
                }
                true
            });
        }

        Ok(messages)
    }

    /// Path to the transcript file.
    pub fn path(&self) -> &Path {
        &self.path
    }
}

impl std::fmt::Debug for SidechainReader {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("SidechainReader")
            .field("path", &self.path)
            .finish()
    }
}
