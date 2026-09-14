from __future__ import annotations

import concurrent.futures
import hashlib
import json
import re
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

import yaiwes_real_workflow_chain_v63_core as core

SCHEMA = "yaiwes.coda.bus/v7"
MCP_REGISTRY = "https://registry.modelcontextprotocol.io/v0.1/servers"

# Discovery is intentionally metadata-only. Unknown plugins are never installed
# or executed automatically. Runtime execution is limited to host-registered,
# benign adapters.
_BLOCKED_TERMS = {
    "exploit", "malware", "credential", "phishing", "payload", "shell",
    "ransomware", "bruteforce", "bypass", "attack", "exfiltration",
}


def _jsonable(value: Any, depth: int = 0) -> Any:
    if depth > 6:
        return "<depth-limit>"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return {"sha256": hashlib.sha256(value).hexdigest(), "size": len(value)}
    if isinstance(value, dict):
        return {str(k): _jsonable(v, depth + 1) for k, v in list(value.items())[:100]}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v, depth + 1) for v in list(value)[:100]]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "__dict__"):
        return _jsonable(vars(value), depth + 1)
    return repr(value)[:1000]


def _digest(value: Any) -> str:
    raw = json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-.")
    return cleaned[:120] or "task"


def _objective(task: dict[str, Any]) -> str:
    for key in ("objective", "task", "question", "instruction", "query"):
        value = task.get(key)
        if value:
            return " ".join(str(value).split())[:1200]
    return " ".join(json.dumps(_jsonable(task), ensure_ascii=False).split())[:1200]


@dataclass(frozen=True)
class ToolDescriptor:
    capability: str
    name: str
    source: str
    description: str = ""
    risk: str = "benign"
    executable: bool = False
    metadata: dict[str, Any] | None = None


