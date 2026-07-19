 <tador-universal/orchestrator/sandbox.py 2>/dev/null
"""
sandbox.py — Docker wrapper + Supervisor (lifecycle de sandboxes aislados).

Reglas:
- G2: Scope Lock, sandbox_id único por agente
- G3: Aislamiento total (--network=none, --read-only salvo /work)
- G8: Recursos limitados (--cpus, --memory, --pids-limit)
- P0-3: Circuit breaker por sandbox (5 fallos → open 60s)
- P0-2: Graceful shutdown
"""
import os
import time
import json
import shlex
import subprocess
import threading
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from enum import Enum


class SandboxStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    DEAD = "dead"
    UNKNOWN = "unknown"


@dataclass
class SandboxConfig:
    sandbox_id: str
    agent_type: str           # "claude_code" | "mimo_code" | "opencode"
    image: str                # docker image
    work_dir: str             # host path montado en /work
    cpu_limit: float = 1.0
    memory_limit: str = "1g"
    pids_limit: int = 256
    timeout_s: int = 300
    env: Dict[str, str] = field(default_factory=dict)


class CircuitBreaker:
    """P0-3: circuit breaker por sandbox."""

    def __init__(self, name: str, failure_threshold: int = 5, cooldown: float = 60.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self.failures = 0
        self.last_failure_ts = 0.0
        self.state = "closed"
        self._lock = threading.Lock()

    def is_open(self) -> bool:
        with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure_ts > self.cooldown:
                    self.state = "half_open"
                    return False
                return True
            return False

    def record_success(self) -> None:
        with self._lock:
            self.state = "closed"
            self.failures = 0

    def record_failure(self) -> None:
        with self._lock:
            self.failures += 1
            self.last_failure_ts = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "open"


class Sandbox:
    """Un sandbox = un contenedor docker con un agente dentro."""

    def __init__(self, config: SandboxConfig, sentinel=None):
        self.config = config
        self.sentinel = sentinel
        self.container_id: Optional[str] = None
        self.status = SandboxStatus.CREATED
        self.breaker = CircuitBreaker(f"sbx-{config.sandbox_id}")
        self._lock = threading.Lock()

    def _log(self, event: dict) -> None:
        event["sandbox_id"] = self.config.sandbox_id
        if self.sentinel:
            self.sentinel.log(event)

    def start(self) -> bool:
        """Arranca el contenedor docker."""
        with self._lock:
            if self.breaker.is_open():
                self._log({"event": "start_skipped_breaker_open"})
                return False
            if self.status == SandboxStatus.RUNNING:
                return True
            try:
                cmd = self._build_docker_run()
                self._log({"event": "starting", "cmd": " ".join(cmd[:5]) + "..."})
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    self.container_id = result.stdout.strip()[:64]
                    self.status = SandboxStatus.RUNNING
                    self.breaker.record_success()
                    self._log({"event": "started", "container_id": self.container_id})
                    return True
                self._log({"event": "start_failed", "stderr": result.stderr[:200]})
                self.breaker.record_failure()
                return False
            except Exception as e:
                self._log({"event": "start_exception", "error": str(e)})
                self.breaker.record_failure()
                return False

    def _build_docker_run(self) -> List[str]:
        c = self.config
        env_args = []
        for k, v in c.env.items():
            env_args += ["-e", f"{k}={v}"]
        return [
            "docker", "run", "-d",
            "--name", c.sandbox_id,
            "--network", "none",          # G3: aislamiento de red
            "--read-only",                 # G3: filesystem read-only
            "--tmpfs", "/tmp:size=100m",   # G3: tmpfs limitado
            "-v", f"{c.work_dir}:/work:rw",  # único path writable
            "-v", "/workspace/skills:/skills:ro",  # skills registry read-only
            "--cpus", str(c.cpu_limit),    # G8: CPU limitada
            "--memory", c.memory_limit,    # G8: RAM limitada
            "--pids-limit", str(c.pids_limit),  # G8: procesos limitados
            "-e", "TZ=UTC",                # determinismo
            *env_args,
            c.image,
            "sleep", "infinity"            # contenedor vive, se le inyectan comandos
        ]

    def exec(self, command: str, timeout: Optional[int] = None) -> dict:
        """Ejecuta un comando dentro del sandbox. Devuelve {stdout, stderr, exit_code, duration_s}."""
        with self._lock:
            if self.status != SandboxStatus.RUNNING:
                if not self.start():
                    return {"stdout": "", "stderr": "sandbox_not_running",
                            "exit_code": -1, "duration_s": 0.0}
            timeout = timeout or self.config.timeout_s
            try:
                start = time.time()
                result = subprocess.run(
                    ["docker", "exec", self.config.sandbox_id, "sh", "-c", command],
                    capture_output=True, text=True, timeout=timeout
                )
                duration = time.time() - start
                out = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                    "duration_s": round(duration, 3),
                }
                if result.returncode != 0:
                    self.breaker.record_failure()
                else:
                    self.breaker.record_success()
                self._log({"event": "exec", "cmd": command[:80],
                           "exit_code": result.returncode, "duration_s": out["duration_s"]})
                return out
            except subprocess.TimeoutExpired:
                self.breaker.record_failure()
                self._log({"event": "exec_timeout", "timeout": timeout})
                return {"stdout": "", "stderr": "timeout", "exit_code": -1, "duration_s": timeout}
            except Exception as e:
                self.breaker.record_failure()
                self._log({"event": "exec_exception", "error": str(e)})
                return {"stdout": "", "stderr": str(e), "exit_code": -1, "duration_s": 0.0}

    def kill(self) -> bool:
        with self._lock:
            try:
                subprocess.run(["docker", "kill", self.config.sandbox_id],
                               capture_output=True, timeout=10)
                self.status = SandboxStatus.STOPPED
                self._log({"event": "killed"})
                return True
            except Exception as e:
                self._log({"event": "kill_failed", "error": str(e)})
                return False

    def destroy(self) -> bool:
        """G10: STOP limpio. Kill + rm."""
        with self._lock:
            self.kill()
            try:
                subprocess.run(["docker", "rm", "-f", self.config.sandbox_id],
                               capture_output=True, timeout=10)
                self.status = SandboxStatus.DEAD
                self._log({"event": "destroyed"})
                return True
            except Exception as e:
                self._log({"event": "destroy_failed", "error": str(e)})
                return False

    def health_check(self) -> bool:
        with self._lock:
            if self.status != SandboxStatus.RUNNING:
                return False
            try:
                r = subprocess.run(
                    ["docker", "inspect", "-f", "{{.State.Running}}", self.config.sandbox_id],
                    capture_output=True, text=True, timeout=5
                )
                healthy = r.stdout.strip() == "true"
                if self.sentinel:
                    self.sentinel.set_sandbox_health(
                        self.config.sandbox_id,
                        "alive" if healthy else "dead"
                    )
                return healthy
            except Exception:
                return False


