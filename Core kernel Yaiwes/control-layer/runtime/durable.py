"""Durable runtime · horas/días · checkpoint · signals · resume · 0% LLM.

Backend: JSON files por mission (sin Temporal obligatorio).
Contrato listo para enchufar SQL/Temporal detrás de la misma API.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class SignalKind(str, Enum):
    CORRECTION = "CORRECTION"
    UPDATE = "UPDATE"
    NEW_TASK = "NEW_TASK"
    HEARTBEAT = "HEARTBEAT"
    CANCEL = "CANCEL"


class MissionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING_SIGNAL = "WAITING_SIGNAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class Signal:
    signal_id: str
    kind: SignalKind
    payload: dict[str, Any]
    created_at: float
    applied: bool = False
    applied_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Signal":
        return Signal(
            signal_id=str(d["signal_id"]),
            kind=SignalKind(str(d["kind"])),
            payload=dict(d.get("payload") or {}),
            created_at=float(d["created_at"]),
            applied=bool(d.get("applied", False)),
            applied_at=d.get("applied_at"),
        )


@dataclass
class Checkpoint:
    checkpoint_id: str
    seq: int
    phase: str
    cursor: dict[str, Any]
    evidence_hash: str | None
    created_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Checkpoint":
        return Checkpoint(
            checkpoint_id=str(d["checkpoint_id"]),
            seq=int(d["seq"]),
            phase=str(d["phase"]),
            cursor=dict(d.get("cursor") or {}),
            evidence_hash=d.get("evidence_hash"),
            created_at=float(d["created_at"]),
        )


@dataclass
class MissionState:
    mission_id: str
    status: MissionStatus
    goal: str
    created_at: float
    updated_at: float
    phase: str = "init"
    cursor: dict[str, Any] = field(default_factory=dict)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    signals: list[Signal] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    run_token: str = ""  # lease / anti-doble ejecución

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "status": self.status.value,
            "goal": self.goal,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "phase": self.phase,
            "cursor": self.cursor,
            "checkpoints": [c.to_dict() for c in self.checkpoints],
            "signals": [s.to_dict() for s in self.signals],
            "meta": self.meta,
            "run_token": self.run_token,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "MissionState":
        return MissionState(
            mission_id=str(d["mission_id"]),
            status=MissionStatus(str(d["status"])),
            goal=str(d.get("goal") or ""),
            created_at=float(d["created_at"]),
            updated_at=float(d["updated_at"]),
            phase=str(d.get("phase") or "init"),
            cursor=dict(d.get("cursor") or {}),
            checkpoints=[Checkpoint.from_dict(c) for c in d.get("checkpoints") or []],
            signals=[Signal.from_dict(s) for s in d.get("signals") or []],
            meta=dict(d.get("meta") or {}),
            run_token=str(d.get("run_token") or ""),
        )

    def last_checkpoint(self) -> Checkpoint | None:
        return self.checkpoints[-1] if self.checkpoints else None


class DurableRuntime:
    """Persistencia por archivo JSON: state_dir/<mission_id>.json"""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, mission_id: str) -> Path:
        safe = re_safe(mission_id)
        return self.state_dir / f"{safe}.json"

    def save(self, state: MissionState) -> None:
        state.updated_at = time.time()
        path = self._path(state.mission_id)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    def load(self, mission_id: str) -> MissionState | None:
        path = self._path(mission_id)
        if not path.is_file():
            return None
        return MissionState.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def create_mission(self, goal: str, *, mission_id: str | None = None, meta: dict | None = None) -> MissionState:
        mid = mission_id or ("m_" + uuid.uuid4().hex[:12])
        now = time.time()
        state = MissionState(
            mission_id=mid,
            status=MissionStatus.PENDING,
            goal=goal,
            created_at=now,
            updated_at=now,
            meta=dict(meta or {}),
            run_token=uuid.uuid4().hex,
        )
        self.save(state)
        return state

    def checkpoint(
        self,
        mission_id: str,
        *,
        phase: str,
        cursor: dict[str, Any] | None = None,
        evidence_hash: str | None = None,
    ) -> Checkpoint:
        state = self.load(mission_id)
        if state is None:
            raise KeyError(f"mission_not_found:{mission_id}")
        seq = len(state.checkpoints) + 1
        raw = f"{mission_id}|{seq}|{phase}|{time.time_ns()}"
        cid = "cp_" + hashlib.sha256(raw.encode()).hexdigest()[:16]
        cp = Checkpoint(
            checkpoint_id=cid,
            seq=seq,
            phase=phase,
            cursor=dict(cursor or state.cursor),
            evidence_hash=evidence_hash,
            created_at=time.time(),
        )
        state.checkpoints.append(cp)
        state.phase = phase
        if cursor is not None:
            state.cursor = dict(cursor)
        state.status = MissionStatus.RUNNING
        self.save(state)
        return cp

    def enqueue_signal(
        self,
        mission_id: str,
        kind: SignalKind | str,
        payload: dict[str, Any] | None = None,
    ) -> Signal:
        state = self.load(mission_id)
        if state is None:
            raise KeyError(f"mission_not_found:{mission_id}")
        k = kind if isinstance(kind, SignalKind) else SignalKind(str(kind).upper())
        if k == SignalKind.NEW_TASK:
            # NEW_TASK no se encola en mission ajena: el caller debe crear otra mission
            raise ValueError("NEW_TASK_must_create_separate_mission")
        sig = Signal(
            signal_id="sig_" + uuid.uuid4().hex[:12],
            kind=k,
            payload=dict(payload or {}),
            created_at=time.time(),
        )
        state.signals.append(sig)
        state.status = MissionStatus.WAITING_SIGNAL
        self.save(state)
        return sig

    def pending_signals(self, mission_id: str) -> list[Signal]:
        state = self.load(mission_id)
        if state is None:
            return []
        return [s for s in state.signals if not s.applied]

    def apply_next_signal(self, mission_id: str) -> Signal | None:
        """Aplica el signal más antiguo pendiente (orden FIFO)."""
        state = self.load(mission_id)
        if state is None:
            raise KeyError(f"mission_not_found:{mission_id}")
        for s in state.signals:
            if not s.applied:
                s.applied = True
                s.applied_at = time.time()
                # cursor patch mínimo
                if s.kind in (SignalKind.CORRECTION, SignalKind.UPDATE):
                    state.cursor["last_signal"] = s.signal_id
                    state.cursor["last_signal_kind"] = s.kind.value
                    if "patch" in s.payload:
                        state.cursor["patch"] = s.payload["patch"]
                if s.kind == SignalKind.CANCEL:
                    state.status = MissionStatus.CANCELLED
                else:
                    state.status = MissionStatus.RUNNING
                self.save(state)
                return s
        return None

    def resume(self, mission_id: str) -> MissionState:
        """Carga estado y deja RUNNING desde último checkpoint."""
        state = self.load(mission_id)
        if state is None:
            raise KeyError(f"mission_not_found:{mission_id}")
        if state.status == MissionStatus.CANCELLED:
            return state
        if state.status == MissionStatus.COMPLETED:
            return state
        cp = state.last_checkpoint()
        if cp:
            state.phase = cp.phase
            state.cursor = dict(cp.cursor)
        state.status = MissionStatus.RUNNING
        state.run_token = uuid.uuid4().hex  # nuevo lease
        self.save(state)
        return state

    def complete(self, mission_id: str, *, ok: bool = True) -> MissionState:
        state = self.load(mission_id)
        if state is None:
            raise KeyError(f"mission_not_found:{mission_id}")
        state.status = MissionStatus.COMPLETED if ok else MissionStatus.FAILED
        self.save(state)
        return state

    def list_missions(self) -> list[str]:
        return sorted(p.stem for p in self.state_dir.glob("*.json") if p.suffix == ".json")


def re_safe(mission_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in mission_id)[:128]
