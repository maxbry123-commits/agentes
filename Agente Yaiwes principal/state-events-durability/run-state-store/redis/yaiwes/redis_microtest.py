"""N24 Redis functional microtest: build/start moved Redis and exercise cache operations."""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path

from redis_adapter import RedisCacheAdapter, RedisEndpoint


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _ensure_server(redis_root: Path) -> Path:
    server = redis_root / "src" / "redis-server"
    if server.is_file():
        return server
    subprocess.run(
        ["make", "-C", str(redis_root), "-j2", "BUILD_TLS=no"],
        check=True,
        timeout=240,
    )
    if not server.is_file():
        raise RuntimeError(f"REDIS_SERVER_BUILD_MISSING:{server}")
    return server


def run_microtest(repo_root: str | Path) -> dict[str, object]:
    root = Path(repo_root).resolve()
    redis_root = root / "Agente Yaiwes principal/state-events-durability/run-state-store/redis"
    server = _ensure_server(redis_root)
    port = _free_port()
    proc = subprocess.Popen(
        [
            str(server),
            "--bind", "127.0.0.1",
            "--port", str(port),
            "--save", "",
            "--appendonly", "no",
            "--protected-mode", "yes",
        ],
        cwd=redis_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    adapter = RedisCacheAdapter(RedisEndpoint(port=port, timeout_s=1.0))
    try:
        deadline = time.time() + 15
        while time.time() < deadline:
            if proc.poll() is not None:
                output = proc.stdout.read() if proc.stdout else ""
                raise RuntimeError(f"REDIS_SERVER_EXITED:{proc.returncode}:{output[-2000:]}")
            try:
                if adapter.ping():
                    break
            except OSError:
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("REDIS_SERVER_NOT_READY")

        key = "yaiwes:n24:microtest"
        assert adapter.set_cache(key, "42", ttl_s=30)
        assert adapter.get_cache(key) == b"42"
        assert adapter.delete_cache(key) == 1
        assert adapter.get_cache(key) is None
        return {
            "status": "PASS",
            "capability": "optional_run_state_cache",
            "operations": ["PING", "SET", "GET", "DEL"],
            "authoritative_audit_store": False,
        }
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    result = run_microtest(root)
    print("YAIWES_REDIS_RESULT=" + json.dumps(result, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
