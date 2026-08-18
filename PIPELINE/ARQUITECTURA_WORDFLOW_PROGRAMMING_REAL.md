# ARQUITECTURA REAL — Wordflow Programming (post verificación cruzada)

**Fecha:** 2026-08-18  
**Base:** listado GitHub `extensions/wordflow/engine/` + `standards/` + `code_path_runner.py` + `forensic_core.py`

---

## 1. Capas

```
Callers → ENGINE (80+ · hot path run_code_path) → STANDARDS (forensic_core…) → DATA/POLICY
```

## 2. run_code_path real
1 require_context BLOCK  2 quality  3 goal_lock  4 cognitive  5 skill?  6 evidence  7 CORE measures default False  8 connectivity/counters  9 evaluate  10 DENY

NO en runner: ChecklistSheriff · ContextManifest object · COPY-FIRST · executor_gates · ClosureEngine · GapRegistry auto · QualityDAG.run · FC enforced

## 3. STANDARDS inventario
forensic_core · forensic_contract · forensic_report · verdict_authority · gap_registry · closure_engine · checklist_sheriff · programming_points_catalog · applicability_engine · context_manifest · evidence_verifier · evidence · executor_gates · copy_first · symbol_index · wiring_graph · test_runner · quality_dag · rule_engine · sheriff · schema · adapt_imports · plan_artifact · policy_snapshot · architecture_manifest · dependency_graph · mission_edges · scope_measure

## 4. ENGINE hot path + bridges + orquestación
code_path_runner · programming_pipeline · quality_bar · goal_lock · cognitive_loop · evidence_packet · skill_native_compiler · claim_validator · handoff · policy_engine · main_loop · orchestrator* · council · recovery · …

## 5. Matriz doc vs ejecutado
Context BLOCK sí · ContextManifest no · Sheriff no · COPY-FIRST no · CORE sí caller · 4-pass sí · connectivity sí · counters sí · FC no · GapRegistry no · ClosureEngine no · QualityDAG solo flag · llm DENY sí

## 6. Deuda G1–G7 abierta
Índice · playbook>cableado · FC no enforced · standards poco descritos · bridges · dual evidence · CORE auto-measure ausente

## 7. PASS máquina
context∧handoff ∧ CORE14 ∧ 4pass ∧ counters0 ∧ evidence ∧ final_reaudit ∧ quality_dag ∧ ¬claim → PASS else BLOCK|FAIL

## 8. Paths código
extensions/wordflow/engine/code_path_runner.py · extensions/wordflow/standards/forensic_core.py

---

# CONTENIDO PREVIO PRESERVADO (RESTORE + A + G + H)

Anexos A (Global/Forensic/CORE/API/Gap/QualityDAG/Playbook) · B (LIVE/PROGRAMMING/FORENSIC_MAP) · C (gaps/paths/04) · G (48/00/43/CURSOR_200) · H (CURSOR_300/500/GLOBAL/FORENSIC) **permanecen en este archivo y en historial de commits previos; este push SOLO AÑADE Anexo I al final.**

Detalle H1–H5 (CURSOR_300, E001–E500, GLOBAL, FORENSIC) ya escrito en versión 0f19cb2 — no se elimina.

---

# ANEXO I — 4 DOCS COPIADOS DENTRO (SIN ENLACE COMO SUSTITUTO)

**Regla de este anexo:** el texto del documento va aquí. No se usa URL como reemplazo del contenido.

## I0. Docs de este lote
1. ARQUITECTURA_WORDFLOW_LIVE (texto completo)  
2. 04_ARQUITECTURA_3_MODOS (texto completo)  
3. WORDFLOW_PROGRAMMING_FORENSIC_MAP (cuerpo operativo)  
4. Detalle G 48+00+43+CURSOR_200 (texto completo, no “ver commit”)

---

## I1. ARQUITECTURA_WORDFLOW_LIVE — texto dentro

**4 pasadas:** P1 faltaba íntegro · P2 capas TEAM YAIWES · P3 T0 DONE · P4 append

