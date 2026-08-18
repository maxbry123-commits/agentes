# FORENSIC CODE AUDIT v1.2.1 — LISTA COMPLETA
**Fecha:** 2026-08-18  
**Fuente de verdad de la auditoría forense de programación de code por tarea.**

## Regla maestra
```
NO CONTEXT → NO PROGRAMMING
NO CONTEXT → NO AUDIT
NO EVIDENCE → NO PASS
GAP → FIX → RE-AUDIT
FIX → 4 PASSES AGAIN
4 PASSES CLEAN → CLOSED
```
CLAIM ≠ PROOF. PASS = VERIFICATION + EVIDENCE.  
0 gaps = 0 bloqueantes aplicables del contrato ≠ cero mejoras posibles en el universo del software.

---

## CORE 14 — siempre (cada tarea de programación)

### 01 REQUIREMENT CLOSURE
- Cada requisito de la tarea debe mapearse a implementación.
- Cadena: REQUIREMENT → IMPLEMENTATION → TEST → EVIDENCE → CLOSED
- Código nuevo sin requisito = UNTRACEABLE_CODE (gap)
- Requisito sin code/test/evidence = unverified_requirement (gap)

### 02 SCOPE / DIFF CLOSURE
- TASK SCOPE vs ACTUAL DIFF
- unexpected_changes = 0 o cada archivo extra con reason + approved
- La IA no modifica archivos fuera de alcance sin justificación aprobada

### 03 IMPLEMENTATION CLOSURE
- DONE literal del Director materializado completo
- Prohibido recortar alcance y declarar terminado
- CODE_EXISTS ≠ FEATURE_COMPLETE

### 04 ARCHITECTURE / BOUNDARY CLOSURE
- Domain boundaries respetadas
- Dependency direction correcta (Domain ← Application ← Ports ← Adapters ← Infrastructure)
- Ports / Adapters presentes donde hay sistema externo
- Forbidden boundary crossings = 0
- Architecture documentada ↔ arquitectura real del repo

### 05 DEPENDENCY CLOSURE
- circular_dependencies = 0
- forbidden_imports = 0
- forbidden_dependencies = 0
- Dependencias nuevas justificadas y resueltas
- Imports prohibidos del ArchitectureManifest no presentes

### 06 CONTRACT CLOSURE
- Si hay API/función/evento/plugin público: input, output, errores explícitos
- Contratos versionados
- Compatibilidad / no breaking silencioso
- Consumer conocido o ORPHAN_PUBLIC_API = gap

### 07 REAL WIRING / FUNCTIONAL CONNECTIVITY CLOSURE
Cadena obligatoria:
```
DECLARED → REGISTERED → RESOLVED → INVOKED → EXECUTED → OUTPUT CONSUMED → BEHAVIOR VERIFIED
```
Detectar:
- broken_connections = 0
- unresolved_dependencies = 0
- unexplained_orphans = 0
- unreachable_required_paths = 0
- unverified_paths = 0
- missing_registrations = 0
Existencia de clase/import/registro ≠ conectado.

### 08 BEHAVIOR / EDGE CLOSURE
- expected behavior ↔ actual behavior
- Escenarios aplicables: NORMAL, EDGE, ERROR, EMPTY, INVALID, DEPENDENCY_FAILURE, TIMEOUT, DUPLICATE, CANCEL
- Solo los aplicables al cambio (no inventar todos)
- Si hay side-effects: idempotency verified bajo retry/repeat

### 09 TEST EFFECTIVENESS
- El test debe fallar si se introduce un defecto intencional en la lógica del DONE
- Test que siempre pasa = TEST_WEAK (gap)
- Proporcional al cambio (no mutation suite completa obligatoria en todo)

### 10 REGRESSION / IMPACT CLOSURE
Cadena:
```
changed symbol → consumers → dependencies → contracts → tests → risk
```
- ¿Qué puede romperse?
- ¿Qué tests cubren a los consumidores?
- Impacto no solo marcado ✓ sin cadena

### 11 ERROR PATH CLOSURE
- APPLICABLE_FAILURE_PATHS identified → handled → tested
- No dejar rutas de error silenciosas en el alcance del cambio