class McpRegistryDiscovery:
    """Read-only discovery against an MCP Registry-compatible REST API.

    The registry is treated as metadata, not as a trust oracle. Results are
    filtered and never installed or executed automatically.
    """

    def __init__(self, url: str = MCP_REGISTRY, ttl_seconds: int = 3600, page_limit: int = 100):
        self.url = url
        self.ttl_seconds = ttl_seconds
        self.page_limit = max(1, min(page_limit, 100))
        self._lock = threading.Lock()
        self._cached_at = 0.0
        self._catalog: list[dict[str, Any]] = []

    def _fetch(self) -> list[dict[str, Any]]:
        with self._lock:
            if self._catalog and (time.time() - self._cached_at) < self.ttl_seconds:
                return list(self._catalog)
            url = self.url + "?" + urllib.parse.urlencode({"limit": self.page_limit})
            req = urllib.request.Request(url, headers={"User-Agent": "YAIWES-CODA/7 metadata-discovery"})
            with urllib.request.urlopen(req, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            servers = payload.get("servers", []) if isinstance(payload, dict) else []
            self._catalog = [x for x in servers if isinstance(x, dict)]
            self._cached_at = time.time()
            return list(self._catalog)

    @staticmethod
    def _flatten_server(item: dict[str, Any]) -> dict[str, Any]:
        server = item.get("server") if isinstance(item.get("server"), dict) else item
        return server if isinstance(server, dict) else item

    @staticmethod
    def _benign(text: str) -> bool:
        low = text.lower()
        return not any(term in low for term in _BLOCKED_TERMS)

    def discover(self, query: str, limit: int = 8) -> list[ToolDescriptor]:
        tokens = {t for t in re.findall(r"[a-z0-9_.-]{3,}", query.lower()) if t not in {"task", "with", "from", "that", "this"}}
        try:
            catalog = self._fetch()
        except Exception:
            return []
        scored: list[tuple[int, ToolDescriptor]] = []
        for item in catalog:
            server = self._flatten_server(item)
            status = str(server.get("status") or item.get("status") or "active").lower()
            if status in {"deleted", "deprecated"}:
                continue
            name = str(server.get("name") or "")
            title = str(server.get("title") or name)
            description = str(server.get("description") or "")
            haystack = f"{name} {title} {description}".lower()
            if not self._benign(haystack):
                continue
            score = sum(1 for token in tokens if token in haystack)
            if tokens and score == 0:
                continue
            scored.append((score, ToolDescriptor(
                capability="plugin.discovered",
                name=title or name,
                source="mcp-registry",
                description=description[:500],
                risk="unverified-metadata",
                executable=False,
                metadata={"server_name": name, "status": status},
            )))
        scored.sort(key=lambda x: (-x[0], x[1].name.lower()))
        return [descriptor for _, descriptor in scored[: max(1, limit)]]


class ToolBroker:
    """Capability registry for explicitly approved benign adapters."""

    def __init__(self, discovery: McpRegistryDiscovery | None = None):
        self.discovery = discovery
        self._adapters: dict[str, tuple[ToolDescriptor, Callable[[dict[str, Any]], Any]]] = {}
        self._lock = threading.Lock()

    def register(self, descriptor: ToolDescriptor, adapter: Callable[[dict[str, Any]], Any]) -> None:
        if descriptor.risk != "benign" or not descriptor.executable:
            raise ValueError("only executable benign adapters can be registered")
        if any(term in (descriptor.capability + " " + descriptor.description).lower() for term in _BLOCKED_TERMS):
            raise ValueError("blocked capability")
        with self._lock:
            self._adapters[descriptor.capability] = (descriptor, adapter)

    def has(self, capability: str) -> bool:
        with self._lock:
            return capability in self._adapters

    def execute(self, capability: str, payload: dict[str, Any]) -> Any:
        with self._lock:
            item = self._adapters.get(capability)
        if item is None:
            raise KeyError(f"capability not registered: {capability}")
        descriptor, adapter = item
        if descriptor.risk != "benign" or not descriptor.executable:
            raise PermissionError("capability is not approved for execution")
        return adapter(dict(payload))

    def discover(self, query: str) -> list[ToolDescriptor]:
        with self._lock:
            local = [descriptor for descriptor, _ in self._adapters.values()]
        remote = self.discovery.discover(query) if self.discovery is not None else []
        return local + remote


class KnowledgeStore:
    """Append-by-task persistence. Parallel branches never overwrite each other."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _component_dir(self, label: str) -> Path:
        return self.root / _safe_id(label)

    def recent(self, label: str, limit: int = 5) -> list[dict[str, Any]]:
        directory = self._component_dir(label)
        if not directory.is_dir():
            return []
        files = sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
        out: list[dict[str, Any]] = []
        for path in files:
            try:
                out.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
        return out

    def save(self, label: str, task_id: str, payload: dict[str, Any]) -> str:
        path = self._component_dir(label) / f"{_safe_id(task_id)}.json"
        core._atomic_write(path, _jsonable(payload))
        return str(path)


class CodaResearchStage:
    """Repeated research/learning stage executed before every CODA workflow."""

    def __init__(self, broker: ToolBroker):
        self.broker = broker

    def run(
        self,
        label: str,
        task: dict[str, Any],
        previous_output: Any,
        learned_context: list[dict[str, Any]],
    ) -> dict[str, Any]:
        query = f"{_objective(task)} | {label} | gaps from previous result: {json.dumps(_jsonable(previous_output), ensure_ascii=False)[:700]}"
        candidates = self.broker.discover(query)
        research_status = "ADAPTER_UNAVAILABLE"
        findings: Any = None
        if self.broker.has("web.research"):
            findings = self.broker.execute("web.research", {
                "query": query,
                "task": _jsonable(task),
                "component": label,
                "previous_output": _jsonable(previous_output),
                "learned_context": _jsonable(learned_context),
            })
            research_status = "EXECUTED"
        return {
            "schema": SCHEMA,
            "component": label,
            "research_status": research_status,
            "query": query,
            "findings": _jsonable(findings),
            "previous_output_hash": _digest(previous_output),
            "learned_context": _jsonable(learned_context),
            "tool_candidates": [asdict(x) for x in candidates[:12]],
            "tool_policy": "DISCOVER_METADATA_ONLY_EXECUTE_REGISTERED_BENIGN_ADAPTERS",
        }


def _plug_state(task_id: str, final_output: Any, history: list[dict[str, Any]]) -> dict[str, Any]:
    final_hash = _digest(final_output)
    upstream = history[-1]["internal_state"]["output_hash"]
    return {
        "schema": SCHEMA,
        "task_id": task_id,
        "status": "READY",
        "checkpoint": "UNIVERSAL_PLUG_RECEIVED_AFTER_24",
        "input_hash": final_hash,
        "upstream_output_hash": upstream,
        "continuity_ok": final_hash == upstream,
    }


def run_coda_chain(
    state_root: str | Path,
    task_id: str,
    task: dict[str, Any] | None = None,
    *,
    broker: ToolBroker | None = None,
    knowledge_root: str | Path | None = None,
) -> dict[str, Any]:
    """Run 24 CODA links.

    Every link performs research/tool discovery first and then delegates the
    actual task-solving step to the existing V6.3 internal-workflow executor.
    No component workflow is replaced by this bus.
    """
    state_root = Path(state_root)
    task = dict(task or {})
    broker = broker or ToolBroker(McpRegistryDiscovery())
    research_stage = CodaResearchStage(broker)
    knowledge = KnowledgeStore(knowledge_root or (state_root / "CODA-KNOWLEDGE"))
    components = core._component_roots_strict()

    internal_history: list[dict[str, Any]] = []
    bus_history: list[dict[str, Any]] = []
    current_output: Any = {"schema": SCHEMA, "task_id": task_id, "task": task, "origin": "CODA_INPUT"}

    for ordinal in range(1, 25):
        label = f"YAIWES {ordinal:02d}"
        learned = knowledge.recent(label)
        research = research_stage.run(label, task, current_output, learned)
        enriched_input = {
            "schema": SCHEMA,
            "task_id": task_id,
            "component": label,
            "previous_output": _jsonable(current_output),
            "previous_output_hash": _digest(current_output),
            "research": research,
            "learned_context": _jsonable(learned),
        }

        internal_state, next_output = core._run_link(
            ordinal,
            components[ordinal],
            task_id,
            task,
            enriched_input,
            state_root,
            internal_history,
        )
        if internal_state.get("input_hash") != _digest(enriched_input):
            raise RuntimeError(f"{label} did not receive its research-enriched CODA input")
        if ordinal > 1 and enriched_input["previous_output_hash"] != internal_history[-1]["output_hash"]:
            raise RuntimeError(f"handoff continuity failure before {label}")

        learned_record = {
            "schema": SCHEMA,
            "task_id": task_id,
            "component": label,
            "research": research,
            "workflow": {
                "status": internal_state.get("workflow_status"),
                "source": internal_state.get("workflow_source"),
                "symbol": internal_state.get("workflow_symbol"),
                "engine": internal_state.get("engine"),
                "output_hash": internal_state.get("output_hash"),
            },
            "lesson": {
                "input_hash": internal_state.get("input_hash"),
                "output_hash": internal_state.get("output_hash"),
                "research_digest": _digest(research),
                "tool_candidates": len(research.get("tool_candidates", [])),
            },
        }
        knowledge_path = knowledge.save(label, task_id, learned_record)
        bus_history.append({
            "order": ordinal,
            "component": label,
            "research_status": research["research_status"],
            "research_digest": _digest(research),
            "tool_candidates": len(research.get("tool_candidates", [])),
            "knowledge_path": knowledge_path,
            "internal_state": internal_state,
        })
        internal_history.append(internal_state)
        current_output = next_output

    if len(bus_history) != 24 or any(x["internal_state"].get("workflow_status") != "COMPLETED" for x in bus_history):
        raise RuntimeError("CODA chain blocked: all 24 internal workflows must complete")

    plug = _plug_state(task_id, current_output, bus_history)
    if not plug["continuity_ok"]:
        raise RuntimeError("universal plug continuity failure")
    core._atomic_write(state_root / "UNIVERSAL_PLUG" / f"{_safe_id(task_id)}.json", plug)

    report = {
        "schema": SCHEMA,
        "task_id": task_id,
        "components": 24,
        "research_cycles": 24,
        "real_internal_workflows_executed": 24,
        "completed_internal_workflows": 24,
        "universal_plug_after_component_24": True,
        "status": "CLOSED_24_CODA",
        "final_output": _jsonable(current_output),
        "evidence": bus_history,
    }
    core._atomic_write(state_root / "REPORTS" / f"{_safe_id(task_id)}.json", report)
    return report


def run_parallel_tasks(
    state_root: str | Path,
    tasks: Iterable[dict[str, Any]],
    *,
    broker: ToolBroker | None = None,
    max_workers: int = 4,
) -> dict[str, Any]:
    """Fan-out independent tasks; each branch still executes its own 24-link CODA chain."""
    state_root = Path(state_root)
    prepared: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    for index, item in enumerate(tasks, 1):
        data = dict(item)
        task_id = str(data.pop("task_id", f"branch-{index}"))
        if task_id in seen:
            raise ValueError(f"duplicate task_id: {task_id}")
        seen.add(task_id)
        prepared.append((task_id, data))
    if not prepared:
        return {"schema": SCHEMA, "branches": 0, "status": "NO_TASKS", "results": []}

    broker = broker or ToolBroker(McpRegistryDiscovery())
    knowledge_root = state_root / "CODA-KNOWLEDGE"

    def _one(entry: tuple[str, dict[str, Any]]) -> dict[str, Any]:
        task_id, payload = entry
        branch_root = state_root / "BRANCHES" / _safe_id(task_id)
        return run_coda_chain(
            branch_root,
            task_id,
            payload,
            broker=broker,
            knowledge_root=knowledge_root,
        )

    workers = max(1, min(max_workers, len(prepared)))
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers, thread_name_prefix="yaiwes-coda") as pool:
        futures = {pool.submit(_one, entry): entry[0] for entry in prepared}
        for future in concurrent.futures.as_completed(futures):
            task_id = futures[future]
            try:
                results.append({"task_id": task_id, "status": "COMPLETED", "report": future.result()})
            except Exception as exc:
                results.append({"task_id": task_id, "status": "FAILED", "error": str(exc)})
    results.sort(key=lambda x: x["task_id"])
    status = "COMPLETED" if all(x["status"] == "COMPLETED" for x in results) else "PARTIAL_FAILURE"
    report = {"schema": SCHEMA, "branches": len(results), "status": status, "results": results}
    core._atomic_write(state_root / "PARALLEL-REPORT.json", report)
    return report
