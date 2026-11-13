# HANDOFF — MAPA COMPLETO DEL WORKFLOW LOOPS CODE YAIWES (corte 2026-10-09)

Documento solo de ubicación (docs). No contiene secretos. Horas en COT (UTC-5). Todos los enlaces fueron comprobados contra la API de GitHub el 2026-10-09.

## 0. Respuesta corta — dónde está el workflow

| # | Ubicación | Repo / rama | Archivos | Estado |
|---|---|---|---|---|
| 1 | [`➡️📂 wordflow loop code Yaiwes/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes) | `agentes` @ `main` (último cambio [62570960cb](https://github.com/maxbry123-commits/agentes/commit/62570960cb8345c0660acdfd9e6d5bde2fe7e6a7), 2026-10-01 12:21 COT) | 154.796 blobs + 13 submódulos (=154.809) | **ORIGINAL y MÁS COMPLETA**. Raíz canónica única. |
| 2 | [`chat router/Workflow Loop code Yaiwes/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes) | router @ `devin/1790824641-chat-agent-plan` ([PR #6](https://github.com/maxbry123-commits/router-universal-router-inteligente-/pull/6), abierto, sin fusionar) — punta [afd424bc9e](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/afd424bc9eb92e164a07e9b6d33709534079d15a) (2026-10-08 22:05 COT) | 15.630 | Raíz única del router desde [93f9a90168](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/93f9a90168a757d9c15535cab8ca9645fcf492ea) (2026-10-08 20:19 COT). Incluye el workflow recortado + plan/estado/evidencia + harness DeepSeek + capas L01–L06. |
| 3 | [`chat router/📂 workflow Loops code Yaiwes/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes) | router, rama Devin, **histórico** (fijado al commit 81e6c43eb6, 2026-10-06 19:48 COT) | 494 | Ya NO existe en la punta de la rama: el 2026-10-08 se aplanó dentro de la ubicación 2. |
| 4 | `main` del router | router @ `main` | — | **El workflow NO está en `main`.** En `main` solo están [`chat router/deepseek-harness-chat/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/deepseek-harness-chat) y [`chat router/chat frontend/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/chat%20frontend). |

Genealogía:

1. `agentes@main` `➡️📂 wordflow loop code Yaiwes` = original. Consolidación de raíces duplicadas el 2026-10-01 ([62570960cb](https://github.com/maxbry123-commits/agentes/commit/62570960cb8345c0660acdfd9e6d5bde2fe7e6a7) «handoff: lock single canonical Wordflow root»).
2. [b214f9fe96](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/b214f9fe96e26091bc0f4e36995d10e8d70bbf65) (2026-10-01 12:20 COT): copia al router en `chat router/wordflow loop code Yaiwes` vía motor_3, 397 archivos VERIFIED_CLOSED, **excluye `wordflow_loop/agent_sources` y `frontend/`** por orden del Director.
3. [0e36940f6d](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/0e36940f6dd2f02fed4087b943bdc147b8a54220) … [b384864666](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/b38486466657586669b9d64e11c3e75138a8f26e) (2026-10-01): Devin añade tests, task_runtime, contracts, adapters, skills_schema (24+ DAG), S-07A 6 motores como Native Toolset.
4. [7b52b8ee18](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/7b52b8ee182c806550d361f98a022751896ee251) (2026-10-02 03:04 COT, Claude «RONDA 0»): crea `chat router/📂 workflow Loops code Yaiwes` como copia exacta (árbol f8aee828). EQUIPO-3/5/7 siguen editándola hasta [b0f9b1efa2](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/b0f9b1efa23d988682a7a6f7a9395ff9426c8165) (2026-10-02 19:47 COT).
5. [81e6c43eb6](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5) (2026-10-06 19:48 COT): handoff «mapa de ubicación».
6. [751483acd5](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/751483acd54917a477abf7539c08ea3fba3cba05) → [93f9a90168](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/93f9a90168a757d9c15535cab8ca9645fcf492ea) (2026-10-08 20:18–20:19 COT): «una sola raíz `chat router/Workflow Loop code Yaiwes` (sin emoji); copias viejas en `_copias-anteriores`». [68e3ad8dfd](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/68e3ad8dfd90c11d199278b026787804c1192e78) estado + GAPs; [c8c0e2b4aa](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/c8c0e2b4aa713327cd415012adb912a7ed61ad45)/[2b0b2221a1](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/2b0b2221a178e11d071640102910439f87baaa48) fix RAIZ.
7. [b34919fb70](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/b34919fb70783838d17d5cbaae49dda1bdffc4d6) … [afd424bc9e](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/afd424bc9eb92e164a07e9b6d33709534079d15a) (2026-10-08 22:05 COT, 9 commits): capas L01–L06 en [`wordflow_loop/wordflow_loop/layers/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/layers).

## 1. Repo `agentes` @ `main` — raíz `➡️📂 wordflow loop code Yaiwes/` (ORIGINAL)

Raíz: [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes). Conteos = archivos (blobs) bajo cada carpeta.

### 1.1 Primer nivel

| Entrada | Tipo | Archivos |
|---|---|---|
| [`Crazy Wall Orquestador`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador) | carpeta | 51 |
| [`GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md) | archivo | 1 |
| [`HANDOFF.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/HANDOFF.md) | archivo | 1 |
| [`PLAN-4-OBJETIVOS`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/PLAN-4-OBJETIVOS) | carpeta | 4 |
| [`PLAN-PROGRAMACION-11-OBJETIVOS-Y-AGENTES.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/PLAN-PROGRAMACION-11-OBJETIVOS-Y-AGENTES.md) | archivo | 1 |
| [`arquitectura`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura) | carpeta | 24 |
| [`backend`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend) | carpeta | 66 |
| [`frontend`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend) | carpeta | 42078 |
| [`minimax_mcp`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/minimax_mcp) | carpeta | 6 |
| [`runtime`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime) | carpeta | 123 |
| [`wordflow_loop`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop) | carpeta | 112329 |
| [`workspace`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/workspace) | carpeta | 6 |
| [`➡️📂 README arquitectura Wordflow LOOP Yaiwes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20README%20arquitectura%20Wordflow%20LOOP%20Yaiwes.md) | archivo | 1 |
| [`➡️📂 readme indice agentes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20readme%20indice%20agentes.md) | archivo | 1 |
| [`➡️📂 readme wordflow loop Yaiwes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20readme%20wordflow%20loop%20Yaiwes.md) | archivo | 1 |
| [`➡️📂motores de descarga extracción copiado movimiento archivos agentes`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes) | carpeta | 7 |
| [`📂 Capa de persistencia open mythos`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20de%20persistencia%20open%20mythos) | carpeta | 2 |
| [`📂 Capa workflow GitHub Action`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20GitHub%20Action) | carpeta | 5 |
| [`📂 Capa workflow evolución`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20evoluci%C3%B3n) | carpeta | 4 |
| [`📂 archivos download`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download) | carpeta | 74 |
| [`📂 notas auditoría Claude`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude) | carpeta | 11 |

### 1.2 `wordflow_loop/` — núcleo + agent_sources (112.329)

`agent_sources/` = 112.202 archivos materializados + 13 submódulos MiniMax/Kimi/mcode (fijan repo+commit; para tenerlos completos hay que inicializar submódulos, ver `.gitmodules`).

| Ruta | Archivos |
|---|---|
| [`README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/README.md) | 1 |
| [`adapters/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/adapters) | 2 |
| [`agent_sources/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources) | 112202 |
| &nbsp;&nbsp;[`agent_sources/agent_zero/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/agent_zero) | 2965 |
| &nbsp;&nbsp;[`agent_sources/aider/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/aider) | 695 |
| &nbsp;&nbsp;[`agent_sources/claude_code/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/claude_code) | 230 |
| &nbsp;&nbsp;[`agent_sources/cline/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/cline) | 3860 |
| &nbsp;&nbsp;[`agent_sources/codex/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/codex) | 6747 |
| &nbsp;&nbsp;[`agent_sources/cua_mcp/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/cua_mcp) | 9 |
| &nbsp;&nbsp;[`agent_sources/goose/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/goose) | 2464 |
| &nbsp;&nbsp;[`agent_sources/hermes/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/hermes) | 13018 |
| &nbsp;&nbsp;[`agent_sources/kimi_agent_rs`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/kimi_agent_rs) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/kimi_agent_sdk`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/kimi_agent_sdk) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/kimi_cli`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/kimi_cli) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/kimi_code`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/kimi_code) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/kimi_k/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/kimi_k) | 6 |
| &nbsp;&nbsp;[`agent_sources/kimi_researcher`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/kimi_researcher) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/mcode`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/mcode) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/meta_agent_cookbook/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/meta_agent_cookbook) | 525 |
| &nbsp;&nbsp;[`agent_sources/meta_muse_code_sdk/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/meta_muse_code_sdk) | 224 |
| &nbsp;&nbsp;[`agent_sources/metacua/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/metacua) | 76 |
| &nbsp;&nbsp;[`agent_sources/mimo_code/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/mimo_code) | 9 |
| &nbsp;&nbsp;[`agent_sources/minimax_code_plugins`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/minimax_code_plugins) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/minimax_coding_plan_mcp`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/minimax_coding_plan_mcp) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/minimax_mcp`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/minimax_mcp) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/minimax_mcp_js`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/minimax_mcp_js) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/minimax_mini_agent`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/minimax_mini_agent) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/minimax_mmx_cli`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/minimax_mmx_cli) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/minimax_openroom`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/minimax_openroom) | submódulo (gitlink 160000) |
| &nbsp;&nbsp;[`agent_sources/mirothinker/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/mirothinker) | 187 |
| &nbsp;&nbsp;[`agent_sources/muse_glimmer/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/muse_glimmer) | 42 |
| &nbsp;&nbsp;[`agent_sources/openclaw/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/openclaw) | 43020 |
| &nbsp;&nbsp;[`agent_sources/opencode/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/opencode) | 6600 |
| &nbsp;&nbsp;[`agent_sources/opendev/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/opendev) | 1183 |
| &nbsp;&nbsp;[`agent_sources/openhands/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/openhands) | 2174 |
| &nbsp;&nbsp;[`agent_sources/orca/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/orca) | 27324 |
| &nbsp;&nbsp;[`agent_sources/qwen_code/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/qwen_code) | 342 |
| &nbsp;&nbsp;[`agent_sources/research_agent_lab/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/research_agent_lab) | 314 |
| &nbsp;&nbsp;[`agent_sources/smolagents/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/smolagents) | 184 |
| [`code_graph/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/code_graph) | 1 |
| [`contracts/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/contracts) | 8 |
| [`evidence/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence) | 67 |
| &nbsp;&nbsp;[`evidence/agent-source-copy-state/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state) | 18 |
| [`intake/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/intake) | 1 |
| [`plugins/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/plugins) | 2 |
| [`prompts/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/prompts) | 3 |
| [`pyproject.toml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/pyproject.toml) | 1 |
| [`research/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/research) | 2 |
| [`skills/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/skills) | 1 |
| [`templates/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/templates) | 1 |
| [`wordflow_loop/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop) | 36 |
| &nbsp;&nbsp;[`wordflow_loop/agent_fleet/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet) | 23 |
| &nbsp;&nbsp;[`wordflow_loop/governance/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/governance) | 8 |
| [`workflows/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/workflows) | 1 |

### 1.3 `frontend/` (42.078)

Primer nivel de subcarpetas (Orca = 27.324, PonytailPlugin, @omniroute, open-sse, src, tests, docs…). Árbol completo a 2 niveles en el Anexo A.

| Ruta | Archivos |
|---|---|
| [`.cbmignore`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.cbmignore) | 1 |
| [`.dockerignore`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.dockerignore) | 1 |
| [`.editorconfig`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.editorconfig) | 1 |
| [`.env.devin-bridge.example`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.env.devin-bridge.example) | 1 |
| [`.env.example`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.env.example) | 1 |
| [`.env.homolog.example`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.env.homolog.example) | 1 |
| [`.gitattributes`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.gitattributes) | 1 |
| [`.github/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.github) | 36 |
| [`.gitignore`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.gitignore) | 1 |
| [`.gitleaks.toml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.gitleaks.toml) | 1 |
| [`.husky/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.husky) | 2 |
| [`.i18n-state.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.i18n-state.json) | 1 |
| [`.mailmap`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.mailmap) | 1 |
| [`.markdownlint.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.markdownlint.json) | 1 |
| [`.mergify.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.mergify.yml) | 1 |
| [`.node-version`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.node-version) | 1 |
| [`.npmignore`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.npmignore) | 1 |
| [`.npmrc`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.npmrc) | 1 |
| [`.nvmrc`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.nvmrc) | 1 |
| [`.prettierignore`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.prettierignore) | 1 |
| [`.size-limit.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.size-limit.json) | 1 |
| [`.trivyignore`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.trivyignore) | 1 |
| [`.vale.ini`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.vale.ini) | 1 |
| [`.vale/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.vale) | 1 |
| [`.vscode/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.vscode) | 1 |
| [`.zizmor.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/.zizmor.yml) | 1 |
| [`@omniroute/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/%40omniroute) | 117 |
| [`AGENTS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/AGENTS.md) | 1 |
| [`AgentSkills/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/AgentSkills) | 22 |
| [`CHANGELOG.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/CHANGELOG.md) | 1 |
| [`CLAUDE.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/CLAUDE.md) | 1 |
| [`CODE_OF_CONDUCT.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/CODE_OF_CONDUCT.md) | 1 |
| [`CONTRIBUTING.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/CONTRIBUTING.md) | 1 |
| [`Dockerfile`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/Dockerfile) | 1 |
| [`Dockerfile.bun`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/Dockerfile.bun) | 1 |
| [`GEMINI.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/GEMINI.md) | 1 |
| [`LICENSE`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/LICENSE) | 1 |
| [`Makefile`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/Makefile) | 1 |
| [`Orca/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/Orca) | 27324 |
| [`PonytailPlugin/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/PonytailPlugin) | 101 |
| [`README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/README.md) | 1 |
| [`ROADMAP.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/ROADMAP.md) | 1 |
| [`SECURITY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/SECURITY.md) | 1 |
| [`THIRD_PARTY_NOTICES.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/THIRD_PARTY_NOTICES.md) | 1 |
| [`bin/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/bin) | 281 |
| [`changelog.d/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/changelog.d) | 210 |
| [`codecov.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/codecov.yml) | 1 |
| [`config/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/config) | 27 |
| [`contrib/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/contrib) | 9 |
| [`docker-compose.prod.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/docker-compose.prod.yml) | 1 |
| [`docker-compose.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/docker-compose.yml) | 1 |
| [`docker/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/docker) | 15 |
| [`docs/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/docs) | 2063 |
| [`electron/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/electron) | 24 |
| [`eslint.complexity-ratchets.config.mjs`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/eslint.complexity-ratchets.config.mjs) | 1 |
| [`eslint.complexity.config.mjs`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/eslint.complexity.config.mjs) | 1 |
| [`eslint.config.mjs`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/eslint.config.mjs) | 1 |
| [`eslint.sonarjs.config.mjs`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/eslint.sonarjs.config.mjs) | 1 |
| [`examples/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/examples) | 15 |
| [`flake.lock`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/flake.lock) | 1 |
| [`flake.nix`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/flake.nix) | 1 |
| [`fly.toml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/fly.toml) | 1 |
| [`images/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/images) | 1 |
| [`knip.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/knip.json) | 1 |
| [`llm.txt`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/llm.txt) | 1 |
| [`news.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/news.json) | 1 |
| [`next.config.mjs`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/next.config.mjs) | 1 |
| [`open-sse/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/open-sse) | 1740 |
| [`package-lock.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/package-lock.json) | 1 |
| [`package.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/package.json) | 1 |
| [`packages/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/packages) | 7 |
| [`playwright.config.ts`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/playwright.config.ts) | 1 |
| [`pnpm-workspace.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/pnpm-workspace.yaml) | 1 |
| [`pnpm.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/pnpm.json) | 1 |
| [`postcss.config.mjs`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/postcss.config.mjs) | 1 |
| [`prettier.config.mjs`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/prettier.config.mjs) | 1 |
| [`promptfooconfig.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/promptfooconfig.yaml) | 1 |
| [`public/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/public) | 152 |
| [`scripts/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/scripts) | 319 |
| [`skills/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/skills) | 50 |
| [`socket.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/socket.yml) | 1 |
| [`sonar-project.properties`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/sonar-project.properties) | 1 |
| [`source.config.ts`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/source.config.ts) | 1 |
| [`src/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/src) | 3417 |
| [`stryker.conf.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/stryker.conf.json) | 1 |
| [`stryker.disablebail.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/stryker.disablebail.json) | 1 |
| [`task-c1-report.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/task-c1-report.md) | 1 |
| [`task-c2-report.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/task-c2-report.md) | 1 |
| [`task-c3-report.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/task-c3-report.md) | 1 |
| [`tests/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/tests) | 6070 |
| [`tsconfig.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/tsconfig.json) | 1 |
| [`tsconfig.typecheck-api.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/tsconfig.typecheck-api.json) | 1 |
| [`tsconfig.typecheck-core.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/tsconfig.typecheck-core.json) | 1 |
| [`tsconfig.typecheck-dashboard.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/tsconfig.typecheck-dashboard.json) | 1 |
| [`tsconfig.typecheck-noimplicit-core.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/tsconfig.typecheck-noimplicit-core.json) | 1 |
| [`vitest.config.ts`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/vitest.config.ts) | 1 |
| [`vitest.e2e-live.config.ts`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/vitest.e2e-live.config.ts) | 1 |
| [`vitest.mcp.config.ts`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/frontend/vitest.mcp.config.ts) | 1 |

### 1.4 `runtime/` (123)

| Ruta | Archivos |
|---|---|
| [`docs/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/docs) | 5 |
| [`plugin-manifest.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/plugin-manifest.yaml) | 1 |
| [`schemas/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/schemas) | 3 |
| [`src/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src) | 70 |
| &nbsp;&nbsp;[`src/agent/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/agent) | 1 |
| &nbsp;&nbsp;[`src/conn/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/conn) | 4 |
| &nbsp;&nbsp;[`src/core/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core) | 38 |
| &nbsp;&nbsp;[`src/governance/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/governance) | 1 |
| &nbsp;&nbsp;[`src/install/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/install) | 3 |
| &nbsp;&nbsp;[`src/mission/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/mission) | 1 |
| &nbsp;&nbsp;[`src/observability/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/observability) | 1 |
| &nbsp;&nbsp;[`src/parallel/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/parallel) | 1 |
| &nbsp;&nbsp;[`src/preflight/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/preflight) | 1 |
| &nbsp;&nbsp;[`src/recovery/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/recovery) | 5 |
| &nbsp;&nbsp;[`src/research/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/research) | 1 |
| &nbsp;&nbsp;[`src/spec/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/spec) | 1 |
| &nbsp;&nbsp;[`src/storage/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/storage) | 1 |
| &nbsp;&nbsp;[`src/tribunal/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/tribunal) | 5 |
| &nbsp;&nbsp;[`src/uek/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/uek) | 6 |
| [`tests/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests) | 44 |

### 1.5 `backend/` (66)

| Ruta | Archivos |
|---|---|
| [`Comand Center/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Comand%20Center) | 5 |
| [`Seals team YAIWES/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES) | 61 |
| &nbsp;&nbsp;[`Seals team YAIWES/Seals team 1 YAIWES/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/Seals%20team%201%20YAIWES) | 1 |
| &nbsp;&nbsp;[`Seals team YAIWES/_fuentes_extraidas/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas) | 18 |
| &nbsp;&nbsp;[`Seals team YAIWES/seals_core/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core) | 36 |

### 1.6 `Crazy Wall Orquestador/` (51)

