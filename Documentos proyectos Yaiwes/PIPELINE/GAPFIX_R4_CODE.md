# GAPFIX R4 — code (no C100)

Cerrado en code (contrato, no claim de repo PASS):

1. `CONN.path_gateway` = WIRED_DENY — `consult_path_gateway` invoca IntelligenceGateway mock.
2. ingest `hops_ok` exige `hop.ok` (plugin fail-closed completo).
3. G-W13b `scope_from_git_diff`.
4. G-W14b `edges_from_mission`.
5. G-W3b disk cache de `symbol_index`.
6. catalogs v1.5.0.
7. T49 publicado como BLOCKED (sin C100).

Pendiente honesto (no es gap de wiring interno):
- ROUTER_URL live / vendor LLM (DENY por diseño)
- OpenClaw/Hermes producción (adapters WIRED_STUB)
- git apply de fase (contrato LOCATE_ONLY)
- evidencia de unittest ejecutada en esta sesión (CI discover existe)
