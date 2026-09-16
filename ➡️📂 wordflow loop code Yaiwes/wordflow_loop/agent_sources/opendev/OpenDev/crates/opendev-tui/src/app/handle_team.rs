//! Handlers for team lifecycle events.

use std::time::Duration;

use super::App;
use crate::widgets::{Toast, ToastLevel};

impl App {
    /// Handle team creation event.
    pub(super) fn handle_team_created(
        &mut self,
        team_id: String,
        _leader_name: String,
        member_names: Vec<String>,
    ) {
        let count = member_names.len();
        self.state.toasts.push(
            Toast::new(
                format!("Team '{team_id}' created with {count} members"),
                ToastLevel::Info,
            )
            .with_duration(Duration::from_secs(3)),
        );
        self.state.dirty = true;
    }

    /// Handle inter-agent message event.
    pub(super) fn handle_team_message(
        &mut self,
        from: String,
        to: String,
        content_preview: String,
    ) {
        // Toast only when task watcher is closed (user is already watching otherwise)
        if !self.state.task_watcher_open {
            let preview: String = content_preview.chars().take(30).collect();
            self.state.toasts.push(
                Toast::new(format!("{from} \u{2192} {to}: {preview}"), ToastLevel::Info)
                    .with_duration(Duration::from_secs(2)),
            );
        }
        self.state.dirty = true;
    }

    /// Handle team deletion event.
    pub(super) fn handle_team_deleted(&mut self, team_id: String) {
        self.state.toasts.push(Toast::new(
            format!("Team '{team_id}' disbanded"),
            ToastLevel::Info,
        ));
        self.state.dirty = true;
    }
}