class SandboxSupervisor:
    """Administra todos los sandboxes del orquestador."""

    def __init__(self, sentinel=None):
        self.sentinel = sentinel
        self.sandboxes: Dict[str, Sandbox] = {}
        self._lock = threading.Lock()

    def get_or_create(self, config: SandboxConfig) -> Sandbox:
        with self._lock:
            if config.sandbox_id in self.sandboxes:
                return self.sandboxes[config.sandbox_id]
            sb = Sandbox(config, sentinel=self.sentinel)
            self.sandboxes[config.sandbox_id] = sb
            return sb

    def destroy_all(self) -> None:
        with self._lock:
            for sb in self.sandboxes.values():
                sb.destroy()
            self.sandboxes.clear()

    def health_check_all(self) -> Dict[str, bool]:
        return {sid: sb.health_check() for sid, sb in self.sandboxes.items()}

    def cleanup_orphans(self) -> int:
        """Limpia contenedores huérfanos al startup."""
        try:
            r = subprocess.run(
                ["docker", "ps", "-aq", "--filter", "label=orchestrator=universal"],
                capture_output=True, text=True, timeout=10
            )
            ids = r.stdout.strip().split()
            for cid in ids:
                subprocess.run(["docker", "rm", "-f", cid], capture_output=True, timeout=5)
            return len(ids)
        except Exception:
            return 0
root@vmi3428294:~# echo 