# HANDOFF V1 — T10→T49 + EXTRAS (autocontenido)
**Repo verdad:** https://github.com/maxbry123-commits/agentes  
**Fecha handoff:** 2026-08-18  
**Para:** otra instancia Grok / agente  
**Regla:** GitHub = verdad · NO sandbox como almacenamiento final · 1 tarea = 1 salida = commit  

---

## 0. Arranque obligatorio (lee esto primero)

### Método de salida (3 pasos por tarea)
1. **PASO 1 SANDBOX_BUILD** — escribe/adapta code en local, prueba, confirma "Sandbox usado: SÍ". Sin enlaces GH.
2. **PASO 2 GITHUB_PUBLISH** — sube archivos, da **solo enlaces** que abren el archivo, re-lee remoto.
3. **PASO 3 FORENSIC** — si hubo code: auditoría forense; gaps → FIX + re-paso 2; sin gaps → DONE.

### Prioridad de code
**COPY/MOVE → LINK → PATCH → ADAPT → GENERATE (último).**  
Nunca reescribir de cero si el archivo ya existe en el path indicado.

### Formato CONTROL DE TRABAJO (cada salida)
```
1. TOTAL V1: 49
2. TERMINADAS: (número)
3. SIGUIENTE: Sxx/Txx
4. ENLACES GH (solo paso 2):
5. CONFIRMACIÓN: GitHub=verdad · sandbox≠DONE
```

### Estado al entregar este handoff
| ID | Estado |
|----|--------|
| T01–T09 | **DONE** |
| AUDIT-5 S01–S05 | **DONE** |
| T06 connect_catalog + list_connections | **DONE** |
| T07 WordflowInstance + registry | **DONE** |
| T08 InstanceStore state.json | **DONE** |
| T09 spawn_wordflow | **DONE** |
| **Siguiente a ejecutar** | **T10** |

Paths ya hechos (NO rehacer salvo bug):
- `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md`
- `PIPELINE/ROOT_MAP_IDS.md`
- `PIPELINE/XRAY_SEED_STATUS.md`
- `PIPELINE/SPEC_HTML_MAPA_MENTAL.md`
- `PIPELINE/AUDIT5_S01_S05.md`
- `extensions/wordflow/connect_catalog.json`
- `extensions/wordflow/engine/list_connections.py`
- `extensions/wordflow_kernel/instance.py`
- `extensions/wordflow_kernel/instance_store.py`
- `extensions/wordflow_kernel/spawn.py`
- `README.md` (sección multi-instancia T02)

### Prohibido en V1
- Fusión Minimax/Kimi completa
- Claim C100/T49 sin T13–T48 PASS
- Borrar arquitectura / append-only en docs maestros
- Regenerar archivos grandes desde LLM si ya existen

---

## 1. FICHAS T10–T12 (Kernel)

### T10 — Extension loader ficha.v2
**Objetivo:** Cargar una ficha `ficha.v2.json` y registrar la capability en el kernel.  
**Función:** Enchufar extensiones sin reescribir el kernel.

**Paths:**
- Existe: `extensions/wordflow_kernel/ficha_loader.py`, `extensions/wordflow_kernel/ficha.v2.json`, `extensions/wordflow/ficha.v2.json`
- Editar/crear: `extensions/wordflow_kernel/ficha_loader.py` (ADAPT)

**Programar exactamente:**
1. Función `load_ficha(path: Path) -> dict` — lee JSON, valida claves mínimas: `id` o `name`, `version`.
2. Función `validate_ficha(data: dict) -> list[str]` — devuelve lista de errores (vacía = OK).
3. Función `register_capability(ficha: dict, registry: dict | None) -> dict` — mete capability en registry en memoria `{ficha_id: ficha}`.
4. Si ficha inválida → no registrar; lanzar `ValueError` o devolver errores (fail hacia T12).
5. `__main__` smoke: load ficha del propio paquete kernel → print id + OK.

**Criterio DONE:** smoke OK + archivo en GH + no inventa campos mágicos.  
**NO hacer:** UI, deploy, LLM calls.

### T11 — Bootstrap multi-instance aware
**Objetivo:** Arranque que conoce `instance_id` (default `v1`).  
**Función:** Una sola entrada de bootstrap crea/usa instancia default sin romper multi-instancia.

