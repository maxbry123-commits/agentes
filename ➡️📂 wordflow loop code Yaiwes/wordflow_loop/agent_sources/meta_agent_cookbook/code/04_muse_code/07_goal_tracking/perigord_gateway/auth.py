"""Auth layer for the Perigord API gateway.

Currently authenticates callers with the legacy Kestrel static-token scheme:
every request carries an `X-Kestrel-Token` header checked against a shared secret.
"""

KESTREL_SHARED_TOKEN = "kestrel-7f3a-shared"


def authenticate(headers):
    """Return the caller identity for a request, or None if unauthenticated.

    Kestrel scheme: the caller sends X-Kestrel-Token; if it matches the shared
    token, the caller is trusted and identified as 'kestrel-client'.
    """
    token = headers.get("X-Kestrel-Token")
    if token == KESTREL_SHARED_TOKEN:
        return "kestrel-client"
    return None
