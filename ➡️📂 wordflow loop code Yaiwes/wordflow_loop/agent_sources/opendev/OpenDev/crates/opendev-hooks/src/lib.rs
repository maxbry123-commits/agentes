//! Lifecycle hook system for OpenDev.
//!
//! Hooks are shell commands triggered by lifecycle events (tool use, session
//! start/end, subagent spawn, etc.). They receive JSON on stdin describing
//! the event and communicate results via exit codes and optional JSON on stdout.
//!
//! # Architecture
//!
//! - [`models`] — Data types: [`HookEvent`], [`HookCommand`], [`HookMatcher`],
//!   [`HookConfig`]
//! - [`executor`] — [`HookExecutor`] runs individual shell commands with
//!   timeout, stdin piping, and output capture
//! - [`manager`] — [`HookManager`] orchestrates hook execution: matches events
//!   to registered hooks, runs them sequentially, aggregates results
//!
//! # Exit Code Protocol
//!
//! - **0**: Success — operation proceeds normally. Hook may emit JSON on stdout
//!   with `additionalContext`, `updatedInput`, `permissionDecision`, or
//!   `decision`.
//! - **2**: Block — operation is denied. Hook may emit JSON with `reason` and
//!   `decision` fields.
//! - **Other**: Error — logged and operation proceeds.
//!
//! # Usage
//!
//! ```no_run
//! use opendev_hooks::{HookConfig, HookEvent, HookManager};
//!
//! # async fn example() {
//! // Load config from settings.json
//! let mut config: HookConfig = serde_json::from_str(r#"{"hooks":{}}"#).unwrap();
//! config.compile_all();
//! config.strip_unknown_events();
//!
//! let manager = HookManager::new(config, "session-id", "/working/dir");
//!
//! // Before executing a tool
//! let outcome = manager.run_hooks(
//!     HookEvent::PreToolUse,
//!     Some("bash"),
//!     None,
//! ).await;
//!
//! if outcome.blocked {
//!     eprintln!("Blocked: {}", outcome.block_reason);
//! }
//! # }
//! ```

pub mod executor;
pub mod manager;
pub mod models;

pub use executor::{HookExecutor, HookResult};
pub use manager::{HookManager, HookOutcome};
pub use models::{HookCommand, HookConfig, HookEvent, HookMatcher};
