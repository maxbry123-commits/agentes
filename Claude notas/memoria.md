# CLAUDE NOTAS - memoria.md
RAIZ UNICA Y REAL DE MEMORIA DESDE 2026-09-16. Reemplaza a Claude readme/,
que queda deprecado con aviso de redireccion, sin borrar (regla del proyecto).
Este archivo NUNCA se resume. Se actualiza anadiendo, nunca borrando historia.

## 1. QUE ES ESTO
Soy Claude, orquestador central del ecosistema Maxbry/NCT. No escribo codigo
de produccion - escribo instrucciones, audito evidencia, y mantengo este
archivo como memoria de trabajo persistente entre sesiones de chat.
Sol GPT queda retirado del rol de orquestador.

## 2. EL ECOSISTEMA COMPLETO (7 proyectos)
1. Agente Yaiwes - repo agentes - Confirmado
2. Osquestador Maxbry - repo Orquestador-Maxbry- - no confirmado
3. Router Inteligente Universal - repo router-universal-router-inteligente- - Confirmado
4. UI Yaiwes - repo nct-hub (hipotesis)
5. Fabrica de UI - repo frontend - Confirmado
6. Osquestador auditor + memoria - repo osquestador-auditor
7. NCT - repo nct-core - Confirmado

Repos activos AHORA: agentes, frontend, router-universal-router-inteligente-

## 3. METODO DE TRABAJO
1. Un paso por salida. 2. Micro-mundos aislados por proyecto. 3. Contrato
de nodo: maximo 3 pasos. 4. Reglas duras: read fresh, solo FREE, REUSE
primero, no PASS sin evidencia, GAP investiga 20 formas, nunca detenerse.
5. Escalera: Sol GPT -> Haiku -> Sonnet -> Opus -> GPT/Astra -> Fables 5.1
6. Nunca resumir. 7. COPY-FIRST antes de generar codigo nuevo.

### 3.1 REGLA DE PRESENTACION: Capacidad/Patron microflujo/LOOP/Aporta/
Usa/Reglas/Fallos/Test para agentes. component_id/name/objective/etc para componentes.

### 3.2-3.3 ORGANIZACION DE RAIZ: 3 componentes por proyecto (Readme+Crazy
Wall+Handoff). Raices oficiales de main ya definidas (ver historial completo).

## 4. PRIORIDAD ACTUAL
1. Cerrar Seals Team YAIWES + Wordflow Loop Code Yaiwes (Salida 8 de 8, cierre formal).
2. Activar Router Inteligente Universal (con OmniRoute) despues.
3. Crear Comand Center/osquestador (Tarea 3).

## 5. JERARQUIA REAL: Yaiwes -> NCT (repo nct-core) -> Wordflow Loop Code
Yaiwes (motor de programacion, 95% Fables) -> Seals Team (worker).

## 6. CIERRE DE SEALS TEAM YAIWES - SALIDAS 1-7 CERRADAS (2026-09-18)
Auditoria externa 5 pasadas (GPT): 32 gaps P0/P1/P2. Progreso real,
CODE+TEST+EVIDENCE por gap:
SALIDA 1: P0-02 P0-03 P0-04 (PASS falsos eliminados).
SALIDA 2: P0-01 (dag_engine.py, YAML gobierna de verdad).
SALIDA 3: P0-05 P0-06 P0-07 (goal_tracking, evidence, CrazyWallAdapter).
SALIDA 4: P0-08 P0-09 P0-10 P0-11 (watchdog corregido - 213 componentes
reales encontrados -, reencolado real, heartbeat, idempotencia real).
SALIDA 5: P0-13 P0-14 P0-15 P0-17 (instalador reescrito: commit
reproducible, verificacion real, sheriff_policy.py, tool_result.py).
P0-16 (ToolRegistry Glimmer) parcial.
SALIDA 6: P1-18 P1-19 P1-22 P1-23 (research_real.py, stuck_detector.py,
work_surface.py con gate CODE+BROWSER+VISUAL).
SALIDA 7: P1-20 P1-21 (worker_bootstrap.py, contrato consumido de
verdad), P1-25 (isolation.py, 1 writer=1 scope), P1-26 (recovery_types.py,
7 clases tipadas), P1-29 (llm_output_schema.py). P2-32: prompt real a Sol
para pip freeze (no se inventaron versiones).

PENDIENTE EXPLICITO, NO OCULTO: P1-24 (MetaCua/CUA-MCP, la propia
auditoria exige no declarar integracion sin leer implementacion real -
no verificada, no tocada), P1-27 (crash/resume, requiere integrar con
CrazyWallAdapter.checkpoint), P1-28 (sandbox/rollback del installer),
P2-31 (drift del Handoff: dice 229 componentes, real=248, requirements.txt
si existe - corregir en Salida 8), P1-30 (test suite: faltan tests de
crash/recovery y de wrong source commit especificos).

SIGUIENTE: SALIDA 8 - cierre formal. Resolver P1-27, P1-28, P2-31
restantes + integrar el REQUISITO-50-mundos-y-Router-Universal.md +
declarar VERIFIED_CLOSED solo si TODO pasa, o dejar GAP explicito si algo
no cierra - nunca fingir cierre.

## 7. AUDITORIA WORDFLOW LOOP (2026-09-17) - cobertura 100%, ver historial
completo en versiones anteriores de este archivo (21/21 carpetas, 20
archivos en "arquitectura wordflow loop code Yaiwes/", Enchufe Universal
YA integrado en uek/, gobernanza confirmada real en los 7 archivos).

## 8. HALLAZGOS CRITICOS 2026-09-18 - ver detalle completo en version
anterior de este archivo: X-Ray de Sol (35+ descargas, destino final no
confirmado en varios lotes), carpeta ajena "Wordflow loop code Yaiwes"
(sin emoji) = proyecto Next.js/Electron distinto (probable big-AGI),
3 skills de frontend confirmados fisicamente ahi mismo, doble commit del
emoji RESUELTO (mismo proyecto, no fork real). Artify=Archify confirmado.

## 9. PENDIENTE: sistema de preguntas previas, 3 lugares (UI interface,
UI backend, Input Shark). SIEMPRE activo. Ver diseno completo en
arquitectura wordflow loop code Yaiwes/DISENO-preguntas-siempre-activo-
input-shark.md.

## 10. REQUISITO CRITICO 2026-09-18 (ver REQUISITO-50-mundos-y-Router-
Universal.md completo): mas de 50 wordflows, cada uno su propio mundo
(Readme+Handoff+Crazy Wall+System prompt). Cerebras = SOLO PRUEBAS. En
produccion todos se conectan al Router Inteligente Universal como
proveedor de API keys. Se verifica en Salida 8 antes de declarar cerrado.
