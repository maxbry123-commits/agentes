//! HTTP transport: communicates with a remote server via HTTP POST requests.

use async_trait::async_trait;
use std::collections::HashMap;

use super::McpTransport;
use super::REQUEST_TIMEOUT;
use crate::error::{McpError, McpResult};
use crate::models::{JsonRpcNotification, JsonRpcRequest, JsonRpcResponse};

/// HTTP transport: communicates with a remote server via HTTP POST requests.
pub struct HttpTransport {
    url: String,
    #[allow(dead_code)]
    headers: HashMap<String, String>,
    client: reqwest::Client,
}

impl HttpTransport {
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
impl McpTransport for HttpTransport {
    async fn connect(&mut self) -> McpResult<()> {
        // HTTP is stateless — no persistent connection needed.
        Ok(())
    }

    async fn send_request(&self, request: &JsonRpcRequest) -> McpResult<JsonRpcResponse> {
        let response = self
            .client
            .post(&self.url)
            .json(request)
            .send()
            .await
            .map_err(|e| McpError::Transport(format!("HTTP request failed: {}", e)))?;

        let status = response.status();
        if !status.is_success() {
            let body = response.text().await.unwrap_or_default();
            return Err(McpError::Transport(format!("HTTP {} — {}", status, body)));
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
            .map_err(|e| McpError::Transport(format!("HTTP notification failed: {}", e)))?;
        Ok(())
    }

    async fn close(&self) -> McpResult<()> {
        Ok(())
    }

    fn is_connected(&self) -> bool {
        true
    }

    fn transport_type(&self) -> &str {
        "http"
    }
}
