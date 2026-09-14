"""Jarvis Graph Orchestrator v18 -- DAG-based workflow engine.

LangGraph-inspired state graph engine with:
  - Conditional edges + router nodes
  - Parallel branches
  - Loop support with cycle protection
  - Checkpoint/resume (HITL)
  - Fluent GraphBuilder API
  - Built-in node handlers
  - Mermaid diagram export

Usage:
    from cognithor.graph import GraphBuilder, GraphEngine, GraphState, END, NodeType

    graph = (
        GraphBuilder("my_flow")
        .add_node("step1", my_handler)
        .add_node("step2", my_handler2)
        .add_edge("step1", "step2")
        .add_edge("step2", END)
        .build()
    )

    engine = GraphEngine()
    result = await engine.run(graph, GraphState(data="input"))
"""

from cognithor.graph.builder import (
    GraphBuilder,
    branch_graph,
    linear_graph,
    loop_graph,
)
from cognithor.graph.engine import GraphEngine
from cognithor.graph.nodes import (
    accumulate_node,
    condition_node,
    counter_node,
    delay_node,
    gate_node,
    key_router,
    llm_node,
    log_node,
    merge_node,
    set_value_node,
    threshold_router,
    tool_node,
    transform_node,
)
from cognithor.graph.state import StateManager
from cognithor.graph.types import (
    END,
    GRAPH_VERSION,
    START,
    Checkpoint,
    Edge,
    EdgeType,
    ExecutionRecord,
    ExecutionStatus,
    GraphDefinition,
    GraphState,
    Node,
    NodeResult,
    NodeStatus,
    NodeType,
)

__all__ = [
    "END",
    # Constants
    "GRAPH_VERSION",
    "START",
    "Checkpoint",
    "Edge",
    "EdgeType",
    "ExecutionRecord",
    "ExecutionStatus",
    # Builder
    "GraphBuilder",
    "GraphDefinition",
    "GraphEngine",
    # Core Types
    "GraphState",
    "Node",
    "NodeResult",
    "NodeStatus",
    # Enums
    "NodeType",
    # Engine & State
    "StateManager",
    "accumulate_node",
    "branch_graph",
    "condition_node",
    "counter_node",
    "delay_node",
    "gate_node",
    "key_router",
    "linear_graph",
    # Built-in Nodes
    "llm_node",
    "log_node",
    "loop_graph",
    "merge_node",
    "set_value_node",
    "threshold_router",
    "tool_node",
    "transform_node",
]