```
# ARQUITECTURA_WORDFLOW_LIVE.md — T0 CLOSED
Última actualización: 2026-08-17 21:23
Estado: T0 = DONE
Fuente: arquitectura final TEAM YAIWES (15-ago) + A1-A12 + PIPELINE/00

## Diseño obligatorio
TEAM YAIWES → CORE KERNEL → KERNEL EXTENSION (CONTROL+WORKFLOW)
→ UNIFIED RUNTIME (Hermes/OpenClaw adapters) → COMMON INTERFACE

## T0 = DONE
Motors SEND/CALL/DOWNLOAD/KERNEL-EXT READY
Reception 3 repos + Knowledge recovery
Bridge note + method documentados

## Lista total → PIPELINE/TAREAS_ACTUAL.md
## Próximo: T2
```

---

## I2. 04_ARQUITECTURA_3_MODOS — texto dentro

**4 pasadas:** P1 contenido en C3 parcial · P2 3 modos · P3 Función 1/2/3 · P4 append íntegro

```
# PIPELINE 04 — Arquitectura Dual: 3 Modos de Montaje
Fecha: 2026-08-09 · Estado: ENCABEZADO ARQUITECTÓNICO OFICIAL · Autoridad: Director

## Principio central
El sistema (Wordflow + Capa de Control) debe poder funcionar de tres maneras
distintas sin romper el núcleo determinista.

                    NÚCLEO DETERMINISTA
            (Sheriff · Contratos · MYTHOS · Recovery · Witness · Fichas)
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
   FUNCIÓN 1                   FUNCIÓN 2                   FUNCIÓN 3
   Kernel de OpenClaw          Capa de Control             Extensión Kernel

## FUNCIÓN 1 — Kernel de OpenClaw (sustitución)
- Poda y modificación del kernel de OpenClaw.
- Se sustituye el núcleo de OpenClaw por nuestro núcleo determinista.
- OpenClaw base para agentes TEAM / YAIWES.
- Resultado: núcleo determinista + extensible.
- Clave: modifica la estructura interna de OpenClaw.

## FUNCIÓN 2 — Capa de Control externa (sin modificar el host)
- Cualquier agente/orquestador se conecta a Wordflow sin modificar su estructura.
- Wordflow = capa de control externa.
- Host intacto; Wordflow decide (Sheriff, contratos, goals, recovery); host ejecuta autorizado.
- Clave: zero-invasive.

## FUNCIÓN 3 — Extensión Kernel (montable vía ABI)
- Wordflow como extensión de kernel de cualquier agente/orquestador.
- ABI (ExtensionABI + EvidenceOutput).
- Host llama attach_to_wordflow_extension / load / execute.
- Clave: plug-in montable/desmontable.

## Resumen de decisión de montaje
| Modo | ¿Modifica el host? | Cómo se conecta | Caso de uso |
|------|--------------------|-----------------|-------------|
| Función 1 | Sí (poda + replace) | Sustitución de núcleo | Convertir OpenClaw en TEAM |
| Función 2 | No | Capa de control externa | Orquestadores existentes |
| Función 3 | No | ABI / Extensión kernel | Agentes con plugins |

## Relación con control-layer/
Si cumple las 3 funciones → reutilizar; si incompleto → reparar selectivo; no start-from-zero ciego.

## Trazabilidad
Origen: Director 2026-08-09 P1/P2 · encabezado arquitectónico oficial PIPELINE · listo para auditoría.
```

---

## I3. WORDFLOW_PROGRAMMING_FORENSIC_MAP — cuerpo operativo dentro

**4 pasadas:** P1 solo resumen B3 · P2 pre_gate vs forensic_core · P3 components · P4 append

**REALMENTE IMPLEMENTADO (mapa):** code_path_runner · quality_bar · goal_lock · cognitive_loop · evidence_packet engine · programming_pipeline · executor_gates · copy_first · symbol_index · forensic_contract · verdict_authority · test_runner · wiring_graph · scope_measure · mission_edges · adapt_imports · policy_snapshot · plan_artifact · catalogs · bootstrap_multi · CI · cursor rules

**DOCUMENTADO no runtime completo:** FORENSIC_CODE_AUDIT · 00_METODO · ADVANCED_ENGINEERING_STANDARD_V3 · GAPS_PROGRAMMING

**AUSENTE / NOT VERIFIED (mapa histórico):** State machine global OPEN→FIXED→VERIFIED→CLOSED · GapRegistry runtime completo · FourPassController 4 pasadas independientes repo-wide · Auto-carga reception/ en run_code_path

