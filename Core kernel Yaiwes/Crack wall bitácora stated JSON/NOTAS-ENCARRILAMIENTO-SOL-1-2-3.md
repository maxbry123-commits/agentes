# NOTAS DE ENCARRILAMIENTO — SOL integración 1 / 2 / 3

## COORDINADOR

`➡️ sol osquestador plan` = coordinador operativo del trabajo de integración.

Estado reconciliado con Crazy Wall fresco y evidencia de `main`: la cola N21–N27 está cerrada. No reclamar, reabrir ni repetir STEP1/STEP2/STEP3 de ningún nodo N1–N27.

Contrato preservado: `STEP1 analizar A/B/C+destino -> STEP2 mover con motor canónico -> STEP3 cablear/podar solo si hace falta+microtest`.
FAST PATH preservado: read-back físico primero; no repetir pasos verificados; separar `COMPONENT_FAIL` de `PUBLISH/WORKFLOW_FAIL`.

## SOL integración 1

- Lane cerrada.
- N21 Dagu = `COMPLETE / STEP3 PASS`; evidencia de cierre: commit `e0b1b0c42bfaccf8f6b4b9aa4d812993db98d871` (`Dagu N21 FABLES real DAG STEP3 PASS`).
- N26 gVisor = `COMPLETE / STEP3 PASS`; evidencia de cierre: commit `7731709fb8552406dbbab08496a65553f145b231`, run `34565671367`, microtest `runsc_do_privileged_ci_ptrace`, resultado 41/returncode 0.
- Instrucción mínima: no tocar N21 ni N26; sin fallback pendiente.

## SOL integración 2

- Lane cerrada.
- N27 pgvector = `COMPLETE / STEP3 PASS`; evidencia de cierre: commit `4de1315443a68ecd5ffb16bd6249acec72b22307` (`pgvector N27 real extension STEP3 PASS`).
- N25 Workalendar = `COMPLETE`; evidencia previa: Motor4 move commit `a97b5d8804ed76996027dbb254af3ad70b9f4c80`, verify run `34545474663`.
- Instrucción mínima: no tocar N27 ni N25; sin fallback pendiente.

## SOL integración 3

- Lane cerrada.
- N23 PostgreSQL = `COMPLETE / STEP3 PASS`; evidencia de cierre: commit `8e0e9d070baa7bd1cff3f47d58c18cb35790760a` (`PostgreSQL N23 real server STEP3 PASS`).
- Instrucción mínima: no tocar N23; sin fallback pendiente.

## NODOS CERRADOS — NO REABRIR

- N1–N20 = `VERIFIED_CLOSED`.
- N21 Dagu = `COMPLETE`.
- N22 Hatchet = `COMPLETE`.
- N23 PostgreSQL = `COMPLETE`.
- N24 Redis = `COMPLETE`.
- N25 Workalendar = `COMPLETE`.
- N26 gVisor = `COMPLETE`.
- N27 pgvector = `COMPLETE`.

## REGLA DE-KERNEL

Se mantiene sin cambios: no adoptar otra cabeza/kernel por defecto; clasificar B/C y extraer workflow/tools/microservicios/componentes. Cualquier valor irreducible requiere `KERNEL_VALUE_REVIEW` y aprobación del usuario antes de integración.

## INVENTARIO ACTUAL

N1–N27: cerrados/verificados según sus evidencias de STEP3 o cierre previo.
Claims coordinados pendientes: ninguno.
Colas SOL1/SOL2/SOL3: vacías.
`next_action`: `NONE_WITHIN_CURRENT_QUEUE; DO_NOT_REOPEN`.

## SINCRONIZACIÓN

Si en el futuro aparece una discrepancia de publicación, aplicar únicamente: `Crazy Wall fresco -> read-back físico/runtime evidence -> distinguir PUBLISH/WORKFLOW_FAIL de COMPONENT_FAIL`. Un fallo de publicación no reabre un componente ya cerrado con evidencia real.
