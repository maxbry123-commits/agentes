# ➡️📂 README arquitectura Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v3`  
Modo: `FAIL_CLOSED_LOOP`  
Arquitectura: modular, determinista por defecto, no monolítica.  
Estado actual: `ACTIVE_LOOP / PLAN30_T16_FICHA_CONTRACTS`.

## 1. Fuente de verdad y orden de lectura

1. `HANDOFF.md` — entrada operativa.
2. Este README — arquitectura actual y plan ejecutable.
3. README histórico `➡️📂 readme wordflow loop Yaiwes.md` — ledger literal/recuperación; no se sustituye.
4. `Crazy Wall Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md` — trazabilidad forense source→SHA→destino→evidencia.
5. `STATE.json` — estado estructurado.
6. `CHECKPOINT.json` — punto recuperable.
7. `RECOVERY-PATCH.md` — restauración.
8. `BITACORA-CRAZY-WALL.md` — eventos humanos/auditoría.
9. `PLAN-LOOP-30-TAREAS.md` — cola T01→T30.
10. Evidencias de cada nodo antes de mutar.

Si dos anclas divergen: `GAP`; no se inventa una reconciliación.

## 2. Objetivo final

`documentos/proyectos YAIWES → requisitos trazables → tareas de programación → reutilización/generación de código → Ficha/contrato → adapter/plugin → registry → agente/engine → ejecución → verificación/repair → auditoría → STATE/CHECKPOINT/evidence → E2E verificable`.

El LOOP es el motor persistente que mantiene este flujo hasta cierre real; no sustituye la arquitectura.

## 3. Cadena LOOP por nodo

`INPUT literal → GOALS 12/12 → prioridades → plan → cola 1×1 → delta autorizado → verify/refute → GAP? research ≥10 vías/hasta 20 soluciones → StrategyDelta distinto → retry/continue safe task → auditor instrucciones ×3 → Council12 → 12 goals salida → 3 refutaciones → cross-check global → CODA → verify_final → persistencia`.

Reglas:
- `REUSE > COPY/MOVE > PATCH QUIRÚRGICO > ADAPTER > GENERATE`.
- Nunca PASS por presencia de archivo.
- Checks reales potencialmente inestables: repetir hasta 10×.
- Check puro/determinista: 1× basta.
- No repetir un delta/estrategia ya fallido.
- Un bloqueo se registra como 🚩/GAP; se continúa solo con otra tarea segura que no viole dependencias.

## 4. Arquitectura por capas

### Capa A — Input / documentos / Mission + Goal Lock
`INPUT literal → schema → MissionContract → GoalLock → provenance de fuente`.

### Capa B — DSL / DAG / contratos
`requisito → DSL → DAG → dependencias → Ficha/contrato → criterios de éxito/fallo`.

### Capa C — Sheriff / gobierno
`contract → Sheriff → Validator → guards → policy → autorización de delta`.

### Capa D — Kernel determinista
`event loop → scheduler → runtime → registry/router → state`.
Kernel/control: `0% LLM`.

### Capa E — Execution orchestration
`cola 1×1 / DAG ready → execution manifest → capability select → dispatcher → checkpoint/recovery`.

### Capa F — Enchufe universal
`Ficha Contract v2 → adapter/plugin → Capability Registry → loader → health → evidence`.

### Capa G — Code programming engine / agentes
`task contract → engine binding → OpenCode execute → OpenHands review/repair → Claude/Mimo wiring review → auditors/council`.

### Capa H — Reasoning on demand
`problema determinista? → algoritmo/capability code → si insuficiente: reasoning/model por contrato`.

### Capa I — State/events/durability
`input_hash + node_id + checkpoint + attempt + strategy/delta → state/event store → recovery/idempotencia`.

### Capa J — Memory/storage/tools/models
`Graphiti/Grapify/SQL/HF storage + model APIs secret_ref + budgets/timeouts/fallback`.

### Capa K — Research/evidence/audit
`fuente→URL/SHA → evidence packet → tests → refutaciones → cross-check → verify_final`.

### Capa L — Output/E2E
`documento→tarea→code→plugin→registry→ejecución→repair→audit→state/evidence→salida`.

## 5. Estructura física objetivo

