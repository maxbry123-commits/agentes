"""
src/core/event_bus.py
CORE_KERNEL_DETERMINISTA — T-001 (archivo 2/4)

Responsabilidad: Backend abstracto de eventos (EventBus) mas tres
implementaciones:
    InMemoryEventBus  -> proceso unico, sin dependencias externas.
    RedisEventBus      -> adapter sobre un cliente compatible con la API
                          async de redis-py (redis.asyncio.Redis).
    NATSEventBus        -> adapter sobre un cliente compatible con la API
                          async de nats.py (nats.aio.client.Client).

Los adapters Redis/NATS reciben el cliente por inyeccion de dependencia
(no crean la conexion de red ellos mismos): esto permite testear la
logica de despacho de eventos con clientes falsos que cumplen el mismo
protocolo, sin requerir un servidor Redis/NATS real. L05: ninguna API
usada aqui es inventada; siguen la firma publica documentada de
redis-py (`publish`, `pubsub().psubscribe`, `pubsub().listen`) y de
nats.py (`publish`, `subscribe(subject, cb=...)`, `unsubscribe`).
"""

from __future__ import annotations

import asyncio
import fnmatch
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional, Protocol

logger = logging.getLogger("pecp.core.event_bus")

EventHandler = Callable[[str, Dict[str, Any]], Awaitable[None]]


# --------------------------------------------------------------------------
# Excepciones
# --------------------------------------------------------------------------


class EventBusError(Exception):
    """Error generico del event bus."""


class SubscriptionNotFoundError(EventBusError):
    """Se intento desuscribir un subscription_id inexistente."""


# --------------------------------------------------------------------------
# Tipos comunes
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Subscription:
    """Registro inmutable de una suscripcion activa."""

    subscription_id: str
    pattern: str


def pattern_matches(pattern: str, name: str) -> bool:
    """True si `name` matchea `pattern` con sintaxis glob (fnmatch)."""
    return fnmatch.fnmatchcase(name, pattern)


# --------------------------------------------------------------------------
# Contrato abstracto
# --------------------------------------------------------------------------


class EventBus(ABC):
    """Contrato abstracto que deben cumplir todos los backends de eventos."""

    @abstractmethod
    async def publish(self, name: str, data: Dict[str, Any]) -> None:
        """Publica un evento `name` con payload `data`."""

    @abstractmethod
    async def subscribe(self, pattern: str, handler: EventHandler) -> str:
        """Suscribe `handler` a eventos que matcheen `pattern` (glob)."""

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """Cancela una suscripcion previamente creada."""

    @abstractmethod
    async def close(self) -> None:
        """Libera recursos del backend (tareas de fondo, conexiones)."""


# --------------------------------------------------------------------------
# InMemory backend
# --------------------------------------------------------------------------


class InMemoryEventBus(EventBus):
    """Backend en memoria de un unico proceso. Determinista, sin I/O."""

    def __init__(self) -> None:
        """Inicializa el registro interno de suscripciones."""
        self._subscriptions: Dict[str, Subscription] = {}
        self._handlers: Dict[str, EventHandler] = {}
        self._lock = asyncio.Lock()

    async def publish(self, name: str, data: Dict[str, Any]) -> None:
        """Despacha `data` a todos los handlers cuyo pattern matchee `name`."""
        matching = await self._matching_handlers(name)
        if matching:
            await asyncio.gather(*(h(name, data) for h in matching))

    async def _matching_handlers(self, name: str) -> List[EventHandler]:
        """Retorna los handlers activos cuyo pattern matchea `name`."""
        async with self._lock:
            return [
                self._handlers[sub.subscription_id]
                for sub in self._subscriptions.values()
                if pattern_matches(sub.pattern, name)
            ]

    async def subscribe(self, pattern: str, handler: EventHandler) -> str:
        """Registra `handler` para `pattern`. Retorna el subscription_id."""
        if not pattern:
            raise EventBusError("pattern vacio")
        subscription_id = uuid.uuid4().hex
        async with self._lock:
            self._subscriptions[subscription_id] = Subscription(
                subscription_id, pattern
            )
            self._handlers[subscription_id] = handler
        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> None:
        """Elimina una suscripcion. Lanza si no existe."""
        async with self._lock:
            if subscription_id not in self._subscriptions:
                raise SubscriptionNotFoundError(subscription_id)
            del self._subscriptions[subscription_id]
            del self._handlers[subscription_id]

    async def close(self) -> None:
        """Limpia todas las suscripciones activas."""
        async with self._lock:
            self._subscriptions.clear()
            self._handlers.clear()


