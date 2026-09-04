# PLAN MAESTRO — DIRECTOR + CLAUDE

Fuente obligatoria 1: `INPUT-DIRECTOR-LITERAL.md` (órdenes del Director, sin reinterpretación).
Fuente obligatoria 2: `INPUT-CLAUDE-LITERAL/` (copias byte-a-byte de los documentos de Claude).
Fuente obligatoria 3: `Readme arquitectura Yaiwes/README.md` (arquitectura canónica).
Fuente obligatoria 4: código real de `main`.

## Paso 1 — X-Ray y arquitectura
Objetivo: auditar documento por documento Lote 1 + Claude contra código real y actualizar únicamente `Readme arquitectura Yaiwes/README.md` con estados REAL/PARCIAL/ESQ/FALTANTE/VERIFIED_CLOSED.
Logro: una arquitectura viva basada en evidencia, sin lista operativa mezclada dentro del README.

## Paso 2 — Lista Claude 1:1 y Crazy Wall
Objetivo: sacar del README la lista operativa 1–70, ampliarla con las tareas 71–90 de Claude y mantener cada mini-prompt, destino, OSS y criterio sin resumir.
Logro: Crazy Wall contiene el backlog completo 1–90 y los input blocks literales del Director y Claude.

## Paso 3 — Inventario de componentes existentes
Objetivo: recorrer código/componentes del repo `agentes`, clasificar cada componente como TOTAL/PARCIAL/ADAPTADOR/RECHAZAR y mapear destino exacto YAIWES.
Logro: matriz componente origen → capacidad → destino → riesgo → tests → estado, lista para aprobación del Director.

## Paso 4 — Movimiento aprobado
Objetivo: tras aprobación del Director, generar prompt determinista a Sol GPT/GitHub Action para mover/copiar solo los componentes aprobados y exigir comprobante origen/destino/SHA.
Logro: archivos físicamente ubicados y verificados antes de tocar cableado.

## Paso 5 — Cableado Codex determinista
Objetivo: crear un ID por integración y dar a Codex DSL + DAG + schema + Sheriff + Validator + Verifier + Sentinel + Supervisor + Judge + Guardian; solo cableado quirúrgico, sin reescritura.
Logro: integración conectada con código mínimo, tests y rollback definido.

## Paso 6 — Cierre de gaps y auditoría final
Objetivo: auditar faltantes contra Claude; buscar primero en `Agentes-motores-Wordflow-YAIWES`, luego OSS si no existe internamente; repetir movimiento→verificación→Codex→auditoría.
Logro: cada requisito Claude se marca `VERIFIED_CLOSED` solo con código, destino, tests y evidencia.

## Gates
- No mover componentes antes de aprobación del Director.
- No dar tarea Codex antes de verificar físicamente destino.
- No reescribir módulos completos si un adaptador/cableado mínimo resuelve el gap.
- No declarar PASS por presencia de carpeta/documento.
- Código real y tests prevalecen sobre cualquier documento.