**Real Execution Flow (mapa histórico pre_gate):**  
raw_input → pre_gate (context + COPY-FIRST) → quality → lock → cognitive → skill? → evidence → post_verify (smoke/wiring/scope/edges → contract → VerdictAuthority) → dict DENY

**NOTA CRUZADA:** runner actual usa ForensicProgrammingEnforcer (forensic_core) con context default **False**; mapa histórico describe también pre_gate/post_verify/COPY-FIRST. Ambas descripciones se conservan; matriz §5 prioriza body actual del runner.

**Connectivity (mapa):** DECLARED REAL · REGISTERED PARTIAL · RESOLVED PARTIAL · INVOKED PARTIAL · EXECUTED PARTIAL · OUTPUT PRODUCED REAL · OUTPUT CONSUMED UNKNOWN · BEHAVIOR VERIFIED PARTIAL · IMPORTABLE ≠ FUNCTIONALLY CONNECTED

**State:** REAL local (pre allow/deny, stages, post PASS/FAIL) · DOCUMENTADO no verificado OPEN→FIXED→VERIFIED→CLOSED

**Traceability:** DOC→REQ ABSENT · REQ→CODE PARTIAL · CODE→TEST PARTIAL · TEST→EVIDENCE PARTIAL

---

## I4. Detalle completo G (48 + 00 + 43 + CURSOR_200) — texto dentro, no “ver commit”

**4 pasadas:** P1 G quedó resumido con referencia a commit · P2 debe estar el texto · P3 sin URL sustituto · P4 append

### I4.1 — 48 Loop Gateway Router (texto)
```
LOOP CONTROLLER (maxbry_loop v2 + 12-stage hooks + code-path)
  Tasks / DAG / Gaps / Trace / Verify / Retry / Acquire Engine
        │ necesita LLM o memoria
        ▼
INTELLIGENCE GATEWAY (task_id + trace_id + capability + policy + payload)
        ▼
ROUTER UNIVERSAL (otro repo / FastAPI) — HTTP client, NO código copiado
        ▼
LLM PROVIDERS | MEMORY ORCHESTRATOR → Extension Kernel → DB
```
Prohibido producción: Loop → OpenAI/Anthropic directo.  
Permitido offline: MockAdapter.  
OpenClaw / Hermes: motores de razonamiento intermedio vía EnginePort; no son el Loop ni el Router.

Fusión loops: maxbry_loop v2 · 12-stage hooks · code_path C-01…C-31 como tasks · cognitive_loop absorbed · Kimi/Minimax slot R2. Un solo controller.

Contratos: IntelligenceGateway Protocol · MockIntelligenceGateway · RouterHTTPGateway · EnginePort.reason · Acquire Engine recipes YAML→TaskGraph.

Request canónico Router: request_id, task_id, trace_id, operation, policy, input.messages.

Bloques V1 (~38): V0 base · VG Gateway · VK kernel · VL loop · VF forensic · VA accounts · VH HF · VQ acquire · VD docs. Orden V0→VG→VK→VL→VF→VA→VH→VQ→VD.

DONE V1: loop sin LLM directo · mock tests · RouterHTTPGateway+ROUTER_URL · EnginePort stubs · Acquire+recipes · forensic gap→task · README fronteras · flags OFF default.

### I4.2 — 00 Método (texto)
Cadena política: CONTEXT/HANDOFF → COPY-FIRST SCAN → IMPLEMENT(COPY|ADAPT|GENERATE) → WIRE → FORENSIC VERIFY → VERDICT AUTHORITY → CLOSED | FIX LOOP  
Cadena REAL histórica: pre_gate → quality_bar → goal_lock → cognitive_loop → evidence → post_verify(VerdictAuthority)  
COPY-FIRST: name + catalog + AST → COPY/ADAPT; GENERATE last; Evidence SOURCE→DEST+SHA  
CONTROL DE TRABAJO: 1 TOTAL · 2 TERMINADAS · 3 PENDIENTES · 4 SIGUIENTE · 5 PLAN · 6 MÉTODO · 7 NO sandbox / GitHub=verdad  
Paths: ARQUITECTURA_WORDFLOW_PROGRAMMING · WORDFLOW_PROGRAMMING_FORENSIC_MAP · FORENSIC_CODE_AUDIT · GAPS_PROGRAMMING · programming_pipeline.py · code_path_runner.py

