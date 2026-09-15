//! Slash command module.
//!
//! Routes `/command` inputs to the appropriate handler.

pub mod builtin;

pub use builtin::{BuiltinCommands, CommandOutcome};
