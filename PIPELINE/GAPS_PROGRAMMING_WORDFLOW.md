# Gaps Wordflow programación de code — post COPY-FIRST wire
**Fecha:** 2026-08-18

## Cerrados en esta iteración
- G-W1 parcial: `programming_pipeline.py` + bootstrap config hooks copy_first/forensic_post_verify
- Scanner: name + component_catalog
- Guía/método: COPY-FIRST + cadena CONTEXT→…→VERDICT

## Abiertos (mejora 100x candidata)
| ID | Gap | Severidad | Mejora 100x |
|----|-----|-----------|-------------|
| G-W2 | Post-verify no ejecuta tests reales | P1 | EdgeCaseRunner + TestEffectivenessChecker en DAG |
| G-W3 | Índice solo stem/catalog no AST symbols | P2 | symbol table / import graph query |
| G-W4 | code_path_runner aún no llama PreImplementGate | P1 | un call-site en code_path_runner.run |
| G-W5 | EvidencePacket no auto-llena SOURCE→DEST | P2 | hook en copy_file_deterministic → packet |
| G-W6 | FailClosed no integrado en CI workflow | P1 | job required gates |
| G-W7 | WiringGraph runtime no construido | P1 | RegistrationChecker sobre engines reales |
| G-W8 | PolicySnapshot no congelado por misión | P2 | snapshot JSON en instance state |
| G-W9 | ADAPT no reescribe imports auto | P2 | rewrite relativo mínimo determinista |
| G-W10 | Multi-repo COPY (router/frontend) no indexado | P2 | roots multi-repo opcionales |

## Cadena objetivo Wordflow programación
CONTEXT/HANDOFF → COPY-FIRST → IMPLEMENT → WIRE → FORENSIC 4-PASS → VERDICT → CLOSED|FIX
