# FORENSIC CODE AUDIT v1.2.1
**Fecha:** 2026-08-18  
**Cambio:** recuperar detalles perdidos/debilitados dentro de categorías existentes (sin nuevas capas de sobreingeniería).

## Regla maestra
NO CONTEXT → NO PROGRAMMING · NO EVIDENCE → NO PASS · GAP → FIX → RE-AUDIT · 4 PASSES CLEAN → CLOSED

---

## CORE 14 (siempre) + detalle recuperado

| # | Capa | Detalle obligatorio |
|---|------|---------------------|
| 01 | REQUIREMENT CLOSURE | REQ→code→test→evidence |
| 02 | SCOPE / DIFF CLOSURE | unexpected_changes=0 o aprobados |
| 03 | IMPLEMENTATION CLOSURE | DONE literal completo |
| 04 | ARCHITECTURE / BOUNDARY | **domain boundaries · dependency direction · ports/adapters · forbidden boundary crossings** |
| 05 | DEPENDENCY CLOSURE | **circular_dependencies=0 · forbidden_imports=0 · forbidden_dependencies=0** |
| 06 | CONTRACT CLOSURE | **contratos versionados + compatibilidad** si API pública |
| 07 | REAL WIRING CLOSURE | declared→registered→resolved→invoked→executed→output consumed→behavior |
| 08 | BEHAVIOR / EDGE | normal/edge/error + **idempotency si hay side-effects** |
| 09 | TEST EFFECTIVENESS | test falla si se rompe la lógica |
| 10 | REGRESSION / IMPACT | **changed symbol → consumers → dependencies → tests → risk** |
| 11 | ERROR PATH CLOSURE | failure paths aplicables |
| 12 | CODE QUALITY | **FILE LOC: preferred≤800 · review>800 · refactor>1000 · critical>1500 · soft_min=300 (referencia, no mínimo obligatorio)** |
| 13 | REPOSITORY TRUTH | paths/commits reales |
| 14 | EVIDENCE + VERDICT | EvidencePacket; **AI output ≠ proof / ≠ verification / ≠ PASS** |

## FC-01..13
FC-01 Arch↔docs · FC-02 Connectivity · FC-03 Gap loop · FC-04 Traceability · FC-05 Impact · FC-06 Behavior · FC-07 Final re-audit · FC-08 Document context · FC-09 Doc↔code cross-verify · FC-10 Functional wiring · FC-11 Evidence-backed verdict · FC-12 Four-pass · FC-13 Anti-overengineering

## Detalles recuperados explícitos (F-01..17)
1. FILE LOC thresholds (arriba en 12)  
2. NO CIRCULAR → circular_dependencies=0  
3. NO FORBIDDEN IMPORTS → forbidden_imports/dependencies=0  
4. DOMAIN BOUNDARIES  
5. PORTS / ADAPTERS  
6. VERSIONED CONTRACTS  
7. CRITICAL VERIFICATION (comportamiento/evidencia crítica)  
8. AGENT RUNTIME AUTHORITY (si aplica: authority + tools allow/deny + enforcement runtime)  
9. NO DEFAULT PROD (si config sensible: unsafe production default = FAIL)  
10. DETERMINISTIC FIRST (si puede ser determinístico → no LLM por defecto)  
11. STATE OWNERSHIP (owner + mutation path + shared state controlado)  
12. CI FAIL-CLOSED: applicable required gate debe ejecutarse; required sin handler = FAIL; required SKIP = FAIL; optional SKIP OK; **SKIP ≠ PASS**  
13. SYMBOL → CONSUMERS → TESTS → RISK  
14. CLOSURE COUNTERS completos (abajo)  
15. IDEMPOTENCY cuando side-effects  
16. CONCURRENCY (si aplica): races · atomicity · locking · ordering · shared state  
17. unexplained_orphans=0 **y** unreachable_required_paths=0 (distintos)

## QualityDAG / gates
FORMAT · LINT · TYPE · STATIC · UNIT · INTEGRATION · CONTRACT · SECURITY · DEPS · ARCH · BUILD · AUDIT  
Solo gates **aplicables requeridos** son obligatorios.  
REQUIRED sin handler → FAIL · REQUIRED SKIP → FAIL · OPTIONAL SKIP → OK · SKIP ≠ PASS

## Closure counters (completos)
```
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

## 4 PASADAS
1 STRUCTURE · 2 CONNECTIVITY · 3 BEHAVIOR · 4 FORENSIC CLOSURE

## CONDITIONAL (solo si aplica)
Security · DB/Migration · Perf · Concurrency (detalle arriba) · External API · AI/Agent (authority runtime) · Production (no default prod) · New dependency · Persistence · Distributed · Multi-repo

## NO bloquear tarea normal
SBOM/licencias universales · compliance genérico · DR/RTO · SLO universal · chaos · shadow traffic · break-glass · rotation · on-call · cost universal · model drift · attestation por edit · offline pack · API freeze · multi-tenant/PII si no aplica

## Salida mínima
```
FORENSIC CODE AUDIT v1.2.1
━━━━━━━━━━━━━━━━━━
PASS 1 STRUCTURE [✓/✗]  PASS 2 CONNECTIVITY [✓/✗]
PASS 3 BEHAVIOR [✓/✗]   PASS 4 FORENSIC CLOSURE [✓/✗]

ARCHITECTURE ↔ DOCS [✓/✗]  CONNECTIVITY [✓/✗]
REQ→CODE→TEST→EVIDENCE [✓/✗]  DEPS/CONTRACTS [✓/✗]
BEHAVIOR/ERROR PATHS [✓/✗]  IMPACT/REGRESSION [✓/✗]
EVIDENCE [✓/✗]

blocking_gaps:0 broken:0 orphans:0 unreachable:0
unresolved_deps:0 unverified:0 pending:0 new_gaps_after_fix:0 unexpected:0
RESULT: PASS / FAIL
```

0 gaps = 0 bloqueantes aplicables del contrato ≠ cero mejoras posibles en el universo.