- `Agente Yaiwes principal/code-programming-engine/`
- `Agente Yaiwes principal/kernel-principal/`
- `Agente Yaiwes principal/execution-orchestration/`
- `Agente Yaiwes principal/control-governance/`
- `Agente Yaiwes principal/state-events-durability/`
- `Agente Yaiwes principal/execution-engine-pool/`
- `Agente Yaiwes principal/reasoning-kernel/`
- `Agente Yaiwes principal/research-evidence/`
- `Agente Yaiwes principal/tools-models-memory-knowledge/`
- `Agente Yaiwes principal/tests/`

Separación obligatoria cuando aplique: `contracts/ adapters/ plugins/ registry/ loader/ guards/ tests/`.

## 6. Objetivos O01–O11

| Objetivo | Definición | Estado |
|---|---|---|
| O01 | LOOP/watchdog + checkpoint/STATE/Crazy Wall/recovery | VERIFIED_CLOSED |
| O02 | investigación de código fuente | VERIFIED_CLOSED |
| O03 | copy/reuse por SHA | VERIFIED_CLOSED |
| O04 | Ficha→adapter/plugin→registry→health→evidence | IN_PROGRESS_T16 |
| O05 | verificación documental 5 pasadas | PENDING |
| O06 | task contracts de agentes | PENDING |
| O07 | integrar agentes/council | PENDING |
| O08 | HF/3 procesadores | PENDING |
| O09 | Graphiti/Grapify/SQL/HF storage | PENDING |
| O10 | APIs/modelos por secret_ref | PENDING |
| O11 | tests/auditoría/E2E | PENDING |

## 7. Plan completo T01→T30

| # | Objetivo | Tarea | Estado |
|---|---|---|---|
| 01 | O02 | Reconciliar anclas/objetivo/roles | VERIFIED_CLOSED |
| 02 | O02 | Inventario de código candidato | VERIFIED_CLOSED |
| 03 | O02 | Verificar runner 1×1 | VERIFIED_CLOSED |
| 04 | O02 | Verificar pause/resume | VERIFIED_CLOSED |
| 05 | O02 | Verificar identidad/reinyección | VERIFIED_CLOSED |
| 06 | O02 | Verificar input_hash/node/attempt/checkpoint | VERIFIED_CLOSED |
| 07 | O02 | Verificar StrategyDelta/failure-memory | VERIFIED_CLOSED |
| 08 | O02 | Mapear candidatos a destino | VERIFIED_CLOSED |
| 09 | O02 | Provenance/compatibilidad/imports | VERIFIED_CLOSED |
| 10 | O03 | Integrar cola 1×1 | VERIFIED_CLOSED |
| 11 | O03 | Integrar pause/resume | VERIFIED_CLOSED |
| 12 | O03 | Integrar identidad/checkpoint | VERIFIED_CLOSED |
| 13 | O03 | Integrar input_hash/node_state | VERIFIED_CLOSED |
| 14 | O03 | Integrar StrategyDelta guard | VERIFIED_CLOSED |
| 15 | O03 | Patches quirúrgicos + tests | VERIFIED_CLOSED |
| 16 | O04 | Ficha Contract v2 de capacidades integradas | EN_CURSO |
| 17 | O04 | Cablear adapters/plugins a registry | PENDIENTE |
| 18 | O04 | Health/evidence/fail-closed | PENDIENTE |
| 19 | O05 | 5 pasadas cross-check documentos/arquitectura/code/contracts/tests | PENDIENTE |
| 20 | O06 | Contratos de tareas de agentes | PENDIENTE |
| 21 | O07 | Cablear OpenCode | PENDIENTE |
| 22 | O07 | Cablear OpenHands | PENDIENTE |
| 23 | O07 | Cablear Claude Code + Mimo Code | PENDIENTE |
| 24 | O07 | Auditores + Council12 + embudo | PENDIENTE |
| 25 | O08 | HF/3 procesadores | PENDIENTE |
| 26 | O09 | Graphiti/Grapify/SQL/HF storage | PENDIENTE |
| 27 | O10 | APIs/modelos secret_ref | PENDIENTE |
| 28 | O11 | Tests unitarios/integración/E2E | PENDIENTE |
| 29 | O11 | estabilidad ×10 + recovery/idempotencia | PENDIENTE |
| 30 | O11 | auditoría final + verify_final | PENDIENTE |

Estado medido del PLAN30: `15/30 VERIFIED_CLOSED = 50%`; T16 en curso.

## 8. Componentes ya integrados

