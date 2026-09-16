use super::*;

#[test]
fn test_http_result_ok() {
    let result = HttpResult::ok(200, serde_json::json!({"message": "hello"}));
    assert!(result.success);
    assert_eq!(result.status, Some(200));
    assert!(!result.interrupted);
    assert!(!result.retryable);
}

#[test]
fn test_http_result_fail() {
    let result = HttpResult::fail("connection refused", true);
    assert!(!result.success);
    assert!(result.retryable);
    assert_eq!(result.error.as_deref(), Some("connection refused"));
}

#[test]
fn test_http_result_interrupted() {
    let result = HttpResult::interrupted();
    assert!(!result.success);
    assert!(result.interrupted);
    assert!(!result.retryable);
}

#[test]
fn test_http_result_retryable_status() {
    let result = HttpResult::retryable_status(429, None, None);
    assert!(!result.success);
    assert!(result.retryable);
    assert_eq!(result.status, Some(429));
}

#[test]
fn test_http_result_retryable_status_with_retry_after() {
    let result = HttpResult::retryable_status(429, None, Some("30".to_string()));
    assert!(!result.success);
    assert!(result.retryable);
    assert_eq!(result.retry_after.as_deref(), Some("30"));
}

// --- HttpError::is_retryable classification (issues #13, #110) ---

#[test]
fn test_retries_exhausted_is_retryable() {
    let err = HttpError::RetriesExhausted {
        message: "[request_id=abc] HTTP 503".into(),
    };
    assert!(err.is_retryable());
}

#[test]
fn test_circuit_open_is_retryable() {
    let err = HttpError::CircuitOpen("Circuit breaker open. Will retry in 27s.".into());
    assert!(err.is_retryable());
}

#[test]
fn test_other_is_not_retryable() {
    // Definitive 4xx failures (401/403/404/400) surface as `Other` from
    // `send_streaming_request` — they must fail fast, never retry.
    let err = HttpError::Other("[request_id=abc] Invalid API key".into());
    assert!(!err.is_retryable());
}

#[test]
fn test_auth_is_not_retryable() {
    assert!(!HttpError::Auth("bad key".into()).is_retryable());
}

#[test]
fn test_interrupted_is_not_retryable() {
    assert!(!HttpError::Interrupted.is_retryable());
}
