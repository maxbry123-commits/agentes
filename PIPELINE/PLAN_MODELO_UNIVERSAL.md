# PIPELINE PLAN MODELO UNIVERSAL

**Proyecto:** maxbry123-commits/agentes
**Estado:** MOLDE
**Forma:** NOTAS-10 HF sin tareas
**Segmentos:** NOTAS-11 YAIWES vaciado
**PLAN_ID:** {{PLAN_ID}}
**N_DESPLEGAR:** {{N}}

GitHub = verdad. FAIL-CLOSED. LLM no declara PASS. HTTP 200 no es PASS.
Original intacto: PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md
Instanciar: PIPELINE/PLAN_{{PLAN_ID}}.md

## REGLA UNIVERSAL
investigar, verificar, deduplicar, resolver GAP, segunda pasada, X-Ray, registrar, PASS, siguiente.
NO-STOP. No mezclar bloques.
Anotar = aditivo: leer, SHA, append, commit, leer, viejo mas nuevo.
Tags: CHAT_APROBADO, PIPELINE_EXISTENTE, INVESTIGACION_NUEVA, GAP, DESCARTADO

## BLOQUE A INPUT Y CABLEADO
TAREA OBJETIVO FUENTE DESTINOS ALCANCE FUERA PASS PLAN_ID
N_DESPLEGAR {{N}}
ENLACE_DESPLEGAR Desplegar/Desplegar {{N}}/
ENLACE_REFACTORIA Refactoria/refactoria-plan-{{PLAN_ID}}/
ENLACE_DESTINO Yaiwes wordflow o Wordflow Code
ENLACE_CHECKPOINT PIPELINE/checkpoints/{{PLAN_ID}}/

Ejemplo: Plan X numero 2 enruta con Desplegar/Desplegar 2/ y Refactoria/refactoria-plan-x-2/
despliegue minusculas no es Desplegar. Sin lote WAIT. No carpeta vacia.

Desplegar para que: inbox del lote de ese plan.
Desplegar como: N del plan; solo ese path; archivo nuevo a destino; archivo que pisa vivo a Refactoria; ZIP hash extract staging el ZIP no se vacia.
Desplegar donde: raiz Desplegar con extensiones Desplegar 1 Desplegar 2 Desplegar N.

Refactoria para que: mesa version vieja junto a nueva.
Refactoria como: source copia exacta del vivo; new reescritura; cruzada x3 diff tests checklist; integrar solo si 3 PASS; no borrar source en el mismo task.
Refactoria donde: Refactoria/refactoria-plan-{{PLAN_ID}}/source y new.
Legado YAIWES: despliegue/refactoria/GAP y Refactoria/GAP. Plan nuevo no usa esos paths.

extension-kernel es ejemplo abi-mount capability-registry mount-guard. No dump.

## BLOQUE B YAIWES VACIO
ESTADO AUDITADO tabla S1 QUEUED checkpoint PIPELINE/checkpoints/PLAN_ID/S1.md
FUENTES: molde, instancia, YAIWES, README wordflows, Desplegar N, Refactoria, Metodo, notas-trabajo-grock
REGLAS: no inventar; no hot path sin paridad; no PASS sin ficha.
LEGO: goal_lock.py execution-orchestration/goal-lock; cognitive_loop.py mission-planning; evidence_packet.py observability/evidence-packet
TOTAL SALIDAS K vacio
Schema S1 con enlace_desplegar enlace_refactoria destino tag sheriff watchdog guardian verificacion_cruzada pass checkpoint
Sheriff extensions/wordflow/standards/sheriff.py
Watchdog extensions/wordflow/engine/watchdog.py
Guardian mount-guard VerdictAuthority
DSL DAG: BIND SHERIFF source new x3 GUARDIAN destino READ-BACK Ficha de cierre CHECKPOINT
Preflight 1.a.1 rama plan checklist enlace o WAIT hot path alcance no pintar PASS
Ficha de cierre: tarea commit repo estado prueba logs errores resultado fecha PASS FAIL OPEN BLOCKED
GAPS tabla OPEN
DEPLOYMENT NOT_CLAIMED
HOT PATH extensions/wordflow/engine/code_path_runner.py
CRECIMIENTO ACQUIRE REUSE PATCH ADAPT

## BLOQUE C COPIA ZIP RAICES
GET PUT SHA; blob tree commit; Actions; fork; clone push
ZIP HASH EXTRACT staging INVENTARIO COPY commit read-back
Raices: Desplegar PIPELINE Metodo de trabajo Refactoria Yaiwes wordflow Wordflow Code notas-trabajo-grock
README parches Readme/Readme1 prohibido crear fuera
METODO-DE-TRABAJO.md GT1 54KB OPEN

## BLOQUE D FASE 2 NO AHORA
1 subir lote Desplegar N
2 X-Ray docs vs code 4 u 8 y 12 goals
3 Grok disena code plugin
4 Director sube code debate
5 cablear plan Desplegar Refactoria

## OPERADOR
RECIBIR LEER PLANIFICAR COMPROBAR PREPARAR ENVIAR REGISTRAR MONITOR GAP REINTENTAR VALIDAR CERRAR