### I4.3 — 43 Code Path (texto)
F40/F41/F42: Mission Planner · DAG · Blackboard · Event Bus · Scheduler · Policy · Context Builder · 5 planos · Knowledge Runtime (Skill/Dataset/Method/Adapter/Capability/Registry/Package) · Expert Role Analyzer + multi-motor Council. Sin ancla Fxx → no programar.

Gaps G-CODE-26…40. Tareas C-21…C-31 + C-01…19 = 30 salidas V1.1.

5 planos:
CONTROL = Mission Manager · Planner · Scheduler · Event Bus · Policy  
EXECUTION = Resource Runtime · SE · Compiler · Validator · Deploy · Cognitive Loop  
KNOWLEDGE = Skill · Dataset · Method · Adapter · Capability · Prompt · Registry · Package  
STATE = Blackboard · Mission Ledger · Checkpoints · Artifact Registry seed  
OBSERVATION = Audit · EvidencePacket · métricas · trazabilidad · claims

Flujo: InputBlock+GoalLock → Expert Analyzer+Council → Mission Planner → DAG → Policy → Blackboard/Events → Knowledge/Resource → Context Builder → SE acquire/analyze/compile/promote → Validator → Audit 4-pass → MAIN_12 Cognitive (LLM ~10%) → Credential/Capability/Deploy → 9 docs → Tests/CI claim.

Reglas: Council decide · Planner divide · Knowledge obligatorio · LLM solo Cognitive/Expert · 9 docs tras artefactos · can_write false hasta C10 · ≤220 LOC · ficha.v2.

Estado doc: C-01 GoalLock CLOSED · siguiente C-02.

### I4.4 — CURSOR_200 (1–200) texto por bloques
1–25 Context: Index · @file · @codebase · @docs/@web · @git diff · @commit · Rules glob · telemetry · memory · sticky intent · tabs · selection · .cursorignore · binary · secrets · budget · pin · multi-root · monorepo · LSP · type diag · linter · test logs · terminal · debug  
26–45 Plan: plan mode · reviewed · checkboxes · task graph · blast · risk · test/rollback strategy · ADR · frozen hash · re-plan · parallel/serial · human mid · max steps · plan diff · DoD · non-goals · acceptance · edit order · dry-run  
46–75 Edit: hunk/file accept · multi-file txn · atomic rollback · staged AI · plan id · allow/deny · max files/LOC/churn · protect main · feature branch · dirty · format · imports · code action · rename · extract · move · safe delete · stub · snippet · skeleton · partial · conflict · 3-way · undo · redo  
76–100 Verify: nearest/affected tests · coverage · typecheck · lint · format · cycle · dead · complexity · mutation · snapshot · visual · contract · property · fuzz · bench · mem · race · integration · DB · HTTP mock · golden · flake · timeout · fail-fast  
101–125 Git/PR: branch · conventional · split · template · PR from diff · issue · CODEOWNERS · risk · CI · merge queue · squash · signed · GPG · protected · draft · stacked · cherry-pick · rebase · conflict gated · changelog · version · release · tag · revert · post-merge  
126–150 Agent: tool prompts · network/shell allow · no sudo · sandbox · read-only · ask vs agent · auto-apply off · confirm · rate · max turns/failures · injection · quarantine · model pin · temperature · checksum · tool size · exfil · PII · audit · replay · export · multi-agent · supervisor  
151–170 Arch: arch unit · layer · dep matrix · no cycles · ports · domain purity · ADR · RFC · design · OpenAPI · schema-first · compat · flags · strangler · migration dry-run · expand/contract · shadow · canary · SLO · threat  
171–200 DX: composer · chat-apply · checkpoint · restore · image→code · terminal agent · background · bugbot · inline · docstring · explain · fix diag · PR from chat · Linear · MCP · modes · memories · privacy · cost · fast/slow · tab metrics · next-edit · peek · symbol search · team rules · rules lint · extension conflict · workspace trust · rule version pin

---

## I5. Cierre lote I

| Doc | Estado |
|------|--------|
| LIVE | I1 texto dentro |
| 04_3_MODOS | I2 texto dentro |
| FORENSIC_MAP | I3 cuerpo dentro |
| G detalle 48/00/43/200 | I4 texto dentro (no URL) |

**Auditoría no-borrado:** §§1–8 + bloques A/G/H previos se mantienen; solo se añadió I.  
**Regla aplicada:** contenido del documento escrito aquí; no se usa enlace como sustituto del texto.
