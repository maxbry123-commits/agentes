//! Error types for channel operations.

use thiserror::Error;

/// Errors that can occur during channel routing.
#[derive(Debug, Error)]
pub enum ChannelError {
    #[error("Channel adapter '{0}' not registered")]
    AdapterNotFound(String),

    #[error("Session error: {0}")]
    Session(String),

    #[error("Delivery failed for channel '{channel}': {message}")]
    DeliveryFailed { channel: String, message: String },

    #[error("Workspace selection required")]
    WorkspaceRequired,

    #[error("Agent executor not configured")]
    NoExecutor,

    #[error("Agent execution error: {0}")]
    AgentError(String),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}

/// Result type alias for channel operations.
pub type ChannelResult<T> = Result<T, ChannelError>;
