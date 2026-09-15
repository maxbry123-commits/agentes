//! Embedded SPA frontend assets.
//!
//! The built web-ui bundle (Vite output) is committed at
//! `crates/opendev-web/static/` and embedded into the binary at compile time,
//! so binaries installed via `cargo install` (or downloaded releases) can
//! serve the frontend without a repo checkout. A filesystem static directory,
//! when provided and present, takes precedence as a dev-time override — see
//! [`crate::server::build_app`].

use axum::http::{Method, StatusCode, Uri, header};
use axum::response::{IntoResponse, Response};
use rust_embed::RustEmbed;

/// Built web-ui bundle embedded at compile time.
#[derive(RustEmbed)]
#[folder = "static/"]
pub struct WebAssets;

/// Axum fallback handler serving the embedded SPA bundle.
///
/// Resolution order:
/// 1. `/api/*` and `/ws` are never served from assets: registered API routes
///    match before the fallback fires, so anything reaching here is an
///    unknown API path and must stay a 404.
/// 2. Exact asset match (`/`, `/icon_blue.png`, `/assets/index-*.js`, ...).
/// 3. SPA fallback: `index.html` for any other GET/HEAD path, so client-side
///    routes resolve on hard refresh.
pub async fn serve_embedded(method: Method, uri: Uri) -> Response {
    let path = uri.path();
    if path == "/ws" || path == "/api" || path.starts_with("/api/") {
        return StatusCode::NOT_FOUND.into_response();
    }
    if method != Method::GET && method != Method::HEAD {
        return StatusCode::METHOD_NOT_ALLOWED.into_response();
    }

    let trimmed = path.trim_start_matches('/');
    let candidate = if trimmed.is_empty() {
        "index.html"
    } else {
        trimmed
    };

    match WebAssets::get(candidate) {
        Some(file) => asset_response(candidate, file),
        None => match WebAssets::get("index.html") {
            Some(file) => asset_response("index.html", file),
            None => StatusCode::NOT_FOUND.into_response(),
        },
    }
}

/// Build a response for an embedded file with the correct Content-Type.
fn asset_response(path: &str, file: rust_embed::EmbeddedFile) -> Response {
    let mime = mime_guess::from_path(path).first_or_octet_stream();
    (
        [(header::CONTENT_TYPE, mime.as_ref())],
        axum::body::Body::from(file.data),
    )
        .into_response()
}
