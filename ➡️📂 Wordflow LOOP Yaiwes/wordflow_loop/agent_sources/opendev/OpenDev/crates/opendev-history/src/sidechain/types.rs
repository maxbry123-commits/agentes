//! Types for sidechain agent transcripts.

use serde::{Deserialize, Serialize};
use serde_json::Value;

/// A single entry in a sidechain transcript (one JSONL line).
#[derive(Debug, Serialize, Deserialize)]
pub struct TranscriptEntry {
    /// Monotonically increasing sequence number within this transcript.
    pub seq: u64,
    /// Timestamp in milliseconds since epoch.
    pub ts: u64,
    /// The entry payload.
    #[serde(flatten)]
    pub entry: EntryKind,
}

/// The kind of transcript entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "k")]
pub enum EntryKind {
    /// The system prompt given to the agent.
    #[serde(rename = "sys")]
    SystemPrompt { content: String },

    /// An assistant (LLM) response, possibly with tool calls.
    #[serde(rename = "ast")]
    AssistantMsg {
        content: String,
        #[serde(skip_serializing_if = "Option::is_none")]
        tool_calls: Option<Vec<Value>>,
    },

    /// Result from a tool execution.
    #[serde(rename = "tr")]
    ToolResult {
        call_id: String,
        name: String,
        output: String,
        ok: bool,
    },

    /// Token usage snapshot.
    #[serde(rename = "tok")]
    Tokens { inp: u64, out: u64 },

    /// Task state change.
    #[serde(rename = "st")]
    StateChange { from: String, to: String },
}