| Ruta | Archivos |
|---|---|
| [`AGENT-RECOVERY-HANDOFFS-20260911.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/AGENT-RECOVERY-HANDOFFS-20260911.md) | 1 |
| [`ANEXO-01-PLAN-CAPAS-FUENTES-RECOVERY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/ANEXO-01-PLAN-CAPAS-FUENTES-RECOVERY.md) | 1 |
| [`AUDITORIA-ORQUESTADOR-CHAT-100X-2026-09-16.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/AUDITORIA-ORQUESTADOR-CHAT-100X-2026-09-16.md) | 1 |
| [`AUDITORIA-XRAY-CORRECCION-1A1.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/AUDITORIA-XRAY-CORRECCION-1A1.md) | 1 |
| [`AUDITORIA-XRAY-PLAN-5-PASADAS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/AUDITORIA-XRAY-PLAN-5-PASADAS.md) | 1 |
| [`BITACORA-CRAZY-WALL.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/BITACORA-CRAZY-WALL.md) | 1 |
| [`BITACORA-SWARM-COLLAB-2026-09-16.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/BITACORA-SWARM-COLLAB-2026-09-16.md) | 1 |
| [`CHECKPOINT.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/CHECKPOINT.json) | 1 |
| [`CODE-CANDIDATE-MANIFEST-PLAN30.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/CODE-CANDIDATE-MANIFEST-PLAN30.md) | 1 |
| [`DSL-DAG-TAREAS-3-PASOS.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/DSL-DAG-TAREAS-3-PASOS.yaml) | 1 |
| [`EVIDENCE-3STEP-STEP1-MOVE-SOURCE-GAP-20260907.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-3STEP-STEP1-MOVE-SOURCE-GAP-20260907.md) | 1 |
| [`EVIDENCE-PLAN30-T10-T15.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T10-T15.md) | 1 |
| [`EVIDENCE-PLAN30-T16-CLOSED.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T16-CLOSED.md) | 1 |
| [`EVIDENCE-PLAN30-T16-PARTIAL.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T16-PARTIAL.md) | 1 |
| [`EVIDENCE-PLAN30-T17-DIRECT-CODEROOT-INSPECTION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-DIRECT-CODEROOT-INSPECTION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-HISTORY-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-HISTORY-REFUTATION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-OSQUESTADOR-AUDITOR-PLUGIN-SEMANTICS-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-OSQUESTADOR-AUDITOR-PLUGIN-SEMANTICS-REFUTATION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-OSQUESTADOR-PHYSICAL-TREE-PLUGIN-SEARCH-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-OSQUESTADOR-PHYSICAL-TREE-PLUGIN-SEARCH-REFUTATION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-RESEARCH-REUSE-AUX-REPOS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-RESEARCH-REUSE-AUX-REPOS.md) | 1 |
| [`EVIDENCE-PLAN30-T17-RESEARCH-REUSE-EQUIVALENT-PATTERNS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-RESEARCH-REUSE-EQUIVALENT-PATTERNS.md) | 1 |
| [`EVIDENCE-PLAN30-T17-RESEARCH-REUSE-MOTORS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-RESEARCH-REUSE-MOTORS.md) | 1 |
| [`EVIDENCE-PLAN30-T17-RESEARCH-REUSE.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-RESEARCH-REUSE.md) | 1 |
| [`EVIDENCE-PLAN30-T17-RUNTIME-CONN-AGENT-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-RUNTIME-CONN-AGENT-REFUTATION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-RUNTIME-INSTALL-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-RUNTIME-INSTALL-REFUTATION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-CHAIN-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-CHAIN-REFUTATION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-CONTRACT-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-CONTRACT-REFUTATION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-EMIT-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-EMIT-REFUTATION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-INIT-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-INIT-REFUTATION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-MAIN-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-MAIN-REFUTATION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-REDUCER-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-REDUCER-REFUTATION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-RUNTIME-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-RUNTIME-REFUTATION.md) | 1 |
| [`EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-VERIFIER-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-VERIFIER-REFUTATION.md) | 1 |
| [`GAPS-INVESTIGACION-CODE-GRAPH-20260910.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/GAPS-INVESTIGACION-CODE-GRAPH-20260910.md) | 1 |
| [`HANDOFF-MOTOR4-MINIMAX-KIMI-2026-09-18.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/HANDOFF-MOTOR4-MINIMAX-KIMI-2026-09-18.md) | 1 |
| [`HF-USAGE-SANDBOX-POLICY-20260911.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/HF-USAGE-SANDBOX-POLICY-20260911.json) | 1 |
| [`INTEGRACION-SOL1-WORKFLOW-READBACK-20260911-1500.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/INTEGRACION-SOL1-WORKFLOW-READBACK-20260911-1500.json) | 1 |
| [`INTEGRACION-SOL1-WORKFLOW-READBACK-20260911-1601.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/INTEGRACION-SOL1-WORKFLOW-READBACK-20260911-1601.json) | 1 |
| [`LEDGER-CANONICO-PARTES-1-4.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/LEDGER-CANONICO-PARTES-1-4.md) | 1 |
| [`MOTOR-DESCARGA-RECOVERY-CHECKPOINT-2026-09-17.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/MOTOR-DESCARGA-RECOVERY-CHECKPOINT-2026-09-17.json) | 1 |
| [`PARCHES-RECUPERACION/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/PARCHES-RECUPERACION) | 3 |
| [`PLAN-LOOP-30-TAREAS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/PLAN-LOOP-30-TAREAS.md) | 1 |
| [`RECOVERY-PATCH.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/RECOVERY-PATCH.md) | 1 |
| [`STATE-SWARM-COLLAB-2026-09-16.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/STATE-SWARM-COLLAB-2026-09-16.json) | 1 |
| [`STATE.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/STATE.json) | 1 |
| [`SWARM-COLLAB-QUEUE-2026-09-16.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/SWARM-COLLAB-QUEUE-2026-09-16.json) | 1 |
| [`SYSTEM-PROMPT-V2-CODE-GRAPH-METHODS-20260911.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/SYSTEM-PROMPT-V2-CODE-GRAPH-METHODS-20260911.json) | 1 |
| [`TAREA-1-SALIDA-1-ARQUITECTURA-CAPAS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/TAREA-1-SALIDA-1-ARQUITECTURA-CAPAS.md) | 1 |
| [`TASK-NODES.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/TASK-NODES.json) | 1 |
| [`TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md) | 1 |

### 1.7 `📂 archivos download/` (74)

| Ruta | Archivos |
|---|---|
| [`📂 LOOP open source 5/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82%20LOOP%20open%20source%205) | 2 |
| [`📂Archivo download 1/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201) | 49 |
| [`📂Archivo download 10/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%2010) | 1 |
| [`📂Archivo download 2/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202) | 15 |
| [`📂Archivo download 3/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%203) | 1 |
| [`📂Archivo download 4/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%204) | 1 |
| [`📂Archivo download 5/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%205) | 1 |
| [`📂Archivo download 6/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%206) | 1 |
| [`📂Archivo download 7/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%207) | 1 |
| [`📂Archivo download 8/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%208) | 1 |
| [`📂Archivo download 9/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%209) | 1 |

### 1.8 `📂 Capa workflow GitHub Action/` (5)

| Ruta | Archivos |
|---|---|
| [`ADVERTENCIA-CODE.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20GitHub%20Action/ADVERTENCIA-CODE.json) | 1 |
| [`FORENSIC-PASS-research-download-chain-final.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20GitHub%20Action/FORENSIC-PASS-research-download-chain-final.yml) | 1 |
| [`FORENSIC-PASS-research_download_chain.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20GitHub%20Action/FORENSIC-PASS-research_download_chain.py) | 1 |
| [`gha-download-extract.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20GitHub%20Action/gha-download-extract.yml) | 1 |
| [`research_download_chain.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20GitHub%20Action/research_download_chain.py) | 1 |

### 1.9 `📂 Capa workflow evolución/` (4)

| Ruta | Archivos |
|---|---|
| [`README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20evoluci%C3%B3n/README.md) | 1 |
| [`evolution_contract.schema.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20evoluci%C3%B3n/evolution_contract.schema.json) | 1 |
| [`evolution_dag.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20evoluci%C3%B3n/evolution_dag.yaml) | 1 |
| [`evolution_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20evoluci%C3%B3n/evolution_engine.py) | 1 |

### 1.10 `📂 Capa de persistencia open mythos/` (2)

| Ruta | Archivos |
|---|---|
| [`README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20de%20persistencia%20open%20mythos/README.md) | 1 |
| [`open_mythos_persistence_loop.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20de%20persistencia%20open%20mythos/open_mythos_persistence_loop.py) | 1 |

### 1.11 Motores descarga/extracción/copiado/movimiento (7)

| Ruta | Archivos |
|---|---|
| [`➡️📂 Motor de extracción zip/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Motor%20de%20extracci%C3%B3n%20zip) | 1 |
| [`➡️📂 skills descargar extraer zip copiar mover archivos readme.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20skills%20descargar%20extraer%20zip%20copiar%20mover%20archivos%20readme.md) | 1 |
| [`➡️📂motor de copiar archivos/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motor%20de%20copiar%20archivos) | 2 |
| [`➡️📂motor de moves archivos/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motor%20de%20moves%20archivos) | 1 |
| [`📂Motor descarga de componentes y extracción de zip/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%F0%9F%93%82Motor%20descarga%20de%20componentes%20y%20extracci%C3%B3n%20de%20zip) | 2 |

### 1.12 `PLAN-4-OBJETIVOS/` (4)

| Ruta | Archivos |
|---|---|
| [`HANDOFF-PLAN-OPUS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/PLAN-4-OBJETIVOS/HANDOFF-PLAN-OPUS.md) | 1 |
| [`PLAN-ANEXO-C-2-PUNTOS-ADICIONALES.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/PLAN-4-OBJETIVOS/PLAN-ANEXO-C-2-PUNTOS-ADICIONALES.md) | 1 |
| [`PLAN-MAESTRO-4-OBJETIVOS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/PLAN-4-OBJETIVOS/PLAN-MAESTRO-4-OBJETIVOS.md) | 1 |
| [`PROMPT-DSL-DAG-PLAN-OPUS.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/PLAN-4-OBJETIVOS/PROMPT-DSL-DAG-PLAN-OPUS.yaml) | 1 |

### 1.13 `arquitectura/` (24)

| Ruta | Archivos |
|---|---|
| [`Anexo - GAPS y mejoras pendientes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Anexo%20-%20GAPS%20y%20mejoras%20pendientes.md) | 1 |
| [`Anexo 2 - Pendientes nuevos y cobertura 100.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Anexo%202%20-%20Pendientes%20nuevos%20y%20cobertura%20100.md) | 1 |
| [`Anexo 3 - Estado real documentos Claude.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Anexo%203%20-%20Estado%20real%20documentos%20Claude.md) | 1 |
| [`Anexo 4 - Docfile y MCP y ambiguedades.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Anexo%204%20-%20Docfile%20y%20MCP%20y%20ambiguedades.md) | 1 |
| [`Anexo 5 - Correccion gobernanza es real.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Anexo%205%20-%20Correccion%20gobernanza%20es%20real.md) | 1 |
| [`CONFIRMACION-4x-biblioteca.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/CONFIRMACION-4x-biblioteca.md) | 1 |
| [`CONTRATO-skill-design-anthropic-frontend.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/CONTRATO-skill-design-anthropic-frontend.md) | 1 |
| [`DISENO-MCP-contexto-compartido.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/DISENO-MCP-contexto-compartido.md) | 1 |
| [`DISENO-preguntas-siempre-activo-input-shark.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/DISENO-preguntas-siempre-activo-input-shark.md) | 1 |
| [`HANDOFF-actualizado-por-Claude.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/HANDOFF-actualizado-por-Claude.md) | 1 |
| [`PROMPT-Sol-descarga-4-componentes-nuevos.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/PROMPT-Sol-descarga-4-componentes-nuevos.md) | 1 |
| [`PROMPT-Sol-investigar-capacidad-frontend-fleet.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/PROMPT-Sol-investigar-capacidad-frontend-fleet.md) | 1 |
| [`Parte 1 - Estructura completa runtime src.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Parte%201%20-%20Estructura%20completa%20runtime%20src.md) | 1 |
| [`Parte 2 - Fase INTAKE y DAG.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Parte%202%20-%20Fase%20INTAKE%20y%20DAG.md) | 1 |
| [`Parte 3 - Fase EXECUTION y GOVERNANCE CHAIN.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Parte%203%20-%20Fase%20EXECUTION%20y%20GOVERNANCE%20CHAIN.md) | 1 |
| [`Parte 4 - Fase RECOVERY y LEDGER.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Parte%204%20-%20Fase%20RECOVERY%20y%20LEDGER.md) | 1 |
| [`Parte 5 - UEK y Agent Fleet.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Parte%205%20-%20UEK%20y%20Agent%20Fleet.md) | 1 |
| [`RESOLUCION-3-pendientes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/RESOLUCION-3-pendientes.md) | 1 |
| [`SCHEMA-frontend-browser-verified.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/SCHEMA-frontend-browser-verified.md) | 1 |
| [`SCHEMA-plantillas-RAG.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/SCHEMA-plantillas-RAG.md) | 1 |
| [`SCHEMA-refactorizacion.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/SCHEMA-refactorizacion.md) | 1 |
| [`SEALS-TEAM-YAIWES-GRUPO-1-radiografia-kernel.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/SEALS-TEAM-YAIWES-GRUPO-1-radiografia-kernel.md) | 1 |
| [`arquitectura wordflow loop code Yaiwes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/arquitectura%20wordflow%20loop%20code%20Yaiwes.md) | 1 |
| [`test.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/test.md) | 1 |

### 1.14 `📂 notas auditoría Claude/` (11)

| Ruta | Archivos |
|---|---|
| [`✅ 01_hoja_de_ruta_fundamentos_limpieza — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2001_hoja_de_ruta_fundamentos_limpieza%20%E2%80%94%20NOTA%20XRAY.md) | 1 |
| [`✅ 02_hoja_de_ruta_razonamiento_gobernanza — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2002_hoja_de_ruta_razonamiento_gobernanza%20%E2%80%94%20NOTA%20XRAY.md) | 1 |
| [`✅ 03_hoja_de_ruta_workflows_pool_memoria — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2003_hoja_de_ruta_workflows_pool_memoria%20%E2%80%94%20NOTA%20XRAY.md) | 1 |
| [`✅ 04_hoja_de_ruta_observabilidad_cierre — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2004_hoja_de_ruta_observabilidad_cierre%20%E2%80%94%20NOTA%20XRAY.md) | 1 |
| [`✅ 05_arquitectura_completa_fables — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2005_arquitectura_completa_fables%20%E2%80%94%20NOTA%20XRAY.md) | 1 |
| [`✅ 06_componentes_open_source_investigados — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2006_componentes_open_source_investigados%20%E2%80%94%20NOTA%20XRAY.md) | 1 |
| [`✅ 07_hoja_de_ruta_loops_multiapi_memoria_chat — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2007_hoja_de_ruta_loops_multiapi_memoria_chat%20%E2%80%94%20NOTA%20XRAY.md) | 1 |
| [`✅ 08_protocolo_cierre_kernel_simple — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2008_protocolo_cierre_kernel_simple%20%E2%80%94%20NOTA%20XRAY.md) | 1 |
| [`✅ 09_guia_decision_integrar_codigo_kernel — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2009_guia_decision_integrar_codigo_kernel%20%E2%80%94%20NOTA%20XRAY.md) | 1 |
| [`✅ 10_plantilla_modulos_razonamiento — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2010_plantilla_modulos_razonamiento%20%E2%80%94%20NOTA%20XRAY.md) | 1 |
| [`✅ 11_catalogo_105_algoritmos_deterministas — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2011_catalogo_105_algoritmos_deterministas%20%E2%80%94%20NOTA%20XRAY.md) | 1 |

### 1.15 `workspace/` (6)

| Ruta | Archivos |
|---|---|
| [`README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/workspace/README.md) | 1 |
| [`code/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/workspace/code) | 1 |
| [`memory/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/workspace/memory) | 1 |
| &nbsp;&nbsp;[`memory/agents/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/workspace/memory/agents) | 1 |
| [`profiles/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/workspace/profiles) | 3 |

### 1.16 `minimax_mcp/` (6)

| Ruta | Archivos |
|---|---|
| [`.env.example`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/minimax_mcp/.env.example) | 1 |
| [`.github/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/minimax_mcp/.github) | 4 |
| &nbsp;&nbsp;[`.github/ISSUE_TEMPLATE/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/minimax_mcp/.github/ISSUE_TEMPLATE) | 4 |
| [`.gitignore`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/minimax_mcp/.gitignore) | 1 |

## 2. Repo `agentes` — Plan Opus, DSL-DAG, workflows de GitHub Actions

### 2.1 `Claude notas/` y `Claude notas/PLAN-OPUS/`

| Archivo | Enlace |
|---|---|
| `Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-DSL-DAG-00-CONTRATO.yaml) |
| `Claude notas/PLAN-DSL-DAG-01-NODOS.yaml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-DSL-DAG-01-NODOS.yaml) |
| `Claude notas/PLAN-DSL-DAG-4-OBJETIVOS.yaml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-DSL-DAG-4-OBJETIVOS.yaml) |
| `Claude notas/PLAN-MAESTRO-4-OBJETIVOS.md` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-MAESTRO-4-OBJETIVOS.md) |
| `Claude notas/PLAN-OPUS/CENTRO-DE-CONTROL.yaml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/CENTRO-DE-CONTROL.yaml) |
| `Claude notas/PLAN-OPUS/CRAZY-WALL-BITACORA-PLAN-OPUS.json` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/CRAZY-WALL-BITACORA-PLAN-OPUS.json) |
| `Claude notas/PLAN-OPUS/HANDOFF-PLAN-OPUS.md` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/HANDOFF-PLAN-OPUS.md) |
| `Claude notas/PLAN-OPUS/PENDIENTE-BANCO-SECRETO-HF.md` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/PENDIENTE-BANCO-SECRETO-HF.md) |
| `Claude notas/PLAN-OPUS/PROMPT-DSL-DAG-PLAN-OPUS.yaml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/PROMPT-DSL-DAG-PLAN-OPUS.yaml) |
| `Claude notas/PLAN-OPUS/📂readme mini LOOP coda bucle.md` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/%F0%9F%93%82readme%20mini%20LOOP%20coda%20bucle.md) |
| `Claude notas/PLAN-OPUS/agentes/README-AGENTE-claude_code.md` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/agentes/README-AGENTE-claude_code.md) |
| `Claude notas/PLAN-OPUS/agentes/README-AGENTE-codex.md` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/agentes/README-AGENTE-codex.md) |
| `Claude notas/PLAN-OPUS/agentes/README-AGENTE-meta_code.md` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/agentes/README-AGENTE-meta_code.md) |
| `Claude notas/PLAN-OPUS/agentes/README-AGENTE-opencode.md` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/agentes/README-AGENTE-opencode.md) |
| `Claude notas/PLAN-OPUS/agentes/README-AGENTE-openhands.md` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/agentes/README-AGENTE-openhands.md) |
| `Claude notas/PLAN-OPUS/runner/plan_opus_loop.py` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/runner/plan_opus_loop.py) |
| `Claude notas/PLAN-OPUS/runner/sonda_apis.py` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/runner/sonda_apis.py) |

Copia de PLAN-MAESTRO-4-OBJETIVOS / HANDOFF-PLAN-OPUS / PROMPT-DSL-DAG-PLAN-OPUS también en [`➡️📂 wordflow loop code Yaiwes/PLAN-4-OBJETIVOS/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/PLAN-4-OBJETIVOS).

### 2.2 Raíz del repo `agentes`

