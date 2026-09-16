//! Todo tracking for plan execution.
//!
//! After a plan is approved, its implementation steps are converted into
//! `TodoItem`s that track progress (pending → in_progress → completed).
//!
//! Mirrors the Python todo handler pattern used in
//! `opendev/core/context_engineering/tools/handlers/todo_handler.py`.

mod item;
mod manager;
mod parsing;
mod status;

pub use item::{SubTodoItem, TodoItem};
pub use manager::TodoManager;
pub use parsing::{parse_plan_steps, parse_status, strip_markdown};
pub use status::TodoStatus;
