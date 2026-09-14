"""Handing custody of a rotating provider credential between this device and the cloud.

Cloud runs execute a user's workflow while their laptop is off, using the user's OWN subscription.
That means our server needs to refresh their token, and providers issue a new refresh token on every
refresh while treating a replayed one as theft, revoking the entire grant family. So a credential
gets exactly ONE holder that can rotate it, and the handover has to be ordered so there is never an
instant where both sides can.

The order is strip-then-upload, never the reverse:
  - Strip first, then upload: worst case nobody can rotate for a moment, which is harmless because
    the access token stays valid for hours. We restore on failure.
  - Upload first, then strip: if the strip fails, BOTH sides hold a rotating token, which is the
    exact incident this whole design exists to prevent.

The one genuinely ambiguous case is an upload that times out after the server already committed.
Restoring blindly there would recreate the two-holder state, so we ask the server who owns it
before deciding.
"""

import logging
from datetime import datetime
from typing import Literal, Optional

import httpx
from pydantic import BaseModel, ConfigDict
from typeguard import typechecked

from backend.apps.nine_router import credential_store
from backend.apps.settings.credentials import proxy_auth
from backend.apps.settings.store import load_settings

logger = logging.getLogger(__name__)

P_TIMEOUT_S = 20.0

LeaseStatus = Literal[
    "leased",
    "released",
    "refreshed",
    "not_signed_in",
    "no_such_connection",
    "not_rotatable",
    "cloud_rejected",
    "local_write_failed",
    "ownership_unknown",
]


class LeaseOutcome(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    status: LeaseStatus
    detail: str = ""


@typechecked
def p_cloud() -> Optional[tuple[str, str]]:
    """(bearer, base_url) for the signed-in user, or None when there is nothing to talk to."""
    token, base = proxy_auth(load_settings())
    if not token or not base:
        return None
    return (token, base)


@typechecked
async def p_lease_is_cloud_owned(connection_id: str) -> Optional[bool]:
    """True/False if we can read ownership, None if we cannot tell. The None case is load-bearing:
    guessing here is how you end up with two rotators."""
    cloud = p_cloud()
    if cloud is None:
        return None
    token, base = cloud
    try:
        async with httpx.AsyncClient(timeout=P_TIMEOUT_S) as client:
            r = await client.get(
                f"{base}/api/credentials/status",
                headers={"Authorization": f"Bearer {token}"},
            )
        if r.status_code != 200:
            return None
        for lease in r.json().get("leases") or []:
            if lease.get("connection_id") == connection_id:
                return lease.get("owner") == "cloud"
        return False
    except (httpx.HTTPError, ValueError):
        return None


@typechecked
async def lease_to_cloud(connection_id: str) -> LeaseOutcome:
    """Give the cloud sole custody so it can run this user's workflows while the laptop is off."""
    cloud = p_cloud()
    if cloud is None:
        return LeaseOutcome(status="not_signed_in")
    token, base = cloud

    cred = credential_store.read_credential(connection_id)
    if cred is None:
        return LeaseOutcome(status="no_such_connection")
    if not cred.refresh_token:
        # Already stripped, or an api-key row. Either way there is no rotating secret to hand over.
        return LeaseOutcome(status="not_rotatable")

    refresh_token = cred.refresh_token
    if not await credential_store.apply_to_connection(connection_id, changes={}, drop=["refreshToken"]):
        return LeaseOutcome(status="local_write_failed")

    payload = {
        "connection_id": connection_id,
        "provider": cred.provider,
        "access_token": cred.access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_ms(cred.expires_at),
    }
    try:
        async with httpx.AsyncClient(timeout=P_TIMEOUT_S) as client:
            r = await client.post(
                f"{base}/api/credentials/lease",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
        if r.status_code == 200:
            return LeaseOutcome(status="leased")
        await p_restore(connection_id, refresh_token)
        return LeaseOutcome(status="cloud_rejected", detail=f"HTTP {r.status_code}")
    except httpx.HTTPError as exc:
        # The request may still have committed server-side, so ask before putting the token back.
        owned = await p_lease_is_cloud_owned(connection_id)
        if owned is True:
            return LeaseOutcome(status="leased", detail="upload reported an error but the lease exists")
        if owned is False:
            await p_restore(connection_id, refresh_token)
            return LeaseOutcome(status="cloud_rejected", detail=str(exc))
        logger.error("lease upload outcome unknown for %s; leaving the token off this device", connection_id)
        return LeaseOutcome(status="ownership_unknown", detail=str(exc))


@typechecked
async def p_restore(connection_id: str, refresh_token: str) -> None:
    if not await credential_store.apply_to_connection(
        connection_id, changes={"refreshToken": refresh_token}, drop=[]
    ):
        logger.error("could not restore the local refresh token for %s; the user must reconnect", connection_id)


@typechecked
def expires_ms(expires_at: Optional[str]) -> int:
    """9Router stores an ISO string; the cloud wants unix ms. Unparseable reads as already expired,
    which makes the server refresh on first use instead of trusting a bad clock."""
    if not expires_at:
        return 0
    try:
        return int(datetime.fromisoformat(expires_at.replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return 0


@typechecked
async def release_to_device(connection_id: str) -> LeaseOutcome:
    """Take custody back. The server hands the live refresh token home and drops its own copy."""
    cloud = p_cloud()
    if cloud is None:
        return LeaseOutcome(status="not_signed_in")
    token, base = cloud
    try:
        async with httpx.AsyncClient(timeout=P_TIMEOUT_S) as client:
            r = await client.post(
                f"{base}/api/credentials/release",
                headers={"Authorization": f"Bearer {token}"},
                json={"connection_id": connection_id},
            )
    except httpx.HTTPError as exc:
        return LeaseOutcome(status="cloud_rejected", detail=str(exc))
    if r.status_code != 200:
        # 409 means a refresh is mid-exchange; the caller retries rather than taking a doomed token.
        return LeaseOutcome(status="cloud_rejected", detail=f"HTTP {r.status_code}")
    body = r.json()
    ok = await credential_store.apply_to_connection(
        connection_id,
        changes={"accessToken": body["access_token"], "refreshToken": body["refresh_token"]},
        drop=[],
    )
    return LeaseOutcome(status="released" if ok else "local_write_failed")


@typechecked
async def pull_access_token(connection_id: str) -> LeaseOutcome:
    """Get a usable access token for a cloud-owned credential. This is what keeps LOCAL work going
    once this device can no longer mint one itself."""
    cloud = p_cloud()
    if cloud is None:
        return LeaseOutcome(status="not_signed_in")
    token, base = cloud
    try:
        async with httpx.AsyncClient(timeout=P_TIMEOUT_S) as client:
            r = await client.get(
                f"{base}/api/credentials/access",
                headers={"Authorization": f"Bearer {token}"},
                params={"connection_id": connection_id},
            )
    except httpx.HTTPError as exc:
        return LeaseOutcome(status="cloud_rejected", detail=str(exc))
    if r.status_code != 200:
        return LeaseOutcome(status="cloud_rejected", detail=f"HTTP {r.status_code}")
    body = r.json()
    ok = await credential_store.apply_to_connection(
        connection_id, changes={"accessToken": body["access_token"]}, drop=[]
    )
    return LeaseOutcome(status="refreshed" if ok else "local_write_failed")
