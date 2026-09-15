//! Append-only JSONL writer for sidechain transcripts.

use std::fs::{self, File, OpenOptions};
use std::io::{self, BufWriter, Write};
use std::path::{Path, PathBuf};

use tracing::warn;

use super::types::{EntryKind, TranscriptEntry};

/// Maximum sidechain file size before we log a warning (50 MB).
const MAX_FILE_SIZE: u64 = 50_000_000;

fn now_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

/// Append-only writer for agent sidechain transcripts.
///
/// Each call to [`append`] serializes one JSONL line and flushes.
/// Writes are fire-and-forget — errors are logged but don't stop
/// the agent from running.
pub struct SidechainWriter {
    file: BufWriter<File>,
    seq: u64,
    bytes_written: u64,
    path: PathBuf,
    warned_size: bool,
}

impl SidechainWriter {
    /// Create a new writer. Creates parent directories if needed.
    ///
    /// Path: `{session_dir}/agents/{agent_id}.jsonl`
    pub fn new(session_dir: &Path, agent_id: &str) -> io::Result<Self> {
        let dir = session_dir.join("agents");
        fs::create_dir_all(&dir)?;

        let path = dir.join(format!("{agent_id}.jsonl"));

        // Get existing file size for byte tracking
        let existing_size = fs::metadata(&path).map(|m| m.len()).unwrap_or(0);

        // Count existing lines for sequence numbering
        let existing_seq = if existing_size > 0 {
            let content = fs::read_to_string(&path).unwrap_or_default();
            content.lines().count() as u64
        } else {
            0
        };

        let file = OpenOptions::new().create(true).append(true).open(&path)?;

        Ok(Self {
            file: BufWriter::new(file),
            seq: existing_seq,
            bytes_written: existing_size,
            path,
            warned_size: false,
        })
    }

    /// Append a transcript entry. Fire-and-forget on error.
    pub fn append(&mut self, entry: EntryKind) -> io::Result<()> {
        if self.bytes_written > MAX_FILE_SIZE && !self.warned_size {
            warn!(
                path = %self.path.display(),
                bytes = self.bytes_written,
                "Sidechain transcript exceeding 50MB"
            );
            self.warned_size = true;
        }

        let record = TranscriptEntry {
            seq: self.seq,
            ts: now_ms(),
            entry,
        };

        let line = serde_json::to_string(&record)?;
        self.file.write_all(line.as_bytes())?;
        self.file.write_all(b"\n")?;
        self.file.flush()?;

        self.seq += 1;
        self.bytes_written += line.len() as u64 + 1;
        Ok(())
    }

    /// Path to the transcript file.
    pub fn path(&self) -> &Path {
        &self.path
    }
}

impl std::fmt::Debug for SidechainWriter {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("SidechainWriter")
            .field("path", &self.path)
            .field("seq", &self.seq)
            .field("bytes_written", &self.bytes_written)
            .finish()
    }
}