# --------------------------------------------------------------------------
# Redis backend (adapter sobre redis.asyncio, cliente inyectado)
# --------------------------------------------------------------------------


class RedisPubSubProtocol(Protocol):
    """Superficie minima usada de redis.asyncio.client.PubSub."""

    async def psubscribe(self, pattern: str) -> None:
        """Suscribe el pubsub a un patron glob de canales."""
        ...

    async def punsubscribe(self, pattern: str) -> None:
        """Cancela la suscripcion a un patron glob de canales."""
        ...

    def listen(self) -> Any:
        """Retorna un async-generator de mensajes entrantes del pubsub."""
        ...

    async def close(self) -> None:
        """Cierra la conexion del objeto pubsub."""
        ...


class RedisClientProtocol(Protocol):
    """Superficie minima usada de redis.asyncio.Redis."""

    async def publish(self, channel: str, message: str) -> int:
        """Publica `message` en `channel`. Retorna cantidad de receptores."""
        ...

    def pubsub(self) -> RedisPubSubProtocol:
        """Crea un objeto pubsub asociado a este cliente."""
        ...


class RedisEventBus(EventBus):
    """Backend sobre Redis Pub/Sub (cliente async inyectado)."""

    def __init__(self, client: RedisClientProtocol) -> None:
        """Recibe un cliente redis.asyncio.Redis ya configurado."""
        self._client = client
        self._pubsub: Optional[RedisPubSubProtocol] = None
        self._subscriptions: Dict[str, Subscription] = {}
        self._handlers: Dict[str, EventHandler] = {}
        self._listener_task: Optional["asyncio.Task[None]"] = None
        self._lock = asyncio.Lock()

    async def publish(self, name: str, data: Dict[str, Any]) -> None:
        """Serializa `data` a JSON y publica en el canal `name`."""
        payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
        await self._client.publish(name, payload)

    async def subscribe(self, pattern: str, handler: EventHandler) -> str:
        """psubscribe a `pattern` y arranca el listener si es la primera vez."""
        if not pattern:
            raise EventBusError("pattern vacio")
        await self._ensure_pubsub_started()
        subscription_id = uuid.uuid4().hex
        async with self._lock:
            self._subscriptions[subscription_id] = Subscription(
                subscription_id, pattern
            )
            self._handlers[subscription_id] = handler
        assert self._pubsub is not None
        await self._pubsub.psubscribe(pattern)
        return subscription_id

    async def _ensure_pubsub_started(self) -> None:
        """Crea el objeto pubsub y la tarea de escucha una sola vez."""
        if self._pubsub is not None:
            return
        self._pubsub = self._client.pubsub()
        self._listener_task = asyncio.create_task(self._listen_loop())

    async def _listen_loop(self) -> None:
        """Consume mensajes 'pmessage' del pubsub y los despacha."""
        assert self._pubsub is not None
        async for message in self._pubsub.listen():
            if message.get("type") != "pmessage":
                continue
            await self._dispatch(message)

    async def _dispatch(self, message: Dict[str, Any]) -> None:
        """Decodifica un mensaje redis y lo entrega a handlers que matcheen."""
        name = message["channel"]
        try:
            data = json.loads(message["data"])
        except (TypeError, ValueError) as exc:
            logger.warning("payload invalido en redis channel=%s: %s", name, exc)
            return
        async with self._lock:
            handlers = [
                self._handlers[sub.subscription_id]
                for sub in self._subscriptions.values()
                if pattern_matches(sub.pattern, name)
            ]
        if handlers:
            await asyncio.gather(*(h(name, data) for h in handlers))

    async def unsubscribe(self, subscription_id: str) -> None:
        """Cancela la suscripcion local y hace punsubscribe en Redis."""
        async with self._lock:
            if subscription_id not in self._subscriptions:
                raise SubscriptionNotFoundError(subscription_id)
            pattern = self._subscriptions[subscription_id].pattern
            del self._subscriptions[subscription_id]
            del self._handlers[subscription_id]
        if self._pubsub is not None:
            await self._pubsub.punsubscribe(pattern)

    async def close(self) -> None:
        """Cancela la tarea de escucha y cierra el pubsub."""
        if self._listener_task is not None:
            self._listener_task.cancel()
        if self._pubsub is not None:
            await self._pubsub.close()
        async with self._lock:
            self._subscriptions.clear()
            self._handlers.clear()


