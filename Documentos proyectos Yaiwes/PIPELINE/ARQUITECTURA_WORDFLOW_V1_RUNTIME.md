# ARQUITECTURA WORDFLOW V1 — runtime real (code publicado)
**Fecha:** 2026-08-18
**Método:** V4 (2 pasos · forense al cierre)
**NO** sustituye `ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md` (append-only).
**C100 = NO. V1 100% = NO.**

## 1. Vista en capas

```
                    UI / handle_message (T21 ping)
                              |
                    preflight (T15) · fail_closed (T12)
                              |
         +--------------------+--------------------+
         v                    v                    v
   KERNEL                 LOOP                  DEPLOY
   wordflow_kernel        maxbry_loop           github_deploy
   ficha · spawn          stage_hooks T25       FakeGitDataPort
   bootstrap · pack       GatewayModel T27      plan_push T32
   memory · engines       goal_bridge T28       protected HOLD T33
   knowledge · resources  gaps enqueue T29      token_ref T39
         |                    |                    |
         +------------+-------+--------+-----------+
                      v                v
              IntelligenceGateway   RepoTruth Fake
                   T26 stub              T31
                      |
              llm_control ban T22
```

## 2. Flujo canónico Fake (T13–T14)

bootstrap instancia → GoalLock dry → code_path dry → loop_bridge Fake → publish Fake  
Sin red, sin vendor LLM.

## 3. Contratos de code (T10–T40)

| Zona | Módulos | Rol |
|------|---------|-----|
| Ficha | `ficha_loader` T10 | load/validate/register |
| Instancia | `bootstrap_multi` T11 · `spawn` | multi-id |
| Cierre | `fail_closed` T12 | ficha inválida |
| Fake E2E | `bootstrap_fake` T13 · `loop_bridge` T14 | etapas + evidence |
| Preflight | `preflight` T15 | checks mínimos |
| Contexto | `context_pack` T16 | hash por instancia |
| Índice | `knowledge_index` T17 | sin embeddings |
| Recursos | `resources/registry` T18 · `validate_resource` T35 | register/validate |
| Memoria | `memory` T19 | get/set |
| Engines | `engine_registry` T20 · slot T40 | attach policy · PLACEHOLDER |
| Mensajes | `handle_message` T21 | ping/echo/status |
| Ban LLM | `llm_control` T22 | scan paths |
| CI | `wordflow_smoke.yml` T23 | kernel/loop/deploy Fake |
| Loop | `stage_hooks` T25 · `model` T27 · `goal_bridge` T28 | hooks/gateway/goals |
| Gaps | `gap_tasks` T29 | enqueue fake |
| Forense code | `claim_validator` T30 · `write_evidence` T34 | claim≠evidence |
| Verdad repo | `repo_truth` T31 | FakeRepoTruth |
| Publish | `plan_push` T32 · `protected` T33 · `token_ref` T39 · `accounts/require` T38 | force/HOLD/ref |
| HF plan | `build_plan_only` T36 | PLAN_ONLY |
| Router | `router_slot/pipeline` T37 | 4 stubs |
| Recepción | `reception/convert` T2–T2.3 | sdpa/mcr/max_context |
| CG | `codegen/dag` | texto→DAG |

## 4. Reglas de frontera

- LLM solo vía `IntelligenceGateway` / `GatewayModel` (stub).
- Publish: `token_ref`, nunca PAT; `force` prohibido; paths protegidos → HOLD.
- Kimi/Minimax: ficha `PLACEHOLDER`, `fusion: false`.
- GitHub = verdad. Sandbox ≠ DONE.

## 5. Huecos honestos

- HANDOFF T15–T21 (AccountResolver/HF/acquire/UI GoalLock) ≠ firmas PATCH ya publicadas.
- `run_code_path` real (hot path) no se reescribió; el E2E V1 es Fake.
- T41–T49 docs pendientes.

## 6. Padre
Arquitectura histórica (NO borrar): `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md`
