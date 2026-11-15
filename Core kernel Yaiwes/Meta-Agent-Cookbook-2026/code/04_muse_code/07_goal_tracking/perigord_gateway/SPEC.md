# Migration: Kestrel -> Falcon auth

The Perigord API gateway currently authenticates callers with the legacy **Kestrel**
static-token scheme (`X-Kestrel-Token` matched against a shared secret). Migrate it to
the **Falcon** request-signing scheme.

## Falcon scheme (the target)

- The caller sends two headers: `X-Falcon-Client` (a client id) and `X-Falcon-Signature`.
- The signature is `HMAC-SHA256(secret, path)` rendered as lowercase hex, where `path`
  is the request path and `secret` is the client's registered secret.
- Registered client: id `peregrine`, secret `falcon-9b2e-secret`.
- On a valid signature, `authenticate` returns the client id (e.g. `peregrine`).
- On a missing or wrong signature, `authenticate` returns `None`.

## Acceptance checks (every one must pass)

1. A request signed correctly for client `peregrine` authenticates and returns that id.
2. A request bearing the OLD Kestrel token header no longer authenticates (returns `None`).
3. The legacy shared-secret constant and all Kestrel code paths are gone from the source.
4. The gateway returns 200 for a validly-signed Falcon request and 401 otherwise.
5. `python3 -m pytest -q` is green.
