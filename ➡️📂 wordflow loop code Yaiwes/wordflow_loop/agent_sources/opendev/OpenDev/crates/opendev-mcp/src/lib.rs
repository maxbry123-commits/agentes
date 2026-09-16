//! MCP (Model Context Protocol) client for OpenDev.
//!
//! This crate provides the MCP client implementation for connecting to
//! and communicating with MCP servers. It supports stdio, SSE, and HTTP
//! transport mechanisms.
//!
//! # Architecture
//!
//! - **config**: Server configuration loading, merging, and env var expansion
//! - **models**: MCP protocol types (tools, resources, prompts, JSON-RPC)
//! - **transport**: Transport trait and implementations (stdio, SSE, HTTP)
//! - **manager**: McpManager coordinating multiple server connections

pub mod config;
pub mod error;
pub mod manager;
pub mod models;
pub mod transport;

pub use config::{McpConfig, McpOAuthConfig, McpServerConfig, TransportType};
pub use error::{McpError, McpResult};
pub use manager::McpManager;
pub use models::{
    JsonRpcNotification, McpContent, McpPromptSummary, McpServerInfo, McpTool, McpToolResult,
    McpToolSchema,
};
pub use transport::McpTransport;
