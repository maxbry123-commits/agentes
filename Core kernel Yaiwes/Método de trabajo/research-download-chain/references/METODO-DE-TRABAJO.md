# Método de trabajo (adjunto del skill research-download-chain)

Fuente: Director MAXBRY / leyes confirmadas 2026-07-26 … 2026-08-26.
Este archivo es adjunto obligatorio. Leer literal en cada salida de este skill.

## INPUT BLOCK

Cada instrucción del Director se anota como ítem. Cruzar la lista en sandbox antes de avanzar. 1 o 100 ítems. No skip.

## Leyes inmutables

- Respuestas máx 5 líneas salvo que el Director pida deliverable largo (JSON, source, skill).
- Léxico programación mixto. Sin analogías no-prog.
- Input blocks leer literal siempre.
- Web ≤1 min. Investigar primero capacidades, luego foros Reddit/HN/SO/GitHubDiscussions/DEV.
- "explica detalladamente" = problema + 5 soluciones. cómo-X = lista enumerada sin cuadros.
- Microdiagramas horizontales. "sistema de pasos" = tareas 1-100 + índice.
- Checkpoint MD solo riesgo de contexto. Nunca docs sin autorización.
- Menor token + más avanzado. Nunca MVP. Mejorar 100x.
- Flujo: audit3 → 6goals in → refut+experto9 → council12 → 12goals out → si docs audit3.
- Un solo objetivo grande por turno. No mezclar temas.
- Primero plan luego código. Revisar arquitectura antes de decidir.
- Diffs/parches antes de cambios masivos. Archivos uno a uno.
- Evitar sobreingeniería. Reglas de trabajo = ley inmutable.
- Si hay pasos de razonamiento, mostrar resultado de cada paso.
- Checkpoints en tareas largas. Migraciones por fases.
- Revisión de rendimiento después de implementar.
- Info nueva fuera de plan → actualizar plan + trazabilidad de documentos.
- Nunca cerrar con gaps. Loops hasta 100%. Autoanálisis + 3 verificaciones antes de cerrado.
- Solicitar varias soluciones ("dame tres enfoques") antes de elegir implementación.
- Analizar todas las necesidades antes de instrucciones y antes de ejecutar.

## LEY AUDIT-5 (2026-08-17)

Cada 5 tareas terminadas (o antes si tarea grande/multipart) auditar método + PIPELINE + forense 100% de las 5. Detectar gaps. Corregir + mejorar 10x. Actualizar arquitectura/historia/bitácora. NO avanzar hasta 100% gaps resueltos. La auditoría se inserta como tarea adicional. Lista de tareas con trazabilidad de documentos (origen/ancla/path). Formato salida = CONTROL DE TRABAJO. Lista completa en PIPELINE/52.

## LEY FORENSIC CODE CLOSURE (2026-08-18)

Tras cada tarea de programación → FORENSIC CODE AUDIT v1.2.1 (CORE 14 + FC-01..13 + 4 pasadas + enforcement) → gaps → FIX → RE-AUDIT hasta PASS.
PASS solo Evidence + VerdictAuthority determinista. LLM nunca declara PASS.
Sin Context/método/Handoff verificado → NO programar ni auditar.
Enforcement: PolicyEngine, StepGate, StateMachine, ContractGate, EvidenceGate, ApplicabilityEngine, PolicySnapshot, InvariantChecker, FinalCleanReAuditGate, VerdictAuthority, AuditTamperGuard. 8 subsistemas Wordflow Audit Engine.

## Ley cuaderno anti-alucinación (prioridad máxima)

En cada input y en loops releer TAREAS-EN-CURSO + BITACORA-RESUMEN + LEY-CUADERNO + docs FROMTED activos (PASO en curso). No memorizar el proyecto. El cuaderno es la fuente de verdad.

## FROMTED

- PASO 1 investigación ≥20 repos OS + manifest sources determinista (sparse).
- Imágenes de diseño van en PASO 2 después de investigación.
- Docs: PROYECTO-FROMTED.md → PASO-1 → PASO-2. Tareas solo en curso. Bitácora solo referencias.
- NUNCA code desde 0. Sin source OS materializado no programar. Solo adaptar/fusionar/conectar.
- CSS no es source.
- Confirmación cada salida: SOURCE path + uso; no-from-scratch; 5 líneas revisión+plan.

## LEY SANDBOX-FIRST (2026-08-26)

Todo documento/plan/código se construye primero en sandbox. Auditoría del chat + INPUT BLOCK. 12 goals in → council → 12 goals out. Loops hasta validación 100%. NO push GitHub y NO salida-entregable en chat hasta PASS sandbox. Excepción de este skill: el Director autorizó explícitamente la copia al repo agentes después del PASS sandbox.

## LEY INPUT-CHECKLIST (2026-08-26)

Cada instrucción del Director = ítem de INPUT BLOCK. Checklist de validación. NO avanzar tarea sin cruzar esa lista en sandbox.

## Setup

movil/iPad + VPS Contabo + GitHub. Control vía query/path token. DSL mín 5 vías.
