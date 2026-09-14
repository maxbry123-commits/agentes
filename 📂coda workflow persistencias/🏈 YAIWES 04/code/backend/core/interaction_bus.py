"""
多智能体交互总线
封装会话、轮次、消息和事件的统一操作
"""
from typing import Any, Dict, List, Optional

from .event_store import EventStore


class InteractionBus:
    """多智能体交互总线"""

    def __init__(self, event_store: Optional[EventStore] = None):
        self.event_store = event_store or EventStore()

    def bind_session(
        self,
        session_id: str,
        target: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.event_store.create_session(session_id, target, metadata)

    def emit_event(
        self,
        session_id: str,
        event_type: str,
        summary: str,
        agent: str = "system",
        round_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.event_store.add_event(
            session_id=session_id,
            round_id=round_id,
            event_type=event_type,
            summary=summary,
            agent=agent,
            details=details,
        )

    def start_round(
        self,
        session_id: str,
        phase: str,
        goal: str,
        participants: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.event_store.start_round(
            session_id=session_id,
            phase=phase,
            goal=goal,
            participants=participants,
            metadata=metadata,
        )

    def complete_round(
        self,
        session_id: str,
        round_id: str,
        summary: str = "",
        status: str = "completed",
    ) -> Optional[Dict[str, Any]]:
        return self.event_store.complete_round(
            session_id=session_id,
            round_id=round_id,
            summary=summary,
            status=status,
        )

    def send_message(
        self,
        session_id: str,
        round_id: str,
        sender: str,
        receiver: str,
        message_type: str,
        content: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.event_store.add_message(
            session_id=session_id,
            round_id=round_id,
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            content=content,
            payload=payload,
        )

    def get_session_events(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        return self.event_store.get_session_events(session_id, limit=limit)

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.event_store.get_recent_events(limit=limit)

    def get_rounds(self, session_id: str) -> List[Dict[str, Any]]:
        return self.event_store.get_rounds(session_id)

    def get_round_messages(self, session_id: str, round_id: str) -> List[Dict[str, Any]]:
        return self.event_store.get_round_messages(session_id, round_id)

    def get_latest_event(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        return self.event_store.get_latest_event(session_id=session_id)
