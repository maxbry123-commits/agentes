# Advanced Engineering Standard V3 + Forensic Closure

**Forense por tarea:** ver PIPELINE/FORENSIC_CODE_AUDIT.md (fuente de verdad de la checklist).

## Integración
- CORE 14 + FC-01..07 en cada tarea de code.
- CONDITIONAL gates solo si aplican.
- Lista 1 (compliance/DR/SLO/chaos/SBOM…) = **no** bloquean tarea normal.
- Lista 2 (traceability, wiring real, test effectiveness, unhandled paths, public API consumers, diff scope) = **sí** en CORE.

## Ejecutable
extensions/wordflow/standards/ (RuleEngine, EvidencePacket, QualityDAG, …)
Salida 2: contrato schema de validación forense en Wordflow (siguiente).