**Paths:**
- Existe: `extensions/wordflow_kernel/bootstrap_v1.py`, `bootstrap_multi.py`
- ADAPT: `bootstrap_multi.py` y/o `bootstrap_v1.py`

**Programar exactamente:**
1. `bootstrap(instance_id: str = "v1", name: str = "default") -> WordflowInstance`
2. Usa `PersistentRegistry` + `spawn_wordflow` o `create` si no existe.
3. Si ya existe en store → `load_into_memory`.
4. Devuelve la instancia activa.
5. Smoke: bootstrap dos ids distintos → dos instancias.

**Criterio DONE:** test local 2 instance_ids + GH.  
**NO hacer:** cableado C100 completo (T13+).

### T12 — Fail_closed ficha inválida
**Objetivo:** Si la ficha es inválida o política lo exige, el sistema **cierra** (no sigue como si fuera OK).  
**Función:** Evitar arranques “verdes” con config rota.

**Paths:**
- Existe: `extensions/wordflow_kernel/fail_closed.py`
- ADAPT ese archivo

**Programar exactamente:**
1. `fail_closed(reason: str) -> None` — registra reason y lanza excepción tipada `FailClosedError`.
2. `assert_ficha_or_fail(ficha: dict) -> dict` — usa validate de T10; si errores → fail_closed.
3. Hook opcional: `llm_control` si aparece en ficha y valor no DENY donde se exija DENY → fail_closed.
4. Smoke: ficha sin id → debe fallar (assert raises).

**Criterio DONE:** test negativo + GH.  
**NO hacer:** ban LLM en todos los paths (eso es T22).

---

## 2. FICHAS T13–T24 (C100 — VERIFY/WIRE, no inventar de cero)

**Regla C100:** si el módulo existe → WIRE + test Fake; solo GENERATE si MISSING real.

### T13 — Bootstrap canónico GoalLock→loop→code_path→deploy Fake
**Objetivo:** Un camino Fake de punta a punta sin vendor LLM.  
**Paths clave:** `extensions/wordflow/engine/goal_lock.py`, `code_path_runner.py`, `main_loop.py`, `extensions/maxbry_loop/`, `extensions/github_deploy/`  
**Programar:** función `run_bootstrap_fake(instance_id="v1")` que: (1) bootstrap instancia (2) GoalLock set goal fake (3) invoca code_path_runner en modo dry/fake (4) deploy Fake no-op.  
**DONE:** un test/script offline imprime PASS etapas. **NO:** publish real.

### T14 — code_path_runner → maxbry_loop bridge → publish Fake
**Objetivo:** Puente runner↔loop con publish simulado.  
**Paths:** `code_path_runner.py`, `loop_bridge.py`, `maxbry_loop/engine.py`, `publish_path.py`  
**Programar:** `bridge_run_fake(payload) -> dict` evidence; publish_path modo Fake.  
**DONE:** evidencia dict con keys status/stages. **NO:** red real.

### T15 — publish_path + AccountResolver multi-account
**Objetivo:** Publish exige resolver cuenta, no token hardcode.  
**Paths:** `extensions/wordflow/accounts/`, `publish_path.py`, `engine/github_publisher.py`  
**Programar:** `resolve_account(account_id) -> dict`; publish_path falla si no hay account_id.  
**DONE:** test sin account → error; con Fake account → OK. **NO:** token en logs.

### T16 — HF ResourceIndex dry-run
**Objetivo:** Índice de skills/datasets/adapters en seco.  
**Paths:** `resource_catalog.py`, `resource_runtime.py`, `hf_index.py`  
**Programar:** `plan_index(resources: list) -> plan` sin descargar.  
**DONE:** plan JSON/list. **NO:** fetch HF real.

### T17 — Acquire recipe dry-run
**Objetivo:** verify/build/promote simulado.  
**Paths:** `acquire_12.py`  
**Programar:** `acquire_dry_run(recipe) -> stages dict`.  
**DONE:** stages include verify/build/promote keys. **NO:** install real.

### T18 — connect_catalog en kernel
**Objetivo:** Kernel puede listar connections (T06 ya tiene API wordflow).  
**Paths:** `list_connections.py`, `wordflow_kernel/` (import o thin wrapper)  
**Programar:** `kernel_list_connections()` que reexporta/usa catalog T06.  
**DONE:** count >= 1. **NO:** mesh runtime completo.

