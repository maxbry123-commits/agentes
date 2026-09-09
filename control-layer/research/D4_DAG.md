# D4 · dag/*.yaml — Investigación

## Fuentes
- orchestra (itsHabib): depends_on agents, DAG tiers
- YAML MultiAgent Orchestrator: sequential/parallel branches
- Temporal/LangGraph: edges, no cycles, checkpoint per node
- Step Functions: Next/End, Catch→Recovery
- UOOS: L08 never skip DAG; entry/exit
- Router: required_capabilities en lugar de agent_id fijo

## Skills (transforms deterministas)
1. parse_dag_yaml
2. validate_no_cycles (Kahn/DFS)
3. validate_nodes_exist_in_registry_or_caps
4. topo_sort
5. entry_exit_check

## Gaps plantilla B4
- Sin required_capabilities por nodo
- Sin timeout por nodo
- Sin on_fail → recovery id