# --------------------------------------------------------------------------
# NATS backend (adapter sobre nats.py, cliente inyectado)
# --------------------------------------------------------------------------


class NATSSubscriptionProtocol(Protocol):
    """Superficie minima usada de nats.aio.subscription.Subscription."""

    async def unsubscribe(self) -> None:
        """Cancela esta suscripcion NATS."""
        ...


class NATSClientProtocol(Protocol):
    """Superficie minima usada de nats.aio.client.Client."""

    async def publish(self, subject: str, payload: bytes) -> None:
        """Publica `payload` en bytes bajo el subject dado."""
        ...

    async def subscribe(
        self, subject: str, cb: Callable[[Any], Awaitable[None]]
    ) -> NATSSubscriptionProtocol:
        """Suscribe `cb` como callback async para mensajes de `subject`."""
        ...

    async def close(self) -> None:
        """Cierra (drena) la conexion del cliente NATS."""
        ...


class NATSEventBus(EventBus):
    """Backend sobre NATS core Pub/Sub (cliente async ya conectado)."""

    def __init__(self, client: NATSClientProtocol) -> None:
        """Recibe un cliente nats.aio.client.Client ya conectado."""
        self._client = client
        self._subscriptions: Dict[str, Subscription] = {}
        self._handlers: Dict[str, EventHandler] = {}
        self._nats_subs: Dict[str, NATSSubscriptionProtocol] = {}

    async def publish(self, name: str, data: Dict[str, Any]) -> None:
        """Serializa `data` a JSON bytes y publica en el subject `name`."""
        payload = json.dumps(
            data, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        await self._client.publish(name, payload)

    async def subscribe(self, pattern: str, handler: EventHandler) -> str:
        """Suscribe un callback interno que reenvia al `handler` dado."""
        if not pattern:
            raise EventBusError("pattern vacio")
        subscription_id = uuid.uuid4().hex

        async def _callback(msg: Any) -> None:
            await self._handle_message(subscription_id, msg)

        nats_sub = await self._client.subscribe(pattern, cb=_callback)
        self._subscriptions[subscription_id] = Subscription(
            subscription_id, pattern
        )
        self._handlers[subscription_id] = handler
        self._nats_subs[subscription_id] = nats_sub
        return subscription_id

    async def _handle_message(self, subscription_id: str, msg: Any) -> None:
        """Decodifica el mensaje NATS y llama al handler registrado."""
        handler = self._handlers.get(subscription_id)
        if handler is None:
            return
        try:
            data = json.loads(msg.data)
        except (TypeError, ValueError) as exc:
            logger.warning(
                "payload invalido en nats subject=%s: %s", msg.subject, exc
            )
            return
        await handler(msg.subject, data)

    async def unsubscribe(self, subscription_id: str) -> None:
        """Cancela la suscripcion NATS y limpia el registro local."""
        if subscription_id not in self._subscriptions:
            raise SubscriptionNotFoundError(subscription_id)
        await self._nats_subs[subscription_id].unsubscribe()
        del self._subscriptions[subscription_id]
        del self._handlers[subscription_id]
        del self._nats_subs[subscription_id]

    async def close(self) -> None:
        """Desuscribe todo y cierra la conexion del cliente NATS."""
        for subscription_id in list(self._subscriptions.keys()):
            await self.unsubscribe(subscription_id)
        await self._client.close()
