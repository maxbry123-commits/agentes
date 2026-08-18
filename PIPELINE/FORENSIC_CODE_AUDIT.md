# FORENSIC CODE AUDIT v1.3 — LISTA COMPLETA + ENFORCEMENT
**Fecha:** 2026-08-18  
**Incluye:** v1.2.1 FULL + componentes ejecutables + enforcement por transición + handoff rule

## Regla maestra
```
NO CONTEXT → NO PROGRAMMING
NO CONTEXT → NO AUDIT
NO HANDOFF VERIFICADO → NO PROGRAMMING / NO AUDIT VÁLIDA
NO EVIDENCE → NO PASS
GAP → FIX → RE-AUDIT
4 PASSES CLEAN → CLOSED
LLM says PASS ≠ PASS
Solo VerdictAuthority produce PASS/FAIL/CLOSED
```
Handoff ≠ trazabilidad completa. Sin Context + información de método de trabajo + Handoff verificado, el agente no puede comenzar a programar ni declarar una auditoría válida.

---

## CORE 14 (siempre) — detalle completo

### 01 REQUIREMENT CLOSURE
REQ → IMPLEMENTATION → TEST → EVIDENCE → CLOSED  
UNTRACEABLE_CODE / unverified_requirement = gap

### 02 SCOPE / DIFF CLOSURE
unexpected_changes = 0 o reason+approved

### 03 IMPLEMENTATION CLOSURE
DONE literal completo · CODE_EXISTS ≠ FEATURE_COMPLETE

### 04 ARCHITECTURE / BOUNDARY
Domain boundaries · dependency direction · ports/adapters · forbidden crossings · doc↔repo

### 05 DEPENDENCY CLOSURE
circular_dependencies=0 · forbidden_imports=0 · forbidden_dependencies=0

### 06 CONTRACT CLOSURE
input/output/errores · versionados · compatibilidad · consumer o ORPHAN_PUBLIC_API

### 07 REAL WIRING
DECLARED→REGISTERED→RESOLVED→INVOKED→EXECUTED→OUTPUT CONSUMED→BEHAVIOR VERIFIED  
broken_connections=0 · unresolved_dependencies=0 · unexplained_orphans=0 · unreachable_required_paths=0 · unverified_paths=0

### 08 BEHAVIOR / EDGE
NORMAL/EDGE/ERROR/EMPTY/INVALID/TIMEOUT/DUPLICATE/CANCEL aplicables · idempotency si side-effects

### 09 TEST EFFECTIVENESS
Test falla si se rompe la lógica · TEST_WEAK = gap

### 10 REGRESSION / IMPACT
symbol → consumers → dependencies → contracts → tests → risk

### 11 ERROR PATH CLOSURE
applicable failure paths identified → handled → tested

### 12 CODE QUALITY
LOC preferred≤800 · review>800 · refactor>1000 · critical>1500 · soft_min=300 (ref) · sin secretos

### 13 REPOSITORY TRUTH
paths/commits reales · sin 404 · docs coherentes

### 14 EVIDENCE + VERDICT
EvidencePacket · AI≠proof · solo VerdictAuthority emite PASS

## FC-01..13
FC-01 Arch↔docs · FC-02 Connectivity · FC-03 Gap loop · FC-04 Traceability · FC-05 Impact · FC-06 Behavior · FC-07 Final re-audit · FC-08 Document context · FC-09 Doc↔code · FC-10 Functional wiring · FC-11 Evidence-backed verdict · FC-12 Four-pass · FC-13 Anti-overengineering

## 4 PASADAS
1 STRUCTURE · 2 CONNECTIVITY · 3 BEHAVIOR · 4 FORENSIC CLOSURE

## Detalles recuperados
FILE LOC · no circular · forbidden imports · domain/ports/adapters · versioned contracts · critical verification · agent runtime authority · no default prod · deterministic first · state ownership · CI SKIP≠PASS · symbol→consumers→tests→risk · idempotency · concurrency detalle · orphans≠unreachable

## Closure counters
gaps · blocking_gaps · broken_connections · unexplained_orphans · unreachable_required_paths · unresolved_dependencies · unverified_paths · unverified_requirements · unverified_claims · pending_fixes · new_gaps_after_fix · unexpected_changes  → todos 0 para CLOSED

## CONDITIONAL / NO bloquear
Conditional: Security DB Perf Concurrency ExternalAPI AI/Agent Production NewDep Persistence Distributed Multi-repo  
No universal: SBOM compliance DR SLO chaos shadow break-glass rotation on-call cost model-drift attestation offline-pack API-freeze multi-tenant/PII si no aplica

---

## WORDFLOW AUDIT ENGINE — 8 subsistemas (ejecutable)

