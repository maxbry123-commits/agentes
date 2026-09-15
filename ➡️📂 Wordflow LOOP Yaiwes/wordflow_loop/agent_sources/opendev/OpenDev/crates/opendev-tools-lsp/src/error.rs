//! Error types for LSP operations.

/// Errors that can occur during LSP operations.
#[derive(Debug, thiserror::Error)]
pub enum LspError {
    #[error("Failed to start language server: {0}")]
    ServerStart(String),

    #[error("Server not running")]
    NotRunning,

    #[error("Server response error: {0}")]
    ServerResponse(String),

    #[error("Protocol error: {0}")]
    Protocol(String),

    #[error("Request timed out: {0}")]
    Timeout(String),

    #[error("No server configured for language: {0}")]
    NoServer(String),

    #[error("File not found: {0}")]
    FileNotFound(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("{0}")]
    Other(String),
}
