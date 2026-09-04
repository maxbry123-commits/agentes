# FORENSE R2 — PASADA 03 BEHAVIOR

## Contratos vs runtime post-fix

| Contrato | R2 |
|----------|----|
| convert normaliza | SÍ |
| ingest llama compiler | SÍ (code) |
| ingest ubica fase | SÍ path; **no** write |
| PLUGIN enchufe | SÍ validate_ficha |
| motor dispatch ingest | SÍ |
| handle ingest | SÍ |
| Fake E2E ≠ C-19 PASS | SÍ `c19_pass=False` |
| C-19 sin context → BLOCK | SÍ |
| force reject / HOLD / token_ref | SÍ |
| audit_to_plan | RuntimeError sin inject |

## Tests añadidos (existencia, no corridos aquí)

- `extensions/wordflow_kernel/tests/test_reception_ingest.py`
- `extensions/wordflow/tests/test_kernel_ext_motor_reception.py`

CORE-09: hay tests nuevos. Efectividad no medida en esta sesión (no unittest ejecutado contra GitHub).

## Error paths

RECEPTION_IMPL_MISSING, INPUT_COMPILER_MISSING, FICHA_NOT_ON_DISK, C-19 BLOCK, UNKNOWN_ACTION: siguen.

Nuevo: ingest con convert ok + compiler invoked puede `ok=True` aunque plugin falle on-disk (ok de ingest solo exige convert+compiler invoked). Eso es un borde: PLUGIN no bloquea ingest.

## Veredicto R2 P3

**BEHAVIOR reception = PASS parcial.**  
**BEHAVIOR repo = FAIL** (apply, loop orquesta, test run no evidenciado, audit_to_plan).
