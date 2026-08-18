# PIPELINE 00 — MÉTODO DE TRABAJO + ARQUITECTURA

**Fecha:** 2026-08-17 (V3 standards)  
**Estándar:** PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md  
**Code:** extensions/wordflow/standards/

## LEY
1. LOC preferido 300–800 **por archivo**; proyecto sin límite de LOC.
2. Code = profesional avanzado — **NUNCA MVP**.
3. Gaps **blocking (P0/P1)** = 100% resueltos antes de avanzar; P2 puede quedar como deuda registrada.
4. GitHub = única verdad; prohibido sandbox storage.
5. AI output ≠ proof of correctness.

## Enforcement
- RuleEngine (collectors reales: LOC, cycles, forbidden imports, evidence, MVP, gaps, AI-proof)
- ArchitectureManifest + DependencyGraph
- EvidencePacket obligatorio en claims críticos
- QualityDAG: required gate sin handler = FAIL (no SKIP→PASS)

## Formato salida
```
# CONTROL DE TRABAJO
1. TOTAL TAREAS V1
2. TERMINADAS
3. PENDIENTES
4. SIGUIENTE
5. PLAN
6. MÉTODO
7. CONFIRMACIÓN: NO sandbox storage · GitHub = verdad
```
