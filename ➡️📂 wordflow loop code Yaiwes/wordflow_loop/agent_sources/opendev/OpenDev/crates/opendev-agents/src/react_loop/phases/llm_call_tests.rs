//! Unit tests for `llm_call` retry-backoff logic.

use std::time::Duration;

use super::{RETRY_FALLBACK_BACKOFF, RETRY_MAX_BACKOFF, parse_retry_hint, retry_backoff_for};

#[test]
fn parses_canonical_circuit_breaker_message() {
    let msg = "Circuit breaker open for provider 'anthropic'. \
               Too many consecutive failures (9). \
               Will retry in 27s.";
    assert_eq!(parse_retry_hint(msg), Some(Duration::from_secs(27)));
}

#[test]
fn parses_with_extra_surrounding_context() {
    let msg = "[request_id=abc] Circuit open. Will retry in 5s. (jittered)";
    assert_eq!(parse_retry_hint(msg), Some(Duration::from_secs(5)));
}

#[test]
fn returns_none_when_phrase_absent() {
    assert_eq!(parse_retry_hint("HTTP 500 internal server error"), None);
    assert_eq!(parse_retry_hint(""), None);
}

#[test]
fn returns_none_when_seconds_unparseable() {
    assert_eq!(parse_retry_hint("Will retry in soons."), None);
    assert_eq!(parse_retry_hint("Will retry in -1s."), None);
}

#[test]
fn backoff_uses_parsed_hint_when_present() {
    let msg = "Circuit open. Will retry in 3s.";
    assert_eq!(retry_backoff_for(msg), Duration::from_secs(3));
}

#[test]
fn backoff_caps_unreasonably_large_hints() {
    let msg = "Will retry in 999999s.";
    assert_eq!(retry_backoff_for(msg), RETRY_MAX_BACKOFF);
}

#[test]
fn backoff_falls_back_when_no_hint() {
    assert_eq!(retry_backoff_for("HTTP 500"), RETRY_FALLBACK_BACKOFF);
    assert_eq!(retry_backoff_for(""), RETRY_FALLBACK_BACKOFF);
}

#[test]
fn parsed_zero_seconds_clamps_up_to_fallback() {
    // Reproduces the half-open boundary case observed in the field:
    // the circuit breaker reports `remaining_secs=0` the moment its
    // cooldown expires. A naive parse would yield a zero-second sleep,
    // letting the loop burst-retry until the breaker fully opens
    // again. The clamp must lift parsed=0 up to the fallback.
    let msg = "Circuit breaker open … Will retry in 0s.";
    assert_eq!(parse_retry_hint(msg), Some(Duration::ZERO));
    assert_eq!(retry_backoff_for(msg), RETRY_FALLBACK_BACKOFF);
}

#[test]
fn parsed_below_fallback_clamps_up() {
    // Any hint smaller than the fallback floor must be lifted, not
    // honored verbatim.
    let msg = "Will retry in 0s.";
    assert!(retry_backoff_for(msg) >= RETRY_FALLBACK_BACKOFF);
}

#[test]
fn fallback_is_at_least_one_log_line_apart() {
    // Sanity: fallback must be large enough to prevent the runaway-loop
    // scenario this fix addresses (sub-millisecond retries flooding logs).
    assert!(
        RETRY_FALLBACK_BACKOFF >= Duration::from_millis(100),
        "fallback backoff too small to prevent log/CPU runaway",
    );
}

// --- Consecutive-failure cap and error surfacing (issues #13, #110) ---
//
// Retryable LLM failures previously looped forever with no UI feedback.
// `execute_llm_call` must now give up after MAX_CONSECUTIVE_LLM_FAILURES
// consecutive failures and return a real `AgentError::LlmError` (which the
// TUI/web error surfaces render), and non-retryable failures (401/404/400)
// must fail fast on the first call.

use serde_json::json;

use super::{MAX_CONSECUTIVE_LLM_FAILURES, debug_hint, execute_llm_call};
use crate::llm_calls::{LlmCallConfig, LlmCaller};
use crate::react_loop::emitter::IterationEmitter;
use crate::react_loop::loop_state::LoopState;
use crate::react_loop::types::LoopAction;
use crate::traits::{AgentError, TaskMonitor};
use opendev_http::{AdaptedClient, HttpClient, RetryConfig};

/// Spawn a local HTTP server that answers every request with the given
/// status line and JSON body, then closes the connection. Returns the URL.
async fn spawn_static_server(status_line: &'static str, body: &'static str) -> String {
    use tokio::io::{AsyncReadExt, AsyncWriteExt};

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    tokio::spawn(async move {
        while let Ok((mut sock, _)) = listener.accept().await {
            tokio::spawn(async move {
                let mut buf = Vec::new();
                let mut chunk = [0u8; 8192];
                loop {
                    let Ok(n) = sock.read(&mut chunk).await else {
                        return;
                    };
                    if n == 0 {
                        return;
                    }
                    buf.extend_from_slice(&chunk[..n]);
                    if let Some(pos) = buf.windows(4).position(|w| w == b"\r\n\r\n") {
                        let headers = String::from_utf8_lossy(&buf[..pos]).to_lowercase();
                        let content_length = headers
                            .lines()
                            .find_map(|l| l.strip_prefix("content-length:"))
                            .and_then(|v| v.trim().parse::<usize>().ok())
                            .unwrap_or(0);
                        if buf.len() >= pos + 4 + content_length {
                            break;
                        }
                    }
                }
                let response = format!(
                    "{status_line}\r\ncontent-type: application/json\r\ncontent-length: {}\r\nconnection: close\r\n\r\n{body}",
                    body.len()
                );
                let _ = sock.write_all(response.as_bytes()).await;
                let _ = sock.shutdown().await;
            });
        }
    });
    format!("http://{addr}")
}

