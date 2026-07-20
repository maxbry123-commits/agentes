# 🗂️ REGISTRIES — 12 Capas del Ecosistema

> Fuente única de verdad para descubrir, registrar y consultar todo lo que el sistema puede hacer.
> Diseñado por M3 (DSL DAG SHERIFF V7). Sin código ejecutable: solo **esquemas, catálogos y discovery**.

## Índice

| # | Registry | Carpeta | Pregunta que responde |
|---|----------|---------|----------------------|
| 1 | Agent Registry | `01-agent/` | ¿Qué agentes hay y cómo los llamo? |
| 2 | Skill Registry | `02-skill/` | ¿Qué skills existen y cómo las invoco? |
| 3 | Tool Registry | `03-tool/` | ¿Qué herramientas (Bash, Git, Docker, OCR, PDF, SQL…) están disponibles? |
| 4 | Prompt Registry | `04-prompt/` | ¿Qué prompts/plantillas/roles/DSL tengo guardados? |
| 5 | MCP Registry | `05-mcp/` | ¿Qué servidores MCP (GitHub, FS, PG, Browser, Slack, Gmail) están vivos? |
| 6 | Capability Registry | `06-capability/` | ¿Qué **capacidades** declaro? (vs tools concretos) |
| 7 | Knowledge Registry | `07-knowledge/` | ¿Qué manuales, API docs, wikis están indexados? |
| 8 | Memory Registry | `08-memory/` | ¿Qué funcionó antes? ¿Qué falló? (memoria operativa) |
| 9 | Workflow Registry | `09-workflow/` | ¿Existe un flujo ya preparado? (Deploy→Git→Docker→Railway) |
| 10 | Harness Registry | `10-harness/` | ¿Dónde ejecuto? (Daytona, E2B, HF, Cloudflare) |
| 11 | Model Registry | `11-model/` | ¿Qué modelo LLM uso para esto? (Claude, Gemini, Qwen, DeepSeek, Groq, OpenAI, **Minimax**) |
| 12 | Policy Registry | `12-policy/` | ¿Qué reglas, permisos y límites debo cumplir? |

## Reglas globales (todos los registries)

- **Schema-first**: cada entry tiene un JSON Schema en `schema.json` y un ejemplo válido en `example.json`.
- **Versionado semántico**: `MAJOR.MINOR.PATCH`. Breaking change → bump MAJOR.
- **Source of truth**: este directorio del repo `maxbry123-commits/agentes` es la fuente. Otros sistemas (VPS, HF, Cloudflare) son réplicas.
- **Discovery-first**: cada registry expone un endpoint de búsqueda local (`search.py` documentado, no instalado).
- **Sin secrets en entries**: las credenciales se referencian por env var (`${OC_GATEWAY_TOKEN}`).

## Estado

- 12/12 carpetas creadas.
- 0/12 schemas publicados (en este turno solo dejamos el esqueleto + propósito).
- Próximo paso: poblar con datos reales de OpenClaw Gateway y bibliotecarios externos.

## Owner

M3 — agente `Mavis` sesión root. Director: Max.
