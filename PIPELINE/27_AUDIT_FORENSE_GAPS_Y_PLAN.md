# PIPELINE 27 — AUDITORÍA FORENSE S1–S8 · GAPS · PLAN RESIDUAL EJECUTABLE

**Versión:** 2.0 FORMA_PIPELINE  
**Fecha:** 2026-08-10  
**Repo:** maxbry123-commits/agentes  
**Estado:** FUENTE DE VERDAD de gaps + plan residual (sustituye claims 22/23/25)  
**Método:** ≤300 LOC/archivo · 1 tarea = 1 salida = 1 commit · YAML=contrato · .py=runtime  

---

## 0. TRAZABILIDAD COMPLETA DE FUENTES

| ID | Documento fuente | Qué aporta a este plan |
|----|------------------|------------------------|
| F01 | `01_SPEC_AUDIT_EXTENSION.md` | EvidencePacket · P0–P3 · verdict 3 capas · run_audit |
| F02 | `02_PLAN_FASE1_IMPLEMENTACION.md` | A-AUD-01…09 · estructura audit_forensic · criterios cierre |
| F03 | `03_PATCH_GAPS_CHAT_A.md` | RepoTruthPort · Fake · phase_seed · P11/P12 |
| F04 | `04_AUDIT_10P_COUNCIL_PANELS.md` | Confirmación post-parche Audit |
| F05 | `01_SPEC_INPUT_GOALS_REFUTE_REPAIR.md` | InputBlock · G_IN/G_OUT 12×12 · L1–L3 · R1–R6 · Version |
| F06 | `02_SPEC_GROUP_LOOPS_SENTINEL_COUNCIL.md` | main_12 · council 12 · watchdog · supervisor · groups |
| F07 | `03_CATALOG_CURSOR_TECHNIQUES.md` | Hooks Cursor → Wordflow (no 100 funciones) |
| F08 | `04_COUNCIL_PANELS_SIMS_PATCH.md` | Council roles · sims · checklist CHAT_A |
| F09 | `05_PATCH_GAPS_PARTE2.md` | Schemas programables · caps repair · A-WF plan |
| F10 | `01_INTEGRACION_SOURCE_EVOLUTION.md` | 4 loops acquire/analyze/reuse/promote · pin · handoff |
| F11 | `02_PATCH_GAPS_PARTE3.md` | VersionPin schema · 9 estados absorb · scores |
| F12 | `03_INTEGRACION_SKILL_NATIVE_C09.md` | C09 compiler · C01–C08 · skill_ir · promote rules |
| F13 | `04_PATCH_GAPS_SKILL_NATIVE.md` | catalog · C08 transitions · handoff write_kernel:false |
| F14 | `00_RAZONAMIENTO_F0_F5.md` / `00b_RAZONAMIENTO_SKILL_NATIVE.md` | LISTA_GLOBAL · skill = materia prima |
| F15 | `DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2.md` | deploy_config · dry-run · SIN_REGLA/BLOQUEADOS · evidence.json |
| F16 | `DESPLIEGUE con el Wordflow.md` | C10 Git Data API · expected_head · no force · manifest · agent≠push |
| F17 | `ENCHUFE_UNIVERSAL_v2` | ficha.v2 · abi_version · mount_mode · perfiles · llm_control DENY |
| F18 | `CHAT_A_EXECUTOR_v4.yaml` | claim forense E1–E9 · blob_sha · tree_sha |
| F19 | Plan rehecho (Pasted Text WAVE1–6) | A-AUD / A-WF / A-SE / A-DEP lista original |
| F20 | Auditoría ingenieros Grok (docs+código+PIPELINE) | Confirmación gaps · workflow audit SÍ existe · 27 faltaba |
| F21 | `PIPELINE/00_METODO…` · `12_PROJECT_DOCUMENTS_NATIVE_FULL` | formato densidad · 9-doc · KTP · ≤300 LOC |
| F22 | Arquitectura Wordflow (master) | visión ancha → OUT MVP en §6 |

**Regla de ancla:** cada tarea residual cita ≥1 ID F0x. Sin ancla → no se ejecuta.

---

## 1. VEREDICTO GLOBAL (post-auditoría ingenieros)

```
VEREDICTO_GLOBAL: PARCIAL_FUERTE
DOCS→PLAN: ~95%
PLAN→CÓDIGO: ~40–50%
MVP_4_OBJ_100: REFUTADO
PLAN_57_DONE: REFUTADO
publisher≡C10: REFUTADO
PIPELINE_22/23/25_DONE: REFUTADO
```

