# Advanced Engineering Standard V3 + Forensic v1.3

**Auditoría forense completa:** PIPELINE/FORENSIC_CODE_AUDIT.md  

## Obligatorio en Wordflow
- CORE 14 + FC-01..13 + 4 pasadas
- 8 subsistemas Audit Engine
- Enforcement: PolicyEngine, StepGate, StateMachine, ContractGate, EvidenceGate, ApplicabilityEngine, PolicySnapshot, InvariantChecker, FinalCleanReAuditGate, VerdictAuthority, AuditTamperGuard
- LLM no declara PASS; VerdictAuthority sí
- Sin Context/Handoff verificado → BLOCK

## LOC
preferred 300–800 por archivo · review >800 · refactor >1000 · critical >1500 · proyecto sin límite LOC

## Código existente standards/
schema · rule_engine · architecture_manifest · dependency_graph · evidence · quality_dag · sheriff  
Salida 2: contrato schema de validación forense cableado en Wordflow.
