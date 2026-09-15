//! Background agent runtime for continuing agent work after Ctrl+B.
//!
//! Creates a lightweight fork of AgentRuntime that shares expensive Arc-wrapped
//! resources but owns its own session, cost tracker, and react loop.

use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

use tracing::{info, warn};

use opendev_agents::llm_calls::{LlmCallConfig, LlmCaller};
use opendev_agents::react_loop::{ReactLoop, ReactLoopConfig};
use opendev_agents::traits::{AgentEventCallback, AgentResult};
use opendev_context::{ArtifactIndex, ContextCompactor};
use opendev_history::SessionManager;
use opendev_models::AppConfig;
use opendev_runtime::{CostTracker, InterruptToken, SessionDebugLogger};
use opendev_tools_core::{ToolContext, ToolRegistry};

use super::AgentRuntime;

/// Lightweight runtime for background agent tasks.
///
/// Shares expensive Arc-wrapped resources (tool_registry, http_client, mcp_manager)
/// with the foreground runtime, but owns its own session, react loop, and cost tracker.
#[allow(dead_code)]
pub struct BackgroundRuntime {
    // Shared (Arc clone from parent)
    tool_registry: Arc<ToolRegistry>,
    http_client: Arc<opendev_http::adapted_client::AdaptedClient>,

    // Owned (fresh per background task)
    config: AppConfig,
    working_dir: PathBuf,
    session_manager: SessionManager,
    llm_caller: LlmCaller,
    react_loop: ReactLoop,
    cost_tracker: Mutex<CostTracker>,
    artifact_index: Mutex<ArtifactIndex>,
    compactor: Mutex<ContextCompactor>,
    todo_manager: Arc<Mutex<opendev_runtime::TodoManager>>,
    debug_logger: Arc<SessionDebugLogger>,
}

impl BackgroundRuntime {
    /// Run a query through the agent pipeline.
    ///
    /// Simplified version of `AgentRuntime::run_query()` that:
    /// - Auto-approves all tools (no `tool_approval_tx`)
    /// - Skips ask-user interactions
    /// - Uses its own fresh interrupt token
    pub async fn run_query(
        &mut self,
        query: &str,
        system_prompt: &str,
        event_callback: Option<&dyn AgentEventCallback>,
        interrupt_token: Option<&InterruptToken>,
    ) -> Result<AgentResult, opendev_agents::traits::AgentError> {
        info!(query_len = query.len(), "Background: running query");

        // Prepare messages from session history
        let session_messages = self
            .session_manager
            .current_session()
            .map(|s| opendev_history::message_convert::chatmessages_to_api_values(&s.messages))
            .unwrap_or_default();

        // Build simple messages array with system prompt + history
        let mut messages = Vec::new();
        messages.push(serde_json::json!({"role": "system", "content": system_prompt}));
        messages.extend(session_messages);

        // Get tool schemas
        let tool_schemas = self.tool_registry.get_schemas();

        // Create tool context (auto-approve — no tool_approval_tx)
        let tool_context = ToolContext {
            working_dir: self.working_dir.clone(),
            is_subagent: false,
            session_id: self.session_manager.current_session().map(|s| s.id.clone()),
            values: HashMap::new(),
            timeout_config: None,
            cancel_token: interrupt_token.map(|t| t.child_token()),
            diagnostic_provider: None,
            shared_state: None,
        };

        // Set original task for completion nudge context
        self.react_loop.set_original_task(Some(query.to_string()));

        // Run the ReAct loop (no tool approval — auto-approve everything)
        let cancel_token = interrupt_token.map(|t| t.child_token());
        let result = self
            .react_loop
            .run(
                &self.llm_caller,
                &self.http_client,
                &mut messages,
                &tool_schemas,
                &self.tool_registry,
                &tool_context,
                interrupt_token,
                event_callback,
                Some(&self.cost_tracker),
                Some(&self.artifact_index),
                Some(&self.compactor),
                Some(&self.todo_manager),
                cancel_token.as_ref(),
                None, // No tool approval — auto-approve in background
                Some(&*self.debug_logger),
            )
            .await?;

        // Save session
        if let Err(e) = self.session_manager.save_current() {
            warn!("Background: failed to save session: {e}");
        }

        // Log cost
        if let Ok(tracker) = self.cost_tracker.lock() {
            info!(
                cost = tracker.format_cost(),
                calls = tracker.call_count,
                "Background: query completed"
            );
        }

        Ok(result)
    }

    /// Get the total cost in USD for this background task.
    pub fn total_cost_usd(&self) -> f64 {
        self.cost_tracker
            .lock()
            .map(|t| t.total_cost_usd)
            .unwrap_or(0.0)
    }
}

impl AgentRuntime {
    /// Create a background runtime that shares Arc resources with this runtime.
    ///
    /// The forked session should be created via `SessionManager::fork_session()`
    /// before calling this method.
    pub fn create_background_runtime(
        &self,
        session_manager: SessionManager,
    ) -> Result<BackgroundRuntime, String> {
        let llm_caller = LlmCaller::new(LlmCallConfig {
            model: self.llm_caller.config.model.clone(),
            temperature: self.llm_caller.config.temperature,
            max_tokens: self.llm_caller.config.max_tokens,
            reasoning_effort: self.llm_caller.config.reasoning_effort.clone(),
        });

        let react_loop = ReactLoop::new(ReactLoopConfig::default());
        let cost_tracker = Mutex::new(CostTracker::new());
        let artifact_index = Mutex::new(ArtifactIndex::new());
        let compactor = Mutex::new(ContextCompactor::new(self.config.max_context_tokens));

        Ok(BackgroundRuntime {
            tool_registry: Arc::clone(&self.tool_registry),
            http_client: Arc::clone(&self.http_client),
            config: self.config.clone(),
            working_dir: self.working_dir.clone(),
            session_manager,
            llm_caller,
            react_loop,
            cost_tracker,
            artifact_index,
            compactor,
            todo_manager: Arc::clone(&self.todo_manager),
            debug_logger: Arc::clone(&self.debug_logger),
        })
    }
}