| Bloque | % | Fuente veredicto |
|--------|---|------------------|
| WAVE1 Audit | ~85% | S1 + ingenieros (CI workflow presente) |
| WAVE2–3 Wordflow | ~78% | S2 |
| SE + Skill | ~25–30% | S3 |
| C10 Obj4 | ~15% | S4 |
| Enchufe extensions | ~60% | S5 (solo control-layer tiene ficha.v2) |

---

## 2. MICRODIAGRAMA TRANSVERSAL

```
F01–F04 ──→ Audit gaps R1 ──→ ficha+C_AUDIT+CI
F05–F09 ──→ WF gaps R1 ────→ schemas+watchdog+G_OUT
F10–F14 ──→ SE/Skill R2 ───→ loops→compiler→promote_12 ──┐
F15–F16 ──→ C10 R3 ───────────────────────────────────────┴→ github_deploy→verify
F12–F13 ──→ RB R4 (paralelo) ──→ C08+handoff
F17–F18 ──→ ABI/Claims R0+R4 ──→ ficha×ext + PIPELINE honesto
F19–F20 ──→ orden residual E1–E27 (no 57)
F21–F22 ──→ formato + frontera IN/OUT
```

```
R0 claims
  ↓
R1 Audit+WF borde
  ↓
R2 SE loops → skill_compiler → promote_12 ──→ request_deploy
  ↓                                              ↓
R4 RB/ABI paralelo                            R3 C10 engine
                                                 ↓
                                            evidence + claim
```

---

## 3. REVOCACIÓN CLAIMS 22–25

| Doc | Claim viejo | Reemplazo | Ancla |
|------|-------------|-----------|-------|
| 22 | A-WF-01..11 DONE | PARTIAL ~78% | F06 F09 S2 |
| 23 | A-SE-01..05 DONE | PARTIAL ~30% (sin loops/skill) | F10 F12 S3 |
| 24/25 | Obj4 DONE vía publisher | REFUTADO publisher≠C10 | F15 F16 S4 |
| 25 | Obj1–4 DONE | REFUTADO | S1–S5 |

---

## 4. PLAN RESIDUAL — QUÉ SE HACE EN CADA TAREA

### R0 — Higiene claims · Salida **E1** · Anclas F18 F20 F21

| ID | Qué se materializa (concreto) |
|----|-------------------------------|
| **R0.1** | Editar cabecera de `PIPELINE/22_*.md`, `23_*.md`, `25_*.md`: banner `SUPERSEDED → ver PIPELINE/27`. No borrar histórico. |
| **R0.2** | Confirmar en 27 §6 IN/OUT MVP congelado (texto ya escrito). Commit único E1 = R0.1+R0.2. |

**Done cuando:** 22/23/25 apuntan a 27 · commit en GH · claim CHAT_A con path+sha.

---

### R1 — WAVE1–3 borde · Salidas **E2–E6** · Anclas F01–F09 F17

| ID | Salida | Qué se materializa (concreto) | Path | LOC max |
|----|--------|-------------------------------|------|---------|
| **R1.1** | E2 | Crear `ficha.v2.json` audit (artifact_id, abi_version 2.0, mount_mode, load_priority, kernel_min, llm_control DENY, entrypoint). Añadir YAML `C_AUDIT_CLAIM.yaml`, `C_AUDIT_EVIDENCE.yaml`, `C_AUDIT_DOC_TRACE.yaml` en contracts/ (required_fields + forbidden). | `extensions/audit_forensic/ficha.v2.json` + `contracts/` | ≤120 |
| **R1.2** | E3 | (a) `report_builder.py` que emita capa1 micro / capa2 mensaje / capa3 detalle desde verdict_engine **o** documentar en manifest que verdict_engine ya cumple 3 capas y cerrar gap por equivalencia. (b) Nota CI: workflow `test-audit-forensic.yml` existe. | `engine/report_builder.py` opcional | ≤120 |
| **R1.3** | E4 | Schemas JSON `architecture_output.schema.json` + `code_output.schema.json` (required: schema_version, artifact_id, files[], evidence_ref). Función map `goals_out → EvidencePacket` stub tipado en entrypoint/tests. | `extensions/wordflow/schemas/` + glue | ≤150 |
| **R1.4** | E5 | `engine/watchdog.py` (triggers: timeout, stuck_step, secret_leak flags → stop). `engine/supervisor.py` (checkpoint dict + TTL). `policies/sheriff.yaml` + `policies/sentinel.yaml` (fail_closed, max_repairs). Tests unit mínimos. | `wordflow/engine/` + `policies/` | ≤300 total split |
| **R1.5** | E6 | `ficha.v2.json` wordflow. Claim PARTIAL WAVE2–3 con lista gaps cerrados R1.1–R1.4. | `extensions/wordflow/ficha.v2.json` | ≤80 |

