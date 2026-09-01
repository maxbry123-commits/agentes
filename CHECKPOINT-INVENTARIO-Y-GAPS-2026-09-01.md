# CHECKPOINT — Migración, estructura y componentes YAIWES/NCT

Fecha UTC: 2026-09-01T13:30:24.867Z

## Estado consolidado

- Estructuras comunes replicadas en 7/7 repositorios: PASS.
- Carpetas adicionales de Frontend: 9/9 PASS.
- Índices Markdown de auditoría de cuatro pasadas: 7/7 creados sin sobrescribir documentos.
- Movimiento de documentos y código desde `agentes/Desplegar`: PASS.
- Movimiento verificado de `agentes/Wordflow Code` a `nct-core/main`: PASS.
- Nombre literal `Fromtend code NCT` en `nct-core/main`: PASS.
- Revisión de posibles residuos: realizada; no se eliminó ningún archivo.
- Destino de componentes: `Agente core kernel Yaiwes principal`.

## Cola activa de componentes

- Workflow nuevo: `kernel-download-sequential-new.yml`.
- Ejecución: https://github.com/maxbry123-commits/agentes/actions/runs/33512303526
- PASS confirmados al crear este checkpoint: reubicación y lotes 01–05.
- En curso: lote 06; después siguen lote 07 y organización final.
- Inventario solicitado deduplicado: 148 componentes.
- Componentes ya existentes reubicados: 13.
- Descargas nuevas esperadas: 135.
- Manifiesto actual: 118 COMPLETE de 119 componentes registrados.

## GAP actual

- `Math-Shepherd`: clone; fuente solicitada https://github.com/RUCAIBox/Math-Shepherd.git devuelve 404.

La fuente pública oficial disponible para Math-Shepherd es el dataset de los autores: https://huggingface.co/datasets/peiyi9979/Math-Shepherd . Debe repararse en un workflow nuevo de GAPS, sin reactivar ejecuciones antiguas.

## Criterio de cierre 100 PASS

1. Ejecución secuencial completada.
2. 135/135 descargas con estado final COMPLETE y 0 SKIPPED vigentes.
3. 13 componentes existentes presentes en el destino final.
4. Partes ZIP presentes, trazables y dentro del límite configurado.
5. Índice final de componentes de cuatro pasadas creado sin sobrescritura.