1. **Serial dispatch 1×1**: `runner.py` blob `daa32a5d6dfeb0d21a975b8a5b8384d68a8aa08e` → `serial_dispatch.py` blob `77017b70239cedcce26f1df4a076272572f0927b`.
2. **Pause/resume**: `runcontrol.py` blob `2c6aff845c97b600d4b3851b5ee9a6e0ee23defb` → `run_control_adapter.py` blob `aa4f62571044d873e3969bc7f747bfc83e3047a6`.
3. **Resume identity/input hash**: Elspeth commit `720d441336434d227c2a00caaac100db48a07d5c` → `resume_identity.py` blob `dc440bd180194d6cef2bf1b38b1ef1b85138ef0b`.
4. **StrategyDelta guard**: indexer-core commit `efcfcb20f09117504b00f682ada1bfff2b04b649` → `strategy_delta_guard.py` blob `46efd22bd7b5ac3c22cc5ca084788d46b4b5b16b`.
5. **Test T10–T15**: `test_plan30_loop_runtime.py` blob `e1b1e3a4e4ca79e5dee00d5676a6038c6426bc31`; `5 passed in 0.06s`.

Trazabilidad source URL/SHA/destino completa:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md

## 9. T16 — Ficha Contract v2

Validador canónico:
https://github.com/maxbry123-commits/agentes/blob/37bef3a8a8f6dadca067638b8ea0c32995fc1d63/skills/research-download-chain/assets/plugin-bus/ficha_contract_v2.py

Commit `37bef3a8a8f6dadca067638b8ea0c32995fc1d63`; blob `b27f14b4d64f77bccf53a893c49b6f20bd58e745`.

Fichas existentes:
- `ficha.serial_dispatch.v2.json` blob `bc885059ed0a97f73aad02572853d1b0a4f8117d`.
- `ficha.run_control.v2.json` blob `7fdb64b7a21fe51c278dcc907b09eb800f2a2770`.
- `ficha.resume_identity.v2.json` blob `4ce82a32faa939177dd22603f097402e9b9e6ed9`.
- `ficha.strategy_delta.v2.json` blob `44aeb5cb48db6d42499bc940e47e912942d7fd40`.

GAP actual: falta ejecución exacta del validador canónico 4/4 + stdout/veredicto + cross-check. T17 no se abre antes.

## 10. Agentes / Council

Council objetivo: Claude Code CLI, OpenClaw, Hermes, Codex, Aider, OpenCode, OpenHands, Mimo Code, Muse/Glimmer Code, Kimi K Code CLI, Smolange y 12.º agente solo con evidencia.

Roles:
- OpenCode: escribe/ejecuta código.
- OpenHands: review/repair.
- Claude Code + Mimo Code: review flow/execution/wiring.
- Auditores: Claude Code, Mimo Code, Codex, Smolange, Hermes, OpenClaw.
- Embudo final: OpenHands + OpenCode.

T21–T24 no están cerradas: presencia en repo no equivale a binding real.

## 11. Skills y adquisición OSS

Si falta componente OSS:
1. investigar GitHub/repos oficiales hasta 10 pasadas;
2. registrar URL/commit/SHA/licencia/destino;
3. usar exclusivamente el skill de descarga/extracción autorizado cuando haga falta adquisición:
https://github.com/maxbry123-commits/agentes/tree/c789e5fe635e220230ffc759d86dc3bbb8e261d4/skills/skills%20Github%20acci%C3%B3n
4. no LFS;
5. no reactivar workflows antiguos;
6. validar destino + `verify_final`.

## 12. Persistencia y evidencia

Cada cambio real debe reconciliar según alcance:
`BITACORA + STATE.json + CHECKPOINT.json + PLAN + RECOVERY + README/HANDOFF`.

Registro mínimo:
`node_id + input_hash + checkpoint_id + attempt_id + strategy_id + delta_hash + cause + source_url + source_sha + destination + test/log + outcome`.

Guard:
`failed delta/strategy → REJECT`; siguiente intento debe ser materialmente distinto.

## 13. Cierre global

Solo `VERIFIED_CLOSED` cuando el flujo completo demuestra:

`documento → requisito → tarea → agente/engine → código → repair → Ficha/plugin/registry → ejecución real → auditoría → test independiente → STATE/CHECKPOINT/evidence → output`.

Si falta una prueba real: `GAP/INCONCLUSIVE`, nunca falso PASS.

## 14. Próximo nodo

`PLAN30_T16_FICHA_CONTRACTS` → ejecutar el validador Ficha Contract v2 canónico contra las cuatro Fichas; si 4/4 PASS + cross-check, cerrar T16 y continuar T17.