---

### R2 — SE + Skill · Salidas **E7–E16** · Anclas F10–F14

| ID | Salida | Qué se materializa (concreto) | Path | LOC max |
|----|--------|-------------------------------|------|---------|
| **R2.1** | E7 | `store/source_registry.yaml`: categorías github/gitlab/hf/url + weight + license_policy_ref. `registry.resolve(source_id) → pin_request`. | `source_evolution/store/` + engine | ≤100 |
| **R2.2** | E8 | Protocol `GitHubAcquirePort`: get_tree, get_blob, get_commit. `FakeAcquirePort` in-memory. Sin red en tests. | `engine/github_acquire_port.py` | ≤160 |
| **R2.3** | E9 | `loops/acquire_12.yaml` (12 steps: auth→pin→fetch_plan→license→download→verify_hash→…). Runner hook en entrypoint que carga YAML y ejecuta steps deterministas (no LLM). | `loops/acquire_12.yaml` + hook | ≤120 + yaml |
| **R2.4** | E10 | `loops/analyze_12.yaml` + schema IR levels 0–4 (path, symbols, deps, risks, capability_hints). Analyzer mínimo sobre tree Fake. | loops + `schemas/ir_level.schema.json` | ≤150 |
| **R2.5** | E11 | `store/capability_registry.yaml` + `reuse_decision(gate)`: REUSE_FIRST | ADAPT | GENERATE_LAST. Test: si capability match → no generate. | engine + store | ≤120 |
| **R2.6** | E12 | `schemas/skill_ir.schema.json` + parser YAML/MD skill → Skill IR (identity, execution, interfaces, security). | `extensions/skill_compiler/schemas/` + parser | ≤150 |
| **R2.7a** | E13 | `skill_compiler/engine/knowledge_compiler.py`: Skill IR → knowledge artifacts (markdown/schema only), runtime_dependency_on_skill=false. | skill_compiler/engine/ | ≤150 |
| **R2.7b** | E14 | `code_compiler.py`: Skill IR → Capability IR (strategy reuse/adapt/generate_last, destination logical root, provenance hashes). | skill_compiler/engine/ | ≤150 |
| **R2.8** | E15 | `store/skill_source_catalog.yaml` tier A seed (≥3 entradas). `security_perm_scan` + quarantine dir policy (no execute until promote). | store + engine/security | ≤120 |
| **R2.9** | E16 | `loops/promote_12.yaml`: checks AuditVerdict CONFIRMADO/PARCIAL aceptable + Witness L1–L4 + goal_lock → `request_deploy` payload (sin token). Hook a C10. | loops/promote_12.yaml + glue | ≤150 |

---

### R3 — C10 Obj4 · Salidas **E17–E23** · Anclas F15 F16 F18 · **Depende R2.9**

| ID | Salida | Qué se materializa (concreto) | Path | LOC max |
|----|--------|-------------------------------|------|---------|
| **R3.1** | E17 | Package nuevo `extensions/github_deploy/` (no renombrar publisher). `deploy_config.yaml`: protected_patterns, allowed_paths, require_expected_head. Loader valida config. | `extensions/github_deploy/` | ≤100 |
| **R3.2** | E18 | `engine/dry_run.py`: plan.json de archivos; EXIT 1 si path sin regla; EXIT 2 si BLOQUEADO por protected_patterns. Tests Fake. | dry_run.py | ≤100 |
| **R3.3** | E19 | `GitDataAPIPort`: create_blob, create_tree, create_commit, update_ref. `FakeGitDataPort` graba ops. **No** git CLI. | git_data_port.py | ≤160 |
| **R3.4** | E20 | `c10_engine.py`: lee deploy_plan + expected_head; si head≠expected → CONFLICT (no force_push); states REQUESTED→PLANNED→APPLYING→VERIFYING→DEPLOYED/FAILED. | c10_engine.py | ≤160 |
| **R3.5** | E21 | `verify.py` post-ref: compara tree/blob shas → escribe `evidence.json`. `deployment_manifest` schema (repo, branch, commit_sha, files[], provenance). | verify.py + schema | ≤120 |
| **R3.6** | E22 | Glue: promote_12.request_deploy → C10.run; on DEPLOYED → señal C08 AVAILABLE (RB o stub). Handoff schema `can_write_github: false`, solo token_ref en runtime C10. | integration + handoff.schema.json | ≤120 |
| **R3.7** | E23 | Claim CHAT_A Obj4: PARTIAL o COMPLETED solo con paths+blob_sha+tests Fake C10. Nunca publisher=C10. | PIPELINE claim md | md |