- [`AGENTS.md`](https://github.com/maxbry123-commits/agentes/blob/main/AGENTS.md)
- [`📂 Bitácora stated JSON Craxy wall.json`](https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Bit%C3%A1cora%20stated%20JSON%20Craxy%20wall.json)
- [`.gitmodules`](https://github.com/maxbry123-commits/agentes/blob/main/.gitmodules) (define los 13 submódulos de agent_sources)
- [`➡️📂motores de descarga extracción copiado movimiento archivos agentes/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes) y [`…archivos router-universal-router-inteligente-/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20router-universal-router-inteligente-)

### 2.3 `.github/workflows/` (32 workflows del loop)

Principal: [`plan-opus-loop.yml`](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/plan-opus-loop.yml) — último cambio [ead28ecb59](https://github.com/maxbry123-commits/agentes/commit/ead28ecb59) (2026-09-21 01:23 COT); última corrida [35604237285](https://github.com/maxbry123-commits/agentes/actions/runs/35604237285) (2026-09-21 08:13 COT, success). Runner: [`Claude notas/PLAN-OPUS/runner/plan_opus_loop.py`](https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/runner/plan_opus_loop.py).

| Workflow | Enlace |
|---|---|
| `plan-opus-loop.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/plan-opus-loop.yml) |
| `wordflow-groq-test.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/wordflow-groq-test.yml) |
| `yaiwes-coda-bus-v7.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-bus-v7.yml) |
| `yaiwes-coda-canonical-identity-cleanup.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-canonical-identity-cleanup.yml) |
| `yaiwes-coda-canonical-identity-fast.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-canonical-identity-fast.yml) |
| `yaiwes-coda-internal-kernel-v4.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-internal-kernel-v4.yml) |
| `yaiwes-coda-internal-surgical-v5.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-internal-surgical-v5.yml) |
| `yaiwes-coda-internal-transform-v1.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-internal-transform-v1.yml) |
| `yaiwes-coda-internal-transform-v4.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-internal-transform-v4.yml) |
| `yaiwes-coda-mesh-v21-fast.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-mesh-v21-fast.yml) |
| `yaiwes-coda-mesh-v21.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-mesh-v21.yml) |
| `yaiwes-coda-organize-noncode.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-organize-noncode.yml) |
| `yaiwes-coda-persistence-tests.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-persistence-tests.yml) |
| `yaiwes-coda-transform-wire-v2.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-transform-wire-v2.yml) |
| `yaiwes-coda-wire-chain-v3.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda-wire-chain-v3.yml) |
| `yaiwes-coda24-download-extract.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-coda24-download-extract.yml) |
| `yaiwes-loop-step2-copy-own-code.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-loop-step2-copy-own-code.yml) |
| `yaiwes-loop5-auditor-repair-01.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-loop5-auditor-repair-01.yml) |
| `yaiwes-loop5-auditor-repair-02-api.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-loop5-auditor-repair-02-api.yml) |
| `yaiwes-loop5-auditor.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-loop5-auditor.yml) |
| `yaiwes-loop5-download-extract.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-loop5-download-extract.yml) |
| `yaiwes-loop5-repair-01.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-loop5-repair-01.yml) |
| `yaiwes-wall-loop-kernel-hold-policy.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-wall-loop-kernel-hold-policy.yml) |
| `yaiwes-wordflow-agent-source-copy.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-wordflow-agent-source-copy.yml) |
| `yaiwes-wordflow-continuity-gate.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-wordflow-continuity-gate.yml) |
| `yaiwes-wordflow-g022-g017-closure-sparse-v2.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-wordflow-g022-g017-closure-sparse-v2.yml) |
| `yaiwes-wordflow-g022-g017-closure.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-wordflow-g022-g017-closure.yml) |
| `yaiwes-wordflow-goose-official-source.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-wordflow-goose-official-source.yml) |
| `yaiwes-wordflow-hf-skills-discovery.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-wordflow-hf-skills-discovery.yml) |
| `yaiwes-wordflow-improvement-pack.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-wordflow-improvement-pack.yml) |
| `yaiwes-wordflow-muse-frontend-gates.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-wordflow-muse-frontend-gates.yml) |
| `yaiwes-wordflow-run-start.yml` | [abrir](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/yaiwes-wordflow-run-start.yml) |

### 2.4 Ramas de resultados del loop (agentes)

- [`plan-opus/G1-35568446154`](https://github.com/maxbry123-commits/agentes/tree/plan-opus/G1-35568446154)
- [`plan-opus/G1-35603492677`](https://github.com/maxbry123-commits/agentes/tree/plan-opus/G1-35603492677)
- [`plan-opus/G1-35604237285`](https://github.com/maxbry123-commits/agentes/tree/plan-opus/G1-35604237285)
- [`plan-opus/all-35566395263`](https://github.com/maxbry123-commits/agentes/tree/plan-opus/all-35566395263)
- [`plan-opus/all-35566843392`](https://github.com/maxbry123-commits/agentes/tree/plan-opus/all-35566843392)
- [`feature/m3-loop-iter1`](https://github.com/maxbry123-commits/agentes/tree/feature/m3-loop-iter1)
- [`feature/yaiwes-native-autoevolution`](https://github.com/maxbry123-commits/agentes/tree/feature/yaiwes-native-autoevolution)

## 3. Repo `agentes` — `📂coda workflow persistencias/` (~756 MB)

Raíz: [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias)

| Carpeta | Enlace |
|---|---|
| `Fables enchufe universal` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/Fables%20enchufe%20universal) |
| `🏈 YAIWES 01` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2001) |
| `🏈 YAIWES 02` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2002) |
| `🏈 YAIWES 03` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2003) |
| `🏈 YAIWES 04` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2004) |
| `🏈 YAIWES 05` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2005) |
| `🏈 YAIWES 06` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2006) |
| `🏈 YAIWES 07` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2007) |
| `🏈 YAIWES 08` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2008) |
| `🏈 YAIWES 09` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2009) |
| `🏈 YAIWES 10` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2010) |
| `🏈 YAIWES 11` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2011) |
| `🏈 YAIWES 12` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2012) |
| `🏈 YAIWES 13` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2013) |
| `🏈 YAIWES 14` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2014) |
| `🏈 YAIWES 15` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2015) |
| `🏈 YAIWES 16` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2016) |
| `🏈 YAIWES 17` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2017) |
| `🏈 YAIWES 18` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2018) |
| `🏈 YAIWES 19` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2019) |
| `🏈 YAIWES 20` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2020) |
| `🏈 YAIWES 21` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2021) |
| `🏈 YAIWES 22` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2022) |
| `🏈 YAIWES 23` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2023) |
| `🏈 YAIWES 24` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20YAIWES%2024) |
| `🏈 cancha deportiva de fútbol` | [abrir](https://github.com/maxbry123-commits/agentes/tree/main/%F0%9F%93%82coda%20workflow%20persistencias/%F0%9F%8F%88%20cancha%20deportiva%20de%20f%C3%BAtbol) |

## 4. Repo router — rama `devin/1790824641-chat-agent-plan` (PR #6) — `chat router/Workflow Loop code Yaiwes/` (15.630)

Raíz: [abrir](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes). Punta [afd424bc9e](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/afd424bc9eb92e164a07e9b6d33709534079d15a). Handoff de la rama: [`03-ESTADO/HANDOFF.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/03-ESTADO/HANDOFF.md) · [`03-ESTADO/memoria.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/03-ESTADO/memoria.md).

| Ruta | Archivos |
|---|---|
| [`00-INSTRUCCIONES/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/00-INSTRUCCIONES) | 5 |
| [`01-PLAN/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/01-PLAN) | 213 |
| &nbsp;&nbsp;[`01-PLAN/ANEXOS/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/01-PLAN/ANEXOS) | 9 |
| &nbsp;&nbsp;[`01-PLAN/REFERENCIAS-UI/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/01-PLAN/REFERENCIAS-UI) | 82 |
| &nbsp;&nbsp;[`01-PLAN/SKILLS-MAXBRY-UI/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/01-PLAN/SKILLS-MAXBRY-UI) | 82 |
| &nbsp;&nbsp;[`01-PLAN/T-11/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/01-PLAN/T-11) | 12 |
| &nbsp;&nbsp;[`01-PLAN/T-12/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/01-PLAN/T-12) | 3 |
| [`02-ARQUITECTURA/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/02-ARQUITECTURA) | 3 |
| [`03-ESTADO/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/03-ESTADO) | 44 |
| &nbsp;&nbsp;[`03-ESTADO/EQUIPOS/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/03-ESTADO/EQUIPOS) | 27 |
| [`05-AGENTES/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/05-AGENTES) | 35 |
| &nbsp;&nbsp;[`05-AGENTES/asistentes/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/05-AGENTES/asistentes) | 12 |
| &nbsp;&nbsp;[`05-AGENTES/colmena/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/05-AGENTES/colmena) | 8 |
| &nbsp;&nbsp;[`05-AGENTES/gobierno/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/05-AGENTES/gobierno) | 14 |
| [`06-ESPEJOS/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/06-ESPEJOS) | 2 |
| &nbsp;&nbsp;[`06-ESPEJOS/puente/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/06-ESPEJOS/puente) | 1 |
| &nbsp;&nbsp;[`06-ESPEJOS/tareas/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/06-ESPEJOS/tareas) | 1 |
| [`07-SENTINELAS/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/07-SENTINELAS) | 8 |
| [`09-CLAUDE-CODE/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/09-CLAUDE-CODE) | 7 |
| &nbsp;&nbsp;[`09-CLAUDE-CODE/tests/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/09-CLAUDE-CODE/tests) | 2 |
| [`10-CHAT-FUNCIONES/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/10-CHAT-FUNCIONES) | 11 |
| &nbsp;&nbsp;[`10-CHAT-FUNCIONES/tests/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/10-CHAT-FUNCIONES/tests) | 2 |
| [`11-EVIDENCIA/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/11-EVIDENCIA) | 117 |
| &nbsp;&nbsp;[`11-EVIDENCIA/equipos/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/11-EVIDENCIA/equipos) | 91 |
| &nbsp;&nbsp;[`11-EVIDENCIA/motor2-o4/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/11-EVIDENCIA/motor2-o4) | 3 |
| &nbsp;&nbsp;[`11-EVIDENCIA/motor2-s07b/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/11-EVIDENCIA/motor2-s07b) | 3 |
| &nbsp;&nbsp;[`11-EVIDENCIA/motor2-skills-ui/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/11-EVIDENCIA/motor2-skills-ui) | 3 |
| &nbsp;&nbsp;[`11-EVIDENCIA/tests/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/11-EVIDENCIA/tests) | 2 |
| [`12-FABRICA-MOTORES/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/12-FABRICA-MOTORES) | 11 |
| &nbsp;&nbsp;[`12-FABRICA-MOTORES/tests/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/12-FABRICA-MOTORES/tests) | 2 |
| [`13-CHAT-UI-SUITE/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/13-CHAT-UI-SUITE) | 6 |
| &nbsp;&nbsp;[`13-CHAT-UI-SUITE/tests/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/13-CHAT-UI-SUITE/tests) | 1 |
| [`Crazy Wall Orquestador/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador) | 51 |
| &nbsp;&nbsp;[`Crazy Wall Orquestador/PARCHES-RECUPERACION/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/PARCHES-RECUPERACION) | 3 |
| [`GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md) | 1 |
| [`HANDOFF.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/HANDOFF.md) | 1 |
| [`PLAN-4-OBJETIVOS/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/PLAN-4-OBJETIVOS) | 1 |
| [`PLAN-PROGRAMACION-11-OBJETIVOS-Y-AGENTES.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/PLAN-PROGRAMACION-11-OBJETIVOS-Y-AGENTES.md) | 1 |
| [`README-ARQUITECTURA-BACKEND.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/README-ARQUITECTURA-BACKEND.md) | 1 |
| [`_copias-anteriores/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/_copias-anteriores) | 473 |
| &nbsp;&nbsp;[`_copias-anteriores/wordflow loop code Yaiwes/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/_copias-anteriores/wordflow%20loop%20code%20Yaiwes) | 450 |
| &nbsp;&nbsp;[`_copias-anteriores/➡️📂 Wordflow LOOP Yaiwes/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/_copias-anteriores/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes) | 7 |
| &nbsp;&nbsp;[`_copias-anteriores/➡️📂motores de descarga extracción copiado movimiento archivos agentes/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/_copias-anteriores/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes) | 16 |
| [`backend/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/backend) | 68 |
| &nbsp;&nbsp;[`backend/Comand Center/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/backend/Comand%20Center) | 5 |
| &nbsp;&nbsp;[`backend/Seals team YAIWES/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES) | 63 |
| [`chat_orders/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/chat_orders) | 2 |
| &nbsp;&nbsp;[`chat_orders/results/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/chat_orders/results) | 1 |
| [`harness plugins/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/harness%20plugins) | 14099 |
| &nbsp;&nbsp;[`harness plugins/deepseek-harness-chat/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/harness%20plugins/deepseek-harness-chat) | 14096 |
| &nbsp;&nbsp;[`harness plugins/memoria/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/harness%20plugins/memoria) | 2 |
| [`memoria/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/memoria) | 88 |
| &nbsp;&nbsp;[`memoria/agent-harness/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/memoria/agent-harness) | 17 |
| &nbsp;&nbsp;[`memoria/memoria_yaiwes/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/memoria/memoria_yaiwes) | 2 |
| &nbsp;&nbsp;[`memoria/motores/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/memoria/motores) | 60 |
| &nbsp;&nbsp;[`memoria/tests/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/memoria/tests) | 3 |
| [`minimax_mcp/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/minimax_mcp) | 6 |
| &nbsp;&nbsp;[`minimax_mcp/.github/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/minimax_mcp/.github) | 4 |
| [`runtime/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/runtime) | 133 |
| &nbsp;&nbsp;[`runtime/docs/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/runtime/docs) | 5 |
| &nbsp;&nbsp;[`runtime/schemas/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/runtime/schemas) | 3 |
| &nbsp;&nbsp;[`runtime/src/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/runtime/src) | 71 |
| &nbsp;&nbsp;[`runtime/tests/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/runtime/tests) | 53 |
| [`skills_schema/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/skills_schema) | 67 |
| [`space/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/space) | 3 |
| [`wordflow_loop/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop) | 146 |
| &nbsp;&nbsp;[`wordflow_loop/adapters/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/adapters) | 8 |
| &nbsp;&nbsp;[`wordflow_loop/contracts/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/contracts) | 15 |
| &nbsp;&nbsp;[`wordflow_loop/evidence/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/evidence) | 67 |
| &nbsp;&nbsp;[`wordflow_loop/plugins/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/plugins) | 2 |
| &nbsp;&nbsp;[`wordflow_loop/prompts/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/prompts) | 3 |
| &nbsp;&nbsp;[`wordflow_loop/research/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/research) | 2 |
| &nbsp;&nbsp;[`wordflow_loop/wordflow_loop/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/wordflow_loop) | 49 |
| [`workspace/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/workspace) | 6 |
| &nbsp;&nbsp;[`workspace/code/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/workspace/code) | 1 |
| &nbsp;&nbsp;[`workspace/memory/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/workspace/memory) | 1 |
| &nbsp;&nbsp;[`workspace/profiles/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/workspace/profiles) | 3 |
| [`➡️📂 README arquitectura Wordflow LOOP Yaiwes.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20README%20arquitectura%20Wordflow%20LOOP%20Yaiwes.md) | 1 |
| [`➡️📂 readme indice agentes.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20readme%20indice%20agentes.md) | 1 |
| [`➡️📂 readme wordflow loop Yaiwes.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20readme%20wordflow%20loop%20Yaiwes.md) | 1 |
| [`➡️📂motores de descarga extracción copiado movimiento archivos agentes/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes) | 7 |
| &nbsp;&nbsp;[`➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂 Motor de extracción zip/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Motor%20de%20extracci%C3%B3n%20zip) | 1 |
| &nbsp;&nbsp;[`➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂motor de copiar archivos/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motor%20de%20copiar%20archivos) | 2 |
| &nbsp;&nbsp;[`➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂motor de moves archivos/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motor%20de%20moves%20archivos) | 1 |
| &nbsp;&nbsp;[`➡️📂motores de descarga extracción copiado movimiento archivos agentes/📂Motor descarga de componentes y extracción de zip/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%F0%9F%93%82Motor%20descarga%20de%20componentes%20y%20extracci%C3%B3n%20de%20zip) | 2 |
| [`📂 notas auditoría Claude/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude) | 11 |

Capas L01–L06 (nuevas, 2026-10-08):

- [`__init__.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/layers/__init__.py)
- [`_common.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/layers/_common.py)
- [`layer_01_research.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/layers/layer_01_research.py)
- [`layer_02_xray_documents.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/layers/layer_02_xray_documents.py)
- [`layer_03_xray_code.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/layers/layer_03_xray_code.py)
- [`layer_04_copy_move.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/layers/layer_04_copy_move.py)
- [`layer_05_download_extract.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/layers/layer_05_download_extract.py)
- [`layer_06_source_evolution.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/layers/layer_06_source_evolution.py)
- [`selftest.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/layers/selftest.py)

## 5. deepseek-harness, chat, Hermes y OpenClaw