```
1. CONTEXT          MissionContract · ContextVerifier · DocumentCrossVerifier
2. REPOSITORY TRUTH RepositoryScanner · ScopeDiff · DependencyGraph
3. ARCHITECTURE     ArchitectureManifest · BoundaryChecker · ContractChecker
4. CONNECTIVITY     WiringGraph · RegistrationChecker · Reachability · OrphanDetector
5. VERIFICATION     Behavior · ErrorPaths · Tests · Impact/Regression
6. EVIDENCE         EvidenceCollector · EvidencePacket · Provenance
7. CLOSURE          GapRegistry · Fix/ReAudit Loop · ClosureCounter · FinalReAudit
8. POLICY           StandardContract · QualityDAG · FailClosed · AntiOverengineering
```

Componentes de referencia (01–44): MissionContract, ContextVerifier, DocumentCrossVerifier, RepositoryTruthScanner, ScopeDiffChecker, RequirementTraceability, ArchitectureManifest, ArchitectureChecker, ImportAnalyzer, DependencyGraph, CycleDetector, ContractRegistry, CompatibilityChecker, WiringGraph, RegistrationChecker, ReachabilityChecker, OrphanDetector, BehaviorVerifier, EdgeCaseRunner, ErrorPathChecker, TestEffectivenessChecker, ImpactAnalyzer, RegressionRunner, CodeQualityAnalyzer, ConcurrencyChecker, IdempotencyChecker, StateOwnershipChecker, EvidenceCollector, EvidencePacket, GapDetector, GapRegistry, FixPlanner, ReAuditController, FourPassController, QualityDAG, FailClosedGate, AntiOverengineeringGuard, ClosureCounter, FinalCleanReAudit, ForensicVerdictEngine, AuditReportGenerator, AuditContractValidator, AuditHistory, PolicyVersionManager.

LLM propone → Wordflow orquesta → Code determinista verifica → Evidence demuestra → Contract define CLOSED.

---

## ENFORCEMENT POR TRANSICIÓN (obligatorio)

| # | Componente | Función |
|---|------------|--------|
| 1 | PolicyEngine | Carga FORENSIC_CODE_CONTRACT; reglas obligatorias/condicionales; agente no las modifica en misión |
| 2 | StepGate | Gate antes de cada transición; precondiciones + evidencia; FAIL/BLOCK → no avanzar |
| 3 | StateMachine | Estados/transiciones permitidas; bloquea IMPLEMENTING→CLOSED, GAP_OPEN→CLOSED, SKIP→PASS, FAIL→PASS |
| 4 | ContractGate | Estado actual vs contrato; falta propiedad obligatoria → BLOCK |
| 5 | EvidenceGate | true crítico requiere evidencia; claim≠evidence; sin evidencia → no PASS |
| 6 | ApplicabilityEngine | Qué condicionales aplican; si applicable=true no se omite |
| 7 | TransitionAudit | state_before, action, rules, gates, evidence, state_after, timestamp, revision |
| 8 | PolicySnapshot | Congela contract+rules+gates al inicio de tarea |
| 9 | InvariantChecker | Invariantes de cierre (counters==0) cuando se requiere CLOSED |
| 10 | FinalCleanReAuditGate | Tras último FIX: 4 pasadas otra vez; gap nuevo → loop |
| 11 | VerdictAuthority | Único autorizado a PASS/FAIL/CLOSED |
| 12 | AuditTamperGuard | No alterar resultados previos sin nueva revisión; evidence ligada a mission/task/change/revision |

Flujo:
```
FORENSIC CONTRACT → POLICY SNAPSHOT
LLM ──proposal──→ STEP GATE → CONTRACT GATE → EVIDENCE GATE → STATE MACHINE → siguiente paso
Cierre: IMPLEMENT→AUDIT→GAP?→FIX/RE-AUDIT o FINAL 4-PASS→EVIDENCE→VERDICT AUTHORITY→CLOSED
```

---

## Formato salida + validación

```
FORENSIC CODE AUDIT v1.3
━━━━━━━━━━━━━━━━━━━━━━━━━━
PASS 1 STRUCTURE [✓/✗]  PASS 2 CONNECTIVITY [✓/✗]
PASS 3 BEHAVIOR [✓/✗]   PASS 4 FORENSIC CLOSURE [✓/✗]
ARCHITECTURE ↔ DOCS [✓/✗]  CONNECTIVITY [✓/✗]
REQ→CODE→TEST→EVIDENCE [✓/✗]  DEPS/CONTRACTS [✓/✗]
BEHAVIOR/ERROR PATHS [✓/✗]  IMPACT/REGRESSION [✓/✗]
EVIDENCE [✓/✗]
counters: gaps blocking broken orphans unreachable unresolved unverified pending new_gaps unexpected
RESULT: PASS / FAIL
VerdictAuthority only. LLM claim is not PASS.
```

## Loop método de trabajo (permanente)
Tras cada tarea: FORENSIC AUDIT → gaps → FIX → RE-AUDIT hasta PASS · luego siguiente tarea.
