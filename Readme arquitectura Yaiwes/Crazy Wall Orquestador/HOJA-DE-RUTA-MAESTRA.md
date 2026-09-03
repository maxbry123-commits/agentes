# HOJA DE RUTA MAESTRA — YAIWES

Estado inicial del Orquestador Sol. Esta hoja fusionará 1:1 las instrucciones de Claude con la arquitectura y el código real. Ninguna tarea se considera válida por documento solamente.

## Fase A — X-Ray de fuentes
- Inventariar todos los archivos de `Documentos arquitectura Yaiwes lote 1/`.
- Inventariar y leer todos los archivos de `Documentos proyectos Yaiwes instrucciones de Claude/`.
- Extraer requisitos, gaps, destinos, dependencias, OSS sugerido, tests y criterios de cierre.
- Detectar duplicados y contradicciones entre documentos.

## Fase B — Actualización de arquitectura
- Cruzar arquitectura declarada con `agente-yaiwes/`, `extensions/wordflow_kernel/`, `extensions/wordflow/`, `control-layer/`, PIPELINE y código real.
- Actualizar la arquitectura dentro de `Readme arquitectura Yaiwes/` con estados REAL/PARCIAL/ESQ/FALTANTE y evidencia.

## Fase C — Plan Claude 1:1
- Convertir cada tarea/gap de Claude en un ID canónico.
- Construir dependencias DAG y orden de ejecución.
- Asignar Sol Programación / Codex 1 / Luna / Grok según contrato del skill.
- Para cada ID: origen, destino, acción, validación, evidencia, rollback y cierre.

## Fase D — X-Ray de componentes externos a la raíz final
- Inventariar código/componentes existentes fuera de la raíz final del agente.
- Identificar capacidad reutilizable, duplicación, placeholders y compatibilidad.
- Producir propuesta de PRIMERA INTEGRACIÓN para aprobación del usuario.
- STOP: no mover/fusionar código hasta aprobación.

## Prioridad inicial derivada de Claude
Bloque 1: primitivas/kernel y eliminación de duplicación; CLI, contratos, wrappers, manifest y regresión de 27 tests.
Bloque 2: reasoning/governance; goals, decision-on-demand, score, router, consensus, schema contracts, timeout, idempotencia, concurrencia, sheriff/judge/forensic y tests.
Bloques restantes: workflows/pool/memoria, observabilidad/cierre y documentos adicionales de arquitectura/loops deben incorporarse antes de congelar el DAG definitivo.

## Gate de ejecución
La primera ejecución de integración requiere aprobación explícita del usuario después de presentar: componente origen → capacidad → destino → cambios → riesgos → pruebas → rollback.
