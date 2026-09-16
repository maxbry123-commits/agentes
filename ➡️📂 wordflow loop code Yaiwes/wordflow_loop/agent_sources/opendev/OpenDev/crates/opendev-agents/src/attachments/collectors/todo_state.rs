//! Injects current todo/task list with actual items and statuses.

use crate::attachments::{Attachment, CadenceGate, ContextCollector, TurnContext};
use crate::prompts::reminders::MessageClass;

pub struct TodoStateCollector {
    cadence: CadenceGate,
}

impl TodoStateCollector {
    pub fn new(interval: usize) -> Self {
        Self {
            cadence: CadenceGate::new(interval),
        }
    }
}

#[async_trait::async_trait]
impl ContextCollector for TodoStateCollector {
    fn name(&self) -> &'static str {
        "todo_state"
    }

    fn should_fire(&self, ctx: &TurnContext<'_>) -> bool {
        // Only check cadence + manager existence here.
        // The actual emptiness check happens in collect() to avoid double-locking.
        self.cadence.should_fire(ctx.turn_number) && ctx.todo_manager.is_some()
    }

    async fn collect(&self, ctx: &TurnContext<'_>) -> Option<Attachment> {
        let mgr = ctx.todo_manager?.lock().ok()?;
        if !mgr.has_todos() {
            return None;
        }

        let status = mgr.format_status_sorted();
        let content = format!(
            "The task tools haven't been used recently. If you're working on tasks that would \
             benefit from tracking progress, consider using TaskCreate to add new tasks and \
             TaskUpdate to update task status (set to in_progress when starting, completed \
             when done). Also consider cleaning up the task list if it has become stale. \
             Only use these if relevant to the current work. This is just a gentle reminder \
             — ignore if not applicable. Make sure that you NEVER mention this reminder to \
             the user\n\n\
             Here are the existing tasks:\n\n{status}"
        );

        Some(Attachment {
            name: "todo_state",
            content,
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
