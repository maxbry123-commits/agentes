//! MCP data models for server configuration and API payloads.

use std::collections::HashMap;

use serde::{Deserialize, Serialize};

/// MCP server configuration stored on disk.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpServerConfig {
    pub command: String,
    #[serde(default)]
    pub args: Vec<String>,
    #[serde(default)]
    pub env: HashMap<String, String>,
    #[serde(default = "default_true")]
    pub enabled: bool,
    #[serde(default)]
    pub auto_start: bool,
}

pub(super) fn default_true() -> bool {
    true
}

/// On-disk MCP config file format.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) struct McpConfigFile {
    #[serde(default, rename = "mcpServers")]
    pub(super) mcp_servers: HashMap<String, McpServerConfig>,
}

/// Create MCP server request.
#[derive(Debug, Deserialize)]
pub struct McpServerCreate {
    pub name: String,
    pub command: String,
    #[serde(default)]
    pub args: Vec<String>,
    #[serde(default)]
    pub env: HashMap<String, String>,
    #[serde(default = "default_true")]
    pub enabled: bool,
    #[serde(default)]
    pub auto_start: bool,
}

/// Update MCP server request.
#[derive(Debug, Deserialize)]
pub struct McpServerUpdate {
    pub command: Option<String>,
    pub args: Option<Vec<String>>,
    pub env: Option<HashMap<String, String>>,
    pub enabled: Option<bool>,
    pub auto_start: Option<bool>,
}
