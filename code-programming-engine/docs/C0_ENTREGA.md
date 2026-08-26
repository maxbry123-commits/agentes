# C0 — Entrega (infra de conexión)

## Archivos

| Archivo | Rol |
|---------|-----|
| `fichas/ficha_contract_template_c0.json` | Plantilla ficha abi 2.0 para módulos del motor |
| `fichas/ficha_validate_c0.py` | Validador fail-closed (CLI + API) |
| `fichas/ficha_ficha_validate_c0.json` | Ficha del validador |
| `fichas/ficha_engine_path_map_c0.json` | Ficha del path map |
| `engine_path_map_c0.yaml` | Legacy agentes → canónico Option A |

## Cómo conectar (sin tocar .py FACT)

1. Todo módulo nuevo bajo `code-programming-engine/` lleva una ficha en `fichas/`.
2. Antes de registrar: `python ficha_validate_c0.py fichas/<ficha>.json`
3. Deploy usa `engine_path_map_c0.yaml` para move/ref — no adivinar paths.

## Qué NO hace C0

- No reescribe enchufe universal.
- No mueve aún los .py FACT (solo mapa).
- No implementa pool / classifier / skills (C1+).

## Siguiente

**C1** — instance-pool (`programming_instance`, `instance_pool`, `usage_metering`) + fichas.