---

### R4 — RB + ABI · Salidas **E24–E27** · Anclas F12 F13 F17 · paralelo post R2.1

| ID | Salida | Qué se materializa (concreto) | Path | LOC max |
|----|--------|-------------------------------|------|---------|
| **R4.1** | E24 | `extensions/resource_brain/`: states DISCOVERED→…→AVAILABLE→DEPRECATED. C08 machine YAML + engine tick. | resource_brain/ | ≤200 |
| **R4.2** | E25 | Selection C04: solo recursos AVAILABLE. C05 logical URIs `kernel://…`. `handoff.schema.json` can_write_kernel:false. | engine + schemas | ≤120 |
| **R4.3** | E26 | ficha.v2.json para: audit (si no en R1.1), SE, publisher, bootstrap (campos ABI mínimos F17). | cada extension/ | ≤80 c/u |
| **R4.4** | E27 | validator_v2 mínimo (required ABI fields + llm_control DENY). Actualizar `control-layer/ficha.v2.json` contract_hash ≠ 000…0. | tools/validator o script + ficha | ≤100 |

---

## 5. TOTAL DE SALIDAS

```
E1  = R0.1 + R0.2
E2  = R1.1
E3  = R1.2
E4  = R1.3
E5  = R1.4
E6  = R1.5
E7  = R2.1
E8  = R2.2
E9  = R2.3
E10 = R2.4
E11 = R2.5
E12 = R2.6
E13 = R2.7a
E14 = R2.7b
E15 = R2.8
E16 = R2.9
E17 = R3.1
E18 = R3.2
E19 = R3.3
E20 = R3.4
E21 = R3.5
E22 = R3.6
E23 = R3.7
E24 = R4.1
E25 = R4.2
E26 = R4.3
E27 = R4.4

TOTAL = 27 salidas residuales
```

---

## 6. FRONTERA MVP (congelada · F22)

**IN residual:** Audit R1 · WF R1 · SE 4 loops · Skill compiler · promote · C10 github_deploy · RB C08 · ficha×ext · claims honestos  

**OUT (no tocar en E1–E27):** C11–C15 · Hermes pack · Memory GraphRAG · Sandbox Broker full · Fase4 Minimax/Kimi · MYTHOS 44 gates · UOOS RT-00..90 package  

---

## 7. CÓDIGO YA PRESENTE (no rehacer · evidencia GH)

| Path | Ancla |
|------|-------|
| `extensions/audit_forensic/` motor+matrices+Fake+workflow | F01–F03 |
| `extensions/wordflow/` input/goals/sentinel/council/main_12 | F05–F09 |
| `extensions/source_evolution/` pin/fetch/license/provenance | F10–F11 |
| `extensions/github_publisher/` token_ref+Fake (**≠C10**) | seed Obj4 |
| `extensions/project_bootstrap/` KTP+microflows | F21 |
| `control-layer/` motor+sheriff+C00–C85+ficha.v2 | F17 |
| `.github/workflows/test-audit-forensic.yml` (+otros test-*) | F20 corrección S1 |

---

## 8. LEY DE CLAIM (F18)

```
COMPLETED ⇔ path + blob_sha + test/CI + doc_anchor F0x 1:1
Si no → PARTIAL + GapID
publisher ≠ github_deploy
bootstrap/registry ≠ resource_brain C08
```

---

## 9. PRÓXIMA PUERTA

```
Director OK → E1 (R0.1+R0.2) commit real
luego E2 (R1.1) una salida = un commit
parar ≤3 min procesamiento entre salidas
```

**Fin PIPELINE 27 v2.**  
Fuente de verdad gaps + plan residual hasta próximo cierre forense.
