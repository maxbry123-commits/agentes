//! Injects live git status (branch + changed files) periodically.

use std::sync::OnceLock;

use crate::attachments::{Attachment, CadenceGate, ContextCollector, TurnContext};
use crate::prompts::reminders::MessageClass;

pub struct GitStatusCollector {
    cadence: CadenceGate,
    is_git_repo: OnceLock<bool>,
}

impl GitStatusCollector {
    pub fn new(interval: usize) -> Self {
        Self {
            cadence: CadenceGate::new(interval),
            is_git_repo: OnceLock::new(),
        }
    }

    fn check_is_git_repo(&self, working_dir: &std::path::Path) -> bool {
        *self
            .is_git_repo
            .get_or_init(|| working_dir.join(".git").exists())
    }
}

#[async_trait::async_trait]
impl ContextCollector for GitStatusCollector {
    fn name(&self) -> &'static str {
        "git_status"
    }

    fn should_fire(&self, ctx: &TurnContext<'_>) -> bool {
        self.check_is_git_repo(ctx.working_dir) && self.cadence.should_fire(ctx.turn_number)
    }

    async fn collect(&self, ctx: &TurnContext<'_>) -> Option<Attachment> {
        let dir = ctx.working_dir;

        // Run git commands concurrently
        let branch_fut = tokio::process::Command::new("git")
            .args(["rev-parse", "--abbrev-ref", "HEAD"])
            .current_dir(dir)
            .output();

        let status_fut = tokio::process::Command::new("git")
            .args(["status", "--short"])
            .current_dir(dir)
            .output();

        let (branch_result, status_result) = tokio::join!(branch_fut, status_fut);

        let branch = branch_result
            .ok()
            .filter(|o| o.status.success())
            .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
            .unwrap_or_else(|| "unknown".to_string());

        let status = status_result
            .ok()
            .filter(|o| o.status.success())
            .map(|o| String::from_utf8_lossy(&o.stdout).to_string())
            .unwrap_or_default();

        let mut lines = vec![
            "Git status (live):".to_string(),
            format!("- Branch: {branch}"),
        ];

        let status_trimmed = status.trim();
        if status_trimmed.is_empty() {
            lines.push("- Working tree: clean".to_string());
        } else {
            lines.push("- Changed files:".to_string());
            for line in status_trimmed.lines().take(30) {
                lines.push(format!("  {line}"));
            }
            let total = status_trimmed.lines().count();
            if total > 30 {
                lines.push(format!("  ... and {} more", total - 30));
            }
        }

        Some(Attachment {
            name: "git_status",
            content: lines.join("\n"),
            class: MessageClass::Nudge,
        })
    }

    fn did_fire(&self, turn: usize) {
        self.cadence.mark_fired(turn);
    }

    fn reset(&self) {
        self.cadence.reset();
    }
}
