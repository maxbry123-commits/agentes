# Wordflow V1 — Fronteras (bitácora V0)

**PIPELINE:** [48_ARQUITECTURA_LOOP_GATEWAY_ROUTER_V1.md](../../PIPELINE/48_ARQUITECTURA_LOOP_GATEWAY_ROUTER_V1.md)  
**Catalog:** [component_catalog.json](./component_catalog.json)

## Fronteras

1. **LOOP** — maxbry_loop v2 + 12-stage hooks + code_path tasks. Gaps → tasks → completion.
2. **GATEWAY** — `IntelligenceGateway` único camino a LLM/memoria.
3. **ROUTER** — FastAPI externo (`ROUTER_URL`). Failover/providers fuera del Loop.
4. **ENGINES** — OpenClaw / Hermes solo `EnginePort.reason` (intermedio Wordflow↔LLM).
5. **ACQUIRE** — Acquire Engine + Recipes (OpenClaw-40 = recipe, no motor).

## Prohibido

- Loop → OpenAI/Anthropic directo
- Token en body de workflow
- Claim 100% universo documental en V1

## Flags default

```
ROUTER_URL=          # vacío = Mock
FETCH_ENABLED=false
ACQUIRE_OS_ENABLED=false
DEPLOY_DRY_RUN=true
```

## Salidas V0

| ID | Commit tema | Estado |
|----|-------------|--------|
| V0-01 | CI test-wordflow-code-path | done |
| V0-02 | component_catalog.json | done |
| V0-03 | este README fronteras | done |

Siguiente bloque: **VG** IntelligenceGateway + RouterHTTP + EnginePort stubs.
