# P0 Enforcement redesign

## Catálogo
- CORE / CONDITIONAL / ADVISORY / REFERENCE
- `programming_points_catalog.py` v2.0.0
- 500 puntos externos = inventario; runtime usa subset con metadatos

## Motores nuevos
- ApplicabilityEngine
- ContextManifest + ContextValidator
- EvidenceVerifier (claim ≠ evidence)
- GapRegistry (OPEN→FIXED→VERIFIED→CLOSED)
- ClosureEngine
- ChecklistSheriff v2 (no downgrade required, version pin)

## Bypass
- `context_verified` / `handoff_verified` default **False**
- `enforce_post_verify` forced True unless `allow_skip_post_verify` (dev only)

## Reglas
- AGENT_CLAIM_IS_NOT_VERIFICATION
- AGENT_CANNOT_DOWNGRADE_REQUIRED_CHECK
