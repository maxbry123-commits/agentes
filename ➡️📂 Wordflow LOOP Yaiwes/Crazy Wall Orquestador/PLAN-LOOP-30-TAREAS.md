# PLAN LOOP — 30 TAREAS — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · cola `1x1`.
Objetivo final: convertir documentos/proyectos YAIWES en requisitos trazables, tareas de programación, código ejecutable modular integrado en el microkernel YAIWES, plugins/cableado, tests, reparación, auditoría, persistencia, recovery y evidencia E2E.

## Cola maestra 30 tareas
| # | Objetivo | Tarea | Estado |
|---|---|---|---|
| 01 | O02 | Reconciliar anclas/objetivo/roles | VERIFIED_CLOSED |
| 02 | O02 | Consolidar inventario de código candidato | VERIFIED_CLOSED |
| 03 | O02 | Verificar runner 1x1 | VERIFIED_CLOSED |
| 04 | O02 | Verificar pause/resume | VERIFIED_CLOSED |
| 05 | O02 | Verificar identidad/reinyección | VERIFIED_CLOSED |
| 06 | O02 | Verificar input_hash/node/attempt/checkpoint | VERIFIED_CLOSED |
| 07 | O02 | Verificar strategy/failure-memory | VERIFIED_CLOSED |
| 08 | O02 | Mapear candidatos a destino | VERIFIED_CLOSED |
| 09 | O02 | Manifiesto provenance/compatibilidad | VERIFIED_CLOSED |
| 10 | O03 | Reusar módulo cola 1x1 | VERIFIED_CLOSED |
| 11 | O03 | Reusar módulo pause/resume | VERIFIED_CLOSED |
| 12 | O03 | Reusar módulo identidad/checkpoint | VERIFIED_CLOSED |
| 13 | O03 | Reusar módulo input_hash/node_state | VERIFIED_CLOSED |
| 14 | O03 | Reusar strategy/failure-memory | VERIFIED_CLOSED |
| 15 | O03 | Patches quirúrgicos necesarios | VERIFIED_CLOSED |
| 16 | O04 | Crear/ajustar Ficha/contrato de módulos integrados | EN_CURSO |
| 17 | O04 | Cablear adapters/plugins a registry | PENDIENTE |
| 18 | O04 | Health/evidence hooks fail-closed | PENDIENTE |
| 19 | O05 | 5 pasadas docs↔arquitectura↔code↔contratos↔tests | PENDIENTE |
| 20 | O06 | Contratos de tareas de agentes | PENDIENTE |
| 21 | O07 | Cablear OpenCode | PENDIENTE |
| 22 | O07 | Cablear OpenHands | PENDIENTE |
| 23 | O07 | Cablear Claude Code + Mimo Code | PENDIENTE |
| 24 | O07 | Auditores + Council12 + embudo | PENDIENTE |
| 25 | O08 | HF/3 procesadores con health real | PENDIENTE |
| 26 | O09 | Graphiti/Grapify/SQL/HF storage | PENDIENTE |
| 27 | O10 | APIs/modelos por secret_ref | PENDIENTE |
| 28 | O11 | Tests unit/integración/E2E | PENDIENTE |
| 29 | O11 | Checks inestables hasta 10x + recovery | PENDIENTE |
| 30 | O11 | Auditoría final + verify_final | PENDIENTE |

## Evidencia reconciliada
- T02–T09: `CODE-CANDIDATE-MANIFEST-PLAN30.md`.
- T10–T15: `EVIDENCE-PLAN30-T10-T15.md` blob `f8a5db43fb0cc9e1712620c75b579229c7bad14a`.
- T10 source `daa32a5d6dfeb0d21a975b8a5b8384d68a8aa08e` → dest `77017b70239cedcce26f1df4a076272572f0927b`.
- Test blob `e1b1e3a4e4ca79e5dee00d5676a6038c6426bc31`, commit `3b7f0cec153ef03656f76dcd693c17fe061f7a78`, resultado registrado `5 passed in 0.06s`.
- T16 parcial: `EVIDENCE-PLAN30-T16-PARTIAL.md`; 4 Fichas Contract v2 materializadas y read-back PASS, pero ejecución exacta del validador canónico quedó bloqueada por resolución de red; T16 NO se cierra.
- T16 evidence hash: `75e2ec13ccfac3d24344a30ba4cfeb438164b2d24ea737bdf46fd97e0bf9b5a6`.
- Evidence hash previo T10–T15: `1c580531ccb6570c2dd8a7a396a6559c86a388c0c7c2eb6da065be5b63bf5119`.

Cadena obligatoria: `INPUT literal → GOALS12 → prioridades → plan → cola1x1 → delta → verify/refute → GAP research10/hasta20 + StrategyDelta distinto → Council12 → auditor×3 → output12 → refutaciones×3 → cross-check → CODA → verify_final → persistencia`.
No PASS por presencia: exigir ruta+SHA/diff+test/log/URL+evidence.