# FORENSIC CODE AUDIT — Lista consolidada (por tarea)
**Fecha:** 2026-08-17  
**Fuente:** A–L + Delta filtrado + Lista1 (eliminar/condicional) + Lista2 (faltantes accionables) + FC-01..07  
**Regla:** CORE siempre · CONDITIONAL solo si aplica · loop hasta PASS

## CORE — siempre (cada tarea de programación)

| # | Capa | Criterio de cierre |
|---|------|--------------------|
| 01 | REQUIREMENT CLOSURE | REQ → code → test → evidence trazable |
| 02 | SCOPE / DIFF CLOSURE | diff ⊆ scope; unexpected files = 0 o aprobados |
| 03 | IMPLEMENTATION CLOSURE | DONE literal materializado (no subconjunto) |
| 04 | ARCHITECTURE / BOUNDARY | boundaries + doc↔repo match |
| 05 | DEPENDENCY CLOSURE | deps resueltas; nuevas deps justificadas |
| 06 | CONTRACT CLOSURE | inputs/outputs/errores explícitos si API pública |
| 07 | REAL WIRING CLOSURE | registered → resolved → called → exercised |
| 08 | BEHAVIOR / EDGE | escenarios aplicables NORMAL/EDGE/ERROR verificados |
| 09 | TEST EFFECTIVENESS | test fallaría si se rompe la lógica |
| 10 | REGRESSION / IMPACT | callers/deps impactados considerados |
| 11 | ERROR PATH CLOSURE | failure paths aplicables handled + tested |
| 12 | CODE QUALITY | complejidad/LOC archivo/cohesión aceptable |
| 13 | REPOSITORY TRUTH | paths/commits reales; sin 404 lógico |
| 14 | EVIDENCE + VERDICT | EvidencePacket completo; PASS solo con evidencia |

## FC — cierre forense (obligatorio)

| ID | Check |
|----|-------|
| FC-01 | Architecture ↔ project documentation |
| FC-02 | Full connectivity / wiring |
| FC-03 | Gap → Fix → Re-Audit loop |
| FC-04 | Requirement → Code → Test → Evidence |
| FC-05 | Change impact analysis |
| FC-06 | Real behavioral verification |
| FC-07 | Final independent re-audit (fixes no crean gaps nuevos) |

## CONDITIONAL — solo si aplica el cambio

| Gate | Activar cuando |
|------|----------------|
| SECURITY | auth, secrets, trust boundary, agent tools |
| DATABASE / MIGRATION | schema, persistencia, migraciones |
| PERFORMANCE | hot path, API latency, jobs pesados |
| CONCURRENCY | threads, async, shared state |
| EXTERNAL API | HTTP/SDK externos |
| AI / AGENT | LLM, tools, prompts, authority |
| PRODUCTION | runtime prod, deploy path |
| NEW DEPENDENCY | nueva lib/paquete |
| PERSISTENCE | state durable |
| DISTRIBUTED | multi-node, queues |
| MULTI-REPO | cambio cruza repos |

## NO bloquear tarea normal (Lista 1)

SBOM completo · licencias transitivas universales · SOC2/ISO/GDPR/HIPAA/PCI genérico · RTO/RPO · multi-region failover · SLO/SLA universales · multi-tenancy si no hay tenants · chaos/fault injection · shadow traffic universal · break-glass · secrets rotation drill · on-call · cost budget universal · model drift universal · artifact attestation por cada edit · offline audit pack por tarea · API freeze windows · PII si no hay datos personales.

## Formato de salida de auditoría (obligatorio)

```
FORENSIC CODE AUDIT
━━━━━━━━━━━━━━━━━━
[✓/✗] 1. ARQUITECTURA ↔ DOCUMENTACIÓN
[✓/✗] 2. CONECTIVIDAD / WIRING COMPLETO
[✓/✗] 3. REQUISITOS → CODE → TEST
[✓/✗] 4. DEPENDENCIAS / CONTRATOS
[✓/✗] 5. FUNCIONALIDAD / VARIANTES / ERRORES
[✓/✗] 6. IMPACTO / REGRESIONES
[✓/✗] 7. EVIDENCIA VERIFICABLE

GAPS:       N
BROKEN:     N
ORPHANS:    N
PENDIENTES: N

RESULTADO: PASS / FAIL
```

## Loop obligatorio

```
IMPLEMENT → AUDIT → GAPS?
  YES → CLASSIFY → FIX → RE-AUDIT → …
  NO  → FINAL RE-AUDIT → CLOSED
```

OPEN → FIXED → VERIFIED → CLOSED (nunca OPEN→CLOSED sin verify).

## Criterio CLOSED

```
blocking_gaps: 0
broken_connections: 0
orphan_components: 0
unresolved_dependencies: 0
unverified_requirements: 0
unverified_claims: 0
final_reaudit_passed: true
```

PASS nunca por afirmación de la IA; solo con evidencia.
