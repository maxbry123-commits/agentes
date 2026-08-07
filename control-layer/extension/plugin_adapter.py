"""Plugin adapter · cara extensión kernel del núcleo dual.

El host (OpenClaw / TEAM / mock) solo habla por este adapter:
  adapter = PluginAdapter()
  adapter.on_mount(ctx)
  out = adapter.on_turn(turn)
  adapter.on_unmount()

Monta Evolution Engine automáticamente (capability evolution.evolve).
"""
from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from extension.abi import EvidenceOutput, WordflowExtension
from format.output_chef import format_output
from runtime.durable import DurableRuntime


@dataclass
class TurnInput:
    text: str
    op_type: str = "LLM_CALL"
    mission_id: str | None = None
    nivel: str = "MID"
    payload: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_mapping(d: Mapping[str, Any]) -> "TurnInput":
        return TurnInput(
            text=str(d.get("text") or d.get("content") or d.get("message") or ""),
            op_type=str(d.get("op_type") or "LLM_CALL"),
            mission_id=d.get("mission_id"),
            nivel=str(d.get("nivel") or d.get("level") or "MID"),
            payload=dict(d.get("payload") or {}),
            meta=dict(d.get("meta") or {}),
        )


@dataclass
class TurnOutput:
    ok: bool
    mission_id: str | None
    evidence: dict[str, Any]
    chat_output: dict[str, Any]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PluginAdapter:
    """Monta WordflowExtension + Evolution como plugin del host."""

    def __init__(self, state_dir: Path | None = None) -> None:
        self.ext = WordflowExtension()
        self.runtime: DurableRuntime | None = None
        self.state_dir = Path(state_dir) if state_dir else None
        self._mounted = False
        self.evolution_svc: Any = None
        self.evolution_mounted: list[str] = []

    def on_mount(self, ctx: Mapping[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(ctx or {})
        ctx.setdefault("mount_mode", "extension")
        ok = self.ext.load(ctx)
        if self.state_dir or ctx.get("state_dir"):
            self.state_dir = Path(ctx.get("state_dir") or self.state_dir or "./extension_state")
            self.runtime = DurableRuntime(self.state_dir)
        self._mounted = bool(ok)

        # Auto-mount Evolution Engine → ABI (evolution.evolve + absorbed caps)
        if ctx.get("enable_evolution", True):
            try:
                from extension.evolution_mount import mount_evolution

                sources = str(ctx.get("evolution_sources") or "evolution/sources")
                self.evolution_svc, self.evolution_mounted = mount_evolution(self.ext, sources_dir=sources)
            except Exception as e:  # noqa: BLE001 — no bloquear mount del host
                self.evolution_mounted = []
                health = self.ext.health().to_dict()
                health["evolution_error"] = str(e)
                return health

        health = self.ext.health().to_dict()
        health["evolution_capabilities"] = list(self.evolution_mounted)
        return health

    def on_unmount(self) -> None:
        self.ext.unload()
        self._mounted = False
        self.evolution_svc = None
        self.evolution_mounted = []

    def health(self) -> dict[str, Any]:
        h = self.ext.health().to_dict()
        h["evolution_capabilities"] = list(self.evolution_mounted)
        return h

    def capabilities(self) -> list[str]:
        return self.ext.capabilities()

    def on_turn(self, turn: TurnInput | Mapping[str, Any]) -> TurnOutput:
        if not self._mounted:
            return TurnOutput(False, None, {}, {}, "plugin_not_mounted")
        t = turn if isinstance(turn, TurnInput) else TurnInput.from_mapping(turn)

        mission_id = t.mission_id
        if self.runtime is not None and not mission_id:
            st = self.runtime.create_mission(t.text[:200] or "turn")
            mission_id = st.mission_id

        payload = dict(t.payload)
        payload.setdefault("text", t.text)
        payload.setdefault("goal", t.text)

        # Ruta directa: evolucionar si op_type lo pide
        if t.op_type in ("EVOLVE", "ABSORB", "evolution.evolve") or payload.get("evolve_path"):
            evo = self.ext.execute(
                "evolution.evolve",
                {
                    "path": payload.get("evolve_path") or payload.get("path") or "",
                    "identity": payload.get("identity") or "absorbed",
                    "source_type": payload.get("source_type") or "agent",
                    "repo_url": payload.get("repo_url") or "",
                    "allow_director_license": bool(payload.get("allow_director_license", False)),
                },
                nivel=t.nivel,
            )
            chat = format_output(
                {
                    "mission_id": mission_id or "",
                    "status": "COMPLETED" if evo.ok else "FAILED",
                    "summary": "evolution_ok" if evo.ok else "evolution_fail",
                    "evidence_hash": evo.evidence_hash or "sha256:none",
                    "sheriff_state": "GREEN" if evo.ok else "RED",
                    "mode": "extension",
                    "steps_done": ["mount", "evolution.evolve"],
                    "errors": [evo.error] if evo.error else [],
                }
            )
            return TurnOutput(evo.ok, mission_id, evo.to_dict(), chat, evo.error)

        gate = self.ext.execute(
            "sheriff_gate",
            {"op_type": t.op_type, "payload": payload},
            nivel=t.nivel,
        )
        if not gate.ok:
            chat = format_output(
                {
                    "mission_id": mission_id or "",
                    "status": "BLOCKED",
                    "summary": "extension_sheriff_blocked",
                    "evidence_hash": gate.evidence_hash or "sha256:none",
                    "sheriff_state": gate.sheriff_state or "RED",
                    "errors": [gate.error or "blocked"],
                    "blocked_reason": gate.error or "blocked",
                    "mode": "extension",
                }
            )
            return TurnOutput(False, mission_id, gate.to_dict(), chat, gate.error)

        routed = self.ext.execute(
            "route_op",
            {"op_type": t.op_type, "payload": payload},
            nivel=t.nivel,
        )
        if self.runtime is not None and mission_id:
            self.runtime.checkpoint(
                mission_id,
                phase="extension_turn",
                cursor={"op": t.op_type},
                evidence_hash=routed.evidence_hash,
            )

        chat = format_output(
            {
                "mission_id": mission_id or "",
                "status": "COMPLETED" if routed.ok else "FAILED",
                "summary": "extension_turn_ok" if routed.ok else "extension_turn_fail",
                "evidence_hash": routed.evidence_hash or "sha256:none",
                "set_hash": routed.set_hash,
                "sheriff_state": gate.sheriff_state or "GREEN",
                "mode": "extension",
                "steps_done": ["mount", "sheriff_gate", "route_op"],
            }
        )
        return TurnOutput(routed.ok, mission_id, routed.to_dict(), chat, routed.error)


def create_adapter(state_dir: str | Path | None = None) -> PluginAdapter:
    return PluginAdapter(Path(state_dir) if state_dir else None)
