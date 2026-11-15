"""Jarvis Human-in-the-Loop v20 -- Graph-Level HITL-Workflows.

Professionelle HITL-Integration auf Graph-Ebene:
  - Approval/Reject/Delegate an beliebigen Knoten
  - Multi-Approval, Eskalation, Timeout-Handling
  - Gate-Nodes mit bedingtem Human-Review
  - Multi-Channel-Notifications (In-App, Webhook, Callback)
  - Selection/Edit-Nodes fuer strukturierte menschliche Eingabe

Usage:
    from cognithor.hitl import ApprovalManager, create_approval_node, HITLConfig
    from cognithor.graph import GraphBuilder, END, NodeType

    manager = ApprovalManager()
    graph = (
        GraphBuilder("review_flow")
        .add_node("process", process_handler)
        .add_node("review", create_approval_node(manager, config=HITLConfig(
            title="Review Results",
            assignees=["supervisor"],
        )), node_type=NodeType.HITL)
        .chain("process", "review", END)
        .build()
    )
"""

from cognithor.hitl.manager import ApprovalManager
from cognithor.hitl.nodes import (
    create_approval_node,
    create_edit_node,
    create_gate_node,
    create_input_node,
    create_review_node,
    create_selection_node,
)
from cognithor.hitl.notifier import HITLNotifier, NotificationRecord
from cognithor.hitl.types import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStatus,
    EscalationAction,
    EscalationPolicy,
    HITLConfig,
    HITLNodeKind,
    NotificationChannel,
    NotificationType,
    ReviewPriority,
    ReviewTask,
)

__all__ = [
    # Manager
    "ApprovalManager",
    # Request/Response
    "ApprovalRequest",
    "ApprovalResponse",
    # Enums
    "ApprovalStatus",
    "EscalationAction",
    "EscalationPolicy",
    "HITLConfig",
    "HITLNodeKind",
    # Notifier
    "HITLNotifier",
    # Config Types
    "NotificationChannel",
    "NotificationRecord",
    "NotificationType",
    "ReviewPriority",
    "ReviewTask",
    # Node Factories
    "create_approval_node",
    "create_edit_node",
    "create_gate_node",
    "create_input_node",
    "create_review_node",
    "create_selection_node",
]
