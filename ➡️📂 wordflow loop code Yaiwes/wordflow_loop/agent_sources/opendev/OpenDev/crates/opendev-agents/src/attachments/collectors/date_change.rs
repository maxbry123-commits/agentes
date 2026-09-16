//! Fires once when the calendar date changes mid-session.

use std::sync::Mutex;

use crate::attachments::{Attachment, ContextCollector, TurnContext};
use crate::prompts::reminders::MessageClass;

const DATE_FMT: &str = "%Y-%m-%d";

pub struct DateChangeCollector {
    last_date: Mutex<String>,
}

impl Default for DateChangeCollector {
    fn default() -> Self {
        Self::new()
    }
}

impl DateChangeCollector {
    pub fn new() -> Self {
        let today = chrono::Local::now().format(DATE_FMT).to_string();
        Self {
            last_date: Mutex::new(today),
        }
    }
}

#[async_trait::async_trait]
impl ContextCollector for DateChangeCollector {
    fn name(&self) -> &'static str {
        "date_change"
    }

    fn should_fire(&self, _ctx: &TurnContext<'_>) -> bool {
        // Always pass — the actual check-and-update is atomic in collect().
        true
    }

    async fn collect(&self, _ctx: &TurnContext<'_>) -> Option<Attachment> {
        let today = chrono::Local::now().format(DATE_FMT).to_string();
        let mut last = self.last_date.lock().ok()?;
        if *last == today {
            return None;
        }
        *last = today.clone();
        Some(Attachment {
            name: "date_change",
            content: format!("The current date has changed to {today}."),
            class: MessageClass::Directive,
        })
    }

    fn reset(&self) {
        if let Ok(mut last) = self.last_date.lock() {
            *last = chrono::Local::now().format(DATE_FMT).to_string();
        }
    }
}
