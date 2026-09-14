# Networked Bootstrap Token Distribution

## Problem

Users deploying Cognithor in LAN/container setups can't get the API token
remotely.  The Flutter Command Center needs the token to authenticate API
calls, but the current mechanism only works when the browser runs on the
same machine as the backend.

## Current design

The token is injected via `<meta name="cognithor-token">` into `index.html`
at startup.  The served page includes the token inline so the Flutter app
can read it from the DOM.  This only works for localhost connections because
the HTML is served by the same process that holds the token.

## Why

Security hardening after **GHSA-cognithor-001** -- the old
`/api/v1/bootstrap` endpoint leaked the token without authentication.  Any
client that could reach the HTTP port could call the endpoint and obtain
full API access.  The meta-tag approach ensures the token is only visible
to a browser that can load the UI page (localhost by default).

## Future solution

- **Ed25519 capability token system:** A device presents a signed
  capability token (obtained via QR pairing or CLI) to prove it is
  authorized.  The API token is returned only after capability-token
  verification.
- **Configurable bind address:** Allow the admin to bind the API to a
  specific interface (e.g., Tailscale IP) rather than `127.0.0.1`.
- **Token only available when capability-token auth is active:** If no
  capability tokens have been provisioned, the bootstrap endpoint remains
  disabled.

## Not implemented in this release

This is documented as a known limitation of v1.0.  The meta-tag injection
is the only supported token-distribution mechanism.  Remote access requires
a reverse proxy with its own authentication layer (e.g., Caddy + basic
auth, Tailscale Funnel).