fn test_client_for(url: &str) -> AdaptedClient {
    let http = HttpClient::new(url, reqwest::header::HeaderMap::new(), None)
        .unwrap()
        .with_retry_config(RetryConfig {
            max_retries: 0,
            initial_delay_ms: 1,
            ..RetryConfig::default()
        });
    AdaptedClient::with_adapter(http, AdaptedClient::adapter_for_provider("openai").unwrap())
}

fn test_caller() -> LlmCaller {
    LlmCaller::new(LlmCallConfig {
        model: "gpt-4o".to_string(),
        temperature: None,
        max_tokens: None,
        reasoning_effort: None,
    })
}

/// Run one `execute_llm_call` against the given client/state.
async fn run_call(client: &AdaptedClient, state: &mut LoopState) -> Result<(), Option<LoopAction>> {
    let caller = test_caller();
    let mut messages = vec![json!({"role": "user", "content": "hello"})];
    let emitter = IterationEmitter::new(None, false);
    let monitor: Option<&dyn TaskMonitor> = None;
    execute_llm_call(
        &caller,
        client,
        &mut messages,
        &[],
        state,
        &emitter,
        monitor,
        None,
        None,
        None,
        None,
    )
    .await
    .map(|_| ())
    .map_err(Some)
}

#[tokio::test]
async fn consecutive_retryable_failures_hit_cap_and_return_error() {
    let url = spawn_static_server(
        "HTTP/1.1 503 Service Unavailable",
        r#"{"error":{"message":"overloaded"}}"#,
    )
    .await;
    let client = test_client_for(&url);
    let mut state = LoopState::new(&std::env::temp_dir());

    // The first MAX-1 failures ask the loop to continue (retry).
    for i in 1..MAX_CONSECUTIVE_LLM_FAILURES {
        match run_call(&client, &mut state).await {
            Err(Some(LoopAction::Continue)) => {}
            other => panic!("call {i}: expected Continue, got {:?}", other.is_ok()),
        }
        assert_eq!(state.consecutive_llm_failures, i);
    }

    // The MAX-th consecutive failure must give up with a real error.
    match run_call(&client, &mut state).await {
        Err(Some(LoopAction::Return(Err(AgentError::LlmError(msg))))) => {
            assert!(msg.contains("times in a row"), "msg: {msg}");
            assert!(msg.contains("OPENDEV_DEBUG=1"), "msg: {msg}");
        }
        other => panic!("expected LlmError after cap, got {:?}", other.is_ok()),
    }
}

#[tokio::test]
async fn non_retryable_failure_fails_fast_on_first_call() {
    let url = spawn_static_server(
        "HTTP/1.1 401 Unauthorized",
        r#"{"error":{"message":"Invalid API key"}}"#,
    )
    .await;
    let client = test_client_for(&url);
    let mut state = LoopState::new(&std::env::temp_dir());

    match run_call(&client, &mut state).await {
        Err(Some(LoopAction::Return(Err(AgentError::LlmError(msg))))) => {
            assert!(msg.contains("Invalid API key"), "msg: {msg}");
            assert!(msg.contains("request_id="), "msg: {msg}");
            assert!(msg.contains("OPENDEV_DEBUG=1"), "msg: {msg}");
        }
        other => panic!(
            "expected immediate LlmError for 401, got {:?}",
            other.is_ok()
        ),
    }
}

#[tokio::test]
async fn successful_call_resets_consecutive_failure_counter() {
    let url = spawn_static_server(
        "HTTP/1.1 200 OK",
        r#"{"choices":[{"index":0,"message":{"role":"assistant","content":"hi"},"finish_reason":"stop"}]}"#,
    )
    .await;
    let client = test_client_for(&url);
    let mut state = LoopState::new(&std::env::temp_dir());
    state.consecutive_llm_failures = MAX_CONSECUTIVE_LLM_FAILURES - 1;

    let result = run_call(&client, &mut state).await;
    assert!(result.is_ok(), "successful call should not error");
    assert_eq!(state.consecutive_llm_failures, 0);
}

#[test]
fn debug_hint_without_logger_mentions_env_var() {
    let hint = debug_hint(None);
    assert!(hint.contains("OPENDEV_DEBUG=1"), "hint: {hint}");
}

#[test]
fn debug_hint_with_active_logger_points_at_log_file() {
    let tmp = std::env::temp_dir();
    let logger = opendev_runtime::SessionDebugLogger::new(&tmp, "hint-test");
    let hint = debug_hint(Some(&logger));
    assert!(hint.contains("hint-test.debug"), "hint: {hint}");
}