### T19 — MemoryGateway unificado en bootstrap
**Objetivo:** Un solo punto de memoria en bootstrap.  
**Paths:** `memory.py`, `memory_slot/`, bootstrap  
**Programar:** `MemoryGateway.get/set` stub + llamada desde bootstrap_multi.  
**DONE:** get/set roundtrip memoria proceso. **NO:** DB externa.

### T20 — EngineRegistry load fichas + attach policy
**Objetivo:** Cargar engines stubs (openclaw/hermes) con policy.  
**Paths:** `wordflow_kernel/engines/`, `engine_attach.py`, `engine_abi.py`  
**Programar:** `EngineRegistry.load(ficha)`, `attach(name, policy)`.  
**DONE:** list engines >= 0 stubs. **NO:** runtime vendor.

### T21 — UI plugin message→GoalLock→code_path Fake
**Objetivo:** Mensaje UI dispara goal + path Fake.  
**Paths:** `ui_gateway/`, `goal_lock.py`  
**Programar:** `handle_message(msg) -> fake result`.  
**DONE:** smoke message. **NO:** frontend React.

### T22 — LLM ban gate scan paths
**Objetivo:** Detectar vendor LLM directo en paths críticos.  
**Paths:** nuevo o `fail_closed.py` / scanner  
**Programar:** `scan_paths_for_llm_ban(roots) -> list[hits]`; CI puede usarlo.  
**DONE:** scanner corre offline. **NO:** banear tests legítimos de gateway.

### T23 — CI workflow matrix kernel+loop+deploy
**Objetivo:** Workflow GH Actions que corra tests smoke offline.  
**Paths:** `.github/workflows/` (crear si MISSING)  
**Programar:** yaml matrix jobs python -m ... spawn/instance/list_connections.  
**DONE:** workflow file en repo. **NO:** secrets reales.

### T24 — Claim final + README E2E links
**Objetivo:** Documento de claim parcial C100 con enlaces archivo.  
**Paths:** `PIPELINE/20_CLAIM_CHAT_A.yaml` o nuevo `PIPELINE/CLAIM_C100_PROGRESS.md`  
**Programar:** markdown/yaml con links a T13–T23 outputs.  
**DONE:** archivo GH. **NO:** claim V1 100% (eso T49).

---

## 3. FICHAS T25–T34 (loops / gateway / residual)

### T25 — Continuous loop 12-stage hooks por instance
**Objetivo:** Hooks de loop atados a instance_id.  
**Paths:** `maxbry_loop/engine.py`, `cognitive_loop.py`, `main_loop.py`  
**Programar:** registrar hooks stage1..12 en dict por instance; `run_stage(instance_id, n)`.  
**DONE:** 2 instancias hooks aislados. **NO:** LLM real en stages.

### T26 — IntelligenceGateway único path LLM
**Objetivo:** Todo LLM pasa por gateway (RouterHTTP stub).  
**Paths:** `wordflow_kernel/gateway/`, `intelligence` si existe  
**Programar:** `IntelligenceGateway.complete(prompt) -> stub text`; ban import vendor fuera.  
**DONE:** stub returns fixed string. **NO:** API keys.

### T27 — GatewayModel en maxbry_loop
**Objetivo:** Loop usa GatewayModel, no vendor directo.  
**Paths:** `maxbry_loop/model.py`, `models.py`  
**Programar:** clase `GatewayModel.generate` delega a gateway T26.  
**DONE:** test mock. **NO:** OpenAI client.

### T28 — GoalLock ↔ loop goals bridge
**Objetivo:** Goals del lock alimentan loop.  
**Paths:** `goal_lock.py`, `maxbry_loop/`, `bridge/`  
**Programar:** `sync_goals(instance_id)`.  
**DONE:** goal visible en loop state. **NO:** UI.

### T29 — Gaps → gap_tasks → code_path_runner
**Objetivo:** Gap detectado encola tarea de path.  
**Paths:** `gap_tasks.py`, `maxbry_loop/gaps.py`, `code_path_runner.py`  
**Programar:** `enqueue_gap(gap) -> task_id`; runner acepta task fake.  
**DONE:** cola 1 gap. **NO:** auto-fix infinito.

