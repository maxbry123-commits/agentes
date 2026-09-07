# RECOVERY PATCH — Wordflow LOOP Yaiwes

Contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Ancla histórica
Recovery anterior recuperable por blob `10f867caef72b284cad2a2e6b349e7e6eb8750eb`. No reconstruir desde memoria.

## Checkpoint actual
- `WFLOOP-PLAN30-0014`.
- T01–T15 `VERIFIED_CLOSED`; T16 `EN_CURSO`; T17–T30 `PENDIENTE`.
- Avance verificable: 15/30 = 50%.
- Nodo único: `PLAN30_T16_FICHA_CONTRACTS`.
- Evidence parcial T16: `EVIDENCE-PLAN30-T16-PARTIAL.md`.
- Evidence hash T16: `75e2ec13ccfac3d24344a30ba4cfeb438164b2d24ea737bdf46fd97e0bf9b5a6`.

## Estado material T16
Cuatro Fichas Contract v2 existen y tienen read-back GitHub PASS: `bc885059ed0a97f73aad02572853d1b0a4f8117d`, `7fdb64b7a21fe51c278dcc907b09eb800f2a2770`, `4ce82a32faa939177dd22603f097402e9b9e6ed9`, `44aeb5cb48db6d42499bc940e47e912942d7fd40`. Descriptor provenance schema=`5c3aa0b42fb9737baeb1f151a933fa83cc72c27d`, registry=`5274c96b79a4862d4081be18b80c1c0b09d9607a`.

## GAP activo
La fuente canónica histórica Ficha Contract v2 está fijada en commit `37bef3a8a8f6dadca067638b8ea0c32995fc1d63`, blob `b27f14b4d64f77bccf53a893c49b6f20bd58e745`. En esta corrida no pudo ejecutarse el archivo exacto en runtime local por fallo de resolución de red. Por FAIL_CLOSED_LOOP, la comprobación estructural local no sustituye `verify_final` canónico.

## Reanudación 1×1
1. Releer HANDOFF, README Wordflow, README arquitectura, STATE, CHECKPOINT, RECOVERY, BITACORA, PLAN y `EVIDENCE-PLAN30-T16-PARTIAL.md`.
2. Mantener exactamente O01–O11.
3. Confirmar blobs 4/4 de Fichas y destinos T10–T14.
4. Materializar/ejecutar la fuente exacta del validador canónico fijado arriba sin cambiar StrategyDelta.
5. Validar 4/4 Fichas y registrar stdout/veredicto reproducible.
6. Si cualquier Ficha falla, volver a T16 con delta materialmente distinto; no tocar T17.
7. Si 4/4 PASS, cross-check paths + auditorías/refutaciones + persistencia; solo entonces T16 `VERIFIED_CLOSED` y T17 puede activarse.

## Fail-closed
Presencia ≠ PASS. No afirmar ejecución exacta del validador hasta tener log real. Check determinista puro 1×; potencialmente inestable hasta 10×. No LFS ni workflows antiguos.