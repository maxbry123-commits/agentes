//! Error types for symbol operations.

use std::path::PathBuf;

/// Errors that can occur during symbol operations.
#[derive(Debug, thiserror::Error)]
pub enum SymbolError {
    #[error("Missing required argument: {0}")]
    MissingArgument(&'static str),

    #[error("Invalid identifier: {0}")]
    InvalidIdentifier(String),

    #[error("File not found: {0}")]
    FileNotFound(PathBuf),

    #[error("Symbol not found: {0}")]
    SymbolNotFound(String),

    #[error("LSP error: {0}")]
    Lsp(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Edit failed: {0}")]
    EditFailed(String),
}

/// Tool result following the OpenDev convention.
#[derive(Debug, Clone, serde::Serialize)]
pub struct ToolResult {
    pub success: bool,
    pub output: String,
    #[serde(flatten)]
    pub extra: serde_json::Value,
}

impl ToolResult {
    pub fn ok(output: impl Into<String>) -> Self {
        Self {
            success: true,
            output: output.into(),
            extra: serde_json::Value::Null,
        }
    }

    pub fn ok_with(output: impl Into<String>, extra: serde_json::Value) -> Self {
        Self {
            success: true,
            output: output.into(),
            extra,
        }
    }

    pub fn err(output: impl Into<String>) -> Self {
        Self {
            success: false,
            output: output.into(),
            extra: serde_json::Value::Null,
        }
    }
}
