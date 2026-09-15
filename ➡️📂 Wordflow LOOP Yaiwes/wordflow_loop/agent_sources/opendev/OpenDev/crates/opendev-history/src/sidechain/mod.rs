//! Sidechain agent transcripts.
//!
//! Stores agent conversations as append-only JSONL files for:
//! - Resume after interruption or backgrounding
//! - Lazy loading in the TUI detail view
//! - Persistent agent history across sessions
//!
//! Storage: `~/.opendev/sessions/{session_id}/agents/{agent_id}.jsonl`

mod reader;
mod types;
mod writer;

pub use reader::SidechainReader;
pub use types::*;
pub use writer::SidechainWriter;

#[cfg(test)]
#[path = "tests.rs"]
mod tests;
