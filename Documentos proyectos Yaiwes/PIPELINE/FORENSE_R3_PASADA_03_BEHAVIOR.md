# FORENSE R3 — PASADA 03 BEHAVIOR

Contrato vs code en `95eb881`. Tests no corridos en esta sesión (sandbox no clonó el repo privado).

## Contratos

| Contrato | R3 evidencia |
|----------|----------------|
| convert normaliza via inbox | SÍ — `_impl()` wordflow.reception.convert |
| ingest llama compiler | SÍ — `_compile` → `compile_or_reason` |
| ingest ubica fase | SÍ path; `wrote=False` |
| PLUGIN enchufe | SÍ `validate_ficha`; fail on-disk no bloquea `ingest.ok` |
| motor dispatch ingest | SÍ `KernelExtMotor.dispatch` |
| Fake E2E ≠ C-19 PASS | SÍ `c19_pass=bool(c19_ok)`; `__main__` exige False |
| C-19 sin context → BLOCK | diseño invocado con `context_verified=False` |
| audit_to_plan | RuntimeError sin inject (test_vk01 lo afirma) |

## Tests (existencia)

- `extensions/wordflow_kernel/tests/test_reception_ingest.py` (1052 B)
- `extensions/wordflow/tests/test_kernel_ext_motor_reception.py`
- CI: `.github/workflows/test-wordflow-code-path.yml` discover `test_*.py`

CORE-09: tests existen. Efectividad = **no medida** (no unittest adjunto).

## Error paths vivos

RECEPTION_IMPL_MISSING, INPUT_COMPILER_MISSING, TASK_CLASSIFIER_MISSING, ENCHUFE_MISSING, FICHA_NOT_ON_DISK, NO_INSTANCE, C-19 BLOCK, UNKNOWN_MOTOR.

## Veredicto R3 P3

**BEHAVIOR reception = PASS parcial.**
**BEHAVIOR repo = FAIL** (apply no, loop no orquesta C-19, tests no ejecutados aquí, audit_to_plan skeleton, plugin no fail-closes ingest).
