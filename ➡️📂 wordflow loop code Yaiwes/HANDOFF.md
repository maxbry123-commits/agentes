# HANDOFF — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4`  
Modo: `FAIL_CLOSED_EXECUTION_LOOP`  
Raíz única autorizada de escritura: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`  
Checkpoint canónico: `WFLOOP-CODE-GRAPH-20260911-0019`.

## Estado canónico fresco — 2026-09-12
Fuente de estado por nodo: `Crazy Wall Orquestador/TASK-NODES.json`.

- 30 GAPs del CODE GRAPH.
- 28 `PASS` verificados en el ledger actual.
- `G-019 PASS` por `SOL_1`; auditoría global real, clasificación y reparación de ruta interna completadas.
- `G-027 PASS` y `G-028 PASS` por `SOL_2`.
- `G-022 BLOCKED_PHYSICAL_ISOLATION`, owner `ASTRA_GPT_LOOP`; no tocar ni convertir a PASS sin aislamiento físico real.
- `G-017 PENDING` depende de G-022 y por tanto no es reclamable todavía.
- `COMP-BROWSER-USE RUNNING` pertenece a `SOL_ORCHESTRATOR`; SOL_1 no lo toca.
- `AUTH_PROVIDER_TEST_PENDING` continúa abierto; no afirmar PASS_REAL externo.
- SOL_1 no tiene actualmente un nodo FREE con dependencias satisfechas.

## Cierre inmediato — G-019 GLOBAL WORDFLOW AUDIT
Owner histórico: `SOL_1`. Claim commit `d6aafd207ab89db0437d8c4f17da016fec534687`.

Objetivo literal:
`inventario + capabilities + duplicados + huérfanos + rutas rotas + code no usado + ledger`.

Cierre verificable:
1. Auditor canónico: `runtime/src/core/wordflow_global_audit.py`, contrato `yaiwes.wordflow_global_audit/v4`.
2. Snapshot real reparada y verificada: commit `a7d9b763304b1cbe5bf01e083f0ed8cf9c34e1a1`, Wordflow tree `7e51de1ef7b53139b3591fdbaa3bd14e8cb6b294`.
3. HF full-tree audit job: `6aa5c76221047bf1b037e8ee`.
4. HF classification job: `6aa5c7ab5527934177ed1d37`.
5. `broken_required_paths=0` y `broken_internal_imports=0` después de reparación.
6. GAP real resuelto: `runtime/src/uek/uek_cluster.py` importaba `src.uek.cache_engine.DeterministicCacheEngine`, componente inexistente. Reparación: REUSE de `src.parallel.mavis_parallel.SmartCache`; commit `a7d9b763304b1cbe5bf01e083f0ed8cf9c34e1a1`.
7. Test exacto sobre snapshot reparada: `PASS_11_OF_11`, return code 0.
8. Microtest UEK: caché `PASS_SEEDED_HIT`; sandbox `BLOCKED_SANDBOX` esperado por fail-closed.
9. 34/34 grupos duplicados = `STAGING_MIRROR`; no auto-delete.
10. 43 candidatos orphan/unused: 42 `REFERENCED_ACTIVE`, 1 `STAGING_ONLY_REFERENCE` (`runtime/src/spec/healing_engine.py`); no auto-delete.
11. Evidence: `wordflow_loop/evidence/G019_GLOBAL_WORDFLOW_AUDIT_2026-09-12.json`, commit `f68a3de1962220412718ac5fe2377fc6eb1d482f`.
12. Cierre `TASK-NODES`: commit `a36da44d74fbd961ebc13998e1732c0d2a90ce68`.

## Cierre anterior — G-013
`G-013 PASS` por SOL_1 en checkpoint `WFLOOP-CODE-GRAPH-20260911-0019`.
- Evidence: `wordflow_loop/evidence/G013_CANONICAL_RECONCILIATION_2026-09-11.json`.
- Test: `PASS_7_OF_7`.
- Truth read-back: `PASS_8_OF_8`.
- TASK-NODES close commit: `5db4739d6bed2a34bd1e148ed23ea820f6b69aa3`.

## Rutas históricas no restaurables sin fuente
No existen actualmente como archivos:
- `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md`
- `PIPELINE/FORENSIC_CODE_AUDIT.md`
- `PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md`

No restaurarlas ni inventarlas sin source canónico.

## Reglas de continuación SOL_1
1. Leer `TASK-NODES.json`, STATE, CHECKPOINT y BITÁCORA frescos antes de cada iteración.
2. Si SOL_1 tiene nodo `CLAIMED/RUNNING`, continuar exclusivamente ese nodo.
3. Sin nodo activo, reclamar solo un nodo `PENDING`, libre y con dependencias satisfechas.
4. `G-017` no puede reclamarse mientras `G-022` no sea PASS.
5. No tocar `G-022` ni `COMP-BROWSER-USE` mientras pertenezcan a otros owners.
6. Flujo 1×1: `investigar → motor solo si hace falta → wire/test/evidence → read-back`.
7. No escribir fuera de `➡️📂 Wordflow LOOP Yaiwes/`.
8. No LFS, no force, no Step4, no refactor lateral, no inventar tareas.
9. Motores COPY/MOVE/DOWNLOAD/EXTRACT solo cuando exista transferencia real.
10. Si no existe nodo SOL_1 elegible, mantener vigilancia por cambios frescos y no mutar trabajo ajeno.

## Histórico local conservado
Fleet=18 · Council12=12 · routing/fail-closed local. Evidence histórica `wordflow_loop/evidence/FINAL_3STEP_CLOSURE_TEST_2026-09-10.json`. Esto no sustituye pruebas externas autenticadas.


## Cierre físico G-022 + G-017 — 2026-09-15

- GitHub Actions run: `34931798702`
- G-022: PASS físico — Docker aislado, filesystem RO, red denegada y límites de memoria/tiempo comprobados.
- G-017: PASS — hash content-addressed, promoción atómica, health/smoke reales y rollback verificado.
- Gate: `PASS_4_OF_4`; CODE_GRAPH: `30/30`.
- Evidencia: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/G022_PHYSICAL_SANDBOX_CLOSURE_2026-09-15.json` y `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/G017_DETERMINISTIC_DEPLOYMENT_CLOSURE_2026-09-15.json`.


