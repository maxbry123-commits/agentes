//! Managers for TUI state coordination.
//!
//! Provides services for display deduplication, message history navigation,
//! interrupt handling, spinner animation, background task tracking,
//! background agent management, and frecency-based suggestion scoring.

pub mod background_agents;
pub mod background_tasks;
pub mod display_ledger;
pub mod frecency;
pub mod interrupt;
pub mod message_history;
pub mod spinner;

pub use background_agents::{BackgroundAgentManager, BackgroundAgentState, BackgroundAgentTask};
pub use background_tasks::{BackgroundTaskManager, TaskState, TaskStatus};
pub use display_ledger::DisplayLedger;
pub use frecency::{FrecencyEntry, FrecencyTracker};
pub use interrupt::InterruptManager;
pub use message_history::MessageHistory;
pub use spinner::SpinnerService;
