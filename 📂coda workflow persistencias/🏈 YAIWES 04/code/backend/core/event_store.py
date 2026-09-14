"""
多智能体交互事件存储
提供会话、轮次、消息和事件的统一内存存储
"""
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional
import uuid


def _now() -> str:
    return datetime.now().isoformat()


@dataclass
class InteractionEvent:
    """交互事件"""
    event_id: str
    session_id: str
    event_type: str
    summary: str
    agent: str = "system"
    round_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "round_id": self.round_id,
            "event_type": self.event_type,
            "summary": self.summary,
            "agent": self.agent,
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class InteractionMessage:
    """Agent 间消息"""
    message_id: str
    session_id: str
    round_id: str
    sender: str
    receiver: str
    message_type: str
    content: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "session_id": self.session_id,
            "round_id": self.round_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type,
            "content": self.content,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


@dataclass
class InteractionRound:
    """多轮协作中的一轮"""
    round_id: str
    session_id: str
    phase: str
    goal: str
    participants: List[str]
    status: str = "running"
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: str = field(default_factory=_now)
    ended_at: Optional[str] = None
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_id": self.round_id,
            "session_id": self.session_id,
            "phase": self.phase,
            "goal": self.goal,
            "participants": self.participants,
            "status": self.status,
            "metadata": self.metadata,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "summary": self.summary,
        }


class EventStore:
    """交互事件存储"""

    def __init__(self, max_events_per_session: int = 1000):
        self.max_events_per_session = max_events_per_session
        self._lock = Lock()
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._latest_event: Optional[Dict[str, Any]] = None

    def create_session(
        self,
        session_id: str,
        target: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            session = self._sessions.setdefault(
                session_id,
                {
                    "session_id": session_id,
                    "target": target,
                    "metadata": metadata or {},
                    "created_at": _now(),
                    "events": [],
                    "rounds": {},
                    "messages": {},
                },
            )
            return {
                "session_id": session["session_id"],
                "target": session["target"],
                "metadata": session["metadata"],
                "created_at": session["created_at"],
            }

    def has_session(self, session_id: str) -> bool:
        return session_id in self._sessions

    def add_event(
        self,
        session_id: str,
        event_type: str,
        summary: str,
        agent: str = "system",
        round_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        event = InteractionEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            round_id=round_id,
            event_type=event_type,
            summary=summary,
            agent=agent,
            details=details or {},
        ).to_dict()

        with self._lock:
            session = self._sessions.setdefault(
                session_id,
                {
                    "session_id": session_id,
                    "target": "",
                    "metadata": {},
                    "created_at": _now(),
                    "events": [],
                    "rounds": {},
                    "messages": {},
                },
            )
            session["events"].append(event)
            if len(session["events"]) > self.max_events_per_session:
                session["events"] = session["events"][-self.max_events_per_session :]
            self._latest_event = event

        return event

    def start_round(
        self,
        session_id: str,
        phase: str,
        goal: str,
        participants: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        round_obj = InteractionRound(
            round_id=f"round_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            phase=phase,
            goal=goal,
            participants=participants,
            metadata=metadata or {},
        ).to_dict()

        with self._lock:
            session = self._sessions.setdefault(
                session_id,
                {
                    "session_id": session_id,
                    "target": "",
                    "metadata": {},
                    "created_at": _now(),
                    "events": [],
                    "rounds": {},
                    "messages": {},
                },
            )
            session["rounds"][round_obj["round_id"]] = round_obj
            session["messages"].setdefault(round_obj["round_id"], [])

        self.add_event(
            session_id=session_id,
            round_id=round_obj["round_id"],
            event_type="round_started",
            summary=f"开始协作轮次: {goal}",
            agent="CoordinatorAgent",
            details={
                "phase": phase,
                "participants": participants,
                "metadata": metadata or {},
            },
        )
        return round_obj

    def complete_round(
        self,
        session_id: str,
        round_id: str,
        summary: str = "",
        status: str = "completed",
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            round_obj = session["rounds"].get(round_id)
            if not round_obj:
                return None
            round_obj["status"] = status
            round_obj["summary"] = summary
            round_obj["ended_at"] = _now()

        self.add_event(
            session_id=session_id,
            round_id=round_id,
            event_type="round_completed",
            summary=summary or "协作轮次完成",
            agent="CoordinatorAgent",
            details={"status": status},
        )
        return round_obj

    def add_message(
        self,
        session_id: str,
        round_id: str,
        sender: str,
        receiver: str,
        message_type: str,
        content: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        message = InteractionMessage(
            message_id=f"msg_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            round_id=round_id,
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            content=content,
            payload=payload or {},
        ).to_dict()

        with self._lock:
            session = self._sessions.setdefault(
                session_id,
                {
                    "session_id": session_id,
                    "target": "",
                    "metadata": {},
                    "created_at": _now(),
                    "events": [],
                    "rounds": {},
                    "messages": {},
                },
            )
            session["messages"].setdefault(round_id, []).append(message)

        self.add_event(
            session_id=session_id,
            round_id=round_id,
            event_type="message_sent",
            summary=f"{sender} -> {receiver}: {content[:80]}",
            agent=sender,
            details={
                "receiver": receiver,
                "message_type": message_type,
                "message_id": message["message_id"],
                "payload": payload or {},
            },
        )
        self.add_event(
            session_id=session_id,
            round_id=round_id,
            event_type="message_received",
            summary=f"{receiver} 收到来自 {sender} 的消息",
            agent=receiver,
            details={
                "sender": sender,
                "message_type": message_type,
                "message_id": message["message_id"],
            },
        )
        return message

    def list_sessions(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "session_id": session["session_id"],
                    "target": session["target"],
                    "created_at": session["created_at"],
                    "round_count": len(session["rounds"]),
                    "event_count": len(session["events"]),
                }
                for session in self._sessions.values()
            ]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            return {
                "session_id": session["session_id"],
                "target": session["target"],
                "metadata": session["metadata"],
                "created_at": session["created_at"],
                "round_count": len(session["rounds"]),
                "event_count": len(session["events"]),
            }

    def get_session_events(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return []
            events = list(session["events"])
        return events[-limit:] if limit else events

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        with self._lock:
            for session in self._sessions.values():
                events.extend(session["events"])
        events.sort(key=lambda item: item["timestamp"], reverse=True)
        return events[:limit]

    def get_rounds(self, session_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return []
            rounds = list(session["rounds"].values())
        rounds.sort(key=lambda item: item["started_at"])
        return rounds

    def get_round_messages(self, session_id: str, round_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return []
            return list(session["messages"].get(round_id, []))

    def get_latest_event(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if session_id:
            events = self.get_session_events(session_id, limit=1)
            return events[-1] if events else None
        return self._latest_event
