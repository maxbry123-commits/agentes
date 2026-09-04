# ARQUITECTURA WORDFLOW — MODULAR (SISTEMA RUNTIME EN UN ARCHIVO)

**Repo:** maxbry123-commits/agentes  
**Fecha:** 2026-08-18  
**Plantilla:** misma modularidad que `PIPELINE/WORDFLOW_PROGRAMMING_MASTER.md` (partes A–P)  
**Alcance:** runtime entero (kernel + producto + loop + deploy), no solo C-19  
**Padre programming (NO borrar):** `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md`  
**Copilot share** `https://github.com/copilot/c/134eace7-b231-442d-934c-124ac2745e63` → login wall; este archivo sigue el MASTER in-repo.  
**C100 = NO.**

---

# PARTE A — QUÉ ES Y QUÉ NO ES

## A1. Definición

Wordflow en este repo es el **control plane determinista** que:

1. Recibe docs/code en reception (inbox).
2. Monta instancias kernel (`ficha.v2.json`, `llm_control: DENY`).
3. Orquesta programming vía `run_code_path` (C-19).
4. Itera trabajo vía `maxbry_loop` sin llamar vendors.
5. Publica solo con `token_ref`, sin force, HOLD en protegidos.
6. Exige 4 pasadas forenses antes de PASS.

## A2. Qué no es

- No es el Wordflow de WordPress ni el de Polo Club.
- No es un IDE.
- No es un LLM.
- No escribe el árbol git “solo”: apply es proceso GitHub autorizado.
- Tener archivo ≠ DONE.

## A3. Planos

| Plano | Path | Función |
|-------|------|--------|
| Inbox | `extensions/wordflow/reception/` | docs de entrada |
| Kernel surface | `extensions/wordflow_kernel/` | instancia, gateway, fail-closed |
| Execution | `extensions/wordflow/engine/` | C-19 + orquestación |
| Control | `extensions/wordflow/standards/` | PASS máquina |
| Loop | `extensions/maxbry_loop/` | iteración |
| Deploy | `extensions/github_deploy/` | plan_push / HOLD / token_ref |
| Policy | `PIPELINE/` | método, handoff, forense |

---

# PARTE B — ARQUITECTURA

```
Caller (agente / CI / Grok)
        |
        v
┌─────────────────────────────────────────┐
│ RECEPTION                               |
│  inbox md/py  → convert                 |
│  kernel LINK  → ingest + locate         |
│  handle_message / KernelExtMotor        |
└──────────────────┬──────────────────────┘
                   | next[] GAP: no llama compiler
                   v
┌─────────────────────────────────────────┐
│ KERNEL                                  |
│  ficha → spawn → preflight → pack       |
│  handle ping | ingest                   |
│  IntelligenceGateway (stub/router)      |
│  repo_truth Fake                        |
└──────────┬───────────────┬──────────────┘
           v               v
     maxbry_loop      wordflow.engine
     GatewayModel      run_code_path
     stage_hooks       standards/*
           |
           v
     github_deploy (Fake / HOLD)
```

Separación obligatoria:

```
CONTROL PLANE (decide BLOCK/PASS)
        ↓
EXECUTION PLANE (cognitive / loop)
        ↓
EXTERNAL APPLY (git)
        ↓
REPOSITORY TRUTH + RE-AUDIT
```

---

# PARTE C — PASO A PASO OPERATIVO

## C1. Reception

1. Subir artefacto a `extensions/wordflow/reception/`.
2. `handle_message({action:"ingest", payload: input_block})`  
   o `KernelExtMotor.dispatch("ingest", payload)`.
3. LINK importa `wordflow.reception.convert`.
4. Hoy: texto normalizado + `locate()`.  
   **No** coloca en fase (GAP).

## C2. Instancia kernel

5. `validate_ficha` → `bootstrap` / `spawn`.
6. `preflight` → `context_pack` → `knowledge_index`.
7. Engines solo stubs. Slots PLACEHOLDER.

## C3. Programming

