# -*- coding: utf-8 -*-
"""RuntimeBus — T2+T5. Manifest presence + optional verify. 0% LLM."""
from __future__ import annotations

from typing import Any, Callable

from .engine_abi import Engine, apply_goal_filter, make_result
from .execution_manifest import job_matches_manifest, verify_manifest
from .goal_lock import verify_lock_integrity


class RuntimeBusError(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


class RuntimeBus:
    """Dispatch jobs only with valid lock + manifest."""

    def __init__(
        self,
        *,
        require_manifest: bool = True,
        verify_manifest_hash: bool = True,
        require_lock_intact: bool = True,
        apply_goal_lock: bool = True,
        on_event: Callable[[dict[str, Any]], None] | None = None,
    ):
        self._engines: dict[str, Engine] = {}
        self.require_manifest = require_manifest
        self.verify_manifest_hash = verify_manifest_hash
        self.require_lock_intact = require_lock_intact
        self.apply_goal_lock = apply_goal_lock
        self.on_event = on_event
        self.history: list[dict[str, Any]] = []

    def register(self, engine: Engine) -> None:
        eid = getattr(engine, "engine_id", None)
        if not eid:
            raise RuntimeBusError("ENGINE_NO_ID")
        self._engines[str(eid)] = engine

    def unregister(self, engine_id: str) -> None:
        self._engines.pop(engine_id, None)

    def list_engines(self) -> list[str]:
        return sorted(self._engines.keys())

    def _emit(self, kind: str, payload: dict[str, Any]) -> None:
        event = {"kind": kind, **payload}
        self.history.append(event)
        if self.on_event:
            self.on_event(event)

    def dispatch(
        self,
        job: dict[str, Any],
        *,
        lock: dict[str, Any] | None = None,
        manifest: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(job, dict) or not job.get("job_id"):
            return make_result(job or {}, status="DENIED", error_code="INVALID_JOB")

        if self.require_manifest:
            mid = job.get("manifest_id")
            if not mid:
                res = make_result(job, status="DENIED", error_code="MANIFEST_REQUIRED")
                self._emit("DENY", {"job_id": job["job_id"], "reason": "MANIFEST_REQUIRED"})
                return res
            if manifest is None:
                res = make_result(job, status="DENIED", error_code="MANIFEST_OBJECT_REQUIRED")
                self._emit("DENY", {"job_id": job["job_id"], "reason": "MANIFEST_OBJECT_REQUIRED"})
                return res
            if self.verify_manifest_hash:
                match = job_matches_manifest(job, manifest)
                if not match["ok"]:
                    res = make_result(
                        job,
                        status="DENIED",
                        error_code=str(match.get("reason") or "MANIFEST_VERIFY_FAIL"),
                    )
                    self._emit("DENY", {"job_id": job["job_id"], "reason": match.get("reason")})
                    return res
            else:
                if manifest.get("manifest_id") != mid:
                    res = make_result(job, status="DENIED", error_code="MANIFEST_MISMATCH")
                    self._emit("DENY", {"job_id": job["job_id"], "reason": "MANIFEST_MISMATCH"})
                    return res

        if self.require_lock_intact:
            if lock is None:
                res = make_result(job, status="DENIED", error_code="LOCK_REQUIRED")
                self._emit("DENY", {"job_id": job["job_id"], "reason": "LOCK_REQUIRED"})
                return res
            integ = verify_lock_integrity(lock)
            if not integ["ok"]:
                res = make_result(
                    job,
                    status="DENIED",
                    error_code="LOCK_INTEGRITY_FAIL",
                    error_detail=str(integ.get("reason")),
                )
                self._emit("DENY", {"job_id": job["job_id"], "reason": "LOCK_INTEGRITY_FAIL"})
                return res
            if job.get("lock_id") and job["lock_id"] != lock.get("lock_id"):
                res = make_result(job, status="DENIED", error_code="LOCK_ID_MISMATCH")
                self._emit("DENY", {"job_id": job["job_id"], "reason": "LOCK_ID_MISMATCH"})
                return res

        engine_id = job.get("engine_id") or ""
        engine = self._engines.get(engine_id)
        if engine is None:
            res = make_result(job, status="DENIED", error_code="ENGINE_NOT_REGISTERED")
            self._emit("DENY", {"job_id": job["job_id"], "reason": "ENGINE_NOT_REGISTERED"})
            return res

        self._emit("DISPATCH", {"job_id": job["job_id"], "engine_id": engine_id})
        try:
            raw = engine.run(job)
        except Exception as exc:  # noqa: BLE001
            res = make_result(
                job,
                status="ERROR",
                error_code="ENGINE_EXCEPTION",
                error_detail=str(exc),
            )
            self._emit("ERROR", {"job_id": job["job_id"], "detail": str(exc)})
            return res

        if not isinstance(raw, dict) or "status" not in raw:
            return make_result(job, status="ERROR", error_code="INVALID_ENGINE_RESULT")

        if self.apply_goal_lock and lock is not None and raw.get("status") == "OK":
            res = apply_goal_filter(lock, job, raw.get("output_text"))
            if raw.get("artifacts") and not res.get("artifacts"):
                res = dict(res)
                res["artifacts"] = list(raw["artifacts"])
        else:
            res = raw

        self._emit(
            "RESULT",
            {"job_id": job["job_id"], "status": res.get("status"), "result_id": res.get("result_id")},
        )
        return res
