# CHECKPOINT — Wordflow V1 gap recovery

**Fecha:** 2026-08-27
**Repo:** `maxbry123-commits/agentes`
**Rama:** `main`
**Regla:** FAIL-CLOSED / no fake PASS

## Alcance

Cerrar los tres gaps reportados en `test-wordflow` run `33040158205`:

1. V1 E2E bloqueado en `mission` por `Q01_objective` y `Q05_success_criteria`.
2. ABI test usando artifact id histórico incorrecto.
3. Re-ejecución CI real antes de declarar PASS.

## Evidencia del FAIL original

Run: `33040158205`
SHA: `94bddab5dd438f1270d4186fa48fe8873440f8ee`
Resultado: `474 tests`, `17 failures`, `11 errors`, `1 skipped`.

La traza muestra que `mission_from_raw()` llegaba a `mission_build → questions` con pendientes `Q01_objective` y `Q05_success_criteria`.

## Parche aplicado

### Mission

`extensions/wordflow/engine/loop_bridge.py`

Se añadió `allow_raw_literal_fallback`, desactivado por defecto. Solo `mission.py` lo habilita. Cuando el contrato literal ya fue validado y únicamente faltan Q01/Q05, el raw literal se copia de forma determinista a `objective` y `success_criteria`.

No se cambia el comportamiento genérico fail-closed de `bridge_to_lock()`.

### Ficha ABI

`extensions/wordflow/tests/test_w_gaps.py`

El test ahora valida el identificador real de `extensions/wordflow/ficha.v2.json`:

`wordflow.yaiwes.v1`

También valida `extension_type` y `entry_point` existentes. No se modificó la ficha para inventar un alias.

### Regresión

`extensions/wordflow/tests/test_mission.py` añade cobertura del fallback literal.

## Archivos tocados

- `extensions/wordflow/engine/loop_bridge.py`
- `extensions/wordflow/engine/mission.py`
- `extensions/wordflow/tests/test_w_gaps.py`
- `extensions/wordflow/tests/test_mission.py`
- este checkpoint

## Hot path

`extensions/wordflow/engine/code_path_runner.py` **NO MODIFICADO**.

## CI

El workflow `.github/workflows/test-wordflow.yml` sigue ejecutando la suite completa de `extensions/wordflow/tests` y tiene `workflow_dispatch`.

**Estado de CI final:** PENDING hasta observar un run posterior a estos cambios. No declarar PASS sin run verde.

## Resultado

- G1 mission gate: **PARCHEADO**
- G2 ficha ABI: **PARCHEADO**
- CI final: **PENDING / FAIL-CLOSED**
- Hot path: **INTACTO**
