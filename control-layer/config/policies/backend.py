from workflow_core.policies import WorkflowPolicy

backend_policy = WorkflowPolicy(
    allowed_groups=frozenset({"backend"}),
    allowed_roles=frozenset({
        "architecture",
        "backend_primary_executor",
        "backend_recovery",
        "backend_repair",
        "backend_final_repair",
    }),
    max_nodes=100,
    require_dependencies=True,
    require_sheriff=True,
)