## Recuperación Motor de descarga — 2026-09-17

Watchdog activo: `Motor de descarga` (cadencia horaria).  
Checkpoint operativo: `Crazy Wall Orquestador/MOTOR-DESCARGA-RECOVERY-CHECKPOINT-2026-09-17.json`.

Estado verificable:
- Orca: destino adicional `wordflow_loop/agent_sources/orca` cerrado con Motor 3 canónico; 27.324/27.324 archivos; source/target tree `4a70b119890500c638cdc5e5115bc13a97fee974`; commit de publicación `50b657b4a914f6fcc4452f1cb74cc08ff08146c6`.
- CL-002: continúa `IN_PROGRESS`. Motor 2 volvió a verificar MiniMax-MCP, MiniMax-MCP-JS, MiniMax-Coding-Plan-MCP, kimi-agent-rs y Kimi-Researcher; publicación conectada queda bloqueada por transporte de blobs/código/binarios, no por descarga/extracción.
- CL-003: `@minimax-ai/code@0.4.10` oficial verificado por npm; integridad y shasum fijados; instalación efímera PASS con `mcode --version = 0.4.10`; no declara repositorio fuente público; publicación física del tarball sigue pendiente.
- CL-004: Motor 3 materializó los symlinks de `kimi-code` y `kimi-cli` como archivos regulares, dejando 0 symlinks; 4.471/4.471 y 988/988 archivos, respectivamente. Publicación cross-repo sigue pendiente porque GitHub rechaza reutilizar trees externas y el bulk blob write quedó bloqueado por controles del conector.

Regla de continuación: no usar GitHub Actions para estas adquisiciones; mantener motores canónicos, SHA/read-back y FAIL_CLOSED. No contar dry-runs o staging como entregado.

## Notas de integración — componentes MiniMax / Kimi / Orca — auditoría 2026-09-18

Regla de verdad: **descarga/extracción temporal verificada no equivale a presencia física en `wordflow_loop/agent_sources/` ni a integración runtime**. Solo Orca está publicado físicamente en el destino nuevo en este checkpoint.

