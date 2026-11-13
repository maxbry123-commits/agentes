//! Error types for the REPL crate.

/// Errors that can occur in the REPL.
#[derive(Debug, thiserror::Error)]
pub enum ReplError {
    /// I/O error (reading input, writing output).
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    /// Agent error during query processing.
    #[error("Agent error: {0}")]
    Agent(#[from] opendev_agents::AgentError),

    /// Tool execution error.
    #[error("Tool error: {0}")]
    Tool(#[from] opendev_tools_core::ToolError),

    /// Session error.
    #[error("Session error: {0}")]
    Session(String),

    /// Command not found.
    #[error("Unknown command: {0}")]
    UnknownCommand(String),

    /// User interrupted (Ctrl+C).
    #[error("Interrupted")]
    Interrupted,

    /// End of input (Ctrl+D / EOF).
    #[error("End of input")]
    Eof,

    /// Generic error.
    #[error("{0}")]
    Other(String),
}
