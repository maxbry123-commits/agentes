//! Approval, ask-user, and plan-approval oneshot-based request handling.

use tokio::sync::oneshot;

use super::{
    AppState, ApprovalResult, AskUserResult, PendingApproval, PendingApprovalSlot, PendingAskUser,
    PendingAskUserSlot, PendingPlanApproval, PendingPlanApprovalSlot, PlanApprovalResult,
};

impl AppState {
    // --- Approvals (oneshot-based) ---

    /// Add a pending approval request.
    ///
    /// Returns a `oneshot::Receiver` that the caller can `.await` to block
    /// until the approval is resolved (or the state is torn down / interrupted).
    pub async fn add_pending_approval(
        &self,
        id: String,
        approval: PendingApproval,
    ) -> oneshot::Receiver<ApprovalResult> {
        let (tx, rx) = oneshot::channel();
        self.inner.pending_approvals.lock().await.insert(
            id,
            PendingApprovalSlot {
                meta: approval,
                tx: Some(tx),
            },
        );
        rx
    }

    /// Resolve a pending approval by sending through the oneshot channel.
    ///
    /// Returns the approval metadata if found, `None` if not found or already resolved.
    pub async fn resolve_approval(
        &self,
        id: &str,
        approved: bool,
        auto_approve: bool,
    ) -> Option<PendingApproval> {
        let mut approvals = self.inner.pending_approvals.lock().await;
        if let Some(mut slot) = approvals.remove(id) {
            if let Some(tx) = slot.tx.take() {
                let _ = tx.send(ApprovalResult {
                    approved,
                    auto_approve,
                });
            }
            Some(slot.meta)
        } else {
            None
        }
    }

    /// Get metadata for a pending approval (without resolving it).
    pub async fn get_pending_approval(&self, id: &str) -> Option<PendingApproval> {
        self.inner
            .pending_approvals
            .lock()
            .await
            .get(id)
            .map(|slot| slot.meta.clone())
    }

    /// Clear all pending approvals for a session (e.g. when session ends).
    ///
    /// Sends rejection through the oneshot channels so any blocked agent
    /// tasks wake up rather than hanging forever.
    pub async fn clear_session_approvals(&self, session_id: &str) {
        let mut approvals = self.inner.pending_approvals.lock().await;
        let to_remove: Vec<String> = approvals
            .iter()
            .filter(|(_, slot)| slot.meta.session_id.as_deref() == Some(session_id))
            .map(|(id, _)| id.clone())
            .collect();

        for id in to_remove {
            if let Some(mut slot) = approvals.remove(&id)
                && let Some(tx) = slot.tx.take()
            {
                let _ = tx.send(ApprovalResult {
                    approved: false,
                    auto_approve: false,
                });
            }
        }
    }

    // --- Ask-user (oneshot-based) ---

    /// Add a pending ask-user request.
    ///
    /// Returns a `oneshot::Receiver` that the agent can `.await`.
    pub async fn add_pending_ask_user(
        &self,
        id: String,
        ask_user: PendingAskUser,
    ) -> oneshot::Receiver<AskUserResult> {
        let (tx, rx) = oneshot::channel();
        self.inner.pending_ask_users.lock().await.insert(
            id,
            PendingAskUserSlot {
                meta: ask_user,
                tx: Some(tx),
            },
        );
        rx
    }

    /// Resolve a pending ask-user request.
    pub async fn resolve_ask_user(
        &self,
        id: &str,
        answers: Option<serde_json::Value>,
        cancelled: bool,
    ) -> Option<PendingAskUser> {
        let mut ask_users = self.inner.pending_ask_users.lock().await;
        if let Some(mut slot) = ask_users.remove(id) {
            if let Some(tx) = slot.tx.take() {
                let _ = tx.send(AskUserResult { answers, cancelled });
            }
            Some(slot.meta)
        } else {
            None
        }
    }

    /// Get metadata for a pending ask-user request.
    pub async fn get_pending_ask_user(&self, id: &str) -> Option<PendingAskUser> {
        self.inner
            .pending_ask_users
            .lock()
            .await
            .get(id)
            .map(|slot| slot.meta.clone())
    }

    // --- Plan approval (oneshot-based) ---

    /// Add a pending plan approval request.
    ///
    /// Returns a `oneshot::Receiver` that the agent can `.await` to block
    /// until the plan is approved, rejected, or revised.
    pub async fn add_pending_plan_approval(
        &self,
        id: String,
        plan_approval: PendingPlanApproval,
    ) -> oneshot::Receiver<PlanApprovalResult> {
        let (tx, rx) = oneshot::channel();
        self.inner.pending_plan_approvals.lock().await.insert(
            id,
            PendingPlanApprovalSlot {
                meta: plan_approval,
                tx: Some(tx),
            },
        );
        rx
    }

    /// Resolve a pending plan approval.
    ///
    /// `action` is typically "approve", "reject", or "revise".
    /// `feedback` is optional textual feedback from the user.
    ///
    /// Returns the plan-approval metadata if found, `None` if already resolved.
    pub async fn resolve_plan_approval(
        &self,
        id: &str,
        action: String,
        feedback: String,
    ) -> Option<PendingPlanApproval> {
        let mut plan_approvals = self.inner.pending_plan_approvals.lock().await;
        if let Some(mut slot) = plan_approvals.remove(id) {
            if let Some(tx) = slot.tx.take() {
                let _ = tx.send(PlanApprovalResult { action, feedback });
            }
            Some(slot.meta)
        } else {
            None
        }
    }

    /// Get metadata for a pending plan approval.
    pub async fn get_pending_plan_approval(&self, id: &str) -> Option<PendingPlanApproval> {
        self.inner
            .pending_plan_approvals
            .lock()
            .await
            .get(id)
            .map(|slot| slot.meta.clone())
    }

    /// Clear all pending plan approvals for a session.
    pub async fn clear_session_plan_approvals(&self, session_id: &str) {
        let mut plan_approvals = self.inner.pending_plan_approvals.lock().await;
        let to_remove: Vec<String> = plan_approvals
            .iter()
            .filter(|(_, slot)| slot.meta.session_id.as_deref() == Some(session_id))
            .map(|(id, _)| id.clone())
            .collect();

        for id in to_remove {
            if let Some(mut slot) = plan_approvals.remove(&id)
                && let Some(tx) = slot.tx.take()
            {
                let _ = tx.send(PlanApprovalResult {
                    action: "reject".to_string(),
                    feedback: "Session ended".to_string(),
                });
            }
        }
    }
}
