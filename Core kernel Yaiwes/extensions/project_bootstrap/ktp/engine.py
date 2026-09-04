# -*- coding: utf-8 -*-
"""
KTP Engine — Kernel Thought Protocol
Máquina de estados determinista basada en emojis.
Fuente: PIPELINE 12 FULL §9, PIPELINE 13, states.yaml
A2 — Implementación ejecutable (no stub)
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None


class StateType(str, Enum):
    D = "D"
    H = "H"
    D_H = "D+H"
    D_STRICT = "D_STRICT"


@dataclass
class KTPState:
    name: str
    emoji: str
    tipo: StateType
    entrada: List[str]
    salida: str
    microflujo: str
    resource_brain: bool
    descripcion: str
    llm_allowed: str = "never"  # never | conditional | always
    resource_query: Optional[str] = None


@dataclass
class CycleRecord:
    cycle_id: str
    from_state: str
    to_state: str
    resources_used: List[str]
    input_hash: str
    output_hash: str
    timestamp: float
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KTPContext:
    """Contexto de un ciclo de pensamiento."""
    current_state: str = "OBJETIVO"
    goal_struct: Optional[Dict] = None
    task_list: Optional[List[Dict]] = None
    execution_plan: Optional[Dict] = None
    next_step: Optional[Dict] = None
    step_result: Optional[Dict] = None
    blockers: List[Dict] = field(default_factory=list)
    selected_capabilities: List[str] = field(default_factory=list)
    history: List[CycleRecord] = field(default_factory=list)
    raw_input: Optional[str] = None


class KTPEngine:
    """
    Motor determinista del Kernel Thought Protocol.
    - Carga states.yaml
    - Valida transiciones
    - Ejecuta microflujos D (sin LLM)
    - Delega a Director solo en estados tipo H
    - Consulta Resource Brain solo cuando resource_brain=True
    """

    def __init__(self, states_path: Optional[Path] = None):
        if states_path is None:
            states_path = Path(__file__).parent / "states.yaml"
        self.states_path = states_path
        self.states: Dict[str, KTPState] = {}
        self.transitions: Dict[str, List[str]] = {}
        self._load_states()

    def _load_states(self) -> None:
        if not self.states_path.exists():
            raise FileNotFoundError(f"states.yaml not found: {self.states_path}")
        if yaml is None:
            raise RuntimeError("PyYAML required: pip install pyyaml")

        with open(self.states_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        raw_states = data.get("states", {})
        for name, cfg in raw_states.items():
            tipo_raw = cfg.get("tipo", "D")
            if tipo_raw == "D+H":
                tipo = StateType.D_H
            elif tipo_raw == "D_STRICT":
                tipo = StateType.D_STRICT
            elif tipo_raw == "H":
                tipo = StateType.H
            else:
                tipo = StateType.D

            llm = cfg.get("llm_allowed", "never")
            if tipo == StateType.H:
                llm = "always"
            elif tipo == StateType.D_STRICT:
                llm = "never"
            elif tipo == StateType.D_H:
                llm = cfg.get("llm_allowed", "conditional")

            self.states[name] = KTPState(
                name=name,
                emoji=cfg.get("emoji", ""),
                tipo=tipo,
                entrada=cfg.get("entrada", []),
                salida=cfg.get("salida", ""),
                microflujo=cfg.get("microflujo", ""),
                resource_brain=bool(cfg.get("resource_brain", False)),
                descripcion=cfg.get("descripcion", ""),
                llm_allowed=llm,
                resource_query=cfg.get("resource_query"),
            )

        self.transitions = data.get("transitions", {})

    def get_state(self, name: str) -> KTPState:
        if name not in self.states:
            raise KeyError(f"Unknown KTP state: {name}")
        return self.states[name]

    def can_transition(self, from_state: str, to_state: str) -> bool:
        allowed = self.transitions.get(from_state, [])
        return to_state in allowed

    def _hash(self, data: Any) -> str:
        raw = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return "sha256:" + hashlib.sha256(raw).hexdigest()

    def transition(
        self,
        ctx: KTPContext,
        to_state: str,
        output_data: Any = None,
        resources_used: Optional[List[str]] = None,
    ) -> KTPContext:
        """Transición validada + registro de evidencia."""
        from_state = ctx.current_state
        if not self.can_transition(from_state, to_state):
            raise ValueError(
                f"Invalid transition: {from_state} → {to_state}. "
                f"Allowed: {self.transitions.get(from_state, [])}"
            )

        input_hash = self._hash({
            "state": from_state,
            "goal": ctx.goal_struct,
            "tasks": ctx.task_list,
            "raw": ctx.raw_input,
        })
        output_hash = self._hash(output_data) if output_data is not None else self._hash({})

        record = CycleRecord(
            cycle_id=str(uuid.uuid4()),
            from_state=from_state,
            to_state=to_state,
            resources_used=resources_used or [],
            input_hash=input_hash,
            output_hash=output_hash,
            timestamp=time.time(),
            evidence={"output": output_data} if output_data is not None else {},
        )
        ctx.history.append(record)
        ctx.current_state = to_state
        return ctx

    def requires_director(self, state_name: str) -> bool:
        st = self.get_state(state_name)
        return st.tipo == StateType.H or st.llm_allowed == "always"

    def requires_resource_brain(self, state_name: str) -> bool:
        return self.get_state(state_name).resource_brain

    def allows_llm(self, state_name: str) -> bool:
        st = self.get_state(state_name)
        if st.tipo == StateType.D_STRICT:
            return False
        if st.llm_allowed == "never":
            return False
        if st.llm_allowed == "always":
            return True
        return st.llm_allowed == "conditional"

    def snapshot(self, ctx: KTPContext) -> Dict[str, Any]:
        return {
            "current_state": ctx.current_state,
            "emoji": self.get_state(ctx.current_state).emoji,
            "goal_struct": ctx.goal_struct,
            "task_list": ctx.task_list,
            "history_len": len(ctx.history),
            "last_cycle": asdict(ctx.history[-1]) if ctx.history else None,
        }


def create_engine(states_path: Optional[str] = None) -> KTPEngine:
    path = Path(states_path) if states_path else None
    return KTPEngine(states_path=path)


if __name__ == "__main__":
    engine = create_engine()
    print(f"KTP Engine loaded: {len(engine.states)} states")
    for name, st in engine.states.items():
        print(f"  {st.emoji} {name} tipo={st.tipo.value} rb={st.resource_brain}")
    ctx = KTPContext(raw_input="test goal")
    print("Initial:", engine.snapshot(ctx))
    ctx = engine.transition(ctx, "TAREA", output_data={"ok": True})
    print("After OBJETIVO→TAREA:", engine.snapshot(ctx))
