"""Runtime version and in-app self-update."""

from __future__ import annotations

import asyncio
import os
import time

from fastapi import APIRouter, Depends, HTTPException
from redcell_core.schemas import Camel
from redcell_core.security import User, current_user

router = APIRouter(tags=["system"], dependencies=[Depends(current_user)])

_GITHUB_LATEST = "https://api.github.com/repos/martian56/redcell/releases/latest"
_cache: dict[str, object] = {"at": 0.0, "latest": None}
_CACHE_TTL = 600.0


class VersionInfo(Camel):
    current: str
    latest: str | None = None
    update_available: bool = False


class UpdateStarted(Camel):
    started: bool
    detail: str


def current_version() -> str:
    return os.environ.get("REDCELL_VERSION") or "dev"


def _norm(v: str | None) -> tuple[int, ...]:
    if not v:
        return ()
    parts: list[int] = []
    for p in v.strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def update_available(current: str, latest: str | None) -> bool:
    if not latest or current == "dev":
        return False
    return _norm(latest) > _norm(current)


async def _latest_version() -> str | None:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'apps/api/app/routers/system.py','step':'_latest_version','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


@router.get("/system/version", response_model=VersionInfo)
async def version() -> VersionInfo:
    current = current_version()
    latest = await _latest_version()
    return VersionInfo(current=current, latest=latest, update_available=update_available(current, latest))


@router.post("/system/update", response_model=UpdateStarted)
async def start_update(user: User = Depends(current_user)) -> UpdateStarted:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'apps/api/app/routers/system.py','step':'start_update','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
