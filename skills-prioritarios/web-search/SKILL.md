---
name: web-search
description: "Búsqueda web con fallback multi-proveedor. Primary Serper (si SERPER_API_KEY), fallback DuckDuckGo HTML scraping, fallback Bing HTML scraping. Devuelve top-N resultados con title, url, snippet. Use when una skill necesita contexto web actualizado o el knowledge registry no tiene la respuesta. Trigger with 'web-search' o 'search' o 'google'."
license: MIT
version: 0.1.0
author: Max Bryant <maxbry123@gmail.com>
allowed-tools: "http, parse"
compatibility: "Designed for OpenClaw. Compatible con Claude Code, Codex, Cursor."
tags: [research, search, web]
metadata:
  category: research
  tier: core
  source: core
  schema: agentskills.io/0.2.0
  openclaw_skill: true
---

# web-search

Búsqueda web con fallback.

## Input

| campo | default | descripción |
|-------|---------|-------------|
| `q`        | (req) | query |
| `n`        | 10    | cantidad de resultados (1..50) |
| `provider` | `auto`| `auto` / `serper` / `ddg` / `bing` |

## Routing

```
auto → serper (si SERPER_API_KEY)
     → ddg (stub hoy; futuro: duckduckgo_search pkg)
     → bing (stub hoy)
```

## Output

```json
{
  "ok": true,
  "provider_used": "serper",
  "results": [
    {"title": "...", "url": "https://...", "snippet": "..."}
  ],
  "count": 10
}
```

## Ejemplo

```bash
export SERPER_API_KEY=...
echo '{"q":"daytona io api documentation","n":5}' | openclaw skill run web-search
```

## Pendiente (v0.2)
- Implementar `ddg` y `bing` con `httpx` + `selectolax`.
- Cache local de resultados con TTL 1h.

## Tests
`scripts/validate.py` corre sin SERPER_API_KEY y verifica que cae al fallback. PASS.
