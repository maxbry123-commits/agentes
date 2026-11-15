"""
tests/core/test_event_bus.py
Tests unitarios de src/core/event_bus.py — T-001 (archivo 2/4)

InMemoryEventBus se testea de forma completa (sin dependencias
externas). RedisEventBus y NATSEventBus se testean inyectando clientes
falsos que cumplen el mismo Protocol que redis-py/nats.py, ya que estas
librerias no son instalables en este sandbox sin acceso a red. Esto
verifica la logica de despacho del adapter, no la conexion de red real.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Tuple

import pytest

from src.core.event_bus import (
    EventBusError,
    InMemoryEventBus,
    NATSEventBus,
    RedisEventBus,
    SubscriptionNotFoundError,
    pattern_matches,
)


# --------------------------------------------------------------------------
# pattern_matches
# --------------------------------------------------------------------------


def test_pattern_matches_exact() -> None:
    assert pattern_matches("node.done", "node.done") is True
    assert pattern_matches("node.done", "node.failed") is False


def test_pattern_matches_wildcard() -> None:
    assert pattern_matches("node.*", "node.done") is True
    assert pattern_matches("node.*", "other.done") is False
    assert pattern_matches("*", "anything") is True


# --------------------------------------------------------------------------
# InMemoryEventBus
# --------------------------------------------------------------------------


def test_inmemory_publish_subscribe_roundtrip() -> None:
    async def scenario() -> None:
        bus = InMemoryEventBus()
        received: List[Tuple[str, Dict[str, Any]]] = []

        async def handler(name: str, data: Dict[str, Any]) -> None:
            received.append((name, data))

        await bus.subscribe("node.*", handler)
        await bus.publish("node.done", {"x": 1})
        await bus.publish("other.event", {"x": 2})

        assert received == [("node.done", {"x": 1})]

    asyncio.run(scenario())


def test_inmemory_subscribe_empty_pattern_raises() -> None:
    async def scenario() -> None:
        bus = InMemoryEventBus()

        async def handler(name: str, data: Dict[str, Any]) -> None:
            pass

        with pytest.raises(EventBusError):
            await bus.subscribe("", handler)

    asyncio.run(scenario())


def test_inmemory_unsubscribe_stops_delivery() -> None:
    async def scenario() -> None:
        bus = InMemoryEventBus()
        received: List[str] = []

        async def handler(name: str, data: Dict[str, Any]) -> None:
            received.append(name)

        sub_id = await bus.subscribe("node.*", handler)
        await bus.unsubscribe(sub_id)
        await bus.publish("node.done", {})

        assert received == []

    asyncio.run(scenario())


def test_inmemory_unsubscribe_unknown_raises() -> None:
    async def scenario() -> None:
        bus = InMemoryEventBus()
        with pytest.raises(SubscriptionNotFoundError):
            await bus.unsubscribe("ghost")

    asyncio.run(scenario())


def test_inmemory_multiple_handlers_same_event() -> None:
    async def scenario() -> None:
        bus = InMemoryEventBus()
        counter = {"n": 0}

        async def handler_a(name: str, data: Dict[str, Any]) -> None:
            counter["n"] += 1

        async def handler_b(name: str, data: Dict[str, Any]) -> None:
            counter["n"] += 10

        await bus.subscribe("node.*", handler_a)
        await bus.subscribe("node.done", handler_b)
        await bus.publish("node.done", {})

        assert counter["n"] == 11

    asyncio.run(scenario())


def test_inmemory_close_clears_subscriptions() -> None:
    async def scenario() -> None:
        bus = InMemoryEventBus()

        async def handler(name: str, data: Dict[str, Any]) -> None:
            pass

        await bus.subscribe("node.*", handler)
        await bus.close()
        with pytest.raises(SubscriptionNotFoundError):
            await bus.unsubscribe("anything")

    asyncio.run(scenario())


# --------------------------------------------------------------------------
# RedisEventBus (cliente fake compatible con el Protocol)
# --------------------------------------------------------------------------


class _FakePubSub:
    def __init__(self) -> None:
        self.queue: "asyncio.Queue[Any]" = asyncio.Queue()
        self.subscribed: List[str] = []
        self.closed = False

    async def psubscribe(self, pattern: str) -> None:
        self.subscribed.append(pattern)

    async def punsubscribe(self, pattern: str) -> None:
        if pattern in self.subscribed:
            self.subscribed.remove(pattern)

    async def listen(self):
        while True:
            message = await self.queue.get()
            if message is None:
                return
            yield message

    async def close(self) -> None:
        self.closed = True
        await self.queue.put(None)


class _FakeRedisClient:
    def __init__(self) -> None:
        self._pubsub = _FakePubSub()
        self.published: List[Tuple[str, str]] = []

    async def publish(self, channel: str, message: str) -> int:
        self.published.append((channel, message))
        return 1

    def pubsub(self) -> _FakePubSub:
        return self._pubsub


def test_redis_publish_serializes_json() -> None:
    async def scenario() -> None:
        client = _FakeRedisClient()
        bus = RedisEventBus(client)
        await bus.publish("node.done", {"x": 1})
        expected = json.dumps({"x": 1}, sort_keys=True, separators=(",", ":"))
        assert client.published == [("node.done", expected)]

    asyncio.run(scenario())


def test_redis_subscribe_dispatches_pmessage() -> None:
    async def scenario() -> None:
        client = _FakeRedisClient()
        bus = RedisEventBus(client)
        received: List[Tuple[str, Dict[str, Any]]] = []

        async def handler(name: str, data: Dict[str, Any]) -> None:
            received.append((name, data))

        await bus.subscribe("node.*", handler)
        assert client._pubsub.subscribed == ["node.*"]

        await client._pubsub.queue.put(
            {
                "type": "pmessage",
                "pattern": "node.*",
                "channel": "node.done",
                "data": json.dumps({"x": 1}),
            }
        )
        for _ in range(50):
            if received:
                break
            await asyncio.sleep(0.01)

        assert received == [("node.done", {"x": 1})]
        await bus.close()

    asyncio.run(scenario())


def test_redis_ignores_non_pmessage_types() -> None:
    async def scenario() -> None:
        client = _FakeRedisClient()
        bus = RedisEventBus(client)
        received: List[Any] = []

        async def handler(name: str, data: Dict[str, Any]) -> None:
            received.append((name, data))

        await bus.subscribe("node.*", handler)
        await client._pubsub.queue.put({"type": "psubscribe", "data": 1})
        await asyncio.sleep(0.05)

        assert received == []
        await bus.close()

    asyncio.run(scenario())


# --------------------------------------------------------------------------
# NATSEventBus (cliente fake compatible con el Protocol)
# --------------------------------------------------------------------------


class _FakeNATSSub:
    def __init__(self) -> None:
        self.unsubscribed = False

    async def unsubscribe(self) -> None:
        self.unsubscribed = True


class _FakeNATSMsg:
    def __init__(self, subject: str, data: bytes) -> None:
        self.subject = subject
        self.data = data


class _FakeNATSClient:
    def __init__(self) -> None:
        self.published: List[Tuple[str, bytes]] = []
        self._callbacks: Dict[str, Any] = {}
        self.closed = False

    async def publish(self, subject: str, payload: bytes) -> None:
        self.published.append((subject, payload))

    async def subscribe(self, subject: str, cb: Any) -> _FakeNATSSub:
        self._callbacks[subject] = cb
        return _FakeNATSSub()

    async def close(self) -> None:
        self.closed = True

    async def deliver(self, subject: str, data: Dict[str, Any]) -> None:
        cb = self._callbacks[subject]
        await cb(_FakeNATSMsg(subject, json.dumps(data).encode("utf-8")))


def test_nats_publish_serializes_json_bytes() -> None:
    async def scenario() -> None:
        client = _FakeNATSClient()
        bus = NATSEventBus(client)
        await bus.publish("node.done", {"x": 1})
        expected = json.dumps(
            {"x": 1}, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        assert client.published == [("node.done", expected)]

    asyncio.run(scenario())


def test_nats_subscribe_delivers_to_handler() -> None:
    async def scenario() -> None:
        client = _FakeNATSClient()
        bus = NATSEventBus(client)
        received: List[Tuple[str, Dict[str, Any]]] = []

        async def handler(name: str, data: Dict[str, Any]) -> None:
            received.append((name, data))

        await bus.subscribe("node.done", handler)
        await client.deliver("node.done", {"x": 42})

        assert received == [("node.done", {"x": 42})]

    asyncio.run(scenario())


def test_nats_unsubscribe_calls_underlying_unsubscribe() -> None:
    async def scenario() -> None:
        client = _FakeNATSClient()
        bus = NATSEventBus(client)

        async def handler(name: str, data: Dict[str, Any]) -> None:
            pass

        sub_id = await bus.subscribe("node.done", handler)
        nats_sub = bus._nats_subs[sub_id]
        await bus.unsubscribe(sub_id)

        assert nats_sub.unsubscribed is True
        with pytest.raises(SubscriptionNotFoundError):
            await bus.unsubscribe(sub_id)

    asyncio.run(scenario())


def test_nats_close_unsubscribes_all_and_closes_client() -> None:
    async def scenario() -> None:
        client = _FakeNATSClient()
        bus = NATSEventBus(client)

        async def handler(name: str, data: Dict[str, Any]) -> None:
            pass

        await bus.subscribe("node.done", handler)
        await bus.close()

        assert client.closed is True

    asyncio.run(scenario())
