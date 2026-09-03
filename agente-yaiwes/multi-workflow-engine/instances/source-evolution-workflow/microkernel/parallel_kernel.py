#!/usr/bin/env python3
"""Run authorized YAIWES workflow lanes concurrently and independently."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

AUTHORIZED: Final = "AUTHORIZED"


class ContractError(ValueError):
    """Raised when a registry or authorization violates the kernel contract."""


@dataclass(frozen=True, kw_only=True)
class Lane:
    lane_id: str
    command: tuple[str, ...]
    cwd: Path
    timeout_seconds: float


@dataclass(frozen=True, kw_only=True)
class LaneResult:
    lane_id: str
    status: str
    returncode: int | None
    duration_ms: int
    stdout: str
    stderr: str


@dataclass(frozen=True, kw_only=True)
class KernelReport:
    run_id: str
    proposal_fingerprint: str
    started_at: str
    finished_at: str
    verdict: str
    results: tuple[LaneResult, ...]


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError(f"{path}: root must be an object")
    return value


def _fingerprint(registry: dict[str, object]) -> str:
    payload = json.dumps(registry, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _validate(registry: dict[str, object], authorization: dict[str, object]) -> tuple[Lane, ...]:
    if authorization.get("state") != AUTHORIZED:
        raise ContractError("director authorization is absent")
    fingerprint = _fingerprint(registry)
    if authorization.get("proposal_fingerprint") != fingerprint:
        raise ContractError("authorization fingerprint does not match registry")
    approved = authorization.get("approved_lane_ids")
    if not isinstance(approved, list) or not all(isinstance(item, str) for item in approved):
        raise ContractError("approved_lane_ids must be a string list")
    raw_lanes = registry.get("lanes")
    if not isinstance(raw_lanes, list) or not raw_lanes:
        raise ContractError("registry must contain lanes")
    lanes: list[Lane] = []
    seen: set[str] = set()
    for raw in raw_lanes:
        if not isinstance(raw, dict):
            raise ContractError("lane must be an object")
        lane_id = raw.get("id")
        command = raw.get("command")
        cwd = raw.get("cwd")
        timeout = raw.get("timeout_seconds", 300)
        if not isinstance(lane_id, str) or not lane_id or lane_id in seen:
            raise ContractError("lane ids must be unique non-empty strings")
        if lane_id not in approved:
            continue
        if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
            raise ContractError(f"{lane_id}: command must be a non-empty argv list")
        if not isinstance(cwd, str) or not Path(cwd).is_dir():
            raise ContractError(f"{lane_id}: cwd must exist")
        if not isinstance(timeout, (int, float)) or not 0 < float(timeout) <= 3600:
            raise ContractError(f"{lane_id}: invalid timeout")
        seen.add(lane_id)
        lanes.append(Lane(lane_id=lane_id, command=tuple(command), cwd=Path(cwd), timeout_seconds=float(timeout)))
    if set(approved) != {lane.lane_id for lane in lanes}:
        raise ContractError("authorization names unknown or unavailable lanes")
    return tuple(lanes)


class ParallelEvolutionKernel:
    """Bounded runner; lane failures are captured instead of cancelling siblings."""

    def __init__(self, *, max_parallel: int = 4, output_limit: int = 100_000) -> None:
        if not 1 <= max_parallel <= 16:
            raise ContractError("max_parallel must be between 1 and 16")
        self._semaphore = asyncio.Semaphore(max_parallel)
        self._output_limit = output_limit

    async def _run_lane(self, lane: Lane) -> LaneResult:
        started = time.monotonic()
        async with self._semaphore:
            process: asyncio.subprocess.Process | None = None
            try:
                process = await asyncio.create_subprocess_exec(
                    *lane.command,
                    cwd=lane.cwd,
                    env={"PATH": os.environ.get("PATH", ""), "PYTHONUNBUFFERED": "1"},
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), lane.timeout_seconds)
                code = process.returncode
                status = "PASS" if code == 0 else "FAIL"
            except TimeoutError:
                if process is not None:
                    process.kill()
                    await process.wait()
                stdout, stderr, code, status = b"", b"timeout", None, "TIMEOUT"
            except Exception as exc:  # boundary converts a lane error into evidence
                stdout, stderr, code, status = b"", repr(exc).encode(), None, "ERROR"
        elapsed = int((time.monotonic() - started) * 1000)
        return LaneResult(
            lane_id=lane.lane_id,
            status=status,
            returncode=code,
            duration_ms=elapsed,
            stdout=stdout.decode(errors="replace")[: self._output_limit],
            stderr=stderr.decode(errors="replace")[: self._output_limit],
        )

    async def run(self, *, lanes: tuple[Lane, ...], fingerprint: str) -> KernelReport:
        started = datetime.now(UTC)
        tasks = [asyncio.create_task(self._run_lane(lane), name=lane.lane_id) for lane in lanes]
        results = tuple(sorted(await asyncio.gather(*tasks), key=lambda item: item.lane_id))
        verdict = "PASS" if all(item.status == "PASS" for item in results) else "FAIL"
        return KernelReport(
            run_id=f"evolution-{started:%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}",
            proposal_fingerprint=fingerprint,
            started_at=started.isoformat(),
            finished_at=datetime.now(UTC).isoformat(),
            verdict=verdict,
            results=results,
        )


def _write_new_atomic(directory: Path, report: KernelReport) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{report.run_id}.json"
    fd, temporary = tempfile.mkstemp(prefix=".kernel-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(asdict(report), handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if destination.exists():
            raise FileExistsError(destination)
        Path(temporary).replace(destination)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    return destination


async def _main(args: argparse.Namespace) -> int:
    registry = _load_json(args.registry)
    authorization = _load_json(args.authorization)
    lanes = _validate(registry, authorization)
    report = await ParallelEvolutionKernel(max_parallel=args.max_parallel).run(
        lanes=lanes, fingerprint=_fingerprint(registry)
    )
    print(_write_new_atomic(args.ledger_dir, report))
    return 0 if report.verdict == "PASS" else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=Path)
    parser.add_argument("authorization", type=Path)
    parser.add_argument("--ledger-dir", type=Path, default=Path("ledgers"))
    parser.add_argument("--max-parallel", type=int, default=4)
    return asyncio.run(_main(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
