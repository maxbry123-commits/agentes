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
1. Un paso por salida.
2. Micro-mundos aislados por proyecto.
3. Contrato de nodo: maximo 3 pasos.
4. Reglas duras de ejecutores: read fresh, solo FREE, REUSE_EXISTING primero,
   no PASS sin evidencia, GAP investiga 20 formas, nunca detenerse.
5. Escalera: Sol GPT -> Haiku -> Sonnet -> Opus -> GPT/Astra -> Fables 5.1
6. Nunca resumir en documentos de trabajo.
7. COPY-FIRST antes de generar codigo nuevo.

### 3.1 REGLA DE PRESENTACION (2026-09-16)
Formato de agente: Capacidad, Patron microflujo horizontal en texto, LOOP,
Aporta, Usa, Reglas, Fallos, Test. Formato de componente: component_id,
name, objective, responsibility, input, output, dependencies, files,
status, failure, recovery.

### 3.2 REGLA DE ORGANIZACION DE RAIZ (2026-09-16)
3 componentes por proyecto: Readme arquitectura + Crazy Wall + Handoff.
Formato: Proyecto/Readme arquitectura Proyecto.md. Versionado: version
nueva 1.1, comparar, borrar vieja solo si es copia fiel.

### 3.3 RAICES OFICIALES DE main (2026-09-16)
AGENTS.md, .github, .cursor (sueltos), Agente Yaiwes principal/, Core
kernel Yaiwes/, Seals team YAIWES/, Componente open source Yaiwes/,
Claude notas/, Motores de descarga y extraccion/, Skills agente/,
Wordflow Loops Yaiwes/, Conecciones router inteligente universal/.

## 4. PRIORIDAD ACTUAL
1. Cerrar Seals Team YAIWES + Wordflow Loop Code Yaiwes (EN CURSO, plan de 8 salidas).
2. Activar Router Inteligente Universal (con OmniRoute) despues de 1.
3. Crear Comand Center/osquestador (Tarea 3).

## 5. JERARQUIA REAL CONFIRMADA (2026-09-18, correccion critica)
Yaiwes (proyecto completo) -> NCT/Neuronas Code Turbo (repo nct-core) ->
Wordflow Loop Code Yaiwes (este motor de programacion, 95% de Fables) ->
Seals Team (worker especializado dentro de este motor). Wordflow Loop NO
es Yaiwes completo, es el motor de codigo dentro de NCT.

## 6. CIERRE DE SEALS TEAM YAIWES - EN CURSO (2026-09-18)
Auditoria externa de 5 pasadas (GPT) encontro 32 gaps P0/P1/P2 reales:
PASS falsos (verificar_existencia, evaluar_componente sin keys, Claude
como oraculo), DAG decorativo no gobierna ejecucion, watchdog roto (campo
incorrecto + no reencola), sin idempotencia real, sin CrazyWallAdapter,
Meta (Muse Code/Glimmer/Cookbook) copiado pero no cableado.

Plan de 8 salidas para cerrar (CODE+TEST+EVIDENCE por gap, nunca declarar
cerrado sin eso):
SALIDA 1 CERRADA: P0-02, P0-03, P0-04 (PASS falsos eliminados en ejecutor.py + verificador.py marcado como opinion advisory). Tests: test_p0_fixes.py.
SALIDA 2 CERRADA: P0-01 (dag_engine.py nuevo, YAML se carga fresco y gobierna de verdad, ejecutor.py cableado). Test: test_p0_01_dag_real.py. pyyaml anadido a requirements.
SALIDA 3 CERRADA: P0-05 (goal_tracking.py, completion audit real, no cierra sin acceptance demostrada), P0-06 (evidence.py, EvidenceRecord tipado, PASS sin evidencia valida = GAP), P0-07 (crazy_wall_adapter.py, claim/checkpoint/record_gap/record_evidencia/release con read-back real via GitHub API). Test: test_p0_05_06_07.py.
SALIDA 4 CERRADA: P0-08 (watchdog.py corrige campo real wall_status, confirmado 213 componentes PENDING_STEP1 reales), P0-09 (reencolado real via reencolar_en(), loop_principal ya no ignora el retorno del watchdog), P0-10 (heartbeat real a archivo watchdog_heartbeat.json), P0-11 (idempotencia.py nuevo: fingerprint+REPLAY+IDEMPOTENCY_CONFLICT, cableado en ejecutor.py). Test: test_p0_08_09_10_11.py.
PENDIENTE: Salida 5 (P0-13 a P0-17: git clone reproducible, Sheriff/Policy, Glimmer ToolRegistry), Salida 6 (P1-18 a P1-25: research real, stuck detection, frontend browser-verified), Salida 7 (P1-26 a P2-32: recovery tipado, test suite, drift Handoff), Salida 8 (cierre formal VERIFIED_CLOSED + eliminar nombre duplicado Wordflow en main + Handoff final).

