# ARQUITECTURA 01 — MAPA DEL REPO (GitHub = verdad)

**Repo:** maxbry123-commits/agentes  
**Ref auditada:** `main` tree SHA `17efb7a9cb6ac9a107a9986e144a2724af24a4cc`  
**C100 = NO. V1 100% = NO.**  
Este archivo describe dónde está cada cosa. No es un claim de completitud.

---

## 1. Respuesta directa

### ¿Dónde está el Wordflow de code?

Paquete producto / motor de programación:

```
https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow
```

Núcleo operativo (lo que corre un ciclo):

| Parte | Path |
|-------|------|
| Engine (ciclo, evidencia, compile, publish) | `extensions/wordflow/engine/` |
| Reception inbox (docs → convert) | `extensions/wordflow/reception/` |
| Cuentas / credential_ref | `extensions/wordflow/accounts/` |
| Connectores GitHub externos | `extensions/wordflow/connectors/` |
| Motores SEND/CALL/DOWNLOAD + KernelExt | `extensions/wordflow/motors/` |
| Estándares / sheriff / copy-first | `extensions/wordflow/standards/` |
| Schemas JSON | `extensions/wordflow/schemas/` |
| Tests | `extensions/wordflow/tests/` |
| Ficha enchufe | `extensions/wordflow/ficha.v2.json` |
| Codegen DAG | `extensions/wordflow/codegen/dag.py` |

Hot path histórico (no reescrito en V1 Fake): `extensions/wordflow/engine/code_path_runner.py` (17742 B).

### ¿Dónde está la extensión kernel?

```
https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow_kernel
```

Ficha: `extensions/wordflow_kernel/ficha.v2.json`  
artifact_id: `wordflow.kernel.extension`  
mount_mode: `extension`  
llm_control: `DENY`

Orquestador: `extensions/wordflow_kernel/workflow.py` → clase `WordflowKernel`.

### Reception: ¿debe ser parte del kernel?

**Sí como superficie. No como inbox.**

| Rol | Path real |
|-----|-----------|
| Inbox + convert implementación | `extensions/wordflow/reception/` |
| LINK kernel (convert/locate/ingest) | `extensions/wordflow_kernel/reception/` |
| Motor que conoce los links | `extensions/wordflow/motors/kernel_ext/motor.py` |

Inbox público que pediste revisar:
https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow/reception

Antes de este commit **no existía** `extensions/wordflow_kernel/reception/` (búsqueda code = 0 hits). Eso era el hueco.

---

## 2. Las 10 extensiones (carpeta `extensions/`)

| Extensión | Qué es | Se conecta a |
|-----------|--------|--------------|
| `wordflow` | Producto: loop 12, compile, evidence, reception, motors | kernel, loop, deploy |
| `wordflow_kernel` | Plano de control determinista: instancia, ficha, gateway stub, repo_truth | wordflow, maxbry_loop, github_deploy |
| `maxbry_loop` | Loop de etapas + GatewayModel + goal_bridge | kernel.gateway, wordflow.engine.loop_bridge |
| `github_deploy` | Publish Fake/plan, protected HOLD, token_ref | wordflow.accounts, wordflow.engine.publish |
| `github_publisher` | Publisher schema/bridge (capa más vieja) | github_deploy |
| `audit_forensic` | Motor forense independiente (matrices, verdict) | kernel.forensic / wordflow.claim_validator |
| `source_evolution` | Acquire / pin / license de fuentes | wordflow.engine.acquire_12 |
| `project_bootstrap` | KTP + microflows + resource_brain | kernel bootstrap |
| `knowledge` | Registry/runtime de conocimiento (otro paquete) | kernel.knowledge_index |
| `adapters` | Contratos de adaptadores | kernel slots |

---

## 3. Árbol Wordflow (producto) — directorios

```
extensions/wordflow/
  accounts/          registry, resolver, require (T38)
  codegen/           dag.py (EXTRA CG)
  connectors/        github_external + yaml cuentas
  context/           builder.py
  contracts/         C_WF_INPUT, C_WF_LOOP
  docs_templates/
  engine/            ~90 módulos del ciclo
    engines/         fake_engine.py
    ports/           memory_port, planning_port
  motors/
    send/ call/ download/ kernel_ext/
  planner/           mission_planner.py
  policies/          engine_attach, sheriff, sentinel
  reception/         INBOX + convert.py   <— aquí el link que pediste
  schemas/           ~35 JSON schemas
  standards/         copy_first, sheriff, forensic_*
  state/             blackboard, ledger
  store/             yaml catálogos
  tests/             1 test por módulo aprox.
  ficha.v2.json
  manifest.yaml
```

## 4. Árbol Kernel — directorios

```
extensions/wordflow_kernel/
  bootstrap_v1.py bootstrap_multi.py bootstrap_fake.py spawn.py
  ficha_loader.py fail_closed.py preflight.py
  context_pack.py knowledge_index.py memory.py
  engine_registry.py handle_message.py llm_control.py
  repo_truth.py gap_tasks.py workflow.py instance.py instance_store.py
  forensic.py forensic_api.py crosscheck.py
  gateway/           intelligence.py router_http.py
  engines/           port.py + hermes_stub + openclaw_stub
  resources/         registry, loaders, validate_resource
  router_slot/       pipeline T37
  memory_slot/       adapter
  slots/             kimi_minimax PLACEHOLDER
  stages/            engine + default_handlers + kernel_hook
  bridge/            gap_bridge goal_bridge
  ui_gateway/        plugin
  reception/         LINK (este commit)
  tests/
```

## 5. Docs PIPELINE vs code

Hay decenas de archivos `PIPELINE/*.md` (método, handoff, masters).  
**No son el runtime.** El runtime es solo `extensions/`.

Padre append-only (no truncar): `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md`

Esta serie de 4 archivos es el mapa de code auditado, no un reemplazo del padre.

## 6. Lo que NO está conectado (huecos honestos)

- `handle_message` no era la puerta de reception hasta este commit.
- `WordflowKernel.audit_to_plan` sigue siendo skeleton (pide inject VK-02/VK-03).
- Engines OpenClaw/Hermes = stubs.
- IntelligenceGateway.complete = stub (sin vendor LLM).
- `run_code_path` real no reescrito; E2E V1 es Fake.
- T41–T49 docs HANDOFF pendientes.
- Reception convert es normalizador de texto, no un colocador de archivos en ruta de fase.
