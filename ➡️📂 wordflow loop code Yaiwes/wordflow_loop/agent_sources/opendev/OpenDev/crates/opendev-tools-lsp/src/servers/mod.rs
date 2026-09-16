//! Language server configurations.
//!
//! Each supported language has a server configuration specifying the command
//! to launch, arguments, and file extensions it handles.

mod configs;

pub use configs::default_server_configs;

use serde::{Deserialize, Serialize};

/// Configuration for a language server.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    /// Command to start the server (e.g., "rust-analyzer", "pyright-langserver").
    pub command: String,
    /// Command-line arguments.
    pub args: Vec<String>,
    /// LSP language identifier (e.g., "rust", "python").
    pub language_id: String,
    /// File extensions this server handles (without dots, e.g., "rs", "py").
    pub extensions: Vec<String>,
}

impl ServerConfig {
    /// Create a new server configuration.
    pub fn new(
        command: impl Into<String>,
        args: Vec<String>,
        language_id: impl Into<String>,
        extensions: Vec<String>,
    ) -> Self {
        Self {
            command: command.into(),
            args,
            language_id: language_id.into(),
            extensions,
        }
    }
}