### T30 — Forensic Claim≠Evidence
**Objetivo:** Claim no es evidencia.  
**Paths:** `forensic.py`, `forensic_api.py`, `claim_validator.py`, `evidence_packet.py`  
**Programar:** `validate_claim(claim, evidence) -> pass|fail`.  
**DONE:** claim sin evidence → fail. **NO:** PASS por texto LLM.

### T31 — RepoTruthPort + FakePort
**Objetivo:** Puerto de verdad de repo con Fake.  
**Paths:** `repo_truth.py`  
**Programar:** interface `get_file/content` + `FakeRepoTruth`.  
**DONE:** fake returns fixture. **NO:** network obligatoria.

### T32 — GitDataAPIPort dry-run no force_push
**Objetivo:** Operaciones git en seco; force_push prohibido.  
**Paths:** github_deploy / publisher  
**Programar:** `plan_push(...)`; si force=True → error.  
**DONE:** test force rechazado. **NO:** push real.

### T33 — Protected patterns + CONFLICT HOLD
**Objetivo:** Paths protegidos no se sobrescriben.  
**Programar:** lista patterns; si conflicto → status HOLD.  
**DONE:** test HOLD. **NO:** borrar main históricos.

### T34 — Evidence/provenance al cerrar path
**Objetivo:** Al cerrar code_path escribir evidence packet.  
**Paths:** `evidence_packet.py`, `evidence_bridge.py`  
**Programar:** `write_evidence(path_result) -> file/dict`.  
**DONE:** packet con timestamp+instance_id. **NO:** claim V1.

---

## 4. FICHAS T35–T40 (recursos / accounts / slots)

### T35 — ResourceContract schema
**Objetivo:** Schema estricto skills/datasets/adapters.  
**Paths:** schemas/ o `resource_catalog.py`  
**Programar:** JSON schema o dict required fields; `validate_resource`.  
**DONE:** inválido falla. **NO:** download.

### T36 — Índice HF PLAN_ONLY
**Objetivo:** Plan de índice remoto sin saturar GH.  
**Programar:** `build_plan_only(index_url_or_list) -> plan`.  
**DONE:** plan serializable. **NO:** fetch masivo.

### T37 — Router micro-kernel discover→map→select→load
**Objetivo:** Cadena bajo demanda.  
**Paths:** `router_slot/`, resource router  
**Programar:** 4 funciones discover/map/select/load stubs.  
**DONE:** pipeline llama las 4. **NO:** 49 endpoints Router full.

### T38 — AccountRegistry multi-account enforced
**Objetivo:** Registry de cuentas obligatorio en publish path.  
**Paths:** `extensions/wordflow/accounts/`  
**Programar:** register/get/list; publish usa get.  
**DONE:** sin cuenta → fail. **NO:** secrets plaintext log.

### T39 — Deploy config token_ref only
**Objetivo:** Solo referencia a token, nunca token en log.  
**Programar:** `DeployConfig.token_ref`; redactor logs.  
**DONE:** assert "ghp_" not in logs fake. **NO:** embutir PAT.

### T40 — Plugin slot Kimi/Minimax solo conexión
**Objetivo:** Slot de conexión **sin** fusionar code V1.  
**Programar:** ficha slot `status: PLACEHOLDER` + register vacío.  
**DONE:** ficha en repo. **NO:** implementar fusión V1.1.

---

## 5. FICHAS T41–T49 (mapa + cierre)

### T41 — HTML mapa mental cascada
**Objetivo:** Un HTML con visión en cascada.  
**Fuente spec (ya incluida en requisitos):** cascada vertical; cada bloque ID canónico; para_qué/sin_esto; colores IMPLEMENTED/PARTIAL/MISSING/PENDING; HTML+CSS inline un archivo; visión ≤5s; status desde XRAY_SEED; no claim C100 hasta T49.  
**Programar:** `docs/mapa_mental_v1.html` o `PIPELINE/mapa_mental_v1.html`.  
**DONE:** abre sin build. **NO:** React.

### T42 — HTML X-Ray IDs
**Objetivo:** Radiografía por IDs ROOT_MAP.  
**Programar:** `docs/xray_ids_v1.html` tabla ID|path|status.  
**DONE:** HTML en GH. **NO:** status inventado.