## 7. AUDITORIA COMPLETA WORDFLOW LOOP (2026-09-17)
Cobertura 100%: 21/21 carpetas auditadas. 16+ archivos en "arquitectura
wordflow loop code Yaiwes/": indice, Partes 1-5 (Glimmer), Anexos 1-5,
3 SCHEMAS (refactorizacion 15 reglas fuente, frontend browser-verified
verbatim, plantillas RAG), prompts para Sol, diseno MCP.
Hallazgo mayor: Enchufe Universal YA integrado en uek/ (30KB). Gobernanza
(sheriff/judge/guardian/sentinel/supervisor/validator/verifier) confirmada
REAL leyendo los 7 archivos completos, no stubs (Anexo 5). MCP confirmado
por el Director = Model Context Protocol, contexto compartido entre
agentes (lo que uno descubre lo comparten los demas).

## 8. HALLAZGOS CRITICOS 2026-09-18 - descargas dispersas y confusion de carpetas

X-RAY DE SOL sobre descargas historicas (35+ componentes identificados):
MiniMax+Kimi (13 pedidos, 10 con descarga temporal, NO verificados en
destino final agent_sources/), Meta (3 materializados en Core kernel
Yaiwes/), T1_ACQUIRE_14 (14 componentes UI incluido big-AGI, NO verificado
14/14), Lote 17-sep (Codebase Memory MCP/OmniRoute/Omarchy/Anydoc
presentes, Orca AUSENTE). Patron repetido: descarga temporal si, destino
final NO confirmado - GAP principal a resolver antes de dar nada por cerrado.

3 skills de frontend (frontend-design, impeccable, skill-creator)
confirmados FISICAMENTE en "Wordflow loop code Yaiwes/skills/" (sin
emoji) - carpeta DISTINTA de "Skills agente/" donde Claude buscaba.

CRITICO: existe una carpeta "Wordflow loop code Yaiwes" (sin emoji, W
mayuscula) que NO es el kernel - es un proyecto Next.js/Electron completo
(probablemente big-AGI de T1_ACQUIRE_14) con package.json, Dockerfile,
electron/, CHANGELOG de 2.7MB. Tiene sus propios ~30 skills nativos
mezclados con los 3 reales que pedimos. PENDIENTE decision del Director:
mover los 3 skills reales a Skills agente/, decidir destino del proyecto
ajeno completo.

RESUELTO: los 2 commits de "doble raiz" del emoji (1db0377 vs afcc0429)
son el MISMO proyecto en 2 puntos de su historia normal - NO hay fork
real, solo difiere Crazy Wall Orquestador/ (el tracker, cambia con el
tiempo). main ya tiene todo consolidado. Emoji del Director (arrow+carpeta)
= convencion semantica propia para marcar destino/raiz en main, no decoracion.

Artify = Archify (confirmado por el Director). Orca + Artify = backend
del futuro Comand Center/osquestador (Tarea 3), NO se integra en Wordflow
todavia - el Director corrigio que Claude iba adelantado en esto.
OmniRoute = pendiente para Router Inteligente Universal, despues de
cerrar Wordflow Loop + Comand Center.

## 9. PENDIENTE: sistema de preguntas previas (tipo Claude), 3 lugares
UI YAIWES interface, UI YAIWES backend, Yaiwes via Input Shark. SIEMPRE
activo (no condicional), confirmado que el mecanismo real de Anthropic
sigue existiendo (preguntas interactivas antes de ejecutar). Diseno
completo en arquitectura wordflow loop code Yaiwes/DISENO-preguntas-
siempre-activo-input-shark.md. Codigo pendiente, 3 implementaciones
independientes (no se comparte codigo entre los 3, se comparte diseno).
