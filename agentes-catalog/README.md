# 🤖 Catálogo de Agentes — 10 (prompt M3 A)

> Documento canónico: prompt M3 DSL DAG SHERIFF V7, sección A.

| # | id | provider | modelo | tier | endpoint patrón |
|---|----|----------|--------|------|-----------------|
| 1 | openclaw    | MiniMax | MiniMax-M3 | platinum | http://127.0.0.1:8083 |
| 2 | claude-code | anthropic | claude-3.7 | gold | http://127.0.0.1:8081 |
| 3 | mimo-code   | anthropic | claude-3.7 | gold | http://127.0.0.1:8082 |
| 4 | opencode    | anthropic | claude-3.x | silver | TBD |
| 5 | codex-cli   | openai  | gpt-4o | silver | TBD |
| 6 | openhands   | openai  | gpt-4o | silver | TBD |
| 7 | kimi-cli    | alibaba | kimi-k2 | silver | TBD |
| 8 | hermes-cli  | nous    | hermes-3 | bronze | TBD |
| 9 | nemotron    | nvidia  | llama-3.1-nemotron | silver | TBD |
| 10 | litellm    | multi  | multi | gold | http://127.0.0.1:4000 |

> **Hermes tiene 3 versiones** (CLI + WebUI + Desktop): para catalogar, se listan como 3 sub-entradas bajo `hermes-cli`. Ver carpeta `hermes-cli/`, `hermes-webui/`, `hermes-desktop/`.

## Las 11 secciones de validación (sección I del prompt)

Por cada agente, su HTML de validación debe tener:

1. **Info general** — id, nombre, provider, modelo, tier, descripción.
2. **Comandos ejecutados** — todos los comandos que se corrieron para validar (con output).
3. **Verificación binario** — `which <bin>`, `version`, `help`.
4. **MCP** (Model Context Protocol) — qué MCPs tiene configurados, ping a cada uno.
5. **API Endpoints** — tabla de endpoints, método, auth, status code, body esperado.
6. **Skills/Tools instalados** — qué skills carga, qué tools invoca.
7. **Test funcional** — prompt real → respuesta real → score.
8. **Config persistente** — dónde está su config, qué env vars usa.
9. **Trazabilidad investigación** — links a docs, changelog, issues consultados.
10. **Conectividad sistema** — puede hablar con el resto (gateway, otros agentes, VPS, HF, Cloudflare).
11. **Tests finales** — batería de N tests de acceptance.

## Estructura

```
agentes-catalog/<id>/
├── index.html       # las 11 secciones embebidas
├── validation.json  # datos estructurados (alimentan el HTML)
├── log.md           # bitácora libre de la sesión de validación
└── assets/          # screenshots, logs, etc.
```

## Estado
- 11/11 carpetas creadas (10 agentes + 1 raíz).
- 1/10 HTMLs completos (OpenClaw como demo).
- 9/10 HTMLs como **template** (placeholders para llenar en próximos turnos).
