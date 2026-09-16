//! Fires once after context compaction to inform the LLM.

use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};

use crate::attachments::{Attachment, ContextCollector, TurnContext};
use crate::prompts::reminders::MessageClass;

pub struct CompactionCollector {
    flag: Arc<AtomicBool>,
}

impl CompactionCollector {
    pub fn new(flag: Arc<AtomicBool>) -> Self {
        Self { flag }
    }
}

#[async_trait::async_trait]
impl ContextCollector for CompactionCollector {
    fn name(&self) -> &'static str {
        "compaction"
    }

    fn should_fire(&self, _ctx: &TurnContext<'_>) -> bool {
        self.flag.load(Ordering::Relaxed)
    }

    async fn collect(&self, _ctx: &TurnContext<'_>) -> Option<Attachment> {
        // Atomically clear the flag — only fire once per compaction event
        if !self.flag.swap(false, Ordering::Relaxed) {
            return None;
        }
        Some(Attachment {
            name: "compaction",
            content: "Context was automatically compacted to free space. Earlier tool results \
                      and conversation details may have been summarized. If you need specific \
                      file contents or command outputs from before compaction, re-read them."
                .to_string(),
            class: MessageClass::Directive,
        })
    }
}