8. ContextManifest + handoff_verified.
9. COPY-FIRST + Sheriff.
10. `run_code_path` con medidas reales.
11. FAIL → GapRegistry → fix → reaudit.

Detalle íntegro: `WORDFLOW_PROGRAMMING_MASTER.md` partes C–N.

## C4. Loop + deploy

12. Loop usa `GatewayModel`, nunca vendor.
13. Publish: `token_ref`, `plan_push` reject force, `protected` HOLD.
14. Fake E2E ≠ PASS C-19.

---

# PARTE D — APIS DE ENTRADA (CÓDIGO REAL)

## D1. `wordflow_kernel.handle_message`

`ping` | `echo` | `status` | `convert` | `ingest` | `reception`

## D2. `wordflow_kernel.reception.convert`

- `convert(input_block, use_sdpa=, branch=, max_context=)`
- `ingest` = convert + locate + `next` declarado
- `locate(kind)` → paths inbox/kernel/motor

## D3. `wordflow.engine.code_path_runner.run_code_path`

Ver MASTER programming Parte D. Defaults `context_verified=False`.

## D4. `maxbry_loop.model.GatewayModel.generate`

Solo `gateway.complete` / `execute`.

## D5. `github_deploy.plan_push` / `protected` / `token_ref`

force → reject; protegido → HOLD; secreto → ref.

---

# PARTE E — FORENSIC (DOS CAPAS)

## E1. Programming (autoridad de PASS de code)

`extensions/wordflow/standards/forensic_core.py`  
CORE-01..14 · FC-01..13 · 4 passes · 12 counters.

## E2. Repo/kernel

`wordflow_kernel/forensic.py`, `forensic_api.py`, `repo_truth.py`  
+ paquete `extensions/audit_forensic/` (segundo home).

PASS de programming **no** se hereda al repo entero.

Auditoría de este corte: `PIPELINE/FORENSE_PASADA_0{1-4}_*.md` → FAIL.

---

# PARTE F — RECEPTION (MÓDULO)

| Pieza | Path |
|-------|------|
| Inbox | `extensions/wordflow/reception/RECEPTION_agentes.md` |
| Template | `RECEPTION_TEMPLATE.md` |
| Links | `KNOWLEDGE_RECEPTION_LINKS.md` |
| Guía | `advanced_engineering_code_standard_guia_maestra.md` |
| Convert producto | `extensions/wordflow/reception/convert.py` |
| LINK kernel | `extensions/wordflow_kernel/reception/` |
| Motor | `extensions/wordflow/motors/kernel_ext/motor.py` |

**WIRED:** convert, LINK, handle, motor.  
**GAP:** ubicar fase + PLUGIN + llamar `input_compiler`.

---

# PARTE G — KERNEL (MÓDULO)

Ficha: `artifact_id: wordflow.kernel.extension`.  
Entry: `WordflowKernel`, `ForensicEngine`, `build_gateway_from_env`.

Grupos:

- ciclo de vida: ficha_loader, bootstrap_*, spawn, instance*, fail_closed, preflight
- contexto: context_pack, knowledge_index, memory, memory_slot
- IO: handle_message, reception, ui_gateway
- LLM: llm_control, gateway, engines stubs, slots PLACEHOLDER
- verdad: repo_truth, forensic*, crosscheck, gap_tasks
- orquestación: workflow (skeleton), stages, bridge, router_slot

---

# PARTE H — WORDFLOW PRODUCTO (MÓDULO)

Hot path: `code_path_runner` → quality_bar → goal_lock → cognitive → evidence → standards.

Resto engine: main_loop, orchestrator*, resources, github_*, council/expert, recovery, waves — **orquestación amplia**, no sustituye C-19.

Standards: lista en MASTER programming Parte O.

---

# PARTE I — LOOP + DEPLOY (MÓDULOS)

```
maxbry_loop.engine
  → stage_hooks
  → MockModel | GatewayModel
       → IntelligenceGateway

github_deploy
  → FakeGitDataPort default
  → plan_push (no force)
  → protected HOLD
  → token_ref
```