### 12 CODE QUALITY / COMPLEXITY
FILE LOC:
- preferred_max: 800
- review_threshold: 800
- refactor_threshold: 1000
- critical_threshold: 1500
- soft_min: 300 (referencia de diseño, NO mínimo obligatorio)
También: complejidad cognitiva/ciclomática razonable, cohesión, sin god-objects, sin secretos en source.

### 13 REPOSITORY TRUTH
- Paths y commits reales en GitHub
- Sin referencias a archivos inexistentes
- PIPELINE/docs coherentes con el árbol
- Sin claim de archivos no commiteados

### 14 EVIDENCE + VERDICT
- EvidencePacket (mission/task/change/revision/files/tests/checks/verdict)
- AI output ≠ evidence
- AI output ≠ verification
- AI output ≠ PASS
- Cada PASS crítico referencia: repository, path, test o commit/revision

---

## FC — cierre forense obligatorio

| ID | Nombre | Qué exige |
|----|--------|-----------|
| FC-01 | Architecture ↔ Project Documentation | Doc y repo alineados |
| FC-02 | Full Connectivity / Wiring | Cadena de conectividad completa |
| FC-03 | Gap → Fix → Re-Audit Loop | OPEN→FIXED→VERIFIED→CLOSED; nunca OPEN→CLOSED |
| FC-04 | Requirement → Code → Test → Evidence | Trazabilidad bidireccional |
| FC-05 | Change Impact Analysis | symbol→consumers→tests→risk |
| FC-06 | Real Behavioral Verification | expected vs actual |
| FC-07 | Final Independent Re-Audit | Fixes no crean gaps nuevos |
| FC-08 | Document Context Verification | Contexto suficiente antes de programar/auditar; si falta → BLOCK |
| FC-09 | Document ↔ Code Cross-Verification | DOC_ONLY, CODE_ONLY, DOC_CODE_MISMATCH, CODE_TEST_MISMATCH, TEST_EVIDENCE_MISMATCH |
| FC-10 | Functional Wiring Verification | declared…behavior verified |
| FC-11 | Evidence-Backed Verdict | Ningún PASS por afirmación |
| FC-12 | Four-Pass Audit | 4 pasadas obligatorias |
| FC-13 | Anti-Overengineering | Minimal audit ≠ minimal quality; no omitir verificación requerida |

---

## 4 PASADAS (FC-12) — todas obligatorias antes de CLOSED

### PASS 1 — STRUCTURE
Revisa: docs → architecture → repository → files → dependencies → boundaries → contracts → documentación desactualizada  
Busca: archivos faltantes, archivos inesperados, arquitectura incorrecta, deps, boundaries, contratos.

### PASS 2 — CONNECTIVITY
Revisa: requirement → component → registration → resolution → invocation → execution → consumer  
Busca: código aislado, wiring roto, registros inexistentes, rutas no alcanzables, outputs no consumidos, referencias sin resolver.

### PASS 3 — BEHAVIOR
Revisa: expected ↔ actual  
Comprueba: casos normales, edge aplicables, errores, estados, regresiones, tests efectivos, idempotencia si side-effects.

### PASS 4 — FORENSIC / CLOSURE
Revisa: findings → fixes → re-audit → evidence → final verdict  
Busca: gaps restantes, conexiones rotas, gaps creados por fixes, claims sin evidencia, cambios fuera de scope, inconsistencias doc↔code.

---

## Detalles recuperados explícitos (no debilitar)

1. FILE LOC thresholds (CORE 12)  
2. circular_dependencies = 0  
3. forbidden_imports = 0 / forbidden_dependencies = 0  
4. Domain boundaries  
5. Ports / Adapters  
6. Versioned contracts + compatibility  
7. Critical verification explícita  
8. Agent runtime authority (si aplica): authority definida, tools permitidas/prohibidas, enforcement en runtime  
9. No default prod (si config sensible): unsafe production default = FAIL  
10. Deterministic first: si puede ser determinístico, no LLM por defecto  
11. State ownership: owner definido, mutation path definido, shared state controlado  
12. CI fail-closed: applicable required gate debe ejecutarse; required sin handler = FAIL; required SKIP = FAIL; optional SKIP permitido; SKIP ≠ PASS  
13. Impact: symbol → consumers → dependencies → tests → risk  
14. Closure counters completos (sección siguiente)  
15. Idempotency cuando hay side-effects  
16. Concurrency si aplica: race conditions, atomicity, locking strategy, ordering, shared state  
17. unexplained_orphans = 0 **y** unreachable_required_paths = 0 (distintos)

