# Revisión de basura y limpieza — agentes/main

Fecha: 2026-09-01  
Estado: **REVISADO — SIN ELIMINACIONES**

## Resultado

No se detectó ningún elemento que pueda eliminarse con seguridad automática sin una decisión de conservación. Se preservaron todos los documentos, código y snapshots.

## Candidatos de normalización

1. `Yaiwes ` — nombre raíz con espacio final. Requiere decidir si se fusiona con `agente-yaiwes` o con otra raíz YAIWES.
2. `Metodo de trabajo` y `Método de trabajo` — nombres similares, árboles diferentes; deben compararse antes de fusionar.
3. `PIPELINE` y `PIPELINE Yaiwes` — raíz general y raíz específica; no son eliminables sin verificar consumidores.
4. `Refactoria` y `Refactoria Yaiwes` — misma condición.
5. `Download code` y `Download code Yaiwes` — contienen inventarios distintos; no se deben borrar.
6. `Documentos proyectos Yaiwes`, `Documentos proyectos agentes Yaiwes` y `Documentos proyectos wordflow code` — revisar trazabilidad antes de consolidar.

## Descargas con nombres repetidos

Se observaron 16 nombres ZIP repetidos correspondientes a Dagster, Kestra y Temporal. La comparación SHA demuestra que **no son copias binarias exactas**: son snapshots o empaquetados diferentes. No se eliminaron.

- Dagster: 13 nombres repetidos, SHA diferentes.
- Kestra: 2 nombres repetidos, SHA diferentes.
- Temporal: 1 nombre repetido, SHA diferente.

## Workflows

Se observaron 27 entradas en `.github/workflows`. Los siete workflows de lotes independientes quedaron en modo manual; el flujo activo es `kernel-download-sequential-new.yml`. No se eliminarán workflows históricos hasta que termine la descarga y la auditoría final 100% PASS.

## Decisión segura

- PASS — revisión realizada.
- PASS — cero borrados.
- PENDIENTE DE AUTORIZACIÓN — fusionar nombres similares, elegir snapshots canónicos o archivar workflows históricos.