### T43 — Matriz MISSING/PARTIAL post-code
**Objetivo:** Actualizar matriz real post T13–T40.  
**Programar:** `PIPELINE/XRAY_MATRIX_POST.md` tabla.  
**DONE:** archivo GH. **NO:** IMPLEMENTED sin archivo.

### T44 — README conectar motores OpenClaw/Hermes
**Objetivo:** Doc cómo attach engines.  
**Programar:** sección en `extensions/wordflow_kernel/README_V1.md` o README raíz.  
**DONE:** enlace archivo.

### T45 — README Router + Memory
**Objetivo:** Cómo conectar orch router/memory.  
**Programar:** sección README. **DONE:** archivo GH.

### T46 — Bitácora V1 vs V1.1
**Objetivo:** Qué quedó en V1 y qué va a V1.1.  
**Programar:** `PIPELINE/BITACORA_V1_CLOSE.md`. **DONE:** lista explícita fuera V1.

### T47 — Suite tests + comandos
**Objetivo:** Documentar cómo correr smokes.  
**Programar:** `docs/TESTS_OFFLINE.md` + opcional tests.  
**DONE:** comandos copy-paste. **NO:** CI flaky red.

### T48 — Re-audit 4 pasadas P0–P7
**Objetivo:** Informe forense binario.  
**Programar:** `PIPELINE/AUDIT_V1_P0_P7.md` PASS/FAIL con links evidencia.  
**DONE:** sin PASS inventado.

### T49 — Claim V1 100%
**Objetivo:** Claim solo si T13–T48 PASS.  
**Programar:** YAML/MD claim con enlaces.  
**DONE:** solo si T48 PASS. **NO:** claim con FAIL abierto.

---

## 6. EXTRAS (chat)

### EXTRA T2 — Reception/conversion motor
**Paths:** `extensions/wordflow/reception/`  
**Programar:** `convert(input_block) -> normalized` + smoke. **Deps:** T0 DONE.

### EXTRA T2.1 — SDPA vía T2
**Programar:** parámetro `use_sdpa` + stub path. **DONE:** flag aceptado.

### EXTRA T2.2 — MCR vía T2
**Programar:** branch MCR stub. **DONE:** branch invocable.

### EXTRA T2.3 — 20M contexto vía T2
**Programar:** config `max_context` + doc (stub si no hay hardware). **DONE:** doc+config.

### EXTRA CG — Code-gen DSL/DAG/schema
**Programar:** módulo input texto → dict DAG; 1 ejemplo. **NO:** lexer completo V1.1.

### EXTRA ARCH — Arquitectura final
**Programar:** SOLO APPEND; **PROHIBIDO** truncar/borrar `ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md`.

### EXTRA DEL — Delete mavis-deploy-keys
**Programar:** buscar y borrar path si existe; commit delete. **DONE:** path ausente.

### EXTRA AUDIT-5
Cada 5 tareas DONE → `PIPELINE/AUDIT5_Sxx_Syy.md` + update `TAREAS_ACTUAL.md` antes de seguir.

---

## 7. Orden de ejecución

```
T10 → T11 → T12
→ T13 → T14 → T22 → T15 → T16 → T17
→ T19 → T20 → T21 → T18 → T23 → T24
→ T25…T34 → T35…T40
→ T41 → T42 → T43 → T44 → T45 → T46 → T47 → T48 → T49
(+ AUDIT-5 cada 5)
```

---

## 8. Checklist anti-gaps
- [ ] Path exacto en commit
- [ ] Smoke offline
- [ ] No IMPLEMENTED sin archivo
- [ ] No token en log
- [ ] Read-back GitHub
- [ ] CONTROL DE TRABAJO
- [ ] Code → forense paso 3

Si falta detalle de producto: **no inventar**; GAP en PIPELINE + COPY del árbol `extensions/`.

---

## 9. Enlaces base
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/52_V1_PLAN_49_TAREAS_METODO_Y_XRAY.md
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/ROOT_MAP_IDS.md
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/XRAY_SEED_STATUS.md
- https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/instance.py
- https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/instance_store.py
- https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/spawn.py
- https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/list_connections.py

**Primera tarea a ejecutar: T10.**
