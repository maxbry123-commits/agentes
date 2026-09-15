//! SSE transport: communicates with a server using Server-Sent Events.

use async_trait::async_trait;
use std::collections::HashMap;

use super::McpTransport;
use super::REQUEST_TIMEOUT;
use crate::error::{McpError, McpResult};
use crate::models::{JsonRpcNotification, JsonRpcRequest, JsonRpcResponse};

/// SSE transport: communicates with a server using Server-Sent Events.
pub struct SseTransport {
    url: String,
    #[allow(dead_code)]
    headers: HashMap<String, String>,
    client: reqwest::Client,
}

impl SseTransport {
    pub fn new(url: String, headers: HashMap<String, String>) -> Self {
        let mut header_map = reqwest::header::HeaderMap::new();
        for (key, value) in &headers {
            if let (Ok(name), Ok(val)) = (
                reqwest::header::HeaderName::from_bytes(key.as_bytes()),
                reqwest::header::HeaderValue::from_str(value),
            ) {
                header_map.insert(name, val);
            }
        }

        let client = reqwest::Client::builder()
            .default_headers(header_map)
            .timeout(REQUEST_TIMEOUT)
            .build()
            .unwrap_or_default();

        Self {
            url,
            headers,
            client,
        }
    }
}

#[async_trait]
impl McpTransport for SseTransport {
    async fn connect(&mut self) -> McpResult<()> {
        Ok(())
    }

    async fn send_request(&self, request: &JsonRpcRequest) -> McpResult<JsonRpcResponse> {
        // SSE transport sends requests via POST and receives responses via SSE stream.
        // For now, use simple HTTP POST (full SSE streaming is a larger implementation).
        let response = self
            .client
            .post(&self.url)
            .json(request)
            .send()
            .await
            .map_err(|e| McpError::Transport(format!("SSE request failed: {}", e)))?;

        let status = response.status();
        if !status.is_success() {
            let body = response.text().await.unwrap_or_default();
            return Err(McpError::Transport(format!(
                "SSE HTTP {} — {}",
                status, body
            )));
        }

        let rpc_response = response.json::<JsonRpcResponse>().await?;
        Ok(rpc_response)
    }

    async fn send_notification(&self, notification: &JsonRpcNotification) -> McpResult<()> {
        self.client
            .post(&self.url)
            .json(notification)
            .send()
            .await
            .map_err(|e| McpError::Transport(format!("SSE notification failed: {}", e)))?;
        Ok(())
    }

    async fn close(&self) -> McpResult<()> {
        Ok(())
    }

    fn is_connected(&self) -> bool {
        true
    }

    fn transport_type(&self) -> &str {
        "sse"
    }
}
