"""Perigord API gateway request handler."""

from auth import authenticate


def handle(request):
    """Handle one request dict {headers, path}. 401 if unauthenticated."""
    identity = authenticate(request.get("headers", {}))
    if identity is None:
        return {"status": 401, "body": "unauthenticated"}
    return {"status": 200, "body": f"hello {identity} -> {request.get('path', '/')}"}
