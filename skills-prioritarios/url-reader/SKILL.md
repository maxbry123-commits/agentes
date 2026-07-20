---
name: url-reader
description: "Lee una URL y devuelve el contenido en markdown limpio (sin ads, sin nav, sin scripts). Use when una skill necesita el contenido principal de una página, después de un web-search, o para ingesta de docs externas al knowledge registry. Trigger with 'read url' o 'fetch' o 'open'."
license: MIT
version: 0.1.0
author: Max Bryant <maxbry123@gmail.com>
allowed-tools: "http, parse"
compatibility: "Designed for OpenClaw. Compatible con Claude Code, Codex, Cursor."
tags: [research, reader, parse, fetch]
metadata:
  category: research
  tier: core
  source: core
  schema: agentskills.io/0.2.0
  openclaw_skill: true
---

# url-reader

Lee URL y devuelve markdown limpio.

## Input

| campo | default | descripción |
|-------|---------|-------------|
| `url`        | (req) | URL a leer |
| `max_chars`  | 50000 | cap al output |
| `timeout_s`  | 20    | timeout HTTP |

## Output

```json
{
  "ok": true,
  "status_code": 200,
  "final_url": "https://github.com/openclaw/openclaw",
  "markdown": "...",
  "length": 18432,
  "truncated": false
}
```

## v0.1 (este spec)
- Strip simple de `<script>`, `<style>`, y tags HTML.
- No es markdown real, es texto plano sin tags.
- User-Agent: `Mavis-Reader/0.1`.

## v0.2 (pendiente)
- Usar `trafilatura` para extracción real → markdown.
- Respetar `robots.txt`.
- Detectar encoding correctamente (hoy asume utf-8).

## Ejemplo

```bash
echo '{"url":"https://github.com/openclaw/openclaw","max_chars":20000}' \
  | openclaw skill run url-reader
```

## Tests
`scripts/validate.py` testea con URL inválida (debe devolver error) y shape del JSON. PASS.