| Componente | Evidencia de adquisición | Presencia física en agent_sources | Nota de integración |
|---|---|---|---|
| Orca | Motor 3; tree `4a70b119890500c638cdc5e5115bc13a97fee974`; commit `50b657b4a914f6fcc4452f1cb74cc08ff08146c6` | **SÍ**: `agent_sources/orca` | Fuente interna ya replicada. No implica runtime PASS por sí sola. |
| MiniMax Mini-Agent | commit `d76a4f6389688cabda39c224a6cdfa274215d47c`; Motor 2 dry-run verificado | **NO** | CL-006 clasificación → CL-007 fleet si pasa gates → CL-008 transporte. |
| MiniMax OpenRoom | commit `02468154c4d99f8925916425bf444d672454fb3d`; Motor 2 dry-run verificado | **NO** | CL-006 clasificar UI/agent; CL-010 solo si aporta valor único. |
| MiniMax mmx CLI | commit `bfbb4cb75ec343149eaccfd668c5011aa27bcf2b`; Motor 2 dry-run verificado | **NO** | CL-010 infraestructura; no crear bus paralelo. |
| MiniMax Code Plugins | commit `d592f422893846c2aac48f8b407a92bd0293c6b1`; Motor 2 dry-run verificado | **NO** | CL-010 capa plugin detrás de ports/bus existentes. |
| MiniMax MCP | commit `0856b9aef8a9d676bb63bdd6b6426d7b640a3b7a`; 28 archivos; tree hash `cf3ed570...` | **NO** | CL-010 MCP port. |
| MiniMax MCP JS | commit `8032f830203a1c61e56760b1680db923654bcb1b`; 38 archivos; tree hash `d3d0e65f...` | **NO** | CL-010 MCP JS port. |
| MiniMax Coding Plan MCP | commit `5dbf3494d7dac35d154958e0c1dab03910b89bbd`; 27 archivos; tree hash `daa6bf47...` | **NO** | CL-010 planning capability. |
| @minimax-ai/code / mcode | npm `0.4.10`; shasum `f4564e4fe8c92f4f496efb75e9718b28716be126`; instalación efímera PASS | **NO** | CL-003 adquisición física → CL-007 fleet → CL-008 ACP/stdio. |
| Kimi Code | commit `1fddc16e3ea2de4c26a18acd764380adf9e2ed64`; Motor 3: 4.471 archivos, symlink materializado | **NO** | CL-004 publicación → CL-007 fleet → CL-008 ACP/stdio. |
| Kimi CLI | commit `86f136422a0aae6b217ea49e7ea1d2e8a1defcd2`; Motor 3: 988 archivos, 2 symlinks materializados | **NO** | CL-004 publicación; CL-011 legacy/fallback solo si demuestra valor. |
| Kimi Agent SDK | commit `ed4be6be5280d02191da88bbafb3f828dcd33d72`; Motor 2 dry-run verificado | **NO** | CL-011 SDK/transport. |
| Kimi Agent RS | commit `f9186cd20b28c02d33721c05fd248e65d56e3e53`; 172 archivos; tree hash `39a2cc96...` | **NO** | CL-011 SDK/transport. |
| Kimi Researcher | commit `9406d821348471bceb6d5fa0b7eba05411106f93`; 16 archivos; tree hash `ce5d2be3...` | **NO** | CL-011 research capability, sujeto a NO_VALUE_GAP. |

**GAP común de publicación:** `PUBLISH_TRANSPORT_SECURITY_GATE`. La adquisición/verificación existe, pero los 13 objetivos nuevos MiniMax/Kimi/mcode todavía no cuentan como entregados físicamente en `agent_sources/`. No marcar CL-002/003/004 como PASS hasta presencia física + hash/read-back en `main`.

## Montaje MiniMax/Kimi — 2026-09-18

Commit de montaje: `28a47f47b7f127ba400c0bcbbb930daa424f6d85`.

Estado verificado por read-back:
- 12 repos GitHub de MiniMax/Kimi están presentes en `wordflow_loop/agent_sources/` como gitlinks/submodules `mode 160000`, fijados a los SHA exactos de adquisición.
- `mcode` está presente como directorio `agent_sources/mcode/` con `package.json` y `SOURCE_NPM.json`, fijando `@minimax-ai/code@0.4.10`, shasum `f4564e4fe8c92f4f496efb75e9718b28716be126`.
- Manifest de montaje: `wordflow_loop/agent_sources/AGENT_SOURCE_MOUNT_MANIFEST_2026-09-18.json`.
- Árbol `agent_sources` leído de `main`: `aa2e2b79b60fe48349fc03998f97560fdbf965d4`.
- GitHub Actions usados para este montaje: **NO**.