---

## QualityDAG / gates de validación de code

Orden de referencia:
FORMAT → LINT → TYPE → STATIC → UNIT → INTEGRATION → CONTRACT → SECURITY → DEPS → ARCH → BUILD → AUDIT

Reglas de ejecución:
- Solo gates **aplicables y requeridos** para el cambio son obligatorios
- REQUIRED gate sin handler → FAIL
- REQUIRED gate SKIP → FAIL
- OPTIONAL gate SKIP → permitido
- SKIP ≠ PASS

---

## Closure counters (todos)

```yaml
closure:
  gaps: 0
  blocking_gaps: 0
  broken_connections: 0
  unexplained_orphans: 0
  unreachable_required_paths: 0
  unresolved_dependencies: 0
  unverified_paths: 0
  unverified_requirements: 0
  unverified_claims: 0
  pending_fixes: 0
  new_gaps_after_fix: 0
  unexpected_changes: 0
```

---

## Gap loop (FC-03)

```
IMPLEMENT → AUDIT → CLASSIFY_GAPS → FIX → RE_AUDIT → …
```
Estados: OPEN → FIXED → VERIFIED → CLOSED  
Prohibido: OPEN → CLOSED sin verificación  
Cada gap: gap_id, severity, description, location, root_cause, required_fix, implemented_fix, verification, evidence, status  
Iteraciones ilimitadas hasta blocking aplicables = 0 y final re-audit limpio.

---

## CONDITIONAL — solo si el cambio lo activa

| Gate | Activar cuando |
|------|----------------|
| SECURITY | auth, secrets, trust boundary, agent tools |
| DATABASE / MIGRATION | schema, persistencia, migraciones |
| PERFORMANCE | hot path, API latency, jobs pesados |
| CONCURRENCY | threads, async, shared state (races/atomicity/locking/ordering) |
| EXTERNAL API | HTTP/SDK externos |
| AI / AGENT | LLM, tools, prompts, authority runtime |
| PRODUCTION | runtime prod, deploy path, no unsafe default prod |
| NEW DEPENDENCY | nueva lib/paquete |
| PERSISTENCE | state durable |
| DISTRIBUTED | multi-node, queues |
| MULTI-REPO | cambio cruza repos |

---

## NO bloquear tarea normal (no universales)

SBOM completo · licencias transitivas universales · SOC2/ISO/GDPR/HIPAA/PCI genérico · RTO/RPO · multi-region failover · backup/restore drills · SLO/SLA/error budget universales · multi-tenancy si no hay tenants · chaos/fault injection universal · shadow traffic/replay universal · break-glass · secrets rotation drill · on-call/incident readiness · cost budget universal · model/provider drift universal · artifact attestation por cada edit · offline audit pack por tarea · cross-team API freeze windows · PII/retention si el cambio no maneja datos personales.

---

## Anti-sobreingeniería (FC-13)

```
MINIMAL AUDIT ≠ MINIMAL QUALITY
ELIMINAR CONTROLES NO APLICABLES ≠ ELIMINAR CONTROLES NECESARIOS
```
La auditoría aplica el nivel mínimo de complejidad necesario para verificar el cambio, sin omitir verificación requerida ni degradar arquitectura, seguridad, conectividad, calidad o funcionalidad.

---

## FORENSIC_CODE_CONTRACT v1.2.1

