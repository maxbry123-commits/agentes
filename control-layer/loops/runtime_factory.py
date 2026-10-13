"""executor_factory — runtimes reales / stub · 0% LLM control
SOURCE: NodesLoader.executor_factory · AgentAdapter · D3 adapter.id
"""
from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable

from loops.agent_adapter import AgentExecResult, AgentAdapter, CallableAgent
from loops.nodes_loader import NodesLoader


ExecFn = Callable[[str, dict[str, Any]], AgentExecResult]


def _stub_fn(spec: dict[str, Any]) -> ExecFn:
    def fn(cap: str, payload: dict[str, Any]) -> AgentExecResult:
        return AgentExecResult(
            ok=True,
            output={
                "agent_id": spec["id"],
                "capability": cap,
                "stub": True,
                "adapter": (spec.get("meta") or {}).get("adapter", {}),
            },
        )
    return fn


def _subprocess_fn(spec: dict[str, Any], cmd_template: list[str]) -> ExecFn:
    """Ejecuta binario/comando con JSON en stdin → stdout JSON."""

    def fn(cap: str, payload: dict[str, Any]) -> AgentExecResult:
        body = json.dumps({"capability": cap, "payload": payload, "agent_id": spec["id"]})
        try:
            r = subprocess.run(
                cmd_template,
                input=body.encode("utf-8"),
                capture_output=True,
                timeout=int((spec.get("meta") or {}).get("timeout_seg") or 600),
                check=False,
            )
            if r.returncode != 0:
                return AgentExecResult(
                    ok=False,
                    error=(r.stderr.decode("utf-8", errors="replace") or f"exit {r.returncode}")[:2000],
                )
            out = r.stdout.decode("utf-8", errors="replace").strip()
            try:
                data = json.loads(out) if out else {}
            except json.JSONDecodeError:
                data = {"raw": out}
            return AgentExecResult(ok=True, output=data if isinstance(data, dict) else {"result": data})
        except subprocess.TimeoutExpired:
            return AgentExecResult(ok=False, error="timeout")
        except Exception as e:  # noqa: BLE001
            return AgentExecResult(ok=False, error=str(e))

    return fn


def temporal_fn(spec: dict[str, Any]) -> ExecFn:
    """
    adapter.id: temporal
    Busca binario:
      1. meta.adapter.entrypoint / TEMPORAL_BIN
      2. ./orquestador-temporal
      3. PATH temporal-agent
    Contrato stdin JSON → stdout JSON.
    """
    meta = spec.get("meta") or {}
    adapter = meta.get("adapter") if isinstance(meta.get("adapter"), dict) else {}
    # nodes yaml may nest adapter at top via parse — also check meta fields
    entry = (
        adapter.get("entrypoint")
        or meta.get("entrypoint")
        or os.environ.get("TEMPORAL_BIN")
        or ""
    )
    candidates = [c for c in [entry, "./orquestador-temporal", "temporal-agent"] if c]
    bin_path = None
    for c in candidates:
        p = Path(c)
        if p.is_file() and os.access(p, os.X_OK):
            bin_path = str(p.resolve())
            break
        # allow bare command on PATH
        if "/" not in c and "\\" not in c:
            bin_path = c
            break
    if not bin_path:
        # fallback stub marked temporal_missing
        base = _stub_fn(spec)

        def missing(cap: str, payload: dict[str, Any]) -> AgentExecResult:
            r = base(cap, payload)
            r.output["temporal_bin"] = "missing"
            r.output["stub"] = True
            return r

        return missing
    return _subprocess_fn(spec, [bin_path, "--agent", spec["id"], "--json"])


def openclaw_fn(spec: dict[str, Any]) -> ExecFn:
    """adapter.id: openclaw — OPENCLAW_BIN o openclaw en PATH."""
    meta = spec.get("meta") or {}
    adapter = meta.get("adapter") if isinstance(meta.get("adapter"), dict) else {}
    entry = adapter.get("entrypoint") or meta.get("entrypoint") or os.environ.get("OPENCLAW_BIN") or "openclaw"
    return _subprocess_fn(spec, [entry, "run", "--agent", spec["id"], "--json"])


def generic_fn(spec: dict[str, Any]) -> ExecFn:
    meta = spec.get("meta") or {}
    adapter = meta.get("adapter") if isinstance(meta.get("adapter"), dict) else {}
    entry = adapter.get("entrypoint") or meta.get("entrypoint")
    if entry:
        # python module:function not executed here — treat as CLI path if file
        p = Path(str(entry))
        if p.is_file():
            return _subprocess_fn(spec, [str(p)])
    return _stub_fn(spec)


FACTORY: dict[str, Callable[[dict[str, Any]], ExecFn]] = {
    "temporal": temporal_fn,
    "openclaw": openclaw_fn,
    "hermes": generic_fn,
    "generic": generic_fn,
    "stub": _stub_fn,
}


def executor_for_spec(spec: dict[str, Any]) -> ExecFn:
    meta = spec.get("meta") or {}
    adapter = meta.get("adapter") if isinstance(meta.get("adapter"), dict) else {}
    # support flat adapter in node yaml via NodesLoader meta dump
    adapter_id = str(
        adapter.get("id")
        or meta.get("adapter_id")
        or "generic"
    ).lower()
    factory = FACTORY.get(adapter_id) or generic_fn
    return factory(spec)


def build_adapter_from_project(project_root: str | Path, *, stub_ok: bool = True) -> AgentAdapter:
    """Carga nodes/*.yaml y registra runtimes según adapter.id."""

    def factory(spec: dict[str, Any]) -> ExecFn:
        return executor_for_spec(spec)

    loader = NodesLoader()
    return loader.load_project(project_root, executor_factory=factory, stub_ok=stub_ok)
