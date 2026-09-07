# RECOVERY PATCH — Wordflow LOOP Yaiwes

Contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Ancla histórica
Recovery anterior recuperable por blob `394056f75cc5f2f5add1a742f142eed2faa666d7`. No reconstruir desde memoria.

## Checkpoint actual
- `WFLOOP-PLAN30-0013`.
- T01–T15 `VERIFIED_CLOSED`; T16 `EN_CURSO`; T17–T30 `PENDIENTE`.
- Avance verificable: 15/30 = 50%.
- Nodo único: `PLAN30_T16_FICHA_CONTRACTS`.
- Evidence `EVIDENCE-PLAN30-T10-T15.md` blob `f8a5db43fb0cc9e1712620c75b579229c7bad14a`.
- Evidence hash `1c580531ccb6570c2dd8a7a396a6559c86a388c0c7c2eb6da065be5b63bf5119`.

## Reanudación 1×1
1. Releer HANDOFF, README Wordflow, README arquitectura, STATE, CHECKPOINT, RECOVERY, BITACORA y PLAN.
2. Mantener exactamente O01–O11; no inventar objetivos.
3. Confirmar T16 único nodo activo y T15 cerrado.
4. Leer módulos T10–T14 + Ficha Contract v2 + Universal Plugin Bus v2 canónicos.
5. Ejecutar solo T16: crear/ajustar Ficha/contratos separados de adapters/plugins/registry/guards/tests.
6. Validar schema/contrato con check falsificable; fallo => GAP + 6 causas + research ≥10 vías/hasta20 soluciones + StrategyDelta distinto.
7. Persistir BITACORA+STATE+CHECKPOINT+PLAN+RECOVERY antes de avanzar.
8. T17 bloqueado hasta verify_final de T16.

## Fail-closed
Presencia ≠ PASS. No afirmar test nuevo si solo se leyó evidencia previa. Divergencia de SHA vuelve al primer nodo afectado. Check determinista puro 1×; potencialmente inestable hasta 10×. No LFS ni reactivar workflows antiguos.

## Rollback
Base previa de esta reconciliación: `main` commit `3ab973ca6cd8993b0bcb35b7fad3556006f43f92`; blobs previos están registrados en CHECKPOINT.