---

# PARTE J — CATÁLOGO DE CONEXIONES

Fuente viva: `extensions/wordflow/connect_catalog.json` v1.2.0  
Estados: WIRED | WIRED_STUB | STUB | PARTIAL | GAP.

No usar v1.1 (todo PARTIAL) como verdad.

`component_catalog.json` todavía dice `pending_mount` para kernel/loop → **DOC_CODE_MISMATCH** (gap).

---

# PARTE K — DETERMINISTIC FIRST

Si path/import/registro/test/hash se puede ver en git → no vale claim.  
LLM solo vía gateway. Kernel paths: DENY.

---

# PARTE L — PLAYBOOK

1. Leer reception inbox + este archivo + MASTER programming si la tarea es code.
2. COPY-FIRST en wordflow + wordflow_kernel.
3. Cablear; no generar paralelo.
4. Medir CORE; no auto-otorgar PASS.
5. Push GitHub. Sandbox ≠ DONE.
6. Re-audit 4 pasadas.

---

# PARTE M — AUDITORÍA 4 PASADAS (ESTE CORTE)

| Pass | File | Verdict |
|------|------|--------|
| 1 STRUCTURE | `FORENSE_PASADA_01_STRUCTURE.md` | FAIL |
| 2 CONNECTIVITY | `FORENSE_PASADA_02_CONNECTIVITY.md` | FAIL |
| 3 BEHAVIOR | `FORENSE_PASADA_03_BEHAVIOR.md` | FAIL |
| 4 CLOSURE | `FORENSE_PASADA_04_CIERRE.md` | FAIL |

---

# PARTE N — DEFINICIÓN MÁQUINA DE PASS (REPO)

```
PASS repo only if:
  4 forensic passes == True
  AND reception cadena OUTPUT_CONSUMED
  AND catalogs == tree
  AND dual-home consumidor único o GAP cerrado
  AND C-19 caller no Fake-as-PASS
  AND counters all_zero
else FAIL
```

Hoy: **FAIL**.

---

# PARTE O — ÍNDICE DE ARCHIVOS

```
extensions/wordflow/reception/
extensions/wordflow/engine/code_path_runner.py
extensions/wordflow/standards/forensic_core.py
extensions/wordflow/motors/kernel_ext/motor.py
extensions/wordflow/connect_catalog.json
extensions/wordflow_kernel/reception/
extensions/wordflow_kernel/handle_message.py
extensions/wordflow_kernel/gateway/intelligence.py
extensions/wordflow_kernel/ficha.v2.json
extensions/maxbry_loop/model.py
extensions/github_deploy/{plan_push,protected,token_ref}.py

PIPELINE/
  ARQUITECTURA_WORDFLOW_MODULAR.md          ← ESTE
  WORDFLOW_PROGRAMMING_MASTER.md            ← C-19
  ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md ← padre append-only
  ARQUITECTURA_01_MAPA_REPO.md
  ARQUITECTURA_02_KERNEL.md
  ARQUITECTURA_03_WORDFLOW.md
  ARQUITECTURA_04_CONEXIONES.md
  FORENSE_PASADA_01_STRUCTURE.md
  FORENSE_PASADA_02_CONNECTIVITY.md
  FORENSE_PASADA_03_BEHAVIOR.md
  FORENSE_PASADA_04_CIERRE.md
```

---

# PARTE P — CHECKLIST HUMANA

- [ ] Abrir reception inbox y kernel LINK
- [ ] Confirmar handle_message ingest
- [ ] Confirmar motor dispatch ingest
- [ ] Confirmar convert no coloca fase (gap consciente)
- [ ] Leer forensic_core + code_path_runner
- [ ] No marcar C100
- [ ] Inventariar dual homes antes de unificar
- [ ] Actualizar component_catalog (pending_mount)

**FIN.** Un archivo modular del runtime Wordflow. El detalle de programming C-19 sigue en el MASTER; este no lo duplica ni lo trunca.
