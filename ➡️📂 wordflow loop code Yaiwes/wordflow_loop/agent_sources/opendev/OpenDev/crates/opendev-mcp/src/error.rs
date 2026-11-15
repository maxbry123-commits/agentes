//! Error types for MCP operations.

use thiserror::Error;

/// Errors that can occur during MCP operations.
#[derive(Debug, Error)]
pub enum McpError {
    #[error("Transport error: {0}")]
    Transport(String),

    #[error("Connection error for server '{server}': {message}")]
    Connection { server: String, message: String },

    #[error("Server '{0}' not found")]
    ServerNotFound(String),

    #[error("Server '{0}' already connected")]
    AlreadyConnected(String),

    #[error("Configuration error: {0}")]
    Config(String),

    #[error("Protocol error: {0}")]
    Protocol(String),

    #[error("Timeout after {0} seconds")]
    Timeout(u64),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("HTTP error: {0}")]
    Http(#[from] reqwest::Error),
}

/// Result type alias for MCP operations.
pub type McpResult<T> = Result<T, McpError>;
