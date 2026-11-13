"""DAG-based workflow execution engine.

Executes workflows defined as directed acyclic graphs with support for:

* **Tool execution** via MCP client with Gatekeeper security checks
* **LLM calls** via configurable callable
* **Conditional branching** with safe expression evaluation (no ``eval``)
* **Human approval gates** via async callback
* **Parallel execution** up to ``max_parallel`` concurrent nodes
* **Retry strategies** (exponential backoff, linear)
* **Checkpoint / resume** for crash recovery

Usage::

    engine = WorkflowEngine(mcp_client=mcp, llm_func=llm, checkpoint_dir=path)
    run = await engine.execute(workflow)
"""

from __future__ import annotations

import asyncio
import contextlib
import re
import time
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from cognithor.core.workflow_schema import (
    NodeResult,
    NodeStatus,
    NodeType,
    RetryStrategy,
    WorkflowDefinition,
    WorkflowNode,
    WorkflowRun,
    WorkflowValidationError,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    pass

log = structlog.get_logger(__name__)

# Template pattern: ${node_id.field}
_TEMPLATE_RE = re.compile(r"\$\{(\w+)\.(\w+)\}")


class WorkflowEngine:
    """Executes workflows as directed acyclic graphs.

    All subsystem dependencies are optional.  When a dependency is absent
    the corresponding node type will fail gracefully with a descriptive error.
    """

    def __init__(
        self,
        *,
        mcp_client: Any = None,
        gatekeeper: Any = None,
        llm_func: Callable[[str], Awaitable[str]] | None = None,
        approval_func: Callable[[str, str], Awaitable[bool]] | None = None,
        checkpoint_dir: Path | None = None,
        status_callback: Callable[[str, str], Awaitable[None]] | None = None,
    ) -> None:
        self._mcp_client = mcp_client
        self._gatekeeper = gatekeeper
        self._llm_func = llm_func
        self._approval_func = approval_func
        self._checkpoint_dir = checkpoint_dir
        self._status_callback = status_callback

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, workflow: WorkflowDefinition) -> list[str]:
        """Validate a workflow definition.  Returns a list of errors (empty = valid)."""
        errors: list[str] = []
        node_ids = workflow.node_ids

        # Duplicate IDs
        seen: set[str] = set()
        for node in workflow.nodes:
            if node.id in seen:
                errors.append(f"Duplicate node ID: '{node.id}'")
            seen.add(node.id)

        # Dependency references
        for node in workflow.nodes:
            for dep in node.depends_on:
                if dep not in node_ids:
                    errors.append(f"Node '{node.id}' depends on unknown node '{dep}'")

        # Condition branch references
        for node in workflow.nodes:
            if node.type == NodeType.CONDITION:
                if node.on_true and node.on_true not in node_ids:
                    errors.append(
                        f"Condition '{node.id}' references unknown on_true '{node.on_true}'"
                    )
                if node.on_false and node.on_false not in node_ids:
                    errors.append(
                        f"Condition '{node.id}' references unknown on_false '{node.on_false}'"
                    )

        # Cycles
        cycle = self._detect_cycle(workflow)
        if cycle:
            errors.append(f"Cycle detected: {' -> '.join(cycle)}")

        # Node-type-specific requirements
        for node in workflow.nodes:
            if node.type == NodeType.TOOL and not node.tool_name:
                errors.append(f"Tool node '{node.id}' missing tool_name")
            if node.type == NodeType.LLM and not node.prompt:
                errors.append(f"LLM node '{node.id}' missing prompt")
            if node.type == NodeType.CONDITION and not node.condition:
                errors.append(f"Condition node '{node.id}' missing condition")

        # Template self-references (node referencing its own output)
        for node in workflow.nodes:
            templates: list[str] = []
            if node.prompt:
                templates.append(node.prompt)
            if node.approval_message:
                templates.append(node.approval_message)
            if node.condition:
                templates.append(node.condition)
            templates.extend(v for v in node.tool_params.values() if isinstance(v, str))
            for tmpl in templates:
                for ref_id, _ in _TEMPLATE_RE.findall(tmpl):
                    if ref_id == node.id:
                        errors.append(f"Node '{node.id}' references itself in template")

        return errors

    async def execute(
        self,
        workflow: WorkflowDefinition,
        *,
        context: dict[str, Any] | None = None,
        session: Any = None,
    ) -> WorkflowRun:
        """Execute a workflow.  Returns the final :class:`WorkflowRun` state."""
        errors = self.validate(workflow)
        if errors:
            raise WorkflowValidationError(errors)

        run = WorkflowRun(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            status=NodeStatus.RUNNING,
            started_at=_utc_now(),
            context=context or {},
        )
        for node in workflow.nodes:
            run.node_results[node.id] = NodeResult(node_id=node.id)

        log.info(
            "workflow_started",
            workflow_id=workflow.id,
            name=workflow.name,
            nodes=len(workflow.nodes),
        )

        try:
            await asyncio.wait_for(
                self._execute_loop(workflow, run, session),
                timeout=workflow.global_timeout_seconds,
            )
        except TimeoutError:
            log.warning(
                "workflow_timeout",
                workflow_id=workflow.id,
                timeout=workflow.global_timeout_seconds,
            )
            for nr in run.node_results.values():
                if nr.status in (NodeStatus.PENDING, NodeStatus.WAITING, NodeStatus.RUNNING):
                    nr.status = NodeStatus.SKIPPED
                    nr.error = "Workflow timeout"
                    nr.completed_at = _utc_now()

        run.completed_at = _utc_now()
        run.status = NodeStatus.SUCCESS if run.is_success else NodeStatus.FAILURE

        duration = (
            int((run.completed_at - run.started_at).total_seconds() * 1000) if run.started_at else 0
        )
        log.info(
            "workflow_completed",
            workflow_id=workflow.id,
            status=run.status,
            failed_nodes=run.failed_nodes,
            duration_ms=duration,
        )
        return run

    async def resume(
        self,
        checkpoint_path: str | Path,
        workflow: WorkflowDefinition,
        *,
        session: Any = None,
    ) -> WorkflowRun:
        """Resume a previously interrupted workflow from a checkpoint file."""
        run = self._load_checkpoint(Path(checkpoint_path))

        # Nodes that were RUNNING when the crash happened are reset to PENDING.
        for nr in run.node_results.values():
            if nr.status == NodeStatus.RUNNING:
                nr.status = NodeStatus.PENDING
                nr.started_at = None

        run.status = NodeStatus.RUNNING
        log.info(
            "workflow_resumed",
            workflow_id=workflow.id,
            run_id=run.id,
            pending=sum(1 for nr in run.node_results.values() if nr.status == NodeStatus.PENDING),
        )

        try:
            await asyncio.wait_for(
                self._execute_loop(workflow, run, session),
                timeout=workflow.global_timeout_seconds,
            )
        except TimeoutError:
            for nr in run.node_results.values():
                if nr.status in (NodeStatus.PENDING, NodeStatus.WAITING, NodeStatus.RUNNING):
                    nr.status = NodeStatus.SKIPPED
                    nr.error = "Workflow timeout (resumed)"
                    nr.completed_at = _utc_now()

        run.completed_at = _utc_now()
        run.status = NodeStatus.SUCCESS if run.is_success else NodeStatus.FAILURE
        return run

    def topological_sort(self, workflow: WorkflowDefinition) -> list[list[str]]:
        """Return node IDs grouped into execution layers (Kahn's algorithm).

        Each layer contains nodes that can execute in parallel.
        Raises :class:`WorkflowValidationError` if the graph contains a cycle.
        """
        in_degree: dict[str, int] = {n.id: 0 for n in workflow.nodes}
        dependents: dict[str, list[str]] = {n.id: [] for n in workflow.nodes}

        for node in workflow.nodes:
            for dep in node.depends_on:
                in_degree[node.id] += 1
                dependents[dep].append(node.id)

        queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
        layers: list[list[str]] = []

        while queue:
            layer = list(queue)
            layers.append(layer)
            queue.clear()
            for nid in layer:
                for dep_id in dependents[nid]:
                    in_degree[dep_id] -= 1
                    if in_degree[dep_id] == 0:
                        queue.append(dep_id)

        processed = sum(len(layer) for layer in layers)
        if processed != len(workflow.nodes):
            raise WorkflowValidationError(["Cycle detected in workflow graph"])

        return layers

    # ------------------------------------------------------------------
    # Private — main execution loop
    # ------------------------------------------------------------------

    async def _execute_loop(
        self,
        workflow: WorkflowDefinition,
        run: WorkflowRun,
        session: Any,
    ) -> None:
        semaphore = asyncio.Semaphore(workflow.max_parallel)

        while not run.is_complete:
            # 1. Propagate failures / skips to dependent nodes
            self._propagate_skips(workflow, run)

            if run.is_complete:
                break

            # 2. Find nodes ready to execute
            ready = self._get_ready_nodes(workflow, run)

            if not ready:
                running = [
                    nid for nid, nr in run.node_results.items() if nr.status == NodeStatus.RUNNING
                ]
                if not running:
                    # Deadlock — no nodes can proceed
                    log.error("workflow_deadlock", workflow_id=run.workflow_id)
                    for nr in run.node_results.values():
                        if nr.status == NodeStatus.PENDING:
                            nr.status = NodeStatus.SKIPPED
                            nr.error = "Deadlock — unreachable node"
                            nr.completed_at = _utc_now()
                    break
                # Some nodes are still running — wait briefly and retry
                await asyncio.sleep(0.05)
                continue

            # 3. Start ready nodes in parallel
            for node in ready:
                run.node_results[node.id].status = NodeStatus.RUNNING
                run.node_results[node.id].started_at = _utc_now()

            tasks = [self._execute_with_semaphore(semaphore, node, run, session) for node in ready]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 4. Process results
            for node, result in zip(ready, results, strict=False):
                if isinstance(result, BaseException):
                    run.node_results[node.id].status = NodeStatus.FAILURE
                    run.node_results[node.id].error = str(result)
                    run.node_results[node.id].completed_at = _utc_now()
                    log.error("node_exception", node_id=node.id, error=str(result))
                else:
                    run.node_results[node.id] = result
                    # Condition branching
                    if node.type == NodeType.CONDITION and result.status == NodeStatus.SUCCESS:
                        self._apply_condition_result(node, result, workflow, run)

            # 5. Checkpoint
            await self._save_checkpoint(run)

    async def _execute_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        node: WorkflowNode,
        run: WorkflowRun,
        session: Any,
    ) -> NodeResult:
        async with semaphore:
            return await self._execute_node(node, run, session)

    # ------------------------------------------------------------------
    # Private — single node execution with retry
    # ------------------------------------------------------------------

    async def _execute_node(
        self,
        node: WorkflowNode,
        run: WorkflowRun,
        session: Any,
    ) -> NodeResult:
        if self._status_callback:
            with contextlib.suppress(Exception):
                await asyncio.wait_for(
                    self._status_callback(node.id, f"Executing: {node.name or node.id}"),
                    timeout=2.0,
                )

        log.info("node_started", node_id=node.id, type=node.type, name=node.name)

        max_attempts = 1 + node.max_retries
        last_error: str | None = None
        last_result: NodeResult | None = None

        for attempt in range(max_attempts):
            start = time.monotonic()
            try:
                result = await asyncio.wait_for(
                    self._dispatch_node(node, run, session),
                    timeout=node.timeout_seconds,
                )
                elapsed_ms = int((time.monotonic() - start) * 1000)
                result.duration_ms = elapsed_ms
                result.retry_count = attempt

                if result.status == NodeStatus.SUCCESS:
                    log.info(
                        "node_completed",
                        node_id=node.id,
                        duration_ms=elapsed_ms,
                        attempt=attempt + 1,
                    )
                    return result

                last_result = result
                last_error = result.error

            except TimeoutError:
                last_result = None
                last_error = f"Timeout nach {node.timeout_seconds}s"
                log.warning(
                    "node_timeout",
                    node_id=node.id,
                    timeout=node.timeout_seconds,
                    attempt=attempt + 1,
                )

            except Exception as exc:
                last_result = None
                last_error = str(exc)
                log.warning(
                    "node_error",
                    node_id=node.id,
                    error=str(exc),
                    attempt=attempt + 1,
                )

            # Retry delay (skip after last attempt)
            if attempt < max_attempts - 1:
                delay = self._calculate_retry_delay(node.retry_strategy, attempt)
                log.info("node_retry", node_id=node.id, attempt=attempt + 2, delay_s=delay)
                await asyncio.sleep(delay)

        # All retries exhausted — return handler result if available, else generic
        log.warning("node_failed", node_id=node.id, attempts=max_attempts, error=last_error)
        if last_result is not None:
            last_result.retry_count = max_attempts - 1
            return last_result
        return NodeResult(
            node_id=node.id,
            status=NodeStatus.FAILURE,
            error=last_error,
            completed_at=_utc_now(),
            retry_count=max_attempts - 1,
        )

    async def _dispatch_node(
        self,
        node: WorkflowNode,
        run: WorkflowRun,
        session: Any,
    ) -> NodeResult:
        """Route to the correct handler based on node type."""
        if node.type == NodeType.TOOL:
            return await self._execute_tool_node(node, run, session)
        if node.type == NodeType.LLM:
            return await self._execute_llm_node(node, run)
        if node.type == NodeType.CONDITION:
            return await self._execute_condition_node(node, run)
        if node.type == NodeType.HUMAN_APPROVAL:
            return await self._execute_human_approval_node(node, run)

        return NodeResult(
            node_id=node.id,
            status=NodeStatus.FAILURE,
            error=f"Unknown node type: {node.type}",
            completed_at=_utc_now(),
        )

    # ------------------------------------------------------------------
    # Node type handlers
    # ------------------------------------------------------------------

    async def _execute_tool_node(
        self,
        node: WorkflowNode,
        run: WorkflowRun,
        session: Any,
    ) -> NodeResult:
        if not self._mcp_client:
            return NodeResult(
                node_id=node.id,
                status=NodeStatus.FAILURE,
                error="No MCP client available",
                completed_at=_utc_now(),
            )

        resolved_params = self._resolve_params(node.tool_params, run)

        # Gatekeeper pre-check
        if self._gatekeeper and session:
            from cognithor.models import ActionPlan, PlannedAction

            action = PlannedAction(tool=node.tool_name or "", params=resolved_params)
            plan = ActionPlan(goal=f"Workflow: {node.name or node.id}", steps=[action])
            decisions = self._gatekeeper.evaluate(plan, session)
            if decisions and not decisions[0].is_allowed:
                return NodeResult(
                    node_id=node.id,
                    status=NodeStatus.FAILURE,
                    error=f"Gatekeeper blocked: {decisions[0].reason}",
                    completed_at=_utc_now(),
                )

        result = await self._mcp_client.call_tool(node.tool_name, resolved_params)

        content = result.content if hasattr(result, "content") else str(result)
        is_error = result.is_error if hasattr(result, "is_error") else False

        return NodeResult(
            node_id=node.id,
            status=NodeStatus.FAILURE if is_error else NodeStatus.SUCCESS,
            output=content,
            error=content if is_error else None,
            completed_at=_utc_now(),
        )

    async def _execute_llm_node(
        self,
        node: WorkflowNode,
        run: WorkflowRun,
    ) -> NodeResult:
        if not self._llm_func:
            return NodeResult(
                node_id=node.id,
                status=NodeStatus.FAILURE,
                error="No LLM function available",
                completed_at=_utc_now(),
            )

        resolved_prompt = self._resolve_template(node.prompt or "", run)
        output = await self._llm_func(resolved_prompt)

        return NodeResult(
            node_id=node.id,
            status=NodeStatus.SUCCESS,
            output=output,
            completed_at=_utc_now(),
        )

    async def _execute_condition_node(
        self,
        node: WorkflowNode,
        run: WorkflowRun,
    ) -> NodeResult:
        expr = node.condition or "false"
        result = self._evaluate_condition(expr, run)
        return NodeResult(
            node_id=node.id,
            status=NodeStatus.SUCCESS,
            output=str(result).lower(),
            completed_at=_utc_now(),
        )

    async def _execute_human_approval_node(
        self,
        node: WorkflowNode,
        run: WorkflowRun,
    ) -> NodeResult:
        if not self._approval_func:
            return NodeResult(
                node_id=node.id,
                status=NodeStatus.FAILURE,
                error="No approval callback available",
                completed_at=_utc_now(),
            )

        message = self._resolve_template(node.approval_message or "Genehmigung erforderlich", run)
        approved = await self._approval_func(node.id, message)

        return NodeResult(
            node_id=node.id,
            status=NodeStatus.SUCCESS if approved else NodeStatus.FAILURE,
            output="approved" if approved else "denied",
            completed_at=_utc_now(),
        )

    # ------------------------------------------------------------------
    # Template resolution
    # ------------------------------------------------------------------

    def _resolve_template(self, template: str, run: WorkflowRun) -> str:
        """Resolve ``${node_id.field}`` references in a string."""

        def _replacer(match: re.Match[str]) -> str:
            node_id = match.group(1)
            field = match.group(2)
            nr = run.node_results.get(node_id)
            if nr is None:
                return match.group(0)  # leave unresolved
            value = getattr(nr, field, None)
            return str(value) if value is not None else ""

        return _TEMPLATE_RE.sub(_replacer, template)

    def _resolve_params(self, params: dict[str, Any], run: WorkflowRun) -> dict[str, Any]:
        """Resolve templates in tool parameter values (string values only)."""
        resolved: dict[str, Any] = {}
        for key, value in params.items():
            if isinstance(value, str):
                resolved[key] = self._resolve_template(value, run)
            else:
                resolved[key] = value
        return resolved

    # ------------------------------------------------------------------
    # Safe condition evaluation (no eval)
    # ------------------------------------------------------------------

    def _evaluate_condition(self, expr: str, run: WorkflowRun) -> bool:
        """Evaluate a simple condition expression safely.

        Supports:
        * ``true`` / ``false``
        * ``"a" == "b"``
        * ``"a" != "b"``
        * ``"text" contains "sub"``
        """
        resolved = self._resolve_template(expr, run).strip()

        if resolved.lower() == "true":
            return True
        if resolved.lower() == "false":
            return False

        if "!=" in resolved:
            left, right = resolved.split("!=", 1)
            return _strip_quotes(left) != _strip_quotes(right)

        if "==" in resolved:
            left, right = resolved.split("==", 1)
            return _strip_quotes(left) == _strip_quotes(right)

        if " contains " in resolved:
            left, right = resolved.split(" contains ", 1)
            return _strip_quotes(right) in _strip_quotes(left)

        return False

    # ------------------------------------------------------------------
    # Graph helpers
    # ------------------------------------------------------------------

    def _get_ready_nodes(
        self, workflow: WorkflowDefinition, run: WorkflowRun
    ) -> list[WorkflowNode]:
        """Nodes that are PENDING with all dependencies SUCCESS."""
        ready: list[WorkflowNode] = []
        for node in workflow.nodes:
            nr = run.node_results.get(node.id)
            if nr is None or nr.status != NodeStatus.PENDING:
                continue
            all_success = True
            for dep in node.depends_on:
                dep_nr = run.node_results.get(dep)
                if dep_nr is None or dep_nr.status != NodeStatus.SUCCESS:
                    all_success = False
                    break
            if all_success:
                ready.append(node)
        return ready

    def _propagate_skips(self, workflow: WorkflowDefinition, run: WorkflowRun) -> None:
        """Transitively skip PENDING nodes whose dependencies FAILED or were SKIPPED."""
        max_iterations = len(workflow.nodes) + 1  # upper bound: one pass per node
        for _ in range(max_iterations):
            changed = False
            for node in workflow.nodes:
                nr = run.node_results.get(node.id)
                if nr is None or nr.status != NodeStatus.PENDING:
                    continue
                for dep in node.depends_on:
                    dep_nr = run.node_results.get(dep)
                    if dep_nr and dep_nr.status in (NodeStatus.FAILURE, NodeStatus.SKIPPED):
                        nr.status = NodeStatus.SKIPPED
                        nr.error = f"Dependency '{dep}' {dep_nr.status}"
                        nr.completed_at = _utc_now()
                        changed = True
                        break
            if not changed:
                break

    def _apply_condition_result(
        self,
        node: WorkflowNode,
        result: NodeResult,
        workflow: WorkflowDefinition,
        run: WorkflowRun,
    ) -> None:
        """After a condition node succeeds, skip the inactive branch."""
        is_true = result.output.strip().lower() == "true"
        skip_node_id = node.on_false if is_true else node.on_true

        if not skip_node_id:
            return

        to_skip = self._get_descendants(skip_node_id, workflow)
        to_skip.add(skip_node_id)

        for nid in to_skip:
            nr = run.node_results.get(nid)
            if nr and nr.status == NodeStatus.PENDING:
                nr.status = NodeStatus.SKIPPED
                nr.error = f"Condition '{node.id}' branched away"
                nr.completed_at = _utc_now()

    def _get_descendants(self, node_id: str, workflow: WorkflowDefinition) -> set[str]:
        """All nodes that transitively depend on *node_id*."""
        descendants: set[str] = set()
        queue = deque([node_id])
        while queue:
            current = queue.popleft()
            for node in workflow.nodes:
                if current in node.depends_on and node.id not in descendants:
                    descendants.add(node.id)
                    queue.append(node.id)
        return descendants

    def _detect_cycle(self, workflow: WorkflowDefinition) -> list[str] | None:
        """Detect cycles via DFS.  Returns the cycle path or ``None``.

        Uses a recursion-stack approach: when a back edge to a GRAY node is
        found, the current stack is walked to reconstruct the cycle.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {n.id: WHITE for n in workflow.nodes}

        # Build adjacency: node → nodes that depend on it
        dependents: dict[str, list[str]] = {n.id: [] for n in workflow.nodes}
        for node in workflow.nodes:
            for dep in node.depends_on:
                if dep in dependents:
                    dependents[dep].append(node.id)

        def dfs(nid: str, stack: list[str]) -> list[str] | None:
            color[nid] = GRAY
            stack.append(nid)
            for neighbor in dependents.get(nid, []):
                if color.get(neighbor) == GRAY:
                    # Back edge found — extract cycle from stack
                    idx = stack.index(neighbor)
                    return [*stack[idx:], neighbor]
                if color.get(neighbor) == WHITE:
                    found = dfs(neighbor, stack)
                    if found:
                        return found
            stack.pop()
            color[nid] = BLACK
            return None

        for node in workflow.nodes:
            if color[node.id] == WHITE:
                found = dfs(node.id, [])
                if found:
                    return found
        return None

    # ------------------------------------------------------------------
    # Retry delay
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_retry_delay(strategy: RetryStrategy, attempt: int) -> float:
        """Seconds to wait before the next retry attempt."""
        if strategy == RetryStrategy.EXPONENTIAL:
            return min(2.0**attempt, 30.0)
        if strategy == RetryStrategy.LINEAR:
            return min(1.0 * (attempt + 1), 15.0)
        return 0.0

    # ------------------------------------------------------------------
    # Checkpoint persistence
    # ------------------------------------------------------------------

    async def _save_checkpoint(self, run: WorkflowRun) -> None:
        if not self._checkpoint_dir:
            return
        try:
            self._checkpoint_dir.mkdir(parents=True, exist_ok=True)
            path = self._checkpoint_dir / f"{run.id}.json"
            data = run.model_dump_json(indent=2)
            await asyncio.to_thread(path.write_text, data, "utf-8")
        except Exception as exc:
            log.warning("checkpoint_save_failed", run_id=run.id, error=str(exc))

    def _load_checkpoint(self, path: Path) -> WorkflowRun:
        data = path.read_text("utf-8")
        return WorkflowRun.model_validate_json(data)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _strip_quotes(s: str) -> str:
    """Strip surrounding whitespace and optional quotes."""
    return s.strip().strip("\"'")