Importante: el gitlink/submodule monta y fija el source upstream, pero no embebe/vendoriza todos los blobs dentro del superproyecto. Kimi Code/Kimi CLI conservan su source upstream en el submodule; la variante materializada sin symlinks fue verificada por Motor 3 y queda como gate separado de vendorización si se exige copia física byte-a-byte dentro del superproyecto. Mcode está montado como pin npm exacto; los bytes completos del paquete no están vendorizados.

## Consolidación canónica de raíces — 2026-10-01

Raíz única autorizada y físicamente presente:

`➡️📂 wordflow loop code Yaiwes/`

Se eliminaron del nivel superior las raíces duplicadas:
- `wordflow loop code Yaiwes/` (solo contenía `.gitkeep`)
- `➡️📂 Wordflow LOOP Yaiwes/` (solo conservaba un META4 copy plan ya recuperado)
- `arquitectura wordflow loop code Yaiwes/` (24 documentos movidos a `➡️📂 wordflow loop code Yaiwes/arquitectura/`)

Plan de 4 objetivos consolidado en:
`➡️📂 wordflow loop code Yaiwes/PLAN-4-OBJETIVOS/`

Contiene:
- `PLAN-MAESTRO-4-OBJETIVOS.md`
- `HANDOFF-PLAN-OPUS.md`
- `PLAN-ANEXO-C-2-PUNTOS-ADICIONALES.md`
- `PROMPT-DSL-DAG-PLAN-OPUS.yaml`

Agentes/fuentes:
`➡️📂 wordflow loop code Yaiwes/wordflow_loop/agent_sources/`

Regla importante: los 13 componentes MiniMax/Kimi/mcode aparecen como gitlinks/submodules (modo Git 160000) y están definidos en la `.gitmodules` del repo. Eso fija repo+commit, pero no significa que sus archivos fuente estén materializados dentro del tree principal de GitHub. Para un checkout completo se requiere inicializar submodules. Los demás agentes materializados siguen como árboles normales.

Invariante: no crear otra raíz Wordflow. Toda nueva integración, documentación, plan, agente o evidencia debe vivir bajo la raíz canónica anterior.

## Mapa completo de ubicación de archivos — 2026-10-09

Detalle archivo por archivo, con enlaces: [`HANDOFF-WORKFLOW-LOOPS-YAIWES.md`](https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes/HANDOFF-WORKFLOW-LOOPS-YAIWES.md) (misma carpeta).

| Ubicación | Archivos | Estado |
|---|---|---|
| [`agentes` main · `➡️📂 wordflow loop code Yaiwes/`](https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes) | 154.796 + 13 submódulos | Original y más completa (agent_sources 112.202, frontend 42.078) |
| [router · rama `devin/1790824641-chat-agent-plan` · `chat router/Workflow Loop code Yaiwes/`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/Workflow%20Loop%20code%20Yaiwes) | 15.630 | Copia recortada + plan/estado + harness + capas L01–L06 ([PR #6](https://github.com/maxbry123-commits/router-universal-router-inteligente-/pull/6), sin fusionar) |
| [router · `chat router/📂 workflow Loops code Yaiwes/` @ 81e6c43eb6](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/81e6c43eb6edf7d7686f90ce54f7bdcb23b65bf5/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes) | 494 | Histórico; aplanado el 2026-10-08 en la raíz anterior |
| router `main` | — | Sin workflow; solo [`deepseek-harness-chat`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/deepseek-harness-chat) y [`chat frontend`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/chat%20frontend) |

Diferencias (sin agent_sources/frontend): 397 rutas comunes · 119 solo en `agentes` (archivos download, 3 capas, arquitectura, PLAN-4-OBJETIVOS) · 97 solo en el router (tests, contracts/adapters seals_motors, skills_schema DAG, orchestrator_*, runner, thinking_system). Plan Opus: [`Claude notas/PLAN-OPUS/`](https://github.com/maxbry123-commits/agentes/tree/main/Claude%20notas/PLAN-OPUS); loop: [`.github/workflows/plan-opus-loop.yml`](https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/plan-opus-loop.yml).