```yaml
FORENSIC_CODE_CONTRACT:
  version: "1.2.1"
  core:
    requirements: REQUIRED
    scope_diff: REQUIRED
    implementation: REQUIRED
    architecture: REQUIRED
    dependencies: REQUIRED
    contracts: REQUIRED
    connectivity: REQUIRED
    behavior: REQUIRED
    tests: REQUIRED
    regression_impact: REQUIRED
    error_paths: REQUIRED
    code_quality: REQUIRED
    repository_truth: REQUIRED
    evidence: REQUIRED
  context:
    required_before_implementation: true
    required_before_audit: true
    missing_context: BLOCK
    cross_verify_documents: true
  connectivity:
    declared: REQUIRED
    registered: REQUIRED
    resolved: REQUIRED
    invoked: REQUIRED
    executed: REQUIRED
    output_consumed: REQUIRED
    behavior_verified: REQUIRED
  audit:
    passes_required: 4
    pass_1: STRUCTURE
    pass_2: CONNECTIVITY
    pass_3: BEHAVIOR
    pass_4: FORENSIC_CLOSURE
    all_passes_required: true
  loop:
    sequence: [IMPLEMENT, AUDIT, CLASSIFY_GAPS, FIX, RE_AUDIT]
    if_gap_found: FIX_AND_REAUDIT
    require_clean_reaudit: true
    unlimited_iterations: true
    states: [OPEN, FIXED, VERIFIED, CLOSED]
    forbidden_transition: [OPEN_TO_CLOSED]
  engineering:
    avoid_overengineering: true
    preserve_architecture: true
    preserve_quality_standard: true
    remove_non_applicable_checks: true
    never_remove_required_verification: true
  file_loc:
    preferred_max: 800
    review_threshold: 800
    refactor_threshold: 1000
    critical_threshold: 1500
    soft_min: 300
  closure:
    gaps: 0
    blocking_gaps: 0
    broken_connections: 0
    unexplained_orphans: 0
    unreachable_required_paths: 0
    unresolved_dependencies: 0
    unverified_paths: 0
    unverified_requirements: 0
    unverified_claims: 0
    pending_fixes: 0
    new_gaps_after_fix: 0
    unexpected_changes: 0
  evidence:
    required: true
    claim_is_not_proof: true
    every_critical_pass_requires_evidence: true
    evidence_must_reference: [repository, path, test, commit_or_revision]
  gates:
    required_without_handler: FAIL
    required_skip: FAIL
    optional_skip: ALLOW
    skip_equals_pass: false
  verdict:
    PASS_ONLY_IF:
      - context_verified
      - all_required_checks_pass
      - all_four_audit_passes_complete
      - blocking_gaps == 0
      - broken_connections == 0
      - unexplained_orphans == 0
      - unreachable_required_paths == 0
      - unresolved_dependencies == 0
      - unverified_requirements == 0
      - unverified_claims == 0
      - pending_fixes == 0
      - new_gaps_after_fix == 0
      - unexpected_changes == 0
      - evidence_complete
      - final_clean_reaudit_passed
    FAIL_IF:
      - required_check_fails
      - required_context_missing
      - blocking_gap_exists
      - broken_connection_exists
      - evidence_missing
      - final_reaudit_fails
```

---

## Formato de salida obligatorio de cada auditoría

```
FORENSIC CODE AUDIT v1.2.1
━━━━━━━━━━━━━━━━━━━━━━━━━━
PASS 1 — STRUCTURE            [✓/✗]
PASS 2 — CONNECTIVITY         [✓/✗]
PASS 3 — BEHAVIOR             [✓/✗]
PASS 4 — FORENSIC CLOSURE     [✓/✗]

ARCHITECTURE ↔ DOCS           [✓/✗]
CONNECTIVITY                  [✓/✗]
REQ → CODE → TEST → EVIDENCE  [✓/✗]
DEPENDENCIES / CONTRACTS      [✓/✗]
BEHAVIOR / ERROR PATHS        [✓/✗]
IMPACT / REGRESSION           [✓/✗]
EVIDENCE                      [✓/✗]

GAPS:                         N
BLOCKING_GAPS:                N
BROKEN:                       N
ORPHANS:                      N
UNREACHABLE:                  N
UNRESOLVED_DEPS:              N
UNVERIFIED:                   N
PENDING:                      N
NEW_GAPS_AFTER_FIX:           N
UNEXPECTED_CHANGES:           N

RESULT: PASS / FAIL
```

VALIDACIÓN: PASS solo si todos los [✓] aplicables + counters bloqueantes = 0 + evidence + final_clean_reaudit.  
FAIL si cualquier [✗] bloqueante o counter > 0.  
La IA no declara PASS por afirmación propia.
