use super::*;
use crate::state::AppState;
use axum::body::Body;
use axum::http::{Request, StatusCode};
use opendev_config::ModelRegistry;
use opendev_history::SessionManager;
use opendev_http::UserStore;
use opendev_models::AppConfig;
use tempfile::TempDir;
use tower::ServiceExt;

fn make_state() -> AppState {
    let tmp = TempDir::new().unwrap();
    let tmp_path = tmp.into_path();
    let session_manager = SessionManager::new(tmp_path.clone()).unwrap();
    let config = AppConfig::default();
    let user_store = UserStore::new(tmp_path).unwrap();
    let model_registry = ModelRegistry::new();
    AppState::new(
        session_manager,
        config,
        "/tmp/test".to_string(),
        user_store,
        model_registry,
    )
}

/// Send a GET request to the app and return the response.
async fn get(app: Router, uri: &str) -> axum::response::Response {
    app.oneshot(Request::builder().uri(uri).body(Body::empty()).unwrap())
        .await
        .unwrap()
}

fn content_type(response: &axum::response::Response) -> String {
    response
        .headers()
        .get(axum::http::header::CONTENT_TYPE)
        .map(|v| v.to_str().unwrap().to_string())
        .unwrap_or_default()
}

async fn body_string(response: axum::response::Response) -> String {
    let bytes = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    String::from_utf8_lossy(&bytes).to_string()
}

#[tokio::test]
async fn test_health_check() {
    let state = make_state();
    let app = build_app(state, None);

    let response = app
        .oneshot(
            Request::builder()
                .uri("/api/health")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);

    let body = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
    assert_eq!(json["status"], "ok");
}

#[tokio::test]
async fn test_embedded_index_served_at_root() {
    let app = build_app(make_state(), None);

    let response = get(app, "/").await;
    assert_eq!(response.status(), StatusCode::OK);
    assert!(content_type(&response).starts_with("text/html"));
    let body = body_string(response).await;
    assert!(body.contains("<div id=\"root\">"));
}

#[tokio::test]
async fn test_embedded_root_level_file() {
    let app = build_app(make_state(), None);

    let response = get(app, "/icon_blue.png").await;
    assert_eq!(response.status(), StatusCode::OK);
    assert_eq!(content_type(&response), "image/png");
}

#[tokio::test]
async fn test_embedded_hashed_assets_content_type() {
    let js = crate::embedded::WebAssets::iter()
        .find(|p| p.starts_with("assets/") && p.ends_with(".js"))
        .expect("embedded bundle must contain a hashed JS asset");
    let css = crate::embedded::WebAssets::iter()
        .find(|p| p.starts_with("assets/") && p.ends_with(".css"))
        .expect("embedded bundle must contain a hashed CSS asset");

    let response = get(build_app(make_state(), None), &format!("/{js}")).await;
    assert_eq!(response.status(), StatusCode::OK);
    assert!(content_type(&response).contains("javascript"));

    let response = get(build_app(make_state(), None), &format!("/{css}")).await;
    assert_eq!(response.status(), StatusCode::OK);
    assert!(content_type(&response).starts_with("text/css"));
}

#[tokio::test]
async fn test_embedded_spa_fallback_for_unknown_route() {
    let app = build_app(make_state(), None);

    let response = get(app, "/sessions/some-client-side-route").await;
    assert_eq!(response.status(), StatusCode::OK);
    assert!(content_type(&response).starts_with("text/html"));
    let body = body_string(response).await;
    assert!(body.contains("<div id=\"root\">"));
}

#[tokio::test]
async fn test_api_routes_not_swallowed_by_spa_fallback() {
    let app = build_app(make_state(), None);

    let response = get(app, "/api/does-not-exist").await;
    assert_eq!(response.status(), StatusCode::NOT_FOUND);
    assert!(!content_type(&response).starts_with("text/html"));
}

#[tokio::test]
async fn test_filesystem_static_dir_overrides_embedded() {
    let tmp = TempDir::new().unwrap();
    std::fs::write(tmp.path().join("index.html"), "<html>dev override</html>").unwrap();

    let app = build_app(make_state(), Some(tmp.path()));

    let response = get(app, "/").await;
    assert_eq!(response.status(), StatusCode::OK);
    let body = body_string(response).await;
    assert!(body.contains("dev override"));
}