- deepseek-harness (base que conecta todo) en router `main`: [`chat router/deepseek-harness-chat/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/deepseek-harness-chat) — 14.095 archivos (`code/` 14.090, `_archives/` 4, [`DOWNLOAD_EXTRACT_MANIFEST.json`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/deepseek-harness-chat/DOWNLOAD_EXTRACT_MANIFEST.json)); último cambio [0750a6d4e0](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/0750a6d4e0) (2026-09-30 16:54 COT).
- Copia en rama Devin: [`harness plugins/deepseek-harness-chat/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes/harness%20plugins/deepseek-harness-chat) (14.096).
- Chat (interfaz) en router `main`: [`chat router/chat frontend/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/chat%20frontend) (movida desde la rama en [d269acf982](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/d269acf982c5aa61e04cffb0718c5449f31360c5)).
- Hermes (base permanente del chat): repo fork [maxbry123-commits/hermes-agent](https://github.com/maxbry123-commits/hermes-agent) + fuente dentro del workflow [`agent_sources/hermes/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/hermes) (13.018).
- OpenClaw (base permanente del chat): repo fork [maxbry123-commits/openclaw](https://github.com/maxbry123-commits/openclaw) + fuente [`agent_sources/openclaw/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/agent_sources/openclaw) (43.020).

## 6. Comparación agentes (sin agent_sources ni frontend: 516) vs copia router `📂 workflow Loops code Yaiwes` (494, commit 81e6c43eb6)

- **397 rutas comunes.** Lista completa en el Anexo B.
- **119 solo en `agentes`** (faltan en el router).
- **97 solo en el router** (no existen en `agentes`).

### 6.1 Solo en `agentes` (119)

- [`PLAN-4-OBJETIVOS/HANDOFF-PLAN-OPUS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/PLAN-4-OBJETIVOS/HANDOFF-PLAN-OPUS.md)
- [`PLAN-4-OBJETIVOS/PLAN-ANEXO-C-2-PUNTOS-ADICIONALES.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/PLAN-4-OBJETIVOS/PLAN-ANEXO-C-2-PUNTOS-ADICIONALES.md)
- [`PLAN-4-OBJETIVOS/PROMPT-DSL-DAG-PLAN-OPUS.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/PLAN-4-OBJETIVOS/PROMPT-DSL-DAG-PLAN-OPUS.yaml)
- [`arquitectura/Anexo - GAPS y mejoras pendientes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Anexo%20-%20GAPS%20y%20mejoras%20pendientes.md)
- [`arquitectura/Anexo 2 - Pendientes nuevos y cobertura 100.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Anexo%202%20-%20Pendientes%20nuevos%20y%20cobertura%20100.md)
- [`arquitectura/Anexo 3 - Estado real documentos Claude.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Anexo%203%20-%20Estado%20real%20documentos%20Claude.md)
- [`arquitectura/Anexo 4 - Docfile y MCP y ambiguedades.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Anexo%204%20-%20Docfile%20y%20MCP%20y%20ambiguedades.md)
- [`arquitectura/Anexo 5 - Correccion gobernanza es real.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Anexo%205%20-%20Correccion%20gobernanza%20es%20real.md)
- [`arquitectura/CONFIRMACION-4x-biblioteca.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/CONFIRMACION-4x-biblioteca.md)
- [`arquitectura/CONTRATO-skill-design-anthropic-frontend.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/CONTRATO-skill-design-anthropic-frontend.md)
- [`arquitectura/DISENO-MCP-contexto-compartido.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/DISENO-MCP-contexto-compartido.md)
- [`arquitectura/DISENO-preguntas-siempre-activo-input-shark.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/DISENO-preguntas-siempre-activo-input-shark.md)
- [`arquitectura/HANDOFF-actualizado-por-Claude.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/HANDOFF-actualizado-por-Claude.md)
- [`arquitectura/PROMPT-Sol-descarga-4-componentes-nuevos.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/PROMPT-Sol-descarga-4-componentes-nuevos.md)
- [`arquitectura/PROMPT-Sol-investigar-capacidad-frontend-fleet.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/PROMPT-Sol-investigar-capacidad-frontend-fleet.md)
- [`arquitectura/Parte 1 - Estructura completa runtime src.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Parte%201%20-%20Estructura%20completa%20runtime%20src.md)
- [`arquitectura/Parte 2 - Fase INTAKE y DAG.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Parte%202%20-%20Fase%20INTAKE%20y%20DAG.md)
- [`arquitectura/Parte 3 - Fase EXECUTION y GOVERNANCE CHAIN.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Parte%203%20-%20Fase%20EXECUTION%20y%20GOVERNANCE%20CHAIN.md)
- [`arquitectura/Parte 4 - Fase RECOVERY y LEDGER.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Parte%204%20-%20Fase%20RECOVERY%20y%20LEDGER.md)
- [`arquitectura/Parte 5 - UEK y Agent Fleet.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/Parte%205%20-%20UEK%20y%20Agent%20Fleet.md)
- [`arquitectura/RESOLUCION-3-pendientes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/RESOLUCION-3-pendientes.md)
- [`arquitectura/SCHEMA-frontend-browser-verified.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/SCHEMA-frontend-browser-verified.md)
- [`arquitectura/SCHEMA-plantillas-RAG.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/SCHEMA-plantillas-RAG.md)
- [`arquitectura/SCHEMA-refactorizacion.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/SCHEMA-refactorizacion.md)
- [`arquitectura/SEALS-TEAM-YAIWES-GRUPO-1-radiografia-kernel.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/SEALS-TEAM-YAIWES-GRUPO-1-radiografia-kernel.md)
- [`arquitectura/arquitectura wordflow loop code Yaiwes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/arquitectura%20wordflow%20loop%20code%20Yaiwes.md)
- [`arquitectura/test.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/arquitectura/test.md)
- [`wordflow_loop/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/README.md)
- [`wordflow_loop/code_graph/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/code_graph/README.md)
- [`wordflow_loop/intake/COMP-CODEBASE-MEMORY-MCP.queue.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/intake/COMP-CODEBASE-MEMORY-MCP.queue.json)
- [`wordflow_loop/pyproject.toml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/pyproject.toml)
- [`wordflow_loop/skills/SKILL-WORDFLOW-LOOP.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/skills/SKILL-WORDFLOW-LOOP.md)
- [`wordflow_loop/templates/NO_VALUE_GAP.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/templates/NO_VALUE_GAP.md)
- [`wordflow_loop/workflows/wordflow-agent-fleet-step3.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/workflows/wordflow-agent-fleet-step3.yml)
- [`📂 Capa de persistencia open mythos/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20de%20persistencia%20open%20mythos/README.md)
- [`📂 Capa de persistencia open mythos/open_mythos_persistence_loop.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20de%20persistencia%20open%20mythos/open_mythos_persistence_loop.py)
- [`📂 Capa workflow GitHub Action/ADVERTENCIA-CODE.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20GitHub%20Action/ADVERTENCIA-CODE.json)
- [`📂 Capa workflow GitHub Action/FORENSIC-PASS-research-download-chain-final.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20GitHub%20Action/FORENSIC-PASS-research-download-chain-final.yml)
- [`📂 Capa workflow GitHub Action/FORENSIC-PASS-research_download_chain.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20GitHub%20Action/FORENSIC-PASS-research_download_chain.py)
- [`📂 Capa workflow GitHub Action/gha-download-extract.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20GitHub%20Action/gha-download-extract.yml)
- [`📂 Capa workflow GitHub Action/research_download_chain.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20GitHub%20Action/research_download_chain.py)
- [`📂 Capa workflow evolución/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20evoluci%C3%B3n/README.md)
- [`📂 Capa workflow evolución/evolution_contract.schema.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20evoluci%C3%B3n/evolution_contract.schema.json)
- [`📂 Capa workflow evolución/evolution_dag.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20evoluci%C3%B3n/evolution_dag.yaml)
- [`📂 Capa workflow evolución/evolution_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20Capa%20workflow%20evoluci%C3%B3n/evolution_engine.py)
- [`📂 archivos download/📂 LOOP open source 5/LOOP5_CHECKPOINT.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82%20LOOP%20open%20source%205/LOOP5_CHECKPOINT.json)
- [`📂 archivos download/📂 LOOP open source 5/LOOP5_MANIFEST.jsonl`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82%20LOOP%20open%20source%205/LOOP5_MANIFEST.jsonl)
- [`📂 archivos download/📂Archivo download 1/(T-004)_ src_uek_sandbox_manager.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/%28T-004%29_%20src_uek_sandbox_manager.py)
- [`📂 archivos download/📂Archivo download 1/EVIDENCIA DE EJECUCIÓN NODO T-007.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/EVIDENCIA%20DE%20EJECUCI%C3%93N%20NODO%20T-007.yaml)
- [`📂 archivos download/📂Archivo download 1/EVIDENCIA DE EJECUCIÓN NODO T-008.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/EVIDENCIA%20DE%20EJECUCI%C3%93N%20NODO%20T-008.yaml)
- [`📂 archivos download/📂Archivo download 1/EVIDENCIA DE EJECUCIÓN NODO T-011.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/EVIDENCIA%20DE%20EJECUCI%C3%93N%20NODO%20T-011.yaml)
- [`📂 archivos download/📂Archivo download 1/EVIDENCIA DE EJECUCIÓN NODO T-013.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/EVIDENCIA%20DE%20EJECUCI%C3%93N%20NODO%20T-013.yaml)
- [`📂 archivos download/📂Archivo download 1/EVIDENCIA DE EJECUCIÓN NODO T-014.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/EVIDENCIA%20DE%20EJECUCI%C3%93N%20NODO%20T-014.yaml)
- [`📂 archivos download/📂Archivo download 1/EVIDENCIA DE EJECUCIÓN NODO T-015.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/EVIDENCIA%20DE%20EJECUCI%C3%93N%20NODO%20T-015.yaml)
- [`📂 archivos download/📂Archivo download 1/NODO T-003_ src_research_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/NODO%20T-003_%20src_research_engine.py)
- [`📂 archivos download/📂Archivo download 1/NODO T-005_ src_install_installation_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/NODO%20T-005_%20src_install_installation_engine.py)
- [`📂 archivos download/📂Archivo download 1/NODO T-006_ src_storage_artifact_router.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/NODO%20T-006_%20src_storage_artifact_router.py)
- [`📂 archivos download/📂Archivo download 1/PECP_MAXBRY_100x_ARQUITECTURA_v4.1.0_FINAL.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/PECP_MAXBRY_100x_ARQUITECTURA_v4.1.0_FINAL.md)
- [`📂 archivos download/📂Archivo download 1/PLAN-TRABAJO-CLAUDE-WORDFLOW.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/PLAN-TRABAJO-CLAUDE-WORDFLOW.md)
- [`📂 archivos download/📂Archivo download 1/PROMPT_FASE_5_DESPLIEGUE.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/PROMPT_FASE_5_DESPLIEGUE.md)
- [`📂 archivos download/📂Archivo download 1/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/README.md)
- [`📂 archivos download/📂Archivo download 1/T001_CHAT_B_CONTRACT.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/T001_CHAT_B_CONTRACT.md)
- [`📂 archivos download/📂Archivo download 1/T007_CHAT_B_CONTRACT.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/T007_CHAT_B_CONTRACT.md)
- [`📂 archivos download/📂Archivo download 1/T011_CHAT_B_CONTRACT.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/T011_CHAT_B_CONTRACT.md)
- [`📂 archivos download/📂Archivo download 1/circuit_breaker_sla.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/circuit_breaker_sla.py)
- [`📂 archivos download/📂Archivo download 1/dag_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/dag_engine.py)
- [`📂 archivos download/📂Archivo download 1/event_bus.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/event_bus.py)
- [`📂 archivos download/📂Archivo download 1/kernel.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/kernel.py)
- [`📂 archivos download/📂Archivo download 1/merkle_governance_core.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/merkle_governance_core.py)
- [`📂 archivos download/📂Archivo download 1/mission_sharder.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/mission_sharder.py)
- [`📂 archivos download/📂Archivo download 1/pecp.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/pecp.json)
- [`📂 archivos download/📂Archivo download 1/resumen fase 1.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/resumen%20fase%201.json)
- [`📂 archivos download/📂Archivo download 1/sbom_adapter_factory.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/sbom_adapter_factory.py)
- [`📂 archivos download/📂Archivo download 1/spec_healing_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/spec_healing_engine.py)
- [`📂 archivos download/📂Archivo download 1/src_agent_agent_router.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_agent_agent_router.py)
- [`📂 archivos download/📂Archivo download 1/src_conn_manager.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_conn_manager.py)
- [`📂 archivos download/📂Archivo download 1/src_conn_rate_limit.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_conn_rate_limit.py)
- [`📂 archivos download/📂Archivo download 1/src_conn_secrets.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_conn_secrets.py)
- [`📂 archivos download/📂Archivo download 1/src_observability_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_observability_engine.py)
- [`📂 archivos download/📂Archivo download 1/src_parallel_mavis_parallel.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_parallel_mavis_parallel.py)
- [`📂 archivos download/📂Archivo download 1/src_preflight_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_preflight_engine.py)
- [`📂 archivos download/📂Archivo download 1/src_recovery_checkpoint.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_recovery_checkpoint.py)
- [`📂 archivos download/📂Archivo download 1/src_recovery_classifier.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_recovery_classifier.py)
- [`📂 archivos download/📂Archivo download 1/src_recovery_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_recovery_engine.py)
- [`📂 archivos download/📂Archivo download 1/src_recovery_reconciliation.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_recovery_reconciliation.py)
- [`📂 archivos download/📂Archivo download 1/src_tribunal_budget_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_tribunal_budget_gate.py)
- [`📂 archivos download/📂Archivo download 1/src_tribunal_constitutional.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_tribunal_constitutional.py)
- [`📂 archivos download/📂Archivo download 1/src_tribunal_cross_validator.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_tribunal_cross_validator.py)
- [`📂 archivos download/📂Archivo download 1/src_tribunal_tribunal.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_tribunal_tribunal.py)
- [`📂 archivos download/📂Archivo download 1/src_uek_boot_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_uek_boot_engine.py)
- [`📂 archivos download/📂Archivo download 1/src_uek_uek_cluster.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/src_uek_uek_cluster.py)
- [`📂 archivos download/📂Archivo download 1/state_machine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/state_machine.py)
- [`📂 archivos download/📂Archivo download 1/test_dag_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/test_dag_engine.py)
- [`📂 archivos download/📂Archivo download 1/test_event_bus.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/test_event_bus.py)
- [`📂 archivos download/📂Archivo download 1/test_state_machine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/test_state_machine.py)
- [`📂 archivos download/📂Archivo download 1/tribunal_hmac_manager.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%201/tribunal_hmac_manager.py)
- [`📂 archivos download/📂Archivo download 10/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%2010/README.md)
- [`📂 archivos download/📂Archivo download 2/DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2.md)
- [`📂 archivos download/📂Archivo download 2/ESPECIFICACION_PIPELINE_NCT.html`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/ESPECIFICACION_PIPELINE_NCT.html)
- [`📂 archivos download/📂Archivo download 2/ESPECIFICACION_PIPELINE_NCT_v2.html`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/ESPECIFICACION_PIPELINE_NCT_v2.html)
- [`📂 archivos download/📂Archivo download 2/GUIA_MAESTRA_PIPELINE_NCT_v2.html`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/GUIA_MAESTRA_PIPELINE_NCT_v2.html)
- [`📂 archivos download/📂Archivo download 2/INSTRUCCIONES_GROK_OPCION_A.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/INSTRUCCIONES_GROK_OPCION_A.md)
- [`📂 archivos download/📂Archivo download 2/PROMPT_MAESTRO_CHAT_A_CHAT_B_VERSION_MADURA.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/PROMPT_MAESTRO_CHAT_A_CHAT_B_VERSION_MADURA.md)
- [`📂 archivos download/📂Archivo download 2/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/README.md)
- [`📂 archivos download/📂Archivo download 2/UOOS_PARTE2_v3_  con este documento es el promt DSL universal para que el agente ejecute los documentos del código de ouss parte 1 RUNTIME.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/UOOS_PARTE2_v3_%20%20con%20este%20documento%20es%20el%20promt%20DSL%20universal%20para%20que%20el%20agente%20ejecute%20los%20documentos%20del%20c%C3%B3digo%20de%20ouss%20parte%201%20RUNTIME.md)
- [`📂 archivos download/📂Archivo download 2/UOOS_v2_ PARTE 1 con este docimentl clude o minimax o cualquier Ai me da los documentos para yo ejecutar con el agente que yo quiero clude code o Open claw AUTORUN-1.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/UOOS_v2_%20PARTE%201%20con%20este%20docimentl%20clude%20o%20minimax%20o%20cualquier%20Ai%20me%20da%20los%20documentos%20para%20yo%20ejecutar%20con%20el%20agente%20que%20yo%20quiero%20clude%20code%20o%20Open%20claw%20AUTORUN-1.md)
- [`📂 archivos download/📂Archivo download 2/🎯🎯🎯promt de extracción de información convierte el docuemento los item en una ficha ejecutable para llevarla para hacer  code 🎯🎯🎯🎯🎯🧩🧩🧩🧩🏗️🏗️🏗️🏗️🏗️🏗️.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/%F0%9F%8E%AF%F0%9F%8E%AF%F0%9F%8E%AFpromt%20de%20extracci%C3%B3n%20de%20informaci%C3%B3n%20convierte%20el%20docuemento%20los%20item%20en%20una%20ficha%20ejecutable%20para%20llevarla%20para%20hacer%20%20code%20%F0%9F%8E%AF%F0%9F%8E%AF%F0%9F%8E%AF%F0%9F%8E%AF%F0%9F%8E%AF%F0%9F%A7%A9%F0%9F%A7%A9%F0%9F%A7%A9%F0%9F%A7%A9%F0%9F%8F%97%EF%B8%8F%F0%9F%8F%97%EF%B8%8F%F0%9F%8F%97%EF%B8%8F%F0%9F%8F%97%EF%B8%8F%F0%9F%8F%97%EF%B8%8F%F0%9F%8F%97%EF%B8%8F.md)
- [`📂 archivos download/📂Archivo download 2/🎯💡 README PARA MAXBRY para saber que son y como se usa los 2 documentos OUSS PARTE 1 Y PARTE 2 UOOS_README🎯🎯🎯🎯🎯🎯🎯💡💡💡💡💡💡.html`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/%F0%9F%8E%AF%F0%9F%92%A1%20README%20PARA%20MAXBRY%20para%20saber%20que%20son%20y%20como%20se%20usa%20los%202%20documentos%20OUSS%20PARTE%201%20Y%20PARTE%202%20UOOS_README%F0%9F%8E%AF%F0%9F%8E%AF%F0%9F%8E%AF%F0%9F%8E%AF%F0%9F%8E%AF%F0%9F%8E%AF%F0%9F%8E%AF%F0%9F%92%A1%F0%9F%92%A1%F0%9F%92%A1%F0%9F%92%A1%F0%9F%92%A1%F0%9F%92%A1.html)
- [`📂 archivos download/📂Archivo download 2/🏗️🏗️🔌🔌 JSON para IA (DSL _ MAXBRY _ YAIWES _ NCT) este es el enchufe de todas las fichas de code del sofware el p...rdicacion para Ai y luego texto libre para mí y luego el Jason code del enchufe 🔌 🔌 🔌 🔌 🔌.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/%F0%9F%8F%97%EF%B8%8F%F0%9F%8F%97%EF%B8%8F%F0%9F%94%8C%F0%9F%94%8C%20JSON%20para%20IA%20%28DSL%20_%20MAXBRY%20_%20YAIWES%20_%20NCT%29%20este%20es%20el%20enchufe%20de%20todas%20las%20fichas%20de%20code%20del%20sofware%20el%20p...rdicacion%20para%20Ai%20y%20luego%20texto%20libre%20para%20m%C3%AD%20y%20luego%20el%20Jason%20code%20del%20enchufe%20%F0%9F%94%8C%20%F0%9F%94%8C%20%F0%9F%94%8C%20%F0%9F%94%8C%20%F0%9F%94%8C.md)
- [`📂 archivos download/📂Archivo download 2/📌✅😀Arquitectura para hacer el código Wordflow.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/%F0%9F%93%8C%E2%9C%85%F0%9F%98%80Arquitectura%20para%20hacer%20el%20c%C3%B3digo%20Wordflow.md)
- [`📂 archivos download/📂Archivo download 2/🔌 enchufe universal parte 1 fusion fables Kimi k 3 universal_plugin_bus_v2_integrated.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/%F0%9F%94%8C%20enchufe%20universal%20parte%201%20fusion%20fables%20Kimi%20k%203%20universal_plugin_bus_v2_integrated.py)
- [`📂 archivos download/📂Archivo download 2/🔌✅ enchufe universal parte 2 fusión de Kimi k 3 y fables ficha_contract_v2.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%202/%F0%9F%94%8C%E2%9C%85%20enchufe%20universal%20parte%202%20fusi%C3%B3n%20de%20Kimi%20k%203%20y%20fables%20ficha_contract_v2.py)
- [`📂 archivos download/📂Archivo download 3/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%203/README.md)
- [`📂 archivos download/📂Archivo download 4/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%204/README.md)
- [`📂 archivos download/📂Archivo download 5/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%205/README.md)
- [`📂 archivos download/📂Archivo download 6/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%206/README.md)
- [`📂 archivos download/📂Archivo download 7/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%207/README.md)
- [`📂 archivos download/📂Archivo download 8/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%208/README.md)
- [`📂 archivos download/📂Archivo download 9/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20archivos%20download/%F0%9F%93%82Archivo%20download%209/README.md)

### 6.2 Solo en el router (97)

- [`README-ARQUITECTURA-BACKEND.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/README-ARQUITECTURA-BACKEND.md)
- [`backend/Seals team YAIWES/seals_core/seals_worker.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/seals_worker.py)
- [`backend/Seals team YAIWES/seals_core/tests/test_seals_worker.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/test_seals_worker.py)
- [`runtime/src/core/task_runtime.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/runtime/src/core/task_runtime.py)
- [`runtime/tests/conftest.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/runtime/tests/conftest.py)
- [`runtime/tests/test_layer_runner.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/runtime/tests/test_layer_runner.py)
- [`runtime/tests/test_n26_typed_recovery_and_router.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/runtime/tests/test_n26_typed_recovery_and_router.py)
- [`runtime/tests/test_orchestrator_adapters.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/runtime/tests/test_orchestrator_adapters.py)
- [`runtime/tests/test_orchestrator_contracts.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/runtime/tests/test_orchestrator_contracts.py)
- [`runtime/tests/test_orchestrator_e2e.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/runtime/tests/test_orchestrator_e2e.py)
- [`runtime/tests/test_seals_motors_adapter.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/runtime/tests/test_seals_motors_adapter.py)
- [`runtime/tests/test_skills_schema.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/runtime/tests/test_skills_schema.py)
- [`runtime/tests/test_thinking_system.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/runtime/tests/test_thinking_system.py)
- [`skills_schema/21st-magic.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/21st-magic.dag.yaml)
- [`skills_schema/agent-reach.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/agent-reach.dag.yaml)
- [`skills_schema/anthropic-skills.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/anthropic-skills.dag.yaml)
- [`skills_schema/awesome-design-index.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/awesome-design-index.dag.yaml)
- [`skills_schema/cinematic-scroll.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/cinematic-scroll.dag.yaml)
- [`skills_schema/design-system.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/design-system.dag.yaml)
- [`skills_schema/design-to-code.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/design-to-code.dag.yaml)
- [`skills_schema/find-skills.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/find-skills.dag.yaml)
- [`skills_schema/firecrawl-agent.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-agent.dag.yaml)
- [`skills_schema/firecrawl-alexandria.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-alexandria.dag.yaml)
- [`skills_schema/firecrawl-build-interact.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-build-interact.dag.yaml)
- [`skills_schema/firecrawl-build-onboarding.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-build-onboarding.dag.yaml)
- [`skills_schema/firecrawl-build-scrape.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-build-scrape.dag.yaml)
- [`skills_schema/firecrawl-build-search.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-build-search.dag.yaml)
- [`skills_schema/firecrawl-build.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-build.dag.yaml)
- [`skills_schema/firecrawl-company-directories.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-company-directories.dag.yaml)
- [`skills_schema/firecrawl-competitive-intel.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-competitive-intel.dag.yaml)
- [`skills_schema/firecrawl-crawl.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-crawl.dag.yaml)
- [`skills_schema/firecrawl-dashboard-reporting.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-dashboard-reporting.dag.yaml)
- [`skills_schema/firecrawl-deep-research.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-deep-research.dag.yaml)
- [`skills_schema/firecrawl-demo-walkthrough.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-demo-walkthrough.dag.yaml)
- [`skills_schema/firecrawl-developer-index.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-developer-index.dag.yaml)
- [`skills_schema/firecrawl-download.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-download.dag.yaml)
- [`skills_schema/firecrawl-interact.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-interact.dag.yaml)
- [`skills_schema/firecrawl-knowledge-base.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-knowledge-base.dag.yaml)
- [`skills_schema/firecrawl-knowledge-ingest.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-knowledge-ingest.dag.yaml)
- [`skills_schema/firecrawl-lead-gen.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-lead-gen.dag.yaml)
- [`skills_schema/firecrawl-lead-research.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-lead-research.dag.yaml)
- [`skills_schema/firecrawl-map.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-map.dag.yaml)
- [`skills_schema/firecrawl-market-research.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-market-research.dag.yaml)
- [`skills_schema/firecrawl-monitor.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-monitor.dag.yaml)
- [`skills_schema/firecrawl-parse.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-parse.dag.yaml)
- [`skills_schema/firecrawl-qa.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-qa.dag.yaml)
- [`skills_schema/firecrawl-research-index.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-research-index.dag.yaml)
- [`skills_schema/firecrawl-research-papers.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-research-papers.dag.yaml)
- [`skills_schema/firecrawl-scrape.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-scrape.dag.yaml)
- [`skills_schema/firecrawl-search.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-search.dag.yaml)
- [`skills_schema/firecrawl-seo-audit.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-seo-audit.dag.yaml)
- [`skills_schema/firecrawl-shop.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-shop.dag.yaml)
- [`skills_schema/firecrawl-website-design-clone.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-website-design-clone.dag.yaml)
- [`skills_schema/firecrawl-workflows.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl-workflows.dag.yaml)
- [`skills_schema/firecrawl.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/firecrawl.dag.yaml)
- [`skills_schema/frontend-design-codex.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/frontend-design-codex.dag.yaml)
- [`skills_schema/frontend-design.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/frontend-design.dag.yaml)
- [`skills_schema/get-shit-done.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/get-shit-done.dag.yaml)
- [`skills_schema/hyperframes-animation.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/hyperframes-animation.dag.yaml)
- [`skills_schema/hyperframes-audio.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/hyperframes-audio.dag.yaml)
- [`skills_schema/hyperframes-cli.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/hyperframes-cli.dag.yaml)
- [`skills_schema/hyperframes-core.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/hyperframes-core.dag.yaml)
- [`skills_schema/hyperframes-creative.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/hyperframes-creative.dag.yaml)
- [`skills_schema/hyperframes-keyframes.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/hyperframes-keyframes.dag.yaml)
- [`skills_schema/hyperframes-registry.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/hyperframes-registry.dag.yaml)
- [`skills_schema/hyperframes-router.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/hyperframes-router.dag.yaml)
- [`skills_schema/image-to-code.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/image-to-code.dag.yaml)
- [`skills_schema/impeccable.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/impeccable.dag.yaml)
- [`skills_schema/local-ultra-review.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/local-ultra-review.dag.yaml)
- [`skills_schema/motion-design-engineering.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/motion-design-engineering.dag.yaml)
- [`skills_schema/one-skill-to-rule-them-all.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/one-skill-to-rule-them-all.dag.yaml)
- [`skills_schema/react-best-practices.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/react-best-practices.dag.yaml)
- [`skills_schema/scrapegraph-ai.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/scrapegraph-ai.dag.yaml)
- [`skills_schema/scrapling.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/scrapling.dag.yaml)
- [`skills_schema/skill-creator.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/skill-creator.dag.yaml)
- [`skills_schema/skill-router.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/skill-router.dag.yaml)
- [`skills_schema/superpowers.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/superpowers.dag.yaml)
- [`skills_schema/taste.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/taste.dag.yaml)
- [`skills_schema/ui-ux-pro-max.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/ui-ux-pro-max.dag.yaml)
- [`skills_schema/web-design-guidelines.dag.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema/web-design-guidelines.dag.yaml)
- [`wordflow_loop/adapters/seals_motors/hf_download_extract_engine.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/adapters/seals_motors/hf_download_extract_engine.py)
- [`wordflow_loop/adapters/seals_motors/motor_1_extract_only.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/adapters/seals_motors/motor_1_extract_only.py)
- [`wordflow_loop/adapters/seals_motors/motor_2_queue_download_extract.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/adapters/seals_motors/motor_2_queue_download_extract.py)
- [`wordflow_loop/adapters/seals_motors/motor_3_copy_batches.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/adapters/seals_motors/motor_3_copy_batches.py)
- [`wordflow_loop/adapters/seals_motors/motor_4_move_batches.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/adapters/seals_motors/motor_4_move_batches.py)
- [`wordflow_loop/adapters/seals_motors/motor_5_zip_root.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/adapters/seals_motors/motor_5_zip_root.py)
- [`wordflow_loop/contracts/seals_motors/hf_download_extract_engine.schema.json`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/contracts/seals_motors/hf_download_extract_engine.schema.json)
- [`wordflow_loop/contracts/seals_motors/manifest.json`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/contracts/seals_motors/manifest.json)
- [`wordflow_loop/contracts/seals_motors/motor_1_extract_only.schema.json`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/contracts/seals_motors/motor_1_extract_only.schema.json)
- [`wordflow_loop/contracts/seals_motors/motor_2_queue_download_extract.schema.json`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/contracts/seals_motors/motor_2_queue_download_extract.schema.json)
- [`wordflow_loop/contracts/seals_motors/motor_3_copy_batches.schema.json`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/contracts/seals_motors/motor_3_copy_batches.schema.json)
- [`wordflow_loop/contracts/seals_motors/motor_4_move_batches.schema.json`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/contracts/seals_motors/motor_4_move_batches.schema.json)
- [`wordflow_loop/contracts/seals_motors/motor_5_zip_root.schema.json`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/contracts/seals_motors/motor_5_zip_root.schema.json)
- [`wordflow_loop/wordflow_loop/orchestrator_adapters.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/wordflow_loop/orchestrator_adapters.py)
- [`wordflow_loop/wordflow_loop/orchestrator_contracts.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/wordflow_loop/orchestrator_contracts.py)
- [`wordflow_loop/wordflow_loop/runner.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/wordflow_loop/runner.py)
- [`wordflow_loop/wordflow_loop/thinking_system.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/wordflow_loop/thinking_system.py)

## 7. Qué falta / qué está incompleto

- **`main` del router no tiene el workflow.** Todo vive en la rama `devin/1790824641-chat-agent-plan` (PR #6 abierto, sin fusionar).
- **La copia del router está recortada:** no tiene `wordflow_loop/agent_sources/` (112.202 archivos + 13 submódulos) ni `frontend/` (42.078, incluye Orca 27.324). Exclusión hecha a propósito en b214f9fe96.
- **En la copia del router faltan 119 archivos de `agentes`**: `📂 archivos download/` (74), las 3 capas (`📂 Capa workflow GitHub Action`, `📂 Capa workflow evolución`, `📂 Capa de persistencia open mythos`), `arquitectura/` (24), 3 de 4 archivos de `PLAN-4-OBJETIVOS/` (ver 6.1).
- **En `agentes` faltan 97 archivos que solo existen en el router**: `runtime/tests` (9), `skills_schema/*.dag.yaml` (24+), `wordflow_loop/contracts/seals_motors`, `adapters/seals_motors`, `orchestrator_*`, `runner.py`, `thinking_system.py`, `README-ARQUITECTURA-BACKEND.md` (ver 6.2), más las capas L01–L06 nuevas. No están sincronizadas entre repos.
- **13 componentes MiniMax/Kimi/mcode son submódulos (gitlinks)**: fijan repo+commit pero sus archivos no están materializados en el árbol; requieren `git submodule update --init`. mcode = solo pin npm `@minimax-ai/code@0.4.10`.
- **`📂coda workflow persistencias/🏈 YAIWES 01..24` y `🏈 cancha deportiva de fútbol` (~756 MB)** solo están en `agentes`; no se copiaron al router ni a la copia local.
- **`plan-opus-loop.yml`** solo corre en `agentes`; última corrida 2026-09-21 08:13 COT. No hay workflow equivalente en el router.
- **Rutas históricas sin fuente** (según HANDOFF.md): `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md`, `PIPELINE/FORENSIC_CODE_AUDIT.md`, `PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md` — no existen.
- **Pendientes técnicos declarados en la rama** (03-ESTADO/HANDOFF.md): P1 invocación real adapters O4-07..14, P2 cablear las 4 capabilities descargadas, P3 S-11/S-12, P4 O4-17/O4-20, P5–P7 flags. `/chat/send` no llama a `memoria_yaiwes.save`.
- **Ruta vieja rota:** `chat router/📂 workflow Loops code Yaiwes/` ya no existe en la punta de la rama (se aplanó el 2026-10-08); usar los enlaces fijados al commit 81e6c43eb6 o la nueva raíz `chat router/Workflow Loop code Yaiwes/`.

## 8. Copia local de trabajo

Caja de agentes: `/workspace/workflow-loops-yaiwes/` (`INDEX.md`, `A_agentes_main/`, `B_router_devin_branch/`, `C_router_handoff/`). Sin agent_sources, frontend ni 🏈 YAIWES 01..24.

## Anexo A — Árbol completo con conteos (agentes, 2 niveles)

```text
[D] Crazy Wall Orquestador/  (51)  sha=42dcab8cd8
  [F] AGENT-RECOVERY-HANDOFFS-20260911.md
  [F] ANEXO-01-PLAN-CAPAS-FUENTES-RECOVERY.md
  [F] AUDITORIA-ORQUESTADOR-CHAT-100X-2026-09-16.md
  [F] AUDITORIA-XRAY-CORRECCION-1A1.md
  [F] AUDITORIA-XRAY-PLAN-5-PASADAS.md
  [F] BITACORA-CRAZY-WALL.md
  [F] BITACORA-SWARM-COLLAB-2026-09-16.md
  [F] CHECKPOINT.json
  [F] CODE-CANDIDATE-MANIFEST-PLAN30.md
  [F] DSL-DAG-TAREAS-3-PASOS.yaml
  [F] EVIDENCE-3STEP-STEP1-MOVE-SOURCE-GAP-20260907.md
  [F] EVIDENCE-PLAN30-T10-T15.md
  [F] EVIDENCE-PLAN30-T16-CLOSED.md
  [F] EVIDENCE-PLAN30-T16-PARTIAL.md
  [F] EVIDENCE-PLAN30-T17-DIRECT-CODEROOT-INSPECTION.md
  [F] EVIDENCE-PLAN30-T17-HISTORY-REFUTATION.md
  [F] EVIDENCE-PLAN30-T17-OSQUESTADOR-AUDITOR-PLUGIN-SEMANTICS-REFUTATION.md
  [F] EVIDENCE-PLAN30-T17-OSQUESTADOR-PHYSICAL-TREE-PLUGIN-SEARCH-REFUTATION.md
  [F] EVIDENCE-PLAN30-T17-RESEARCH-REUSE-AUX-REPOS.md
  [F] EVIDENCE-PLAN30-T17-RESEARCH-REUSE-EQUIVALENT-PATTERNS.md
  [F] EVIDENCE-PLAN30-T17-RESEARCH-REUSE-MOTORS.md
  [F] EVIDENCE-PLAN30-T17-RESEARCH-REUSE.md
  [F] EVIDENCE-PLAN30-T17-RUNTIME-CONN-AGENT-REFUTATION.md
  [F] EVIDENCE-PLAN30-T17-RUNTIME-INSTALL-REFUTATION.md
  [F] EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-CHAIN-REFUTATION.md
  [F] EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-CONTRACT-REFUTATION.md
  [F] EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-EMIT-REFUTATION.md
  [F] EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-INIT-REFUTATION.md
  [F] EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-MAIN-REFUTATION.md
  [F] EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-REDUCER-REFUTATION.md
  [F] EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-RUNTIME-REFUTATION.md
  [F] EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-VERIFIER-REFUTATION.md
  [F] GAPS-INVESTIGACION-CODE-GRAPH-20260910.md
  [F] HANDOFF-MOTOR4-MINIMAX-KIMI-2026-09-18.md
  [F] HF-USAGE-SANDBOX-POLICY-20260911.json
  [F] INTEGRACION-SOL1-WORKFLOW-READBACK-20260911-1500.json
  [F] INTEGRACION-SOL1-WORKFLOW-READBACK-20260911-1601.json
  [F] LEDGER-CANONICO-PARTES-1-4.md
  [F] MOTOR-DESCARGA-RECOVERY-CHECKPOINT-2026-09-17.json
  [D] PARCHES-RECUPERACION/  (3)  sha=95debf59e6
  [F] PLAN-LOOP-30-TAREAS.md
  [F] RECOVERY-PATCH.md
  [F] STATE-SWARM-COLLAB-2026-09-16.json
  [F] STATE.json
  [F] SWARM-COLLAB-QUEUE-2026-09-16.json
  [F] SYSTEM-PROMPT-V2-CODE-GRAPH-METHODS-20260911.json
  [F] TAREA-1-SALIDA-1-ARQUITECTURA-CAPAS.md
  [F] TASK-NODES.json
  [F] TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md
[F] GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md
[F] HANDOFF.md
[D] PLAN-4-OBJETIVOS/  (4)  sha=7571b99659
  [F] HANDOFF-PLAN-OPUS.md
  [F] PLAN-ANEXO-C-2-PUNTOS-ADICIONALES.md
  [F] PLAN-MAESTRO-4-OBJETIVOS.md
  [F] PROMPT-DSL-DAG-PLAN-OPUS.yaml
[F] PLAN-PROGRAMACION-11-OBJETIVOS-Y-AGENTES.md
[D] arquitectura/  (24)  sha=a42d4ea383
  [F] Anexo - GAPS y mejoras pendientes.md
  [F] Anexo 2 - Pendientes nuevos y cobertura 100.md
  [F] Anexo 3 - Estado real documentos Claude.md
  [F] Anexo 4 - Docfile y MCP y ambiguedades.md
  [F] Anexo 5 - Correccion gobernanza es real.md
  [F] CONFIRMACION-4x-biblioteca.md
  [F] CONTRATO-skill-design-anthropic-frontend.md
  [F] DISENO-MCP-contexto-compartido.md
  [F] DISENO-preguntas-siempre-activo-input-shark.md
  [F] HANDOFF-actualizado-por-Claude.md
  [F] PROMPT-Sol-descarga-4-componentes-nuevos.md
  [F] PROMPT-Sol-investigar-capacidad-frontend-fleet.md
  [F] Parte 1 - Estructura completa runtime src.md
  [F] Parte 2 - Fase INTAKE y DAG.md
  [F] Parte 3 - Fase EXECUTION y GOVERNANCE CHAIN.md
  [F] Parte 4 - Fase RECOVERY y LEDGER.md
  [F] Parte 5 - UEK y Agent Fleet.md
  [F] RESOLUCION-3-pendientes.md
  [F] SCHEMA-frontend-browser-verified.md
  [F] SCHEMA-plantillas-RAG.md
  [F] SCHEMA-refactorizacion.md
  [F] SEALS-TEAM-YAIWES-GRUPO-1-radiografia-kernel.md
  [F] arquitectura wordflow loop code Yaiwes.md
  [F] test.md
[D] backend/  (66)  sha=504d10550f
  [D] Comand Center/  (5)  sha=b24db8a353
  [D] Seals team YAIWES/  (61)  sha=ad0e9425a5
    [D] Seals team 1 YAIWES/  (1)  sha=36c580e583
    [D] _fuentes_extraidas/  (18)  sha=1dd75a7463
    [D] seals_core/  (36)  sha=acd993a9b1
[D] frontend/  (42078)  sha=3fa5933cb3
  [F] .cbmignore
  [F] .dockerignore
  [F] .editorconfig
  [F] .env.devin-bridge.example
  [F] .env.example
  [F] .env.homolog.example
  [F] .gitattributes
  [D] .github/  (36)  sha=f84d779abe
    [D] ISSUE_TEMPLATE/  (4)  sha=1967344a16
    [D] actions/  (1)  sha=0e8b79e433
    [D] workflows/  (26)  sha=f142f69ffc
  [F] .gitignore
  [F] .gitleaks.toml
  [D] .husky/  (2)  sha=afd1b91ec2
  [F] .i18n-state.json
  [F] .mailmap
  [F] .markdownlint.json
  [F] .mergify.yml
  [F] .node-version
  [F] .npmignore
  [F] .npmrc
  [F] .nvmrc
  [F] .prettierignore
  [F] .size-limit.json
  [F] .trivyignore
  [F] .vale.ini
  [D] .vale/  (1)  sha=0c1a1a77fe
    [D] styles/  (1)  sha=32516a27d4
  [D] .vscode/  (1)  sha=86de537789
  [F] .zizmor.yml
  [D] @omniroute/  (117)  sha=003b1f9588
    [D] opencode-plugin-v2/  (68)  sha=9c6ed6cae8
    [D] opencode-plugin/  (39)  sha=66a1a3c20f
    [D] opencode-provider/  (10)  sha=1a42c51dd1
  [F] AGENTS.md
  [D] AgentSkills/  (22)  sha=eb0273dc48
    [D] skills-ref/  (16)  sha=dc2d22177c
  [F] CHANGELOG.md
  [F] CLAUDE.md
  [F] CODE_OF_CONDUCT.md
  [F] CONTRIBUTING.md
  [F] Dockerfile
  [F] Dockerfile.bun
  [F] GEMINI.md
  [F] LICENSE
  [F] Makefile
  [D] Orca/  (27324)  sha=4a70b11989
    [D] .github/  (93)  sha=d753d180c0
    [D] .husky/  (1)  sha=03dd72c093
    [D] Casks/  (2)  sha=d7fa51a3df
    [D] cloud/  (489)  sha=f2cd90898b
    [D] config/  (620)  sha=48a357b34c
    [D] docs/  (190)  sha=0ce9c7e967
    [D] examples/  (5)  sha=c1c3bf115d
    [D] mobile/  (2774)  sha=4b55a88cb5
    [D] native/  (40)  sha=40469861ed
    [D] resources/  (83)  sha=1867e68ec6
    [D] skill-guides/  (23)  sha=1cc00651ed
    [D] skill-stubs/  (9)  sha=f2ca219ee6
    [D] skills/  (8)  sha=1fd203b8e6
    [D] src/  (22170)  sha=68c881230f
    [D] tests/  (801)  sha=fea3d976ce
  [D] PonytailPlugin/  (101)  sha=e918392135
    [D] .agents/  (2)  sha=6a96ff3587
    [D] .claude-plugin/  (2)  sha=a6e9935aeb
    [D] .clinerules/  (1)  sha=74f838ff68
    [D] .codex-plugin/  (1)  sha=04f85cb3ad
    [D] .cursor/  (1)  sha=8f2b9b8758
    [D] .devin-plugin/  (1)  sha=8552dadcf9
    [D] .github/  (1)  sha=e94607bf45
    [D] .grok-plugin/  (1)  sha=26f0e85f07
    [D] .kiro/  (1)  sha=4e5962ab54
    [D] .openclaw/  (6)  sha=0fdc3b7c76
    [D] .opencode/  (8)  sha=dd32fdc567
    [D] .qoder-plugin/  (1)  sha=796417dae8
    [D] .qoder/  (1)  sha=9cd131bd3c
    [D] .windsurf/  (1)  sha=9cd131bd3c
    [D] benchmarks/  (4)  sha=f11caab427
    [D] commands/  (6)  sha=e65ef47b1b
    [D] hooks/  (12)  sha=f41de4edb4
    [D] pi-extension/  (4)  sha=51ba290a3c
    [D] ponytail-mcp/  (5)  sha=054e9a7419
    [D] scripts/  (6)  sha=23b1c0d1d0
    [D] skills/  (6)  sha=d15d0642ce
    [D] tests/  (16)  sha=6e1bc153b2
  [F] README.md
  [F] ROADMAP.md
  [F] SECURITY.md
  [F] THIRD_PARTY_NOTICES.md
  [D] bin/  (281)  sha=e3f56f5639
    [D] cli/  (267)  sha=4826b9b8b8
  [D] changelog.d/  (210)  sha=55c6fc7024
    [D] features/  (19)  sha=ba1508b96b
    [D] fixes/  (173)  sha=adab2c73fa
    [D] maintenance/  (17)  sha=e010682917
  [F] codecov.yml
  [D] config/  (27)  sha=c6f6b4c345
    [D] quality/  (19)  sha=62725b1763
    [D] release/  (4)  sha=4f5057d2ea
  [D] contrib/  (9)  sha=20aee88908
    [D] podman/  (6)  sha=d24da37471
    [D] vps/  (3)  sha=eeb17730ad
  [F] docker-compose.prod.yml
  [F] docker-compose.yml
  [D] docker/  (15)  sha=85884d88d9
    [D] chatgpt-web-codex-browser/  (2)  sha=4425ffc197
    [D] devin-bridge/  (8)  sha=9f4618fd26
    [D] vnc-browser/  (5)  sha=d1e5194d9b
  [D] docs/  (2063)  sha=d09f4121a7
    [D] architecture/  (14)  sha=78730b1627
    [D] assets/  (58)  sha=fe43111a85
    [D] changelog/  (2)  sha=bf68534039
    [D] comparison/  (2)  sha=4f7da4c41a
    [D] compression/  (8)  sha=120b5cbd48
    [D] diagrams/  (31)  sha=449ff388ff
    [D] frameworks/  (27)  sha=d06ca519d4
    [D] getting-started/  (6)  sha=527566c44e
    [D] guides/  (27)  sha=183c6f8dcd
    [D] i18n/  (1796)  sha=b6b86fc838
    [D] ops/  (19)  sha=1fb7db5ce3
    [D] plans/  (2)  sha=7c91a60c18
    [D] providers/  (11)  sha=20adaac73e
    [D] reference/  (13)  sha=a3a02aca8f
    [D] routing/  (8)  sha=692272387d
    [D] screenshots/  (15)  sha=af495947af
    [D] security/  (15)  sha=87ad88f7a5
  [D] electron/  (24)  sha=c5dfae7bcc
    [D] assets/  (5)  sha=062640e161
    [D] lib/  (8)  sha=402b40c926
  [F] eslint.complexity-ratchets.config.mjs
  [F] eslint.complexity.config.mjs
  [F] eslint.config.mjs
  [F] eslint.sonarjs.config.mjs
  [D] examples/  (15)  sha=c410fd7251
    [D] omniroute-cmd-hello/  (1)  sha=44b3708dd8
    [D] plugins/  (9)  sha=3fd922d80e
    [D] quickstart/  (5)  sha=f4dc1def44
  [F] flake.lock
  [F] flake.nix
  [F] fly.toml
  [D] images/  (1)  sha=ce8af470fa
  [F] knip.json
  [F] llm.txt
  [F] news.json
  [F] next.config.mjs
  [D] open-sse/  (1740)  sha=f7b7053e54
    [D] config/  (353)  sha=9dab15d9bd
    [D] executors/  (201)  sha=d0b89ffdb8
    [D] handlers/  (177)  sha=95d0e0f4ab
    [D] lib/  (3)  sha=04adcc6965
    [D] mcp-server/  (63)  sha=1d5d5251b8
    [D] services/  (691)  sha=6c44800d2a
    [D] shared/  (1)  sha=1135013aba
    [D] transformer/  (1)  sha=bdc1e26097
    [D] translator/  (62)  sha=9d40099770
    [D] utils/  (138)  sha=f78c66e156
    [D] vendor/  (46)  sha=bfac333962
  [F] package-lock.json
  [F] package.json
  [D] packages/  (7)  sha=c2d9940ac1
    [D] browser-pool/  (7)  sha=2aeda79309
  [F] playwright.config.ts
  [F] pnpm-workspace.yaml
  [F] pnpm.json
  [F] postcss.config.mjs
  [F] prettier.config.mjs
  [F] promptfooconfig.yaml
  [D] public/  (152)  sha=947ffced2f
    [D] images/  (2)  sha=eda84f6e6a
    [D] providers/  (141)  sha=581a48f8b2
    [D] sponsors/  (1)  sha=1ff0b59ef0
  [D] scripts/  (319)  sha=fdc7ca21df
    [D] ad-hoc/  (20)  sha=215a9e1259
    [D] build/  (38)  sha=420802f1ba
    [D] check/  (88)  sha=c37af55468
    [D] ci/  (2)  sha=bd5917881e
    [D] cli/  (1)  sha=0a6d53dcfc
    [D] compression-eval/  (1)  sha=630f7fd298
    [D] compression/  (1)  sha=4aa2722bdd
    [D] dev/  (26)  sha=ba361c37d6
    [D] devin-bridge/  (13)  sha=39dd336fc9
    [D] docker/  (3)  sha=b6757eb76a
    [D] docs/  (7)  sha=6bd2fa0293
    [D] features/  (8)  sha=4dd58ec657
    [D] homolog/  (7)  sha=a0c92d9821
    [D] i18n/  (42)  sha=d0f9c49b53
    [D] ops/  (8)  sha=fdcf780547
    [D] packs/  (2)  sha=96fc745c70
    [D] perf/  (7)  sha=ac766aaf68
    [D] quality/  (16)  sha=a7af22c6ce
    [D] release/  (12)  sha=e7b5ae237d
    [D] research/  (1)  sha=1d60798fc4
    [D] router-eval/  (5)  sha=e82e957005
    [D] skills/  (1)  sha=84150fc0ea
    [D] sre/  (3)  sha=e12f543a42
    [D] test/  (2)  sha=8f605fa4f9
    [D] vps/  (2)  sha=01b243a331
  [D] skills/  (50)  sha=2fecc68c44
    [D] cli-a2a/  (1)  sha=af1aa9f3bc
    [D] cli-backup-sync/  (1)  sha=26f55d00d8
    [D] cli-batches/  (1)  sha=ab39aa3e83
    [D] cli-chat/  (1)  sha=50cd3aefb3
    [D] cli-compression/  (1)  sha=41da34b2a7
    [D] cli-contexts/  (1)  sha=aa7a020e34
    [D] cli-cost-usage/  (1)  sha=fa0e87e417
    [D] cli-eval/  (1)  sha=4cb01047fd
    [D] cli-health/  (1)  sha=a38a3dea2e
    [D] cli-keys/  (1)  sha=97571c8c6d
    [D] cli-mcp/  (1)  sha=402d2a90cf
    [D] cli-models/  (1)  sha=11cac87869
    [D] cli-plugins-skills/  (1)  sha=78661780d8
    [D] cli-policy-audit/  (1)  sha=628f73a4a5
    [D] cli-providers/  (1)  sha=9925635ac6
    [D] cli-resilience/  (1)  sha=16b8299c18
    [D] cli-routing/  (1)  sha=3ae8fdbc90
    [D] cli-serve/  (1)  sha=ef7fb3aa2e
    [D] cli-setup/  (1)  sha=93e0fb4281
    [D] cli-skill-collector/  (1)  sha=664d2b8f40
    [D] cli-tunnel/  (1)  sha=b9a68e500a
    [D] config-codex-cli/  (1)  sha=0dd7d42590
    [D] frontend-design/  (1)  sha=28af03c1c2
    [D] impeccable/  (1)  sha=4a68d3b4a9
    [D] omni-agents-a2a/  (1)  sha=435f1d17d1
    [D] omni-api-keys/  (1)  sha=ef65e182cc
    [D] omni-auth/  (1)  sha=de3b2d7fe4
    [D] omni-budget/  (1)  sha=1d186f974b
    [D] omni-cache/  (1)  sha=1b04116666
    [D] omni-cli-tools/  (1)  sha=11628156d7
    [D] omni-combos-routing/  (1)  sha=e13c1c33b2
    [D] omni-compression/  (1)  sha=0d15f542fb
    [D] omni-context-rtk/  (1)  sha=3dcfe8429c
    [D] omni-db-backups/  (1)  sha=38bc11a697
    [D] omni-github-skills/  (1)  sha=570743ea6c
    [D] omni-inference/  (1)  sha=3cdc16776a
    [D] omni-mcp/  (1)  sha=749017fd25
    [D] omni-models/  (1)  sha=0239ecac2f
    [D] omni-providers/  (1)  sha=4449db9718
    [D] omni-proxies/  (1)  sha=d27b89e568
    [D] omni-resilience/  (1)  sha=8f39e49106
    [D] omni-settings/  (1)  sha=9cd78eee83
    [D] omni-sync-cloud/  (1)  sha=56f8cf0a6b
    [D] omni-tunnels/  (1)  sha=835830e7ec
    [D] omni-usage-logs/  (1)  sha=d059cee585
    [D] omni-version-manager/  (1)  sha=86ca9d4508
    [D] omni-webhooks/  (1)  sha=70365ea615
    [D] ponytail/  (1)  sha=0be32208e7
    [D] skill-creator/  (1)  sha=6e9bbf62c0
  [F] socket.yml
  [F] sonar-project.properties
  [F] source.config.ts
  [D] src/  (3417)  sha=6cb993298b
    [D] app/  (1691)  sha=04478a9497
    [D] domain/  (23)  sha=d469517885
    [D] hooks/  (4)  sha=55f4162452
    [D] i18n/  (70)  sha=23a760bc25
    [D] lib/  (1070)  sha=409bc59ed5
    [D] middleware/  (1)  sha=85d2b1ada9
    [D] mitm/  (85)  sha=219716af9b
    [D] models/  (1)  sha=914a700ef2
    [D] scripts/  (1)  sha=d5ec1d5f60
    [D] server/  (21)  sha=89494cc3d4
    [D] shared/  (394)  sha=1e80f17e91
    [D] sse/  (42)  sha=af1e4d4b80
    [D] store/  (5)  sha=a1e1d8bc98
    [D] types/  (6)  sha=707b82cbd3
  [F] stryker.conf.json
  [F] stryker.disablebail.json
  [F] task-c1-report.md
  [F] task-c2-report.md
  [F] task-c3-report.md
  [D] tests/  (6070)  sha=492007874e
    [D] _helpers/  (1)  sha=ebbfc3332c
    [D] _setup/  (4)  sha=0594fd343a
    [D] benchmarks/  (1)  sha=6d449c47d6
    [D] boundary/  (5)  sha=ea4a60a685
    [D] e2e/  (43)  sha=4bfccd251a
    [D] fixtures/  (38)  sha=7d34024d9b
    [D] golden-set/  (5)  sha=9fa91b3b6b
    [D] helpers/  (7)  sha=00e0325952
    [D] homolog/  (5)  sha=6086b3e593
    [D] integration/  (142)  sha=016f2f17c5
    [D] live/  (1)  sha=93244c5557
    [D] llm-security/  (1)  sha=e6a218b3f4
    [D] load/  (2)  sha=690bc0e171
    [D] manual/  (7)  sha=c904873c2a
    [D] security/  (4)  sha=a73477354e
    [D] snapshots/  (14)  sha=f077ff230a
    [D] translator/  (1)  sha=0ddfec9255
    [D] unit/  (5785)  sha=3e70d87df3
  [F] tsconfig.json
  [F] tsconfig.typecheck-api.json
  [F] tsconfig.typecheck-core.json
  [F] tsconfig.typecheck-dashboard.json
  [F] tsconfig.typecheck-noimplicit-core.json
  [F] vitest.config.ts
  [F] vitest.e2e-live.config.ts
  [F] vitest.mcp.config.ts
[D] minimax_mcp/  (6)  sha=beda89ecf9
  [F] .env.example
  [D] .github/  (4)  sha=fde9b41390
    [D] ISSUE_TEMPLATE/  (4)  sha=7463098425
  [F] .gitignore
[D] runtime/  (123)  sha=deb6542fa4
  [D] docs/  (5)  sha=647f72ff5e
  [F] plugin-manifest.yaml
  [D] schemas/  (3)  sha=2341957c9b
  [D] src/  (70)  sha=0444cee1e4
    [D] agent/  (1)  sha=6f0ab85f9d
    [D] conn/  (4)  sha=d454e3d9fa
    [D] core/  (38)  sha=2e4d0a2a2b
    [D] governance/  (1)  sha=4aa2d2c66e
    [D] install/  (3)  sha=d263c53cf8
    [D] mission/  (1)  sha=d7a4280f0a
    [D] observability/  (1)  sha=3013e3eb1b
    [D] parallel/  (1)  sha=b6be374cef
    [D] preflight/  (1)  sha=7b42b8fa8b
    [D] recovery/  (5)  sha=ecdb14125a
    [D] research/  (1)  sha=28ba81de7e
    [D] spec/  (1)  sha=c5f28befd1
    [D] storage/  (1)  sha=dc777f63d5
    [D] tribunal/  (5)  sha=c06dae61f7
    [D] uek/  (6)  sha=1e4818aa44
  [D] tests/  (44)  sha=0b5992410d
[D] wordflow_loop/  (112329)  sha=5a80a8ea46
  [F] README.md
  [D] adapters/  (2)  sha=4298ed7de7
  [D] agent_sources/  (112202)  sha=a219e5939c
    [D] agent_zero/  (2965)  sha=3f64907b95
    [D] aider/  (695)  sha=f83ceb02bf
    [D] claude_code/  (230)  sha=8bc6f609eb
    [D] cline/  (3860)  sha=42e6fb4827
    [D] codex/  (6747)  sha=52ef893c73
    [D] cua_mcp/  (9)  sha=2abc20acd6
    [D] goose/  (2464)  sha=431d370b9e
    [D] hermes/  (13018)  sha=b2b3aef161
    [commit] kimi_agent_rs
    [commit] kimi_agent_sdk
    [commit] kimi_cli
    [commit] kimi_code
    [D] kimi_k/  (6)  sha=851f463176
    [commit] kimi_researcher
    [commit] mcode
    [D] meta_agent_cookbook/  (525)  sha=089a327e62
    [D] meta_muse_code_sdk/  (224)  sha=e3042c4a28
    [D] metacua/  (76)  sha=bfbd3e505b
    [D] mimo_code/  (9)  sha=34a67bc81f
    [commit] minimax_code_plugins
    [commit] minimax_coding_plan_mcp
    [commit] minimax_mcp
    [commit] minimax_mcp_js
    [commit] minimax_mini_agent
    [commit] minimax_mmx_cli
    [commit] minimax_openroom
    [D] mirothinker/  (187)  sha=f50ef918ce
    [D] muse_glimmer/  (42)  sha=a3cd2b19a6
    [D] openclaw/  (43020)  sha=313e224abc
    [D] opencode/  (6600)  sha=3e72d587a4
    [D] opendev/  (1183)  sha=bd69117aeb
    [D] openhands/  (2174)  sha=5598f214c8
    [D] orca/  (27324)  sha=4a70b11989
    [D] qwen_code/  (342)  sha=7c86e0151a
    [D] research_agent_lab/  (314)  sha=6ac3adf5f3
    [D] smolagents/  (184)  sha=da0b725f55
  [D] code_graph/  (1)  sha=b3947b5f64
  [D] contracts/  (8)  sha=def2fc9509
  [D] evidence/  (67)  sha=0d7bc6a16c
    [D] agent-source-copy-state/  (18)  sha=a7192a58c5
  [D] intake/  (1)  sha=7563f750d5
  [D] plugins/  (2)  sha=17590ce331
  [D] prompts/  (3)  sha=bc80dbaaa5
  [F] pyproject.toml
  [D] research/  (2)  sha=eb00150676
  [D] skills/  (1)  sha=965ffa00e4
  [D] templates/  (1)  sha=48c652105f
  [D] wordflow_loop/  (36)  sha=b13069709c
    [D] agent_fleet/  (23)  sha=cdf3ef74d5
    [D] governance/  (8)  sha=8f7b31b611
  [D] workflows/  (1)  sha=c7a89e13c6
[D] workspace/  (6)  sha=e9cb662300
  [F] README.md
  [D] code/  (1)  sha=f8bb6b95f2
  [D] memory/  (1)  sha=af5fba78b8
    [D] agents/  (1)  sha=62c707d3b3
  [D] profiles/  (3)  sha=dd71d7a057
[F] ➡️📂 README arquitectura Wordflow LOOP Yaiwes.md
[F] ➡️📂 readme indice agentes.md
[F] ➡️📂 readme wordflow loop Yaiwes.md
[D] ➡️📂motores de descarga extracción copiado movimiento archivos agentes/  (7)  sha=4951574898
  [D] ➡️📂 Motor de extracción zip/  (1)  sha=00b3d23f47
  [F] ➡️📂 skills descargar extraer zip copiar mover archivos readme.md
  [D] ➡️📂motor de copiar archivos/  (2)  sha=db8ef7064e
  [D] ➡️📂motor de moves archivos/  (1)  sha=f3c115edf3
  [D] 📂Motor descarga de componentes y extracción de zip/  (2)  sha=c52e87183c
[D] 📂 Capa de persistencia open mythos/  (2)  sha=99d51adb61
  [F] README.md
  [F] open_mythos_persistence_loop.py
[D] 📂 Capa workflow GitHub Action/  (5)  sha=76d79758c8
  [F] ADVERTENCIA-CODE.json
  [F] FORENSIC-PASS-research-download-chain-final.yml
  [F] FORENSIC-PASS-research_download_chain.py
  [F] gha-download-extract.yml
  [F] research_download_chain.py
[D] 📂 Capa workflow evolución/  (4)  sha=cf029c82e8
  [F] README.md
  [F] evolution_contract.schema.json
  [F] evolution_dag.yaml
  [F] evolution_engine.py
[D] 📂 archivos download/  (74)  sha=7006b93e9c
  [D] 📂 LOOP open source 5/  (2)  sha=2038965a82
  [D] 📂Archivo download 1/  (49)  sha=a1e02ac463
  [D] 📂Archivo download 10/  (1)  sha=3aa9f4c439
  [D] 📂Archivo download 2/  (15)  sha=1cee9461d4
  [D] 📂Archivo download 3/  (1)  sha=0635a4b000
  [D] 📂Archivo download 4/  (1)  sha=a5756f1ef3
  [D] 📂Archivo download 5/  (1)  sha=88633c663c
  [D] 📂Archivo download 6/  (1)  sha=db022fbca2
  [D] 📂Archivo download 7/  (1)  sha=55af328a68
  [D] 📂Archivo download 8/  (1)  sha=57d3cd6dd6
  [D] 📂Archivo download 9/  (1)  sha=8c0c905e8c
[D] 📂 notas auditoría Claude/  (11)  sha=d07582fe8b
  [F] ✅ 01_hoja_de_ruta_fundamentos_limpieza — NOTA XRAY.md
  [F] ✅ 02_hoja_de_ruta_razonamiento_gobernanza — NOTA XRAY.md
  [F] ✅ 03_hoja_de_ruta_workflows_pool_memoria — NOTA XRAY.md
  [F] ✅ 04_hoja_de_ruta_observabilidad_cierre — NOTA XRAY.md
  [F] ✅ 05_arquitectura_completa_fables — NOTA XRAY.md
  [F] ✅ 06_componentes_open_source_investigados — NOTA XRAY.md
  [F] ✅ 07_hoja_de_ruta_loops_multiapi_memoria_chat — NOTA XRAY.md
  [F] ✅ 08_protocolo_cierre_kernel_simple — NOTA XRAY.md
  [F] ✅ 09_guia_decision_integrar_codigo_kernel — NOTA XRAY.md
  [F] ✅ 10_plantilla_modulos_razonamiento — NOTA XRAY.md
  [F] ✅ 11_catalogo_105_algoritmos_deterministas — NOTA XRAY.md
TOTAL 154796
```

## Anexo B — 397 rutas comunes (agentes ↔ router 81e6c43eb6)

<details><summary>ver lista</summary>

- [`Crazy Wall Orquestador/AGENT-RECOVERY-HANDOFFS-20260911.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/AGENT-RECOVERY-HANDOFFS-20260911.md)
- [`Crazy Wall Orquestador/ANEXO-01-PLAN-CAPAS-FUENTES-RECOVERY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/ANEXO-01-PLAN-CAPAS-FUENTES-RECOVERY.md)
- [`Crazy Wall Orquestador/AUDITORIA-ORQUESTADOR-CHAT-100X-2026-09-16.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/AUDITORIA-ORQUESTADOR-CHAT-100X-2026-09-16.md)
- [`Crazy Wall Orquestador/AUDITORIA-XRAY-CORRECCION-1A1.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/AUDITORIA-XRAY-CORRECCION-1A1.md)
- [`Crazy Wall Orquestador/AUDITORIA-XRAY-PLAN-5-PASADAS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/AUDITORIA-XRAY-PLAN-5-PASADAS.md)
- [`Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/BITACORA-CRAZY-WALL.md)
- [`Crazy Wall Orquestador/BITACORA-SWARM-COLLAB-2026-09-16.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/BITACORA-SWARM-COLLAB-2026-09-16.md)
- [`Crazy Wall Orquestador/CHECKPOINT.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/CHECKPOINT.json)
- [`Crazy Wall Orquestador/CODE-CANDIDATE-MANIFEST-PLAN30.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/CODE-CANDIDATE-MANIFEST-PLAN30.md)
- [`Crazy Wall Orquestador/DSL-DAG-TAREAS-3-PASOS.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/DSL-DAG-TAREAS-3-PASOS.yaml)
- [`Crazy Wall Orquestador/EVIDENCE-3STEP-STEP1-MOVE-SOURCE-GAP-20260907.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-3STEP-STEP1-MOVE-SOURCE-GAP-20260907.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T10-T15.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T10-T15.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T16-CLOSED.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T16-CLOSED.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T16-PARTIAL.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T16-PARTIAL.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-DIRECT-CODEROOT-INSPECTION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-DIRECT-CODEROOT-INSPECTION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-HISTORY-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-HISTORY-REFUTATION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-OSQUESTADOR-AUDITOR-PLUGIN-SEMANTICS-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-OSQUESTADOR-AUDITOR-PLUGIN-SEMANTICS-REFUTATION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-OSQUESTADOR-PHYSICAL-TREE-PLUGIN-SEARCH-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-OSQUESTADOR-PHYSICAL-TREE-PLUGIN-SEARCH-REFUTATION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-RESEARCH-REUSE-AUX-REPOS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-RESEARCH-REUSE-AUX-REPOS.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-RESEARCH-REUSE-EQUIVALENT-PATTERNS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-RESEARCH-REUSE-EQUIVALENT-PATTERNS.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-RESEARCH-REUSE-MOTORS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-RESEARCH-REUSE-MOTORS.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-RESEARCH-REUSE.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-RESEARCH-REUSE.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-RUNTIME-CONN-AGENT-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-RUNTIME-CONN-AGENT-REFUTATION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-RUNTIME-INSTALL-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-RUNTIME-INSTALL-REFUTATION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-CHAIN-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-CHAIN-REFUTATION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-CONTRACT-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-CONTRACT-REFUTATION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-EMIT-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-EMIT-REFUTATION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-INIT-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-INIT-REFUTATION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-MAIN-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-MAIN-REFUTATION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-REDUCER-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-REDUCER-REFUTATION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-RUNTIME-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-RUNTIME-REFUTATION.md)
- [`Crazy Wall Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-VERIFIER-REFUTATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/EVIDENCE-PLAN30-T17-TRACEABILITY-LOOP-ENGINEER-VERIFIER-REFUTATION.md)
- [`Crazy Wall Orquestador/GAPS-INVESTIGACION-CODE-GRAPH-20260910.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/GAPS-INVESTIGACION-CODE-GRAPH-20260910.md)
- [`Crazy Wall Orquestador/HANDOFF-MOTOR4-MINIMAX-KIMI-2026-09-18.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/HANDOFF-MOTOR4-MINIMAX-KIMI-2026-09-18.md)
- [`Crazy Wall Orquestador/HF-USAGE-SANDBOX-POLICY-20260911.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/HF-USAGE-SANDBOX-POLICY-20260911.json)
- [`Crazy Wall Orquestador/INTEGRACION-SOL1-WORKFLOW-READBACK-20260911-1500.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/INTEGRACION-SOL1-WORKFLOW-READBACK-20260911-1500.json)
- [`Crazy Wall Orquestador/INTEGRACION-SOL1-WORKFLOW-READBACK-20260911-1601.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/INTEGRACION-SOL1-WORKFLOW-READBACK-20260911-1601.json)
- [`Crazy Wall Orquestador/LEDGER-CANONICO-PARTES-1-4.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/LEDGER-CANONICO-PARTES-1-4.md)
- [`Crazy Wall Orquestador/MOTOR-DESCARGA-RECOVERY-CHECKPOINT-2026-09-17.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/MOTOR-DESCARGA-RECOVERY-CHECKPOINT-2026-09-17.json)
- [`Crazy Wall Orquestador/PARCHES-RECUPERACION/PARCHE-ASTRA-GPT-LOOP.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/PARCHES-RECUPERACION/PARCHE-ASTRA-GPT-LOOP.md)
- [`Crazy Wall Orquestador/PARCHES-RECUPERACION/PARCHE-SOL-1-LOOP.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/PARCHES-RECUPERACION/PARCHE-SOL-1-LOOP.md)
- [`Crazy Wall Orquestador/PARCHES-RECUPERACION/PARCHE-SOL-2-LOOP.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/PARCHES-RECUPERACION/PARCHE-SOL-2-LOOP.md)
- [`Crazy Wall Orquestador/PLAN-LOOP-30-TAREAS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/PLAN-LOOP-30-TAREAS.md)
- [`Crazy Wall Orquestador/RECOVERY-PATCH.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/RECOVERY-PATCH.md)
- [`Crazy Wall Orquestador/STATE-SWARM-COLLAB-2026-09-16.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/STATE-SWARM-COLLAB-2026-09-16.json)
- [`Crazy Wall Orquestador/STATE.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/STATE.json)
- [`Crazy Wall Orquestador/SWARM-COLLAB-QUEUE-2026-09-16.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/SWARM-COLLAB-QUEUE-2026-09-16.json)
- [`Crazy Wall Orquestador/SYSTEM-PROMPT-V2-CODE-GRAPH-METHODS-20260911.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/SYSTEM-PROMPT-V2-CODE-GRAPH-METHODS-20260911.json)
- [`Crazy Wall Orquestador/TAREA-1-SALIDA-1-ARQUITECTURA-CAPAS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/TAREA-1-SALIDA-1-ARQUITECTURA-CAPAS.md)
- [`Crazy Wall Orquestador/TASK-NODES.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/TASK-NODES.json)
- [`Crazy Wall Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/Crazy%20Wall%20Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md)
- [`GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md)
- [`HANDOFF.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/HANDOFF.md)
- [`PLAN-4-OBJETIVOS/PLAN-MAESTRO-4-OBJETIVOS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/PLAN-4-OBJETIVOS/PLAN-MAESTRO-4-OBJETIVOS.md)
- [`PLAN-PROGRAMACION-11-OBJETIVOS-Y-AGENTES.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/PLAN-PROGRAMACION-11-OBJETIVOS-Y-AGENTES.md)
- [`backend/Comand Center/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Comand%20Center/README.md)
- [`backend/Comand Center/comandante_tactico_seal.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Comand%20Center/comandante_tactico_seal.py)
- [`backend/Comand Center/config_disparo.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Comand%20Center/config_disparo.json)
- [`backend/Comand Center/idempotencia.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Comand%20Center/idempotencia.py)
- [`backend/Comand Center/webhook_listener.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Comand%20Center/webhook_listener.py)
- [`backend/Seals team YAIWES/Handoff seals team.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/Handoff%20seals%20team.md)
- [`backend/Seals team YAIWES/PROMPT-Sol-requirements-lock.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/PROMPT-Sol-requirements-lock.md)
- [`backend/Seals team YAIWES/Seals team 1 YAIWES/task_contract.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/Seals%20team%201%20YAIWES/task_contract.json)
- [`backend/Seals team YAIWES/Seals team.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/Seals%20team.md)
- [`backend/Seals team YAIWES/_fuentes_extraidas/EXTRACTION_EVIDENCE_MUSE.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/EXTRACTION_EVIDENCE_MUSE.json)
- [`backend/Seals team YAIWES/_fuentes_extraidas/MUSE-KnowledgeXLab/SOURCE_COMMIT.txt`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/MUSE-KnowledgeXLab/SOURCE_COMMIT.txt)
- [`backend/Seals team YAIWES/_fuentes_extraidas/MUSE-KnowledgeXLab/SOURCE_URL.txt`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/MUSE-KnowledgeXLab/SOURCE_URL.txt)
- [`backend/Seals team YAIWES/_fuentes_extraidas/MUSE-KnowledgeXLab/agent.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/MUSE-KnowledgeXLab/agent.py)
- [`backend/Seals team YAIWES/_fuentes_extraidas/MUSE-KnowledgeXLab/memory_manager.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/MUSE-KnowledgeXLab/memory_manager.py)
- [`backend/Seals team YAIWES/_fuentes_extraidas/MUSE-KnowledgeXLab/monitor.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/MUSE-KnowledgeXLab/monitor.py)
- [`backend/Seals team YAIWES/_fuentes_extraidas/Meta-Agent-Cookbook-2026/04_muse_code/07_goal_tracking/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/Meta-Agent-Cookbook-2026/04_muse_code/07_goal_tracking/README.md)
- [`backend/Seals team YAIWES/_fuentes_extraidas/Meta-Agent-Cookbook-2026/04_muse_code/09_loop_and_cron/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/Meta-Agent-Cookbook-2026/04_muse_code/09_loop_and_cron/README.md)
- [`backend/Seals team YAIWES/_fuentes_extraidas/Meta-Agent-Cookbook-2026/SOURCE_COMMIT.txt`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/Meta-Agent-Cookbook-2026/SOURCE_COMMIT.txt)
- [`backend/Seals team YAIWES/_fuentes_extraidas/Meta-Agent-Cookbook-2026/SOURCE_URL.txt`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/Meta-Agent-Cookbook-2026/SOURCE_URL.txt)
- [`backend/Seals team YAIWES/_fuentes_extraidas/Meta-Muse-Code-SDK-2026/SOURCE_COMMIT.txt`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/Meta-Muse-Code-SDK-2026/SOURCE_COMMIT.txt)
- [`backend/Seals team YAIWES/_fuentes_extraidas/Meta-Muse-Code-SDK-2026/SOURCE_URL.txt`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/Meta-Muse-Code-SDK-2026/SOURCE_URL.txt)
- [`backend/Seals team YAIWES/_fuentes_extraidas/Meta-Muse-Code-SDK-2026/clients/sdk-cookbook/src/recipes/queue-steer-reclaim.ts`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/Meta-Muse-Code-SDK-2026/clients/sdk-cookbook/src/recipes/queue-steer-reclaim.ts)
- [`backend/Seals team YAIWES/_fuentes_extraidas/Meta-Muse-Code-SDK-2026/clients/sdk-cookbook/src/recipes/retry-without-double-submitting.ts`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/Meta-Muse-Code-SDK-2026/clients/sdk-cookbook/src/recipes/retry-without-double-submitting.ts)
- [`backend/Seals team YAIWES/_fuentes_extraidas/Muse-Agent/SOURCE_COMMIT.txt`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/Muse-Agent/SOURCE_COMMIT.txt)
- [`backend/Seals team YAIWES/_fuentes_extraidas/Muse-Agent/SOURCE_URL.txt`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/Muse-Agent/SOURCE_URL.txt)
- [`backend/Seals team YAIWES/_fuentes_extraidas/Muse-Agent/packages/agent-core/src/checkpoint.ts`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/Muse-Agent/packages/agent-core/src/checkpoint.ts)
- [`backend/Seals team YAIWES/_fuentes_extraidas/Muse-Agent/packages/agent-core/src/plan-execute-loop.ts`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/_fuentes_extraidas/Muse-Agent/packages/agent-core/src/plan-execute-loop.ts)
- [`backend/Seals team YAIWES/dag_schema.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/dag_schema.yaml)
- [`backend/Seals team YAIWES/requirements.txt`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/requirements.txt)
- [`backend/Seals team YAIWES/seals_core/consultor_experto.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/consultor_experto.py)
- [`backend/Seals team YAIWES/seals_core/consultor_groq.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/consultor_groq.py)
- [`backend/Seals team YAIWES/seals_core/crash_resume.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/crash_resume.py)
- [`backend/Seals team YAIWES/seals_core/crazy_wall_adapter.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/crazy_wall_adapter.py)
- [`backend/Seals team YAIWES/seals_core/dag_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/dag_engine.py)
- [`backend/Seals team YAIWES/seals_core/ejecutor.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/ejecutor.py)
- [`backend/Seals team YAIWES/seals_core/evidence.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/evidence.py)
- [`backend/Seals team YAIWES/seals_core/goal_tracking.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/goal_tracking.py)
- [`backend/Seals team YAIWES/seals_core/idempotencia.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/idempotencia.py)
- [`backend/Seals team YAIWES/seals_core/instalador_deterministico.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/instalador_deterministico.py)
- [`backend/Seals team YAIWES/seals_core/isolation.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/isolation.py)
- [`backend/Seals team YAIWES/seals_core/llm_output_schema.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/llm_output_schema.py)
- [`backend/Seals team YAIWES/seals_core/recovery_types.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/recovery_types.py)
- [`backend/Seals team YAIWES/seals_core/research_real.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/research_real.py)
- [`backend/Seals team YAIWES/seals_core/router_modelos.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/router_modelos.py)
- [`backend/Seals team YAIWES/seals_core/sheriff_policy.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/sheriff_policy.py)
- [`backend/Seals team YAIWES/seals_core/stuck_detector.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/stuck_detector.py)
- [`backend/Seals team YAIWES/seals_core/tests/evidencia_runs/groq_test_20260919T041247Z.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/evidencia_runs/groq_test_20260919T041247Z.json)
- [`backend/Seals team YAIWES/seals_core/tests/evidencia_runs/groq_test_20260919T041417Z.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/evidencia_runs/groq_test_20260919T041417Z.json)
- [`backend/Seals team YAIWES/seals_core/tests/evidencia_runs/groq_test_20260919T041540Z.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/evidencia_runs/groq_test_20260919T041540Z.json)
- [`backend/Seals team YAIWES/seals_core/tests/evidencia_runs/groq_test_20260919T041616Z.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/evidencia_runs/groq_test_20260919T041616Z.json)
- [`backend/Seals team YAIWES/seals_core/tests/evidencia_runs/groq_test_20260921T033014Z.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/evidencia_runs/groq_test_20260921T033014Z.json)
- [`backend/Seals team YAIWES/seals_core/tests/evidencia_runs/ultimo_run_console.txt`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/evidencia_runs/ultimo_run_console.txt)
- [`backend/Seals team YAIWES/seals_core/tests/test_ejecutor.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/test_ejecutor.py)
- [`backend/Seals team YAIWES/seals_core/tests/test_groq_real.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/test_groq_real.py)
- [`backend/Seals team YAIWES/seals_core/tests/test_p0_01_dag_real.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/test_p0_01_dag_real.py)
- [`backend/Seals team YAIWES/seals_core/tests/test_p0_05_06_07.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/test_p0_05_06_07.py)
- [`backend/Seals team YAIWES/seals_core/tests/test_p0_08_09_10_11.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/test_p0_08_09_10_11.py)
- [`backend/Seals team YAIWES/seals_core/tests/test_p0_13_14_15_17.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/test_p0_13_14_15_17.py)
- [`backend/Seals team YAIWES/seals_core/tests/test_p0_fixes.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/test_p0_fixes.py)
- [`backend/Seals team YAIWES/seals_core/tests/test_p1_18_19_22_23.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/test_p1_18_19_22_23.py)
- [`backend/Seals team YAIWES/seals_core/tests/test_p1_20_21_25_26_29.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tests/test_p1_20_21_25_26_29.py)
- [`backend/Seals team YAIWES/seals_core/tool_result.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/tool_result.py)
- [`backend/Seals team YAIWES/seals_core/verificador.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/verificador.py)
- [`backend/Seals team YAIWES/seals_core/work_surface.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/work_surface.py)
- [`backend/Seals team YAIWES/seals_core/worker_bootstrap.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/seals_core/worker_bootstrap.py)
- [`backend/Seals team YAIWES/watchdog.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/backend/Seals%20team%20YAIWES/watchdog.py)
- [`minimax_mcp/.env.example`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/minimax_mcp/.env.example)
- [`minimax_mcp/.github/ISSUE_TEMPLATE/Bad case about the model.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/minimax_mcp/.github/ISSUE_TEMPLATE/Bad%20case%20about%20the%20model.yml)
- [`minimax_mcp/.github/ISSUE_TEMPLATE/Bug Report for MCP.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/minimax_mcp/.github/ISSUE_TEMPLATE/Bug%20Report%20for%20MCP.yml)
- [`minimax_mcp/.github/ISSUE_TEMPLATE/Feature request.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/minimax_mcp/.github/ISSUE_TEMPLATE/Feature%20request.yml)
- [`minimax_mcp/.github/ISSUE_TEMPLATE/Model Inquiry.yml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/minimax_mcp/.github/ISSUE_TEMPLATE/Model%20Inquiry.yml)
- [`minimax_mcp/.gitignore`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/minimax_mcp/.gitignore)
- [`runtime/docs/PECP_MAXBRY_100x_ARQUITECTURA_v4.1.0_FINAL.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/docs/PECP_MAXBRY_100x_ARQUITECTURA_v4.1.0_FINAL.md)
- [`runtime/docs/PLAN-TRABAJO-CLAUDE-WORDFLOW.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/docs/PLAN-TRABAJO-CLAUDE-WORDFLOW.md)
- [`runtime/docs/T001_CHAT_B_CONTRACT.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/docs/T001_CHAT_B_CONTRACT.md)
- [`runtime/docs/T007_CHAT_B_CONTRACT.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/docs/T007_CHAT_B_CONTRACT.md)
- [`runtime/docs/T011_CHAT_B_CONTRACT.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/docs/T011_CHAT_B_CONTRACT.md)
- [`runtime/plugin-manifest.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/plugin-manifest.yaml)
- [`runtime/schemas/component-intake-v2.schema.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/schemas/component-intake-v2.schema.json)
- [`runtime/schemas/goals12-v1.schema.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/schemas/goals12-v1.schema.json)
- [`runtime/schemas/huggingface-bridge-v1.schema.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/schemas/huggingface-bridge-v1.schema.json)
- [`runtime/src/agent/agent_router.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/agent/agent_router.py)
- [`runtime/src/conn/huggingface_bridge.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/conn/huggingface_bridge.py)
- [`runtime/src/conn/manager.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/conn/manager.py)
- [`runtime/src/conn/rate_limit.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/conn/rate_limit.py)
- [`runtime/src/conn/secrets.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/conn/secrets.py)
- [`runtime/src/core/agent_memory_loader.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/agent_memory_loader.py)
- [`runtime/src/core/agent_source_copy_runner.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/agent_source_copy_runner.py)
- [`runtime/src/core/architecture_chat_bridge.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/architecture_chat_bridge.py)
- [`runtime/src/core/auto_loop_builder.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/auto_loop_builder.py)
- [`runtime/src/core/canonical_motor_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/canonical_motor_gate.py)
- [`runtime/src/core/code_generation_policy.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/code_generation_policy.py)
- [`runtime/src/core/code_graph_workspace.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/code_graph_workspace.py)
- [`runtime/src/core/code_task_graph.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/code_task_graph.py)
- [`runtime/src/core/completion_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/completion_gate.py)
- [`runtime/src/core/component_intake.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/component_intake.py)
- [`runtime/src/core/continuity_supervisor.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/continuity_supervisor.py)
- [`runtime/src/core/crazy_wall_concurrency.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/crazy_wall_concurrency.py)
- [`runtime/src/core/crazywall_claim_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/crazywall_claim_gate.py)
- [`runtime/src/core/dag_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/dag_engine.py)
- [`runtime/src/core/event_bus.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/event_bus.py)
- [`runtime/src/core/existing_code_intake.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/existing_code_intake.py)
- [`runtime/src/core/fables_binding_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/fables_binding_gate.py)
- [`runtime/src/core/file_audit_contract.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/file_audit_contract.py)
- [`runtime/src/core/goals12.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/goals12.py)
- [`runtime/src/core/goose_official_acquisition_runner.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/goose_official_acquisition_runner.py)
- [`runtime/src/core/graph_visual_projection.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/graph_visual_projection.py)
- [`runtime/src/core/graphiti_temporal_adapter.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/graphiti_temporal_adapter.py)
- [`runtime/src/core/kernel.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/kernel.py)
- [`runtime/src/core/llm_boundary.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/llm_boundary.py)
- [`runtime/src/core/no_value_gap.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/no_value_gap.py)
- [`runtime/src/core/parallel_scheduler.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/parallel_scheduler.py)
- [`runtime/src/core/placement_classifier.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/placement_classifier.py)
- [`runtime/src/core/project_intake_pipeline.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/project_intake_pipeline.py)
- [`runtime/src/core/reuse_selector.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/reuse_selector.py)
- [`runtime/src/core/run_launcher.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/run_launcher.py)
- [`runtime/src/core/security_rewriter.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/security_rewriter.py)
- [`runtime/src/core/source_truth_reconciler.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/source_truth_reconciler.py)
- [`runtime/src/core/state_machine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/state_machine.py)
- [`runtime/src/core/structured_action_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/structured_action_gate.py)
- [`runtime/src/core/task_skill_selector.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/task_skill_selector.py)
- [`runtime/src/core/truth_reconciler.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/truth_reconciler.py)
- [`runtime/src/core/unsafe_behavior_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/unsafe_behavior_gate.py)
- [`runtime/src/core/wordflow_global_audit.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/core/wordflow_global_audit.py)
- [`runtime/src/governance/merkle_governance_core.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/governance/merkle_governance_core.py)
- [`runtime/src/install/deployment_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/install/deployment_gate.py)
- [`runtime/src/install/deterministic_deployer.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/install/deterministic_deployer.py)
- [`runtime/src/install/installation_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/install/installation_engine.py)
- [`runtime/src/mission/sharder.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/mission/sharder.py)
- [`runtime/src/observability/engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/observability/engine.py)
- [`runtime/src/parallel/mavis_parallel.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/parallel/mavis_parallel.py)
- [`runtime/src/preflight/engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/preflight/engine.py)
- [`runtime/src/recovery/checkpoint.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/recovery/checkpoint.py)
- [`runtime/src/recovery/circuit_breaker_sla.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/recovery/circuit_breaker_sla.py)
- [`runtime/src/recovery/classifier.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/recovery/classifier.py)
- [`runtime/src/recovery/engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/recovery/engine.py)
- [`runtime/src/recovery/reconciliation.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/recovery/reconciliation.py)
- [`runtime/src/research/engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/research/engine.py)
- [`runtime/src/spec/healing_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/spec/healing_engine.py)
- [`runtime/src/storage/artifact_router.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/storage/artifact_router.py)
- [`runtime/src/tribunal/budget_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/tribunal/budget_gate.py)
- [`runtime/src/tribunal/constitutional.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/tribunal/constitutional.py)
- [`runtime/src/tribunal/cross_validator.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/tribunal/cross_validator.py)
- [`runtime/src/tribunal/hmac_manager.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/tribunal/hmac_manager.py)
- [`runtime/src/tribunal/tribunal.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/tribunal/tribunal.py)
- [`runtime/src/uek/boot_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/uek/boot_engine.py)
- [`runtime/src/uek/ficha_contract_v2.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/uek/ficha_contract_v2.py)
- [`runtime/src/uek/sandbox_manager.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/uek/sandbox_manager.py)
- [`runtime/src/uek/sbom_adapter_factory.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/uek/sbom_adapter_factory.py)
- [`runtime/src/uek/uek_cluster.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/uek/uek_cluster.py)
- [`runtime/src/uek/universal_plugin_bus_v2_integrated.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/src/uek/universal_plugin_bus_v2_integrated.py)
- [`runtime/tests/g022_g017_closure_runner.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/g022_g017_closure_runner.py)
- [`runtime/tests/g022_g017_finalize.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/g022_g017_finalize.py)
- [`runtime/tests/g022_g017_physical_closure.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/g022_g017_physical_closure.py)
- [`runtime/tests/test_agent_memory_loader.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_agent_memory_loader.py)
- [`runtime/tests/test_architecture_chat_bridge.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_architecture_chat_bridge.py)
- [`runtime/tests/test_auto_loop_builder.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_auto_loop_builder.py)
- [`runtime/tests/test_browser_use_adapter.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_browser_use_adapter.py)
- [`runtime/tests/test_canonical_motor_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_canonical_motor_gate.py)
- [`runtime/tests/test_checkpoint_durability.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_checkpoint_durability.py)
- [`runtime/tests/test_code_generation_policy.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_code_generation_policy.py)
- [`runtime/tests/test_code_graph_controls_batch1.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_code_graph_controls_batch1.py)
- [`runtime/tests/test_code_graph_workspace.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_code_graph_workspace.py)
- [`runtime/tests/test_code_task_graph.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_code_task_graph.py)
- [`runtime/tests/test_codebase_memory_mcp_adapter.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_codebase_memory_mcp_adapter.py)
- [`runtime/tests/test_component_intake.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_component_intake.py)
- [`runtime/tests/test_continuity_supervisor.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_continuity_supervisor.py)
- [`runtime/tests/test_crazywall_claim_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_crazywall_claim_gate.py)
- [`runtime/tests/test_dag_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_dag_engine.py)
- [`runtime/tests/test_event_bus.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_event_bus.py)
- [`runtime/tests/test_existing_code_intake_g007.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_existing_code_intake_g007.py)
- [`runtime/tests/test_fables_binding_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_fables_binding_gate.py)
- [`runtime/tests/test_file_audit_contract.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_file_audit_contract.py)
- [`runtime/tests/test_goals12_runner.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_goals12_runner.py)
- [`runtime/tests/test_goose_source_normalization.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_goose_source_normalization.py)
- [`runtime/tests/test_graph_visual_projection_g026.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_graph_visual_projection_g026.py)
- [`runtime/tests/test_graphiti_temporal_adapter_g027.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_graphiti_temporal_adapter_g027.py)
- [`runtime/tests/test_huggingface_bridge_g023.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_huggingface_bridge_g023.py)
- [`runtime/tests/test_install_sandbox_deploy_gates.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_install_sandbox_deploy_gates.py)
- [`runtime/tests/test_llm_boundary_g024.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_llm_boundary_g024.py)
- [`runtime/tests/test_mavis_parallel_g025.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_mavis_parallel_g025.py)
- [`runtime/tests/test_muse_frontend_completion_gates.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_muse_frontend_completion_gates.py)
- [`runtime/tests/test_no_value_gap.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_no_value_gap.py)
- [`runtime/tests/test_parallel_scheduler_g021.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_parallel_scheduler_g021.py)
- [`runtime/tests/test_placement_classifier.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_placement_classifier.py)
- [`runtime/tests/test_planning_stack_g029.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_planning_stack_g029.py)
- [`runtime/tests/test_project_intake_pipeline.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_project_intake_pipeline.py)
- [`runtime/tests/test_reuse_selector.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_reuse_selector.py)
- [`runtime/tests/test_run_launcher.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_run_launcher.py)
- [`runtime/tests/test_sandbox_enforcement_g022.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_sandbox_enforcement_g022.py)
- [`runtime/tests/test_source_truth_reconciler.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_source_truth_reconciler.py)
- [`runtime/tests/test_state_machine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_state_machine.py)
- [`runtime/tests/test_task_skill_selector.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_task_skill_selector.py)
- [`runtime/tests/test_unsafe_behavior_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_unsafe_behavior_gate.py)
- [`runtime/tests/test_wordflow_global_audit_g019.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/runtime/tests/test_wordflow_global_audit_g019.py)
- [`wordflow_loop/adapters/browser_use_adapter.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/adapters/browser_use_adapter.py)
- [`wordflow_loop/adapters/codebase_memory_mcp_adapter.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/adapters/codebase_memory_mcp_adapter.py)
- [`wordflow_loop/contracts/MVP-COMPONENT-REGISTRY.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/contracts/MVP-COMPONENT-REGISTRY.json)
- [`wordflow_loop/contracts/ficha.agent_fleet.v2.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/contracts/ficha.agent_fleet.v2.json)
- [`wordflow_loop/contracts/ficha.browser_use.v2.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/contracts/ficha.browser_use.v2.json)
- [`wordflow_loop/contracts/ficha.codebase_memory_mcp.v2.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/contracts/ficha.codebase_memory_mcp.v2.json)
- [`wordflow_loop/contracts/mavis-parallel-g025-matrix.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/contracts/mavis-parallel-g025-matrix.json)
- [`wordflow_loop/contracts/planning-stack-g029-matrix.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/contracts/planning-stack-g029-matrix.json)
- [`wordflow_loop/contracts/workflow.dsl.yaml`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/contracts/workflow.dsl.yaml)
- [`wordflow_loop/contracts/workflow.schema.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/contracts/workflow.schema.json)
- [`wordflow_loop/evidence/AGENT_SOURCE_COPY_2026-09-15.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/AGENT_SOURCE_COPY_2026-09-15.json)
- [`wordflow_loop/evidence/BROWSER_USE_ADAPTER_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/BROWSER_USE_ADAPTER_2026-09-11.json)
- [`wordflow_loop/evidence/CG01_REUSE_AUDIT_2026-09-10.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/CG01_REUSE_AUDIT_2026-09-10.json)
- [`wordflow_loop/evidence/CL002_PUBLICATION_TRANSPORT_RETEST_2026-09-17.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/CL002_PUBLICATION_TRANSPORT_RETEST_2026-09-17.json)
- [`wordflow_loop/evidence/CODE_GRAPH_CYCLE_0002_2026-09-10.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/CODE_GRAPH_CYCLE_0002_2026-09-10.json)
- [`wordflow_loop/evidence/COMP_CODEBASE_MEMORY_MCP_PREWIRE_2026-09-14.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/COMP_CODEBASE_MEMORY_MCP_PREWIRE_2026-09-14.json)
- [`wordflow_loop/evidence/FINAL_3STEP_CLOSURE_TEST_2026-09-10.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/FINAL_3STEP_CLOSURE_TEST_2026-09-10.json)
- [`wordflow_loop/evidence/G001_CODE_GRAPH_WORKSPACE_2026-09-10.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G001_CODE_GRAPH_WORKSPACE_2026-09-10.json)
- [`wordflow_loop/evidence/G002_FILE_AUDIT_COUNCIL_2026-09-10.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G002_FILE_AUDIT_COUNCIL_2026-09-10.json)
- [`wordflow_loop/evidence/G003_TASK_GRAPH_2026-09-10.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G003_TASK_GRAPH_2026-09-10.json)
- [`wordflow_loop/evidence/G004_PLACEMENT_CLASSIFIER_2026-09-10.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G004_PLACEMENT_CLASSIFIER_2026-09-10.json)
- [`wordflow_loop/evidence/G005_REUSE_SELECTOR_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G005_REUSE_SELECTOR_2026-09-11.json)
- [`wordflow_loop/evidence/G006_BLOCKED_FABLES_DEPENDENCY_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G006_BLOCKED_FABLES_DEPENDENCY_2026-09-11.json)
- [`wordflow_loop/evidence/G006_CODE_GENERATION_POLICY_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G006_CODE_GENERATION_POLICY_2026-09-12.json)
- [`wordflow_loop/evidence/G007_EXISTING_CODE_CANONICAL_TRANSFER_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G007_EXISTING_CODE_CANONICAL_TRANSFER_2026-09-12.json)
- [`wordflow_loop/evidence/G008_UNSAFE_BEHAVIOR_GATE_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G008_UNSAFE_BEHAVIOR_GATE_2026-09-11.json)
- [`wordflow_loop/evidence/G009_NO_VALUE_GAP_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G009_NO_VALUE_GAP_2026-09-11.json)
- [`wordflow_loop/evidence/G011_CANONICAL_COPY_MOVE_MOTORS_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G011_CANONICAL_COPY_MOVE_MOTORS_2026-09-11.json)
- [`wordflow_loop/evidence/G011_CANONICAL_MOTORS_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G011_CANONICAL_MOTORS_2026-09-11.json)
- [`wordflow_loop/evidence/G012_COMPONENT_INTAKE_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G012_COMPONENT_INTAKE_2026-09-12.json)
- [`wordflow_loop/evidence/G013_CANONICAL_RECONCILIATION_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G013_CANONICAL_RECONCILIATION_2026-09-11.json)
- [`wordflow_loop/evidence/G013_SOURCE_TRUTH_RECONCILER_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G013_SOURCE_TRUTH_RECONCILER_2026-09-11.json)
- [`wordflow_loop/evidence/G014_AGENT_MEMORY_PREINJECTION_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G014_AGENT_MEMORY_PREINJECTION_2026-09-11.json)
- [`wordflow_loop/evidence/G015_GOALS12_INPUT_OUTPUT_RUNNER_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G015_GOALS12_INPUT_OUTPUT_RUNNER_2026-09-11.json)
- [`wordflow_loop/evidence/G016_CHAT_A_CHAT_B_SOURCE_PROOF_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G016_CHAT_A_CHAT_B_SOURCE_PROOF_2026-09-12.json)
- [`wordflow_loop/evidence/G017_DETERMINISTIC_DEPLOYMENT_CLOSURE_2026-09-15.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G017_DETERMINISTIC_DEPLOYMENT_CLOSURE_2026-09-15.json)
- [`wordflow_loop/evidence/G018_FABLES_BINDING_READBACK_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G018_FABLES_BINDING_READBACK_2026-09-11.json)
- [`wordflow_loop/evidence/G018_FABLES_EXACT_BLOB_PYTEST_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G018_FABLES_EXACT_BLOB_PYTEST_2026-09-12.json)
- [`wordflow_loop/evidence/G018_SOL2_WATCHDOG_GAP_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G018_SOL2_WATCHDOG_GAP_2026-09-11.json)
- [`wordflow_loop/evidence/G019_CLASSIFICATION_LEDGER_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G019_CLASSIFICATION_LEDGER_2026-09-12.json)
- [`wordflow_loop/evidence/G019_GLOBAL_WORDFLOW_AUDIT_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G019_GLOBAL_WORDFLOW_AUDIT_2026-09-12.json)
- [`wordflow_loop/evidence/G021_PARALLEL_SCHEDULER_KERNEL_WIRING_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G021_PARALLEL_SCHEDULER_KERNEL_WIRING_2026-09-12.json)
- [`wordflow_loop/evidence/G022_BACKEND_MATRIX_BLOCKER_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G022_BACKEND_MATRIX_BLOCKER_2026-09-12.json)
- [`wordflow_loop/evidence/G022_PHYSICAL_SANDBOX_CLOSURE_2026-09-15.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G022_PHYSICAL_SANDBOX_CLOSURE_2026-09-15.json)
- [`wordflow_loop/evidence/G022_SANDBOX_FAIL_CLOSED_BLOCKER_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G022_SANDBOX_FAIL_CLOSED_BLOCKER_2026-09-12.json)
- [`wordflow_loop/evidence/G023_HUGGINGFACE_PUBLIC_BRIDGE_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G023_HUGGINGFACE_PUBLIC_BRIDGE_2026-09-12.json)
- [`wordflow_loop/evidence/G024_LLM_DETERMINISTIC_BOUNDARY_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G024_LLM_DETERMINISTIC_BOUNDARY_2026-09-12.json)
- [`wordflow_loop/evidence/G025_MAVIS_PATTERN_MATRIX_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G025_MAVIS_PATTERN_MATRIX_2026-09-12.json)
- [`wordflow_loop/evidence/G026_CRAZY_WALL_VISUAL_PROJECTION_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G026_CRAZY_WALL_VISUAL_PROJECTION_2026-09-12.json)
- [`wordflow_loop/evidence/G027_GRAPHITI_TEMPORAL_ADAPTER_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G027_GRAPHITI_TEMPORAL_ADAPTER_2026-09-12.json)
- [`wordflow_loop/evidence/G028_GRAPHOLOGY_NO_VALUE_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G028_GRAPHOLOGY_NO_VALUE_2026-09-12.json)
- [`wordflow_loop/evidence/G029_PLANNING_STACK_DECISION_2026-09-12.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G029_PLANNING_STACK_DECISION_2026-09-12.json)
- [`wordflow_loop/evidence/G030_CRAZYWALL_CLAIM_GATE_2026-09-11.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/G030_CRAZYWALL_CLAIM_GATE_2026-09-11.json)
- [`wordflow_loop/evidence/GOOSE_OFFICIAL_ACQUISITION_2026-09-15.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/GOOSE_OFFICIAL_ACQUISITION_2026-09-15.json)
- [`wordflow_loop/evidence/MUSE_FRONTEND_COMPLETION_GATES_2026-09-15.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/MUSE_FRONTEND_COMPLETION_GATES_2026-09-15.json)
- [`wordflow_loop/evidence/ORCA_ADDITIONAL_DESTINATION_MOTOR3_2026-09-17.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/ORCA_ADDITIONAL_DESTINATION_MOTOR3_2026-09-17.json)
- [`wordflow_loop/evidence/SCOPE_MIGRATION_2026-09-09.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/SCOPE_MIGRATION_2026-09-09.json)
- [`wordflow_loop/evidence/STEP3_AGENT_FLEET_VERIFY.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/STEP3_AGENT_FLEET_VERIFY.json)
- [`wordflow_loop/evidence/WORDFLOW_IMPROVEMENT_PACK_2026-09-15.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/WORDFLOW_IMPROVEMENT_PACK_2026-09-15.json)
- [`wordflow_loop/evidence/agent-source-copy-state/agent_zero.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/agent_zero.json)
- [`wordflow_loop/evidence/agent-source-copy-state/aider.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/aider.json)
- [`wordflow_loop/evidence/agent-source-copy-state/claude_code.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/claude_code.json)
- [`wordflow_loop/evidence/agent-source-copy-state/cline.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/cline.json)
- [`wordflow_loop/evidence/agent-source-copy-state/codex.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/codex.json)
- [`wordflow_loop/evidence/agent-source-copy-state/goose.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/goose.json)
- [`wordflow_loop/evidence/agent-source-copy-state/hermes.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/hermes.json)
- [`wordflow_loop/evidence/agent-source-copy-state/kimi_k.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/kimi_k.json)
- [`wordflow_loop/evidence/agent-source-copy-state/mimo_code.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/mimo_code.json)
- [`wordflow_loop/evidence/agent-source-copy-state/mirothinker.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/mirothinker.json)
- [`wordflow_loop/evidence/agent-source-copy-state/muse_glimmer.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/muse_glimmer.json)
- [`wordflow_loop/evidence/agent-source-copy-state/openclaw.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/openclaw.json)
- [`wordflow_loop/evidence/agent-source-copy-state/opencode.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/opencode.json)
- [`wordflow_loop/evidence/agent-source-copy-state/opendev.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/opendev.json)
- [`wordflow_loop/evidence/agent-source-copy-state/openhands.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/openhands.json)
- [`wordflow_loop/evidence/agent-source-copy-state/qwen_code.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/qwen_code.json)
- [`wordflow_loop/evidence/agent-source-copy-state/research_agent_lab.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/research_agent_lab.json)
- [`wordflow_loop/evidence/agent-source-copy-state/smolagents.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/evidence/agent-source-copy-state/smolagents.json)
- [`wordflow_loop/plugins/ficha_contract_v2.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/plugins/ficha_contract_v2.py)
- [`wordflow_loop/plugins/universal_plugin_bus_v2_integrated.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/plugins/universal_plugin_bus_v2_integrated.py)
- [`wordflow_loop/prompts/DIRECTOR-CODE-GRAPH-METHODS.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/prompts/DIRECTOR-CODE-GRAPH-METHODS.md)
- [`wordflow_loop/prompts/GRAPHIFY-MVP-INTEGRATION.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/prompts/GRAPHIFY-MVP-INTEGRATION.md)
- [`wordflow_loop/prompts/SYSTEM_PROMPT.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/prompts/SYSTEM_PROMPT.md)
- [`wordflow_loop/research/community_sources.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/research/community_sources.json)
- [`wordflow_loop/research/reuse_catalog_g005.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/research/reuse_catalog_g005.json)
- [`wordflow_loop/wordflow_loop/__init__.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/__init__.py)
- [`wordflow_loop/wordflow_loop/agent_fleet/AGENT_FLEET_READY_FOR_TEST.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/AGENT_FLEET_READY_FOR_TEST.json)
- [`wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_adapter.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_adapter.py)
- [`wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_health.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_health.json)
- [`wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_plugin_registration.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_plugin_registration.json)
- [`wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/agent_zero/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/agent_zero/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/aider/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/aider/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/claude_code/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/claude_code/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/cline/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/cline/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/codex/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/codex/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/goose/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/goose/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/hermes/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/hermes/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/kimi_k/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/kimi_k/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/mimo_code/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/mimo_code/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/mirothinker/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/mirothinker/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/muse_glimmer/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/muse_glimmer/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/openclaw/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/openclaw/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/opencode/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/opencode/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/opendev/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/opendev/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/openhands/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/openhands/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/qwen_code/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/qwen_code/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/research_agent_lab/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/research_agent_lab/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/agent_fleet/memory/smolagents/agente-readme-memoria.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/memory/smolagents/agente-readme-memoria.md)
- [`wordflow_loop/wordflow_loop/contracts.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/contracts.py)
- [`wordflow_loop/wordflow_loop/governance/__init__.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/governance/__init__.py)
- [`wordflow_loop/wordflow_loop/governance/guardian.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/governance/guardian.py)
- [`wordflow_loop/wordflow_loop/governance/judge.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/governance/judge.py)
- [`wordflow_loop/wordflow_loop/governance/sentinel.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/governance/sentinel.py)
- [`wordflow_loop/wordflow_loop/governance/sheriff.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/governance/sheriff.py)
- [`wordflow_loop/wordflow_loop/governance/supervisor.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/governance/supervisor.py)
- [`wordflow_loop/wordflow_loop/governance/validator.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/governance/validator.py)
- [`wordflow_loop/wordflow_loop/governance/verifier.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/governance/verifier.py)
- [`wordflow_loop/wordflow_loop/ledger.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/ledger.py)
- [`wordflow_loop/wordflow_loop/llm_gate.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/llm_gate.py)
- [`wordflow_loop/wordflow_loop/model_api_router_mvp.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/wordflow_loop/wordflow_loop/model_api_router_mvp.py)
- [`workspace/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/workspace/README.md)
- [`workspace/code/README.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/workspace/code/README.md)
- [`workspace/memory/agents/➡️📂 readme memoria agentes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/workspace/memory/agents/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20readme%20memoria%20agentes.md)
- [`workspace/profiles/CLAUDE.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/workspace/profiles/CLAUDE.md)
- [`workspace/profiles/PROFILE-TEMPLATE.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/workspace/profiles/PROFILE-TEMPLATE.md)
- [`workspace/profiles/README perfiles agentes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/workspace/profiles/README%20perfiles%20agentes.md)
- [`➡️📂 README arquitectura Wordflow LOOP Yaiwes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20README%20arquitectura%20Wordflow%20LOOP%20Yaiwes.md)
- [`➡️📂 readme indice agentes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20readme%20indice%20agentes.md)
- [`➡️📂 readme wordflow loop Yaiwes.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20readme%20wordflow%20loop%20Yaiwes.md)
- [`➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂 Motor de extracción zip/motor_1_extract_only.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Motor%20de%20extracci%C3%B3n%20zip/motor_1_extract_only.py)
- [`➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂 skills descargar extraer zip copiar mover archivos readme.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20skills%20descargar%20extraer%20zip%20copiar%20mover%20archivos%20readme.md)
- [`➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂motor de copiar archivos/motor_3_copy_batches.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motor%20de%20copiar%20archivos/motor_3_copy_batches.py)
- [`➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂motor de copiar archivos/motor_copy_root_to_repo.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motor%20de%20copiar%20archivos/motor_copy_root_to_repo.py)
- [`➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂motor de moves archivos/motor_4_move_batches.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motor%20de%20moves%20archivos/motor_4_move_batches.py)
- [`➡️📂motores de descarga extracción copiado movimiento archivos agentes/📂Motor descarga de componentes y extracción de zip/hf_download_extract_engine.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%F0%9F%93%82Motor%20descarga%20de%20componentes%20y%20extracci%C3%B3n%20de%20zip/hf_download_extract_engine.py)
- [`➡️📂motores de descarga extracción copiado movimiento archivos agentes/📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20agentes/%F0%9F%93%82Motor%20descarga%20de%20componentes%20y%20extracci%C3%B3n%20de%20zip/motor_2_queue_download_extract.py)
- [`📂 notas auditoría Claude/✅ 01_hoja_de_ruta_fundamentos_limpieza — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2001_hoja_de_ruta_fundamentos_limpieza%20%E2%80%94%20NOTA%20XRAY.md)
- [`📂 notas auditoría Claude/✅ 02_hoja_de_ruta_razonamiento_gobernanza — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2002_hoja_de_ruta_razonamiento_gobernanza%20%E2%80%94%20NOTA%20XRAY.md)
- [`📂 notas auditoría Claude/✅ 03_hoja_de_ruta_workflows_pool_memoria — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2003_hoja_de_ruta_workflows_pool_memoria%20%E2%80%94%20NOTA%20XRAY.md)
- [`📂 notas auditoría Claude/✅ 04_hoja_de_ruta_observabilidad_cierre — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2004_hoja_de_ruta_observabilidad_cierre%20%E2%80%94%20NOTA%20XRAY.md)
- [`📂 notas auditoría Claude/✅ 05_arquitectura_completa_fables — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2005_arquitectura_completa_fables%20%E2%80%94%20NOTA%20XRAY.md)
- [`📂 notas auditoría Claude/✅ 06_componentes_open_source_investigados — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2006_componentes_open_source_investigados%20%E2%80%94%20NOTA%20XRAY.md)
- [`📂 notas auditoría Claude/✅ 07_hoja_de_ruta_loops_multiapi_memoria_chat — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2007_hoja_de_ruta_loops_multiapi_memoria_chat%20%E2%80%94%20NOTA%20XRAY.md)
- [`📂 notas auditoría Claude/✅ 08_protocolo_cierre_kernel_simple — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2008_protocolo_cierre_kernel_simple%20%E2%80%94%20NOTA%20XRAY.md)
- [`📂 notas auditoría Claude/✅ 09_guia_decision_integrar_codigo_kernel — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2009_guia_decision_integrar_codigo_kernel%20%E2%80%94%20NOTA%20XRAY.md)
- [`📂 notas auditoría Claude/✅ 10_plantilla_modulos_razonamiento — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2010_plantilla_modulos_razonamiento%20%E2%80%94%20NOTA%20XRAY.md)
- [`📂 notas auditoría Claude/✅ 11_catalogo_105_algoritmos_deterministas — NOTA XRAY.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/%F0%9F%93%82%20notas%20auditor%C3%ADa%20Claude/%E2%9C%85%2011_catalogo_105_algoritmos_deterministas%20%E2%80%94%20NOTA%20XRAY.md)

</details>

