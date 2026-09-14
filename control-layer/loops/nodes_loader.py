"""Auto-register agentes desde nodes/*.yaml · 0% LLM
SOURCE: mejora B · plug-and-play cualquier agente
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Callable

from loops.agent_adapter import AgentAdapter, AgentExecResult, CallableAgent, AgentRuntime


def _load_yaml(path: Path) -> dict[str, Any]:
    import yaml
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def parse_node_doc(data: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    """Normaliza node yaml → {id, capabilities, priority, meta}."""
    node = data.get("node") or data.get("agent") or data
    agent_id = str(
        node.get("id") or node.get("agent_id") or node.get("name")
        or (path.stem if path else "unknown")
    )
    caps = node.get("capabilities") or node.get("caps") or []
    if isinstance(caps, str):
        caps = [caps]
    priority = int(node.get("priority") or 100)
    return {
        "id": agent_id,
        "capabilities": [str(c) for c in caps],
        "priority": priority,
        "meta": {k: v for k, v in node.items() if k not in ("id", "agent_id", "name", "capabilities", "caps", "priority")},
    }


def discover_node_files(nodes_dir: str | Path) -> list[Path]:
    root = Path(nodes_dir)
    if not root.is_dir():
        return []
    files = sorted(root.glob("*.yaml")) + sorted(root.glob("*.yml"))
    return files


class NodesLoader:
    """Escanea nodes/ y registra runtimes en AgentAdapter."""

    def __init__(self, adapter: AgentAdapter | None = None) -> None:
        self.adapter = adapter or AgentAdapter()
        self.loaded: list[dict[str, Any]] = []

    def load_dir(
        self,
        nodes_dir: str | Path,
        *,
        executor_factory: Callable[[dict[str, Any]], Callable[[str, dict], AgentExecResult]] | None = None,
        stub_ok: bool = True,
    ) -> AgentAdapter:
        """
        executor_factory(node_spec) → fn(capability, payload) → AgentExecResult
        Si no hay factory y stub_ok: registra stub que devuelve ok con meta.
        """
        for path in discover_node_files(nodes_dir):
            try:
                data = _load_yaml(path)
            except Exception:
                continue
            spec = parse_node_doc(data, path)
            if not spec["capabilities"]:
                # sin caps no se registra
                continue
            if executor_factory:
                fn = executor_factory(spec)
            elif stub_ok:
                def _make(s: dict[str, Any]) -> Callable[[str, dict], AgentExecResult]:
                    def stub(cap: str, payload: dict) -> AgentExecResult:
                        return AgentExecResult(
                            ok=True,
                            output={"agent_id": s["id"], "capability": cap, "stub": True, "payload_keys": list(payload.keys())},
                        )
                    return stub
                fn = _make(spec)
            else:
                continue
            runtime: AgentRuntime = CallableAgent(spec["id"], spec["capabilities"], fn)
            self.adapter.register_runtime(runtime, priority=spec["priority"])
            self.loaded.append({**spec, "path": str(path)})
        return self.adapter

    def load_project(self, project_root: str | Path, **kwargs: Any) -> AgentAdapter:
        nodes = Path(project_root) / "nodes"
        return self.load_dir(nodes, **kwargs)
