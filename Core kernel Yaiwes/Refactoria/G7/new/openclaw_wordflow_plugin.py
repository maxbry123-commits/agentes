"""G7 OpenClaw route plugin.

PLUGIN-ID: openclaw.wordflow.route.v1
IMMUTABLE: true
SOURCE: maxbry123-commits/Agentes-motores-Wordflow-YAIWES@main/openclaw.mjs

The plugin is the connection point; the OpenClaw source is not edited to connect it.
The route fails closed when the OpenClaw executable/agent is not configured.
"""
from __future__ import annotations

import json
import os
import subprocess
from typing import Any

from wordflow_kernel.gateway.intelligence import IntelligenceGateway
from .port import EngineRequest, EngineResult


class OpenClawWordflowRoute:
    """Adapt a Wordflow EngineRequest to a real OpenClaw CLI agent turn."""

    plugin_id = "openclaw.wordflow.route.v1"
    engine_id = "openclaw"
    immutable = True

    def reason(self, request: EngineRequest, gateway: IntelligenceGateway) -> EngineResult:
        entrypoint = os.environ.get("OPENCLAW_ENTRYPOINT", "openclaw").strip()
        agent = os.environ.get("OPENCLAW_AGENT", "main").strip()
        if not entrypoint or not agent:
            return EngineResult(
                engine_id=self.engine_id,
                status="DENY",
                content="",
                meta={"reason": "openclaw_route_not_configured", "plugin_id": self.plugin_id},
            )

        message = json.dumps(
            {
                "task_id": request.task_id,
                "trace_id": request.trace_id,
                "messages": request.messages,
                "context": request.context,
                "policy": request.policy,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        cmd = [entrypoint, "agent", "--agent", agent, "--message", message, "--json"]
        try:
            proc = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                timeout=float(os.environ.get("OPENCLAW_TIMEOUT_S", "600")),
                check=False,
            )
        except (OSError, ValueError) as exc:
            return EngineResult(
                engine_id=self.engine_id,
                status="ERROR",
                content="",
                meta={"reason": type(exc).__name__, "plugin_id": self.plugin_id},
            )

        if proc.returncode != 0:
            return EngineResult(
                engine_id=self.engine_id,
                status="ERROR",
                content="",
                meta={
                    "returncode": proc.returncode,
                    "stderr": proc.stderr[-1000:],
                    "plugin_id": self.plugin_id,
                },
            )

        try:
            payload: dict[str, Any] = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return EngineResult(
                engine_id=self.engine_id,
                status="ERROR",
                content="",
                meta={"reason": "openclaw_json_invalid", "plugin_id": self.plugin_id},
            )

        output = payload.get("output") or payload.get("result") or payload
        content = str(output.get("text", "")) if isinstance(output, dict) else str(output)
        return EngineResult(
            engine_id=self.engine_id,
            status="OK",
            content=content,
            meta={"plugin_id": self.plugin_id, "source": "Agentes-motores-Wordflow-YAIWES/openclaw.mjs"},
        )
