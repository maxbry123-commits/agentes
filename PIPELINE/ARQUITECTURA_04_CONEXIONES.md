# ARQUITECTURA 04 — CONEXIONES (qué está cableado de verdad)

Auditoría sobre tree `17efb7a9` + commit reception LINK.  
Leyenda: **WIRED** = import/llamada existe. **STUB** = firma presente, impl Fake/vacía. **GAP** = doc lo pide, code no lo hace.

---

## 1. Diagrama de paquetes

```
                    [inbox .md/.py]
                            |
                            v
         wordflow/reception/convert.py          WORD FLOW PRODUCT
                            ^
                            | import fail-closed
                            |
         wordflow_kernel/reception/             KERNEL LINK  (WIRED este commit)
                            |
                            v
         wordflow_kernel/handle_message         T21 + convert/ingest
                            |
         +------------------+------------------+
         v                  v                  v
   ficha/spawn/       IntelligenceGateway   repo_truth Fake
   preflight/pack         STUB                    |
         |                  ^                     v
         |                  |              github_deploy
         |           maxbry_loop.model      plan_push / HOLD
         |           stage_hooks            token_ref
         v                  |
   wordflow/engine    loop_bridge Fake
   code_path_runner         |
   input_compiler     WordflowKernel.audit_to_plan  GAP (skeleton)
```

## 2. Tabla cruzada

| Desde | Hacia | Estado | Evidencia |
|-------|-------|--------|-----------|
| `wordflow_kernel.reception` | `wordflow.reception.convert` | WIRED | import en convert.py kernel |
| `handle_message` | `reception.ingest` | WIRED | actions convert/ingest/reception |
| `KernelExtMotor` | links reception | WIRED | `motors/kernel_ext/motor.py` |
| `KernelExtMotor` | `wordflow_kernel.reception` | GAP | motor no importa el LINK nuevo |
| `maxbry_loop.model` | `gateway.intelligence` | WIRED/STUB | generate → complete stub |
| `maxbry_loop` | `wordflow.engine.loop_bridge` | WIRED/STUB | T14 Fake |
| `maxbry_loop.goal_bridge` | kernel/wordflow goals | WIRED | 1237 B |
| `wordflow.engine` | `github_deploy` | PARCIAL | publish_path + plan_push |
| `github_deploy.plan_push` | force_push | WIRED reject | T32 |
| `github_deploy.protected` | HOLD | WIRED | T33 |
| `wordflow.accounts.require` | token_ref | WIRED | T38/T39 |
| `engine_registry` | openclaw/hermes | STUB | engines/*_stub.py |
| `resources/*` | HF fetch | STUB | PLAN_ONLY |
| `router_slot.pipeline` | discover/map/select/load | STUB | T37 |
| `slots/kimi_minimax` | fusion runtime | PLACEHOLDER | fusion:false |
| `WordflowKernel.audit_to_plan` | forensic+compiler | GAP | RuntimeError sin inject |
| `reception.convert` | ubicar code en fase + PLUGIN | GAP | solo normaliza texto |
| `knowledge` ext | `knowledge_index` | PARCIAL | paquetes distintos |
| `audit_forensic` | `wordflow.claim_validator` | PARCIAL | dos motores forenses |
| `source_evolution` | `acquire_12` | PARCIAL | mismos conceptos, dos homes |
| `project_bootstrap` | kernel bootstrap | PARCIAL | KTP separado |

## 3. Flujo reception → kernel → engine (objetivo vs real)

**Inbox dice:** leo literal → completo gaps → ubico code ruta exacta → PLUGIN.

**Code hoy:**
1. Usuario deja archivo en `extensions/wordflow/reception/`.
2. Alguien llama `convert({raw_text})` o `handle_message({action:"ingest"})`.
3. Sale texto normalizado + flags sdpa/mcr.
4. `ingest` adjunta `locate()` (paths). No escribe archivos de fase.
5. `next` declarado: `input_compiler`, `context_pack`. No hay llamada automática.

Eso es el hueco de conexión reception→fase. El LINK al kernel ya existe.

## 4. Fake vs real (no mezclar)

| Pieza | Modo publicado |
|-------|----------------|
| loop_bridge | Fake etapas + evidence |
| RepoTruth | FakeRepoTruth |
| GitDataPort | Fake |
| IntelligenceGateway.complete | stub |
| Engines | stubs |
| HF | plan_only |
| Kimi/Minimax | PLACEHOLDER |
| code_path_runner | code grande histórico; E2E V1 no lo reescribe |

## 5. Duplicaciones a no ignorar

Hay dos hogares para varias ideas. No unificar en este commit (append-only).

| Concepto | Home A | Home B |
|----------|--------|--------|
| Reception | wordflow/reception | wordflow_kernel/reception (LINK) |
| Goal bridge | maxbry_loop/goal_bridge.py | wordflow_kernel/bridge/goal_bridge.py |
| Stage hooks | maxbry_loop/stage_hooks.py | wordflow_kernel/stages/ |
| Forense | audit_forensic/ | wordflow_kernel/forensic* + wordflow/claim_validator |
| Publisher | wordflow/engine/github_publisher.py | extensions/github_publisher/ |
| Knowledge | extensions/knowledge/ | wordflow_kernel/knowledge_index.py |

## 6. Índice de los 4 archivos

1. `PIPELINE/ARQUITECTURA_01_MAPA_REPO.md` — dónde está cada extensión
2. `PIPELINE/ARQUITECTURA_02_KERNEL.md` — kernel módulo a módulo
3. `PIPELINE/ARQUITECTURA_03_WORDFLOW.md` — producto engine + reception
4. Este archivo — qué está cableado / stub / gap

Padre histórico (no borrar): `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md`
