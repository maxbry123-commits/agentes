# CLAUDE NOTAS - memoria.md
RAIZ UNICA Y REAL DE MEMORIA DESDE 2026-09-16. Reemplaza a Claude readme/,
que queda deprecado con aviso de redireccion, sin borrar (regla del proyecto).
Este archivo NUNCA se resume. Se actualiza anadiendo, nunca borrando historia.

## 1. QUE ES ESTO
Soy Claude, orquestador central del ecosistema Maxbry/NCT. No escribo codigo
de produccion - escribo instrucciones, audito evidencia, y mantengo este
archivo como memoria de trabajo persistente entre sesiones de chat.
Sol GPT queda retirado del rol de orquestador. DESDE 2026-09-19: Sol GPT
retirado tambien de TODO trabajo mecanico/codigo - Claude ejecuta directo,
sin delegar (instruccion explicita del Director).

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

## 4. PRIORIDAD ACTUAL (actualizado 2026-09-19)
PRIORIDAD 1 - Wordflow Loop Code Yaiwes + test real -> CERRADA (ver #11).
PRIORIDAD 2 - Seals Team YAIWES + test real con Groq -> EN CURSO.
PRIORIDAD 3 - Osquestador Comand Center + test real -> PENDIENTE, siguiente paso.
PRIORIDAD 4 - Mejoras/gaps continuos + Router Inteligente Universal.

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

## 11. PRIORIDAD 1 CERRADA 2026-09-19 - TEST REAL WORDFLOW + GROQ + GITHUB ACTION
No hay CEREBRAS_API_KEY_* ni ANTHROPIC_API_KEY en el entorno de Claude.
El Director entrego 7 GROQ_API_KEY_1..7. Se ejecuto el ciclo completo:

1. Las 7 keys se sellaron con libsodium real (ctypes sobre libsodium.so.23
   del sistema, sin PyNaCl porque pip no puede resolver paquetes nuevos en
   este entorno) y se subieron como GitHub Actions Secrets reales del repo
   agentes (PUT /repos/.../actions/secrets/GROQ_API_KEY_1..7).
2. Se creo router_modelos.py con proveedor "groq" (fallback determinista
   si Cerebras no tiene keys), consultor_groq.py (cliente real), y
   .github/workflows/wordflow-groq-test.yml - UNICO uso de Actions,
   solo test, tal como ordeno el Director.
3. GAP encontrado y corregido: el repo agentes pesa 16.4GB (size real via
   API), un checkout completo se colgaba indefinidamente. Se cambio a
   sparse-checkout (solo seals_core) -> paso de colgarse a 8s.
4. GAP encontrado y corregido: GROQ_API_KEY_1 da HTTP 401 real (invalida) -
   confirmado 2 veces via GET /models. Las keys 2-7 son validas.
   ACCION PENDIENTE DEL DIRECTOR: revisar/regenerar GROQ_API_KEY_1 en
   Groq console, esta copiada o revocada.
5. GAP encontrado y corregido: los modelos pedidos originalmente
   (llama-3.3-70b-versatile, qwen/qwen3-32b, moonshotai/kimi-k2-instruct)
   NO existen en el catalogo real de esta cuenta Groq (HTTP 404). Catalogo
   real verificado (13 modelos, GET /models real): whisper-large-v3,
   openai/gpt-oss-20b, groq/compound, meta-llama/llama-prompt-guard-2-86m,
   canopylabs/orpheus-arabic-saudi, allam-2-7b,
   openai/gpt-oss-safeguard-20b, openai/gpt-oss-120b,
   canopylabs/orpheus-v1-english, qwen/qwen3.8-27b,
   meta-llama/llama-prompt-guard-2-22m, groq/compound-mini,
   whisper-large-v3-turbo. router_modelos.py corregido para usar solo
   IDs reales, con fail-closed si se pide un modelo no verificado.
6. RESULTADO FINAL REAL: PASS 3/3 (openai/gpt-oss-120b, openai/gpt-oss-20b,
   groq/compound), HTTP 200 + contenido no vacio en los tres, keys 2/3/4
   ejercitadas por rotacion real. Test Oracle objetivo (nunca texto-match
   de LLM) en test_groq_real.py. Evidencia real commiteada en
   seals_core/tests/evidencia_runs/ (JSON + consola) y en el propio run
   de GitHub Actions.

Commits clave (repo agentes, rama main): 4ed87f7 (workflow inicial),
f8170f0 (fix sparse-checkout 16.4GB), 93871bd (commit evidencia de
vuelta al repo), 9f09d00 (diagnostico real por key), ea5b86c
(router_modelos con catalogo real + key1 excluida), c12fe65 (test
lockeado a los 3 modelos reales). Run final PASS:
https://github.com/maxbry123-commits/agentes/actions/runs/35420819763

SIGUIENTE: PRIORIDAD 2 (Seals Team YAIWES, test real con el mismo
mecanismo Groq ya montado) y en paralelo investigacion de componentes
para Comand Center (Herder, MatPoco Skills, DeepSeek Harness, Open
Montage, Mander Diffling, Orca).
