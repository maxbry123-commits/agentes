# Advanced Engineering Code Standard V2
**Origen:** reception/advanced_engineering_code_standard_guia_maestra.md  
**Mejorado:** Cursor-native + Wordflow ejecutable  
**Fecha:** 2026-08-17

## LEY explícita (Director)
1. **≤300–800 LOC = límite por archivo**, no del proyecto ni de la calidad.
2. **Code = nivel profesional avanzado — NUNCA MVP.**
3. **Gaps de auditoría = 100% resueltos antes de avanzar.**

## Definición de code avanzado (18 criterios)
Correctness · Diseño · Baja complejidad accidental · Modularidad · Bajo acoplamiento · Alta cohesión · Contratos · Dependencias controladas · Testabilidad · Seguridad · Fiabilidad · Observabilidad · Auditabilidad · Escalabilidad · Reproducibilidad · Evolución controlada · Automatización de calidad · Gobierno de agentes IA.

## Cursor / AI-Native (obligatorio)
```
Generate → Inspect → Plan → Edit → Test → Verify → Review → Evidence → Merge
```
Nunca: Generate → Merge.  
AI output ≠ proof of correctness.  
Context: CQ1–CQ8 (repo map, arch rules, domain, files, contracts, tests, deps, decisions).

## RULES machine-enforced (sheriff)
RULE-001 FILE_LOC preferred ≤800  
RULE-002 PROJECT_LOC unlimited  
RULE-003 NO circular dependencies  
RULE-004 NO forbidden imports  
RULE-005 Domain isolated from infrastructure  
RULE-006 External systems via ports/adapters  
RULE-007 Public contracts versioned  
RULE-008 Critical ops produce evidence  
RULE-009 Critical changes require verification  
RULE-010 Architecture rules machine-enforced  
RULE-011 Agents under explicit authority  
RULE-012 Production access not default  
RULE-013 Secrets never in source  
RULE-014 Dependencies auditable  
RULE-015 Changes require impact analysis  
RULE-016 AI output never proof of correctness  
RULE-017 Deterministic execution preferred  
RULE-018 Scale via modules not mega-files  
RULE-019 State/side-effects explicit ownership  
RULE-020 CI fails closed on critical violations  
RULE-021 Gaps 100% resolved before next task  
RULE-022 Never MVP — professional advanced only  

## Quality gate DAG (resumen)
FORMAT → LINT → TYPE → STATIC → UNIT → INTEGRATION → CONTRACT → SECURITY → DEPS → ARCH → BUILD → AUDIT → PASS | FAIL_CLOSED

## Implementación ejecutable
- `extensions/wordflow/standards/schema.py` — contrato del estándar
- `extensions/wordflow/standards/sheriff.py` — gates RULE-001..022
- `extensions/wordflow/standards/quality_dag.py` — DAG de quality gates

## Guía original (fuente)
https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/reception/advanced_engineering_code_standard_guia_maestra.md
