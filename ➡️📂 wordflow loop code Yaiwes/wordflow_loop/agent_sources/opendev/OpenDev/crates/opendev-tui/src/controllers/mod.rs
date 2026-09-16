//! Controllers for coordinating UI actions with application state.

pub mod agent_creator;
pub mod approval;
pub mod ask_user;
pub mod autocomplete_popup;
pub mod mcp_command;
pub mod message;
pub mod model_picker;
pub mod plan_approval;
pub mod session_picker;
pub mod skill_creator;
pub mod slash_commands;
pub mod spinner;

pub use agent_creator::{AgentCreatorController, AgentSpec};
pub use approval::ApprovalController;
pub use ask_user::AskUserController;
pub use autocomplete_popup::{AutocompletePopupController, CompletionItem};
pub use mcp_command::{McpCommandController, McpServerInfo};
pub use message::MessageController;
pub use model_picker::{ModelOption, ModelPickerController};
pub use plan_approval::{PlanApprovalController, PlanDecision, PlanStatus};
pub use session_picker::{SessionOption, SessionPickerController};
pub use skill_creator::{SkillCreatorController, SkillSpec};
pub use slash_commands::{BUILTIN_COMMANDS, SlashCommand, find_matching_commands, is_command};
pub use spinner::SpinnerController;
