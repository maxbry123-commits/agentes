"""Acceptance checks for the Falcon migration. All must pass to finish the goal."""

import hashlib
import hmac
import subprocess

from auth import authenticate
from gateway import handle

FALCON_SECRET = "falcon-9b2e-secret"


def _sign(secret, path):
    return hmac.new(secret.encode(), path.encode(), hashlib.sha256).hexdigest()


def test_valid_falcon_signature_authenticates():
    path = "/ping"
    headers = {"X-Falcon-Client": "peregrine", "X-Falcon-Signature": _sign(FALCON_SECRET, path)}
    assert authenticate(headers, path) == "peregrine"


def test_wrong_falcon_signature_rejected():
    headers = {"X-Falcon-Client": "peregrine", "X-Falcon-Signature": "deadbeef"}
    assert authenticate(headers, "/ping") is None


def test_old_kestrel_token_no_longer_authenticates():
    # The legacy header must be dead.
    assert authenticate({"X-Kestrel-Token": "kestrel-7f3a-shared"}, "/ping") is None


def test_kestrel_secret_removed_from_repo():
    hits = subprocess.run(
        ["grep", "-rIl", "KESTREL_SHARED_TOKEN", "."],
        capture_output=True, text=True,
    ).stdout.strip()
    # Only this acceptance test may name the old constant; no source file may.
    offenders = [f for f in hits.splitlines() if f not in ("./test_falcon_acceptance.py",)]
    assert offenders == [], f"Kestrel token still referenced in: {offenders}"


def test_gateway_200_on_valid_falcon():
    path = "/ping"
    sig = _sign(FALCON_SECRET, path)
    resp = handle({"headers": {"X-Falcon-Client": "peregrine", "X-Falcon-Signature": sig}, "path": path})
    assert resp["status"] == 200


def test_gateway_401_without_signature():
    assert handle({"headers": {}, "path": "/ping"})["status"] == 401
