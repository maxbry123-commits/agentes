"""YAIWES Redis adapter: optional cache backend over RESP/TCP.

Redis is not the authoritative audit ledger. This adapter exposes only
best-effort cache primitives for YAIWES run-state acceleration.
"""
from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Any

PLUGIN_ID = "yaiwes.state.redis_cache"
ROLE = "optional_run_state_cache"


@dataclass(frozen=True)
class RedisEndpoint:
    host: str = "127.0.0.1"
    port: int = 6379
    timeout_s: float = 2.0


class RedisProtocolError(RuntimeError):
    pass


class RedisCacheAdapter:
    def __init__(self, endpoint: RedisEndpoint | None = None) -> None:
        self.endpoint = endpoint or RedisEndpoint()

    @staticmethod
    def _encode(parts: tuple[Any, ...]) -> bytes:
        chunks = [f"*{len(parts)}\r\n".encode()]
        for part in parts:
            raw = str(part).encode("utf-8") if not isinstance(part, bytes) else part
            chunks.append(f"${len(raw)}\r\n".encode())
            chunks.append(raw + b"\r\n")
        return b"".join(chunks)

    @staticmethod
    def _read_line(stream) -> bytes:
        line = stream.readline()
        if not line.endswith(b"\r\n"):
            raise RedisProtocolError("RESP_LINE_INCOMPLETE")
        return line[:-2]

    @classmethod
    def _decode(cls, stream):
        prefix = stream.read(1)
        if prefix == b"+":
            return cls._read_line(stream).decode("utf-8")
        if prefix == b"-":
            raise RedisProtocolError(cls._read_line(stream).decode("utf-8"))
        if prefix == b":":
            return int(cls._read_line(stream))
        if prefix == b"$":
            size = int(cls._read_line(stream))
            if size == -1:
                return None
            payload = stream.read(size)
            if len(payload) != size or stream.read(2) != b"\r\n":
                raise RedisProtocolError("RESP_BULK_INCOMPLETE")
            return payload
        if prefix == b"*":
            count = int(cls._read_line(stream))
            if count == -1:
                return None
            return [cls._decode(stream) for _ in range(count)]
        raise RedisProtocolError(f"RESP_PREFIX_BAD:{prefix!r}")

    def execute(self, *parts: Any):
        if not parts:
            raise ValueError("REDIS_COMMAND_REQUIRED")
        with socket.create_connection(
            (self.endpoint.host, self.endpoint.port),
            timeout=self.endpoint.timeout_s,
        ) as sock:
            sock.settimeout(self.endpoint.timeout_s)
            sock.sendall(self._encode(parts))
            with sock.makefile("rb") as stream:
                return self._decode(stream)

    def ping(self) -> bool:
        return self.execute("PING") == "PONG"

    def set_cache(self, key: str, value: bytes | str, ttl_s: int | None = None) -> bool:
        command: list[Any] = ["SET", key, value]
        if ttl_s is not None:
            if ttl_s <= 0:
                raise ValueError("REDIS_TTL_MUST_BE_POSITIVE")
            command.extend(["EX", ttl_s])
        return self.execute(*command) == "OK"

    def get_cache(self, key: str) -> bytes | None:
        value = self.execute("GET", key)
        if value is None or isinstance(value, bytes):
            return value
        raise RedisProtocolError(f"REDIS_GET_BAD_TYPE:{type(value).__name__}")

    def delete_cache(self, key: str) -> int:
        value = self.execute("DEL", key)
        if not isinstance(value, int):
            raise RedisProtocolError(f"REDIS_DEL_BAD_TYPE:{type(value).__name__}")
        return value


def descriptor() -> dict[str, Any]:
    return {
        "plugin_id": PLUGIN_ID,
        "role": ROLE,
        "transport": "RESP/TCP",
        "authoritative_audit_store": False,
        "operations": ["PING", "SET", "GET", "DEL"],
    }
