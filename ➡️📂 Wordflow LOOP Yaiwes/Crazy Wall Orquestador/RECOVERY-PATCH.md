# RECOVERY PATCH — Wordflow LOOP Yaiwes

Anclas canónicas:
- README: `➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme wordflow loop Yaiwes.md`
- STATE: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/STATE.json`
- CHECKPOINT: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/CHECKPOINT.json`
- BITÁCORA: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`

## Contrato de recuperación
1. Antes de mutar un nodo, registrar checkpoint, fuente, destino, SHA previo y objetivo literal.
2. Si falla una verificación, no continuar: marcar GAP, conservar evidencia del fallo y volver a investigación.
3. Investigar exactamente 20 alternativas distintas al delta fallido cuando aplique el LOOP de recuperación.
4. Seleccionar una alternativa por reglas deterministas y registrar por qué fue elegida.
5. Aplicar solo el delta autorizado; mantener el original recuperable por SHA/commit.
6. Repetir verificación real; si vuelve a fallar, reinyección del objetivo original y nuevo lote de 20 alternativas.
7. `ROLLBACK` restaura el SHA/commit anterior del archivo afectado; nunca se reconstruye de memoria.
8. Un nodo solo pasa a DONE cuando tiene `evidence_hash`, prueba verificable y trazabilidad al documento/chat fuente.
9. Las claves API nunca forman parte del parche: solo referencias a secretos.
10. Si README, STATE, CHECKPOINT o BITÁCORA divergen, el estado efectivo es GAP hasta reconciliación verificable.

## Recuperación del ledger histórico
El contenido literal histórico del README previo a la recuperación está anclado al commit `2d1c718f28333ef4b77e9c362f757bb74ff9c5cc` y blob `474af741abe3ac9c816f4406f0fc6e4e4490c2aa`; se usa como fuente de restauración, no como sustituto de evidencia actual.
