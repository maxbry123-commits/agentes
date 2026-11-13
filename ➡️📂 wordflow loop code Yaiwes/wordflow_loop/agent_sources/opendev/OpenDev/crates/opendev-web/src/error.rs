//! Error types for the web server.

use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use serde_json::json;

/// Web server error type.
#[derive(Debug, thiserror::Error)]
pub enum WebError {
    #[error("not found: {0}")]
    NotFound(String),

    #[error("bad request: {0}")]
    BadRequest(String),

    #[error("unauthorized: {0}")]
    Unauthorized(String),

    #[error("conflict: {0}")]
    Conflict(String),

    #[error("internal error: {0}")]
    Internal(String),

    #[error("session error: {0}")]
    Session(#[from] std::io::Error),

    #[error("serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}

impl IntoResponse for WebError {
    fn into_response(self) -> Response {
        let (status, message) = match &self {
            WebError::NotFound(msg) => (StatusCode::NOT_FOUND, msg.clone()),
            WebError::BadRequest(msg) => (StatusCode::BAD_REQUEST, msg.clone()),
            WebError::Unauthorized(msg) => (StatusCode::UNAUTHORIZED, msg.clone()),
            WebError::Conflict(msg) => (StatusCode::CONFLICT, msg.clone()),
            WebError::Internal(msg) => (StatusCode::INTERNAL_SERVER_ERROR, msg.clone()),
            WebError::Session(e) => (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()),
            WebError::Serialization(e) => (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()),
        };

        let body = json!({
            "error": message,
        });

        (status, axum::Json(body)).into_response()
    }
}
