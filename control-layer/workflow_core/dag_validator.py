from .dag import DAGDefinition
from .errors import ContractViolationError


class DAGValidator:

    def validate(self, dag: DAGDefinition) -> None:
        self._validate_unique_nodes(dag)
        self._validate_dependencies(dag)
        self._validate_no_cycles(dag)

    def _validate_unique_nodes(self, dag: DAGDefinition) -> None:
        ids = [node.node_id for node in dag.nodes]
        if len(ids) != len(set(ids)):
            raise ContractViolationError("DAG contains duplicated node IDs")

    def _validate_dependencies(self, dag: DAGDefinition) -> None:
        node_ids = {node.node_id for node in dag.nodes}
        for node in dag.nodes:
            for dependency in node.dependencies:
                if dependency not in node_ids:
                    raise ContractViolationError(
                        f"Node '{node.node_id}' depends on unknown node '{dependency}'"
                    )

    def _validate_no_cycles(self, dag: DAGDefinition) -> None:
        graph = {node.node_id: node.dependencies for node in dag.nodes}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visiting:
                raise ContractViolationError(f"DAG cycle detected at '{node_id}'")
            if node_id in visited:
                return
            visiting.add(node_id)
            for dependency in graph[node_id]:
                visit(dependency)
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in graph:
            visit(node_id)
