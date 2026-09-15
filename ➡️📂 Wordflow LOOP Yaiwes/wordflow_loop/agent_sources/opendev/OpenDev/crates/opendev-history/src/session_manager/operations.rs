//! Session operations: fork, archive, revert, search, title management.

use tracing::info;

use opendev_models::Session;

use crate::event_store::SessionEvent;

use super::SessionManager;
use super::titles::{generate_title_from_messages, get_forked_title};

impl SessionManager {
    /// Set the title for a session.
    ///
    /// Updates the title in metadata, regenerates the slug, and persists.
    /// If it's the current session, updates in-memory; otherwise loads from disk.
    pub fn set_title(&mut self, session_id: &str, title: &str) -> std::io::Result<()> {
        let title = if title.len() > 50 {
            &title[..title.floor_char_boundary(50)]
        } else {
            title
        };

        // Update in-memory if it's the current session
        if let Some(session) = &mut self.current_session
            && session.id == session_id
        {
            session.metadata.insert(
                "title".to_string(),
                serde_json::Value::String(title.to_string()),
            );
            session.slug = Some(session.generate_slug(Some(title)));
            let session_clone = session.clone();
            self.save_session(&session_clone)?;
            info!(session_id, title, "Updated session title (in-memory)");
        } else {
            // Otherwise load, update, save on disk
            let mut session = self.load_session(session_id)?;
            session.metadata.insert(
                "title".to_string(),
                serde_json::Value::String(title.to_string()),
            );
            session.slug = Some(session.generate_slug(Some(title)));
            self.save_session(&session)?;
            info!(session_id, title, "Updated session title (on-disk)");
        }

        self.emit_event(
            session_id,
            SessionEvent::TitleChanged {
                title: title.to_string(),
            },
        );
        Ok(())
    }

    /// Fork a session from a specific message index.
    ///
    /// Loads the source session, copies messages up to `fork_point`
    /// (exclusive), creates a new session with the parent reference, saves
    /// it, and returns the fork.  If `fork_point` is `None`, all messages
    /// are copied.
    pub fn fork_session(
        &self,
        session_id: &str,
        fork_point: Option<usize>,
    ) -> std::io::Result<Session> {
        let source = self.load_session(session_id)?;

        let at_message_index = fork_point.unwrap_or(source.messages.len());

        if at_message_index > source.messages.len() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                format!(
                    "fork_point {} exceeds message count {}",
                    at_message_index,
                    source.messages.len()
                ),
            ));
        }

        let mut forked = Session::new();
        forked.messages = source.messages[..at_message_index].to_vec();
        forked.parent_id = Some(session_id.to_string());
        forked.working_directory = source.working_directory.clone();
        forked.context_files = source.context_files.clone();
        forked.channel = source.channel.clone();
        forked.channel_user_id = source.channel_user_id.clone();

        // Generate fork title: inherit parent title and add fork numbering
        let parent_title = source
            .metadata
            .get("title")
            .and_then(|v| v.as_str())
            .map(String::from)
            .or_else(|| generate_title_from_messages(&source.messages))
            .unwrap_or_else(|| format!("Session {}", session_id));
        let title = get_forked_title(&parent_title);
        forked
            .metadata
            .insert("title".to_string(), serde_json::Value::String(title));

        self.save_session(&forked)?;

        self.emit_event(
            &forked.id,
            SessionEvent::SessionForked {
                source_session_id: session_id.to_string(),
                fork_point: Some(at_message_index),
            },
        );

        info!(
            "Forked session {} from {} at message {}",
            forked.id, session_id, at_message_index
        );
        Ok(forked)
    }

    /// Archive a session by setting its `time_archived` timestamp.
    pub fn archive_session(&self, session_id: &str) -> std::io::Result<()> {
        let mut session = self.load_session(session_id)?;
        session.archive();
        self.save_session(&session)?;

        self.emit_event(
            session_id,
            SessionEvent::SessionArchived {
                time_archived: chrono::Utc::now(),
            },
        );

        info!("Archived session {}", session_id);
        Ok(())
    }

    /// Unarchive a previously archived session.
    pub fn unarchive_session(&self, session_id: &str) -> std::io::Result<()> {
        let mut session = self.load_session(session_id)?;
        session.unarchive();
        self.save_session(&session)?;
        info!("Unarchived session {}", session_id);
        Ok(())
    }

    /// List sessions, optionally including archived ones.
    ///
    /// Delegates to the session index for fast metadata lookups.
    pub fn list_sessions(&self, include_archived: bool) -> Vec<opendev_models::SessionMetadata> {
        let listing = crate::listing::SessionListing::new(self.session_dir.clone());
        listing.list_sessions(None, include_archived)
    }

    /// Delete a session permanently (removes JSON + JSONL files and index entry).
    pub fn delete_session(&self, session_id: &str) -> std::io::Result<()> {
        let listing = crate::listing::SessionListing::new(self.session_dir.clone());
        listing.delete_session(session_id)
    }

    /// Revert a session to a given message step.
    ///
    /// Truncates the session's messages to `step` entries (keeping messages
    /// at indices `0..step`) and saves the result.  Returns an error if the
    /// session does not exist or `step` exceeds the current message count.
    pub fn revert_session(&self, session_id: &str, step: usize) -> std::io::Result<()> {
        let mut session = self.load_session(session_id)?;

        if step > session.messages.len() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                format!(
                    "step {} exceeds message count {}",
                    step,
                    session.messages.len()
                ),
            ));
        }

        session.messages.truncate(step);
        session.updated_at = chrono::Utc::now();
        self.save_session(&session)?;
        info!("Reverted session {} to step {}", session_id, step);
        Ok(())
    }

    /// Search all session files for messages matching a query string.
    ///
    /// Returns a list of `(session_id, matching_message_indices)` pairs for
    /// every session that contains at least one message whose content includes
    /// the query (case-insensitive).
    pub fn search_sessions(&self, query: &str) -> Vec<(String, Vec<usize>)> {
        let query_lower = query.to_lowercase();
        let mut results: Vec<(String, Vec<usize>)> = Vec::new();

        let entries = match std::fs::read_dir(&self.session_dir) {
            Ok(e) => e,
            Err(_) => return results,
        };

        for entry in entries.flatten() {
            let path = entry.path();
            // Only look at .json metadata files (skip index, tmp files, etc.)
            let Some(ext) = path.extension() else {
                continue;
            };
            if ext != "json" {
                continue;
            }
            let Some(stem) = path.file_stem().and_then(|s| s.to_str()) else {
                continue;
            };
            // Skip the sessions-index file
            if stem == "sessions-index" {
                continue;
            }

            let session = match self.load_session(stem) {
                Ok(s) => s,
                Err(_) => continue,
            };

            let matching_indices: Vec<usize> = session
                .messages
                .iter()
                .enumerate()
                .filter(|(_, msg)| msg.content.to_lowercase().contains(&query_lower))
                .map(|(i, _)| i)
                .collect();

            if !matching_indices.is_empty() {
                results.push((session.id, matching_indices));
            }
        }

        results
    }
}
