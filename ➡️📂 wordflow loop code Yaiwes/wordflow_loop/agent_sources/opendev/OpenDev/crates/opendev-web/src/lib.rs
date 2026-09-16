//! Axum-based web server for the OpenDev AI coding assistant.
//!
//! Provides:
//! - REST API routes (auth, config, sessions, chat)
//! - WebSocket handler for real-time communication
//! - Shared application state
//! - Static file serving for the SPA frontend

pub mod embedded;
pub mod error;
pub mod protocol;
pub mod routes;
pub mod server;
pub mod state;
pub mod websocket;
