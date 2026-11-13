//! Bridge mode, injection queues, and agent executor management.

use std::sync::Arc;

use tokio::sync::mpsc;

use super::{AgentExecutor, AppState, INJECTION_QUEUE_CAPACITY};

impl AppState {
    // --- Bridge mode ---

    /// Check if bridge mode is active (TUI owns execution, Web UI mirrors).
    pub async fn is_bridge_mode(&self) -> bool {
        self.inner.bridge.read().await.active
    }

    /// Get the bridge session ID, if bridge mode is active.
    pub async fn bridge_session_id(&self) -> Option<String> {
        let bridge = self.inner.bridge.read().await;
        if bridge.active {
            bridge.session_id.clone()
        } else {
            None
        }
    }

    /// Activate bridge mode for a given session.
    ///
    /// While active, the Web UI should not start its own agent execution
    /// for this session; instead it should route messages to the TUI injector.
    pub async fn set_bridge_session(&self, session_id: String) {
        let mut bridge = self.inner.bridge.write().await;
        bridge.active = true;
        bridge.session_id = Some(session_id);
    }

    /// Deactivate bridge mode.
    pub async fn clear_bridge_session(&self) {
        let mut bridge = self.inner.bridge.write().await;
        bridge.active = false;
        bridge.session_id = None;
    }

    /// Check whether a mutation on a session should be blocked because
    /// the TUI owns it in bridge mode.
    ///
    /// Returns `true` if the session is bridge-owned and should not be
    /// mutated by the web server's own agent executor.
    pub async fn is_bridge_guarded(&self, session_id: &str) -> bool {
        let bridge = self.inner.bridge.read().await;
        bridge.active && bridge.session_id.as_deref() == Some(session_id)
    }

    // --- Injection queues ---

    /// Get or create the injection queue sender for a session.
    ///
    /// Returns `(sender, Option<receiver>)`. The receiver is `Some` only when the
    /// queue was first created -- the caller that creates the session's agent loop
    /// should take the receiver. Subsequent callers get `None` for the receiver.
    pub async fn get_or_create_injection_queue(
        &self,
        session_id: &str,
    ) -> (mpsc::Sender<String>, Option<mpsc::Receiver<String>>) {
        let mut queues = self.inner.injection_queues.lock().await;
        if let Some(tx) = queues.get(session_id) {
            (tx.clone(), None)
        } else {
            let (tx, rx) = mpsc::channel(INJECTION_QUEUE_CAPACITY);
            queues.insert(session_id.to_string(), tx.clone());
            (tx, Some(rx))
        }
    }

    /// Try to inject a message into a running session's queue.
    ///
    /// Returns `Ok(())` on success, `Err(message)` if queue is full or not found.
    pub async fn try_inject_message(
        &self,
        session_id: &str,
        message: String,
    ) -> Result<(), String> {
        let queues = self.inner.injection_queues.lock().await;
        if let Some(tx) = queues.get(session_id) {
            tx.try_send(message)
                .map_err(|e| format!("Injection queue full or closed: {}", e))
        } else {
            Err("No injection queue for session".to_string())
        }
    }

    /// Remove the injection queue for a session.
    pub async fn clear_injection_queue(&self, session_id: &str) {
        self.inner.injection_queues.lock().await.remove(session_id);
    }

    // --- Agent executor ---

    /// Set the agent executor implementation.
    pub async fn set_agent_executor(&self, executor: Arc<dyn AgentExecutor>) {
        *self.inner.agent_executor.lock().await = Some(executor);
    }

    /// Get the agent executor (if set).
    pub async fn agent_executor(&self) -> Option<Arc<dyn AgentExecutor>> {
        self.inner.agent_executor.lock().await.clone()
    }
}
