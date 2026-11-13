"""Legacy unit checks for the Kestrel-era gateway (green before the migration)."""

from auth import authenticate
from gateway import handle


def test_valid_kestrel_token_authenticates():
    assert authenticate({"X-Kestrel-Token": "kestrel-7f3a-shared"}) == "kestrel-client"


def test_missing_token_is_rejected():
    assert authenticate({}) is None


def test_gateway_200_on_valid_token():
    resp = handle({"headers": {"X-Kestrel-Token": "kestrel-7f3a-shared"}, "path": "/ping"})
    assert resp["status"] == 200


def test_gateway_401_on_missing_token():
    assert handle({"headers": {}, "path": "/ping"})["status"] == 401
