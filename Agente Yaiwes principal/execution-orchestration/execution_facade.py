# -*- coding: utf-8 -*-
"""execution_facade — G4. Route resource* vs engine* (Bus+Manifest). 0% LLM."""
from __future__ import annotations

from typing import Any

from .capability_passport import authorize, default_engine_passport, verify_passport
from .engine_abi import make_job
from .execution_manifest import attach_manifest_to_job, sign_manifest
from .goal_lock import verify_lock_integrity
from .resource_broker import ResourceBroker
from .resource_catalog import ResourceCatalog
from .runtime_bus import RuntimeBus


class ExecutionFacade:
    """Single entry for post-lock work. No engine call without Bus+Manifest."""

    def __init__(
        self,
        *,
        bus: RuntimeBus | None = None,
        catalog: ResourceCatalog | None = None,
        passport: dict[str, Any] | None = None,
    ):
        self.bus = bus or RuntimeBus()
        self.catalog = catalog or ResourceCatalog()
        self.passport = passport
        self.broker = ResourceBroker(self.catalog, passport=passport)

    def route(
        self,
        lock: dict[str, Any],
        *,
        kind: str,
        resource_id: str | None = None,
        engine_id: str | None = None,
        prompt: str = "",
        route_name: str = "ANALYSIS",
        echo_block: str | None = None,
    ) -> dict[str, Any]:
        integ = verify_lock_integrity(lock)
        if not integ.get("ok"):
            return {"ok": False, "stage": "lock", "detail": integ}

        kind_u = (kind or "").lower()
        if kind_u in ("resource", "resource_read", "resource_load"):
            return self._resource(lock, resource_id=resource_id, load=kind_u == "resource_load")
        if kind_u in ("engine", "engine_job"):
            return self._engine(
                lock,
                engine_id=engine_id or "fake_static",
                prompt=prompt,
                route_name=route_name,
                echo_block=echo_block,
            )
        return {"ok": False, "stage": "route", "reason": f"UNKNOWN_KIND_{kind}"}

    def _resource(
        self,
        lock: dict[str, Any],
        *,
        resource_id: str | None,
        load: bool,
    ) -> dict[str, Any]:
        if not resource_id:
            return {"ok": False, "stage": "resource", "reason": "MISSING_RESOURCE_ID"}
        prep = self.broker.prepare(resource_id)
        if not prep.get("ok"):
            return {"ok": False, "stage": "resource_prepare", "detail": prep}
        if not load:
            return {"ok": True, "stage": "resource_prepare", "result": prep}
        loaded = self.broker.load(resource_id)
        return {
            "ok": bool(loaded.get("ok")),
            "stage": "resource_load",
            "result": loaded,
            "lock_id": lock.get("lock_id"),
        }

    def _engine(
        self,
        lock: dict[str, Any],
        *,
        engine_id: str,
        prompt: str,
        route_name: str,
        echo_block: str | None,
    ) -> dict[str, Any]:
        passport = self.passport or default_engine_passport(engine_id)
        pv = verify_passport(passport)
        if not pv.get("ok"):
            return {"ok": False, "stage": "passport", "detail": pv}
        cap = authorize(passport, f"route:{route_name}")
        if not cap.get("ok"):
            # ANALYSIS default often allowed; try bus:receive_job
            cap2 = authorize(passport, "bus:receive_job")
            if not cap2.get("ok"):
                return {"ok": False, "stage": "passport_cap", "detail": cap}

        job0 = make_job(
            lock_id=lock.get("lock_id") or "",
            engine_id=engine_id,
            route=route_name,
            prompt=prompt or (lock.get("objective") or ""),
            echo_block=echo_block,
        )
        man = sign_manifest(lock=lock, job=job0)
        job = attach_manifest_to_job(job0, man)
        result = self.bus.dispatch(job, lock=lock, manifest=man)
        status = result.get("status")
        ok = status in ("OK", "SUCCESS")
        return {
            "ok": ok,
            "stage": "engine_bus",
            "job": job,
            "manifest_id": man.get("manifest_id"),
            "result": result,
        }
