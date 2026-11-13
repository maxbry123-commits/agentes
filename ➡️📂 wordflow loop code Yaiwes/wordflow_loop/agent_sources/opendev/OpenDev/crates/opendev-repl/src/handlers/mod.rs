//! Tool handler middleware layer.
//!
//! Mirrors `opendev/core/context_engineering/tools/handlers/`.
//!
//! Provides a middleware pipeline that wraps tool execution with:
//! - Pre-execution approval checks
//! - Operation/audit tracking
//! - Post-execution result formatting (truncation, metadata)
//! - File change tracking

pub mod file_handler;
pub mod process_handler;
pub mod registry;
pub mod thinking_handler;
pub mod traits;

pub use registry::HandlerRegistry;
pub use traits::{HandlerResult, PreCheckResult, ToolHandler};
