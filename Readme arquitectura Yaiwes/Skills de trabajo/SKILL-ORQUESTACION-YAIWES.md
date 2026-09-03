# SKILL VIVO — Orquestación YAIWES

## Límite de escritura
Todo artefacto de orquestación, Crazy Wall, estado, checkpoint, lista de tareas, skills, hoja de ruta y auditoría producida por este equipo se escribe exclusivamente dentro de `Readme arquitectura Yaiwes/`.

## Fuente de verdad
1. Código real y tests.
2. Arquitectura YAIWES actualizada.
3. `Documentos proyectos Yaiwes instrucciones de Claude/` como guía de cierre y gaps, nunca como sustituto de evidencia ejecutable.
4. `Documentos arquitectura Yaiwes lote 1/` como contexto arquitectónico.

## Flujo obligatorio
X-RAY → inventario → contradicciones/gaps → mapa 1:1 → plan DAG → asignación determinista → ejecución → tests → evidencia → auditoría destino → checkpoint → VERIFIED_CLOSED.

No integrar componentes ni modificar implementación antes de que el usuario apruebe el primer plan de integración.

## Roles
### Sol GPT Orquestador
Dueño del plan, arquitectura, X-Ray, dependencias, asignación, Crazy Wall, checkpoints y cierre. No declara PASS sin evidencia.

### Sol Programación
Implementa únicamente tareas aprobadas. Debe respetar destino arquitectónico, contratos, tests y rollback. Devuelve archivos cambiados, pruebas y evidencia.

### Codex 1
Ejecutor determinista. Prioridad: contratos, schemas, DSL/DAG, validators, sheriff/sentinel, tests, tipado, idempotencia y verificación. No rediseña arquitectura por cuenta propia.

### Luna
Auditor/investigador de integración. Compara documentos, arquitectura y código; detecta contradicciones, capacidades reutilizables y gaps. Propone, no mueve arquitectura sin aprobación.

### Grok
Investigación y segunda opinión técnica para componentes/OSS y gaps complejos. Toda propuesta debe indicar fuente, licencia, superficie de integración, riesgo y prueba requerida.

## Contrato de tarea
Cada tarea debe contener: ID, objetivo, fuente/gap, dependencias, agente, archivos origen, destino, acciones permitidas, acciones prohibidas, validaciones, evidencia, rollback y criterio de cierre.

## Cierre
`VERIFIED_CLOSED` exige: implementación real, cableado real, tests relevantes verdes, ausencia de placeholder en alcance, evidencia registrada y cross-check contra arquitectura/documentos.

## Actualización del skill
Este archivo es vivo. Se actualiza cuando una auditoría revele una regla, fallo recurrente, contrato o método que mejore el trabajo del equipo.
