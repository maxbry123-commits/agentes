"""Safe read/modify/write of 9Router's on-disk provider credentials.

9Router owns ~/.9router/db.json and rewrites the whole file whenever it refreshes a token or a
user edits a provider, and its HTTP API has no route that can write an OAuth connection's tokens
(PUT /api/providers/[id] accepts name/priority/isActive/apiKey only, and apiKey only for apikey
connections). So the only way to move an OAuth credential is to edit the file, which means we have
to not race the router for it. Every mutation here happens with the router stopped.

The reason any of this exists: providers hand back a NEW refresh token on every refresh and treat
a replayed one as theft, revoking the whole grant family. So a credential may have exactly one
holder that can refresh it. Removing `refreshToken` from a connection is what makes a given
9Router instance structurally unable to rotate, because its refresh dispatcher bails on a falsy
refreshToken before it ever calls the provider.
"""

import asyncio
import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, ConfigDict
from typeguard import typechecked

from backend.apps.nine_router import process

logger = logging.getLogger(__name__)

P_SHUTDOWN_TIMEOUT_S = 5.0
P_DOWN_POLL_INTERVAL_S = 0.1
P_DOWN_WAIT_S = 10.0


class ProviderCredential(BaseModel):
    """The transferable half of a 9Router provider connection."""

    model_config = ConfigDict(validate_assignment=True)

    connection_id: str
    provider: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[str] = None


@typechecked
def db_path() -> str:
    return os.path.join(process.nine_router_data_dir(), "db.json")


@typechecked
def p_load_db() -> Optional[Dict[str, Any]]:
    try:
        with open(db_path(), encoding="utf-8") as f:
            db = json.load(f)
        return db if isinstance(db, dict) else None
    except (OSError, ValueError):
        logger.warning("could not read 9router db.json", exc_info=True)
        return None


@typechecked
def p_write_db(db: Dict[str, Any]) -> bool:
    """Atomic replace at 0600. A half-written db.json costs the user every provider connection."""
    path = db_path()
    directory = os.path.dirname(path)
    handle, temp_path = tempfile.mkstemp(dir=directory, prefix=".db.json.", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, path)
        return True
    except OSError:
        logger.warning("could not write 9router db.json", exc_info=True)
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        return False


@typechecked
def read_credential(connection_id: str) -> Optional[ProviderCredential]:
    """The tokens for one connection, readable whether or not the router is up."""
    for c in process.read_persisted_connections():
        if c.get("id") != connection_id:
            continue
        access = c.get("accessToken")
        if not isinstance(access, str) or not access:
            return None
        refresh = c.get("refreshToken")
        expires = c.get("expiresAt")
        return ProviderCredential(
            connection_id=connection_id,
            provider=str(c.get("provider") or ""),
            access_token=access,
            refresh_token=refresh if isinstance(refresh, str) and refresh else None,
            expires_at=expires if isinstance(expires, str) else None,
        )
    return None


@typechecked
def list_oauth_connection_ids() -> List[str]:
    """Connections that carry a rotating credential; apikey rows have nothing to lease."""
    return [
        str(c.get("id"))
        for c in process.read_persisted_connections()
        if c.get("authType") == "oauth" and c.get("id")
    ]


@typechecked
async def request_shutdown() -> None:
    """Ask the router to exit over HTTP. Its own seam so a test can never reach a real router."""
    try:
        async with httpx.AsyncClient(timeout=P_SHUTDOWN_TIMEOUT_S, headers=process.cli_auth_headers()) as client:
            await client.post(f"{process.NINE_ROUTER_API}/shutdown")
    except (httpx.HTTPError, AttributeError):
        pass


@typechecked
async def p_stop_router() -> bool:
    """Down the router however we can reach it. `stop()` alone only kills one we spawned; an
    adopted port-holder has no handle, so ask it to shut itself down over HTTP first."""
    await request_shutdown()
    process.stop()
    waited = 0.0
    while waited < P_DOWN_WAIT_S:
        if not process.is_running():
            return True
        await asyncio.sleep(P_DOWN_POLL_INTERVAL_S)
        waited += P_DOWN_POLL_INTERVAL_S
    return not process.is_running()


@typechecked
async def apply_to_connection(connection_id: str, changes: Dict[str, Any], drop: List[str]) -> bool:
    """Set `changes` and delete `drop` on one connection, with the router stopped throughout.

    Refuses to run if the router will not go down, because a concurrent refresh would either lose
    our edit or, far worse, resurrect a refresh token we are in the middle of handing away.
    """
    if not await p_stop_router():
        logger.error("refusing to edit 9router db.json: router would not stop")
        return False
    try:
        db = p_load_db()
        if db is None:
            return False
        connections = db.get("providerConnections")
        if not isinstance(connections, list):
            return False
        target = next((c for c in connections if isinstance(c, dict) and c.get("id") == connection_id), None)
        if target is None:
            logger.error("9router connection %s not found", connection_id)
            return False
        target.update(changes)
        for key in drop:
            target.pop(key, None)
        return p_write_db(db)
    finally:
        await process.ensure_running()
