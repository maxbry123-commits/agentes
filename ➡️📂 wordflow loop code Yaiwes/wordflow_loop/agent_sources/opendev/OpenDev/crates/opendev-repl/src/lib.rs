//! REPL loop and command handling for OpenDev.
//!
//! This crate provides:
//! - [`repl`] — Main REPL loop: read input -> process -> display
//! - [`query_processor`] — Process user queries, enhance with context, delegate to ReAct
//! - [`tool_executor`] — Execute tools and format results
//! - [`commands`] — Slash command routing and built-in commands
//! - [`error`] — Error types

pub mod commands;
pub mod error;
pub mod file_injector;
pub mod handlers;
pub mod query_enhancer;
pub mod query_processor;
pub mod repl;
pub mod skills;
pub mod tool_executor;

pub use error::ReplError;
pub use handlers::HandlerRegistry;
pub use query_enhancer::QueryEnhancer;
pub use query_processor::QueryProcessor;
pub use repl::Repl;
pub use skills::{Skill, list_cached_skills, load_skill_from_file, load_skill_from_url};
pub use tool_executor::ToolExecutor;
