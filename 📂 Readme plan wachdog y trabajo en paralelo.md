# 📂 WATCHDOG YAIWES — PLAN OPERATIVO DE 3 PASOS

**Estado:** `ACTIVE_3_STEP_SUPERVISOR`  
**Fecha:** 2026-09-10  
**Repositorio:** `maxbry123-commits/agentes`

## Objetivo

El Watchdog existe para que Grok, Sol y Astra integren componentes en paralelo sin pisarse y sin abrir trabajo extra. **Cada componente es un nodo independiente en Crazy Wall.**

## Contrato que vigila

```text
PASO 1 — A/B/C + DESTINO + MOVE
PASO 2 — PODAR SOLO SI HACE FALTA + ENCHUFE FABLES
PASO 3 — TEST REAL
```

No existe Paso 4. A/B/C no es una fase: solo decide tipo/destino.

### PASO 1

```text
read minimum code/README
→ A autónomo | B motor de trabajo | C capacidad
→ elegir raíz existente en Agente Yaiwes principal/
→ Motor4 MOVE si todavía hace falta
→ hash/read-back
```

No adivinar destino. Los 20 originales ya tienen MOVE cerrado y no se mueven de nuevo.

### PASO 2

```text
prune only if evidence says it is needed
→ ficha_contract_v2.validar()
→ real adapter/port
→ UniversalPluginBus.enchufar()
→ WIRING
```

El Enchufe Universal FABLES es obligatorio. `source_probe()` y “la carpeta existe” no cierran integración.

### PASO 3

```text
ficha valid
→ import/build
→ FABLES mount
→ real behavior positive case
→ failure path
→ health/evidence/read-back
→ PASS | GAP
```

FAIL no crea fase nueva: se corrige el nodo y se repite.

## Crazy Wall — coordinación

Archivo: `📂 Bitácora stated JSON Craxy wall.json`.

Cada nodo guarda `owner`, `lock`, `current_step`, `status`, `abc`, `target`, `checkpoint.before`, `checkpoint.after`, `evidence`, `history`.

```text
READ FRESH
→ TAKE FREE NODE
→ owner=GROK|SOL|ASTRA
→ lock=CLAIMED
→ checkpoint.before
→ execute current_step
→ checkpoint.after + evidence
→ advance/PASS/GAP
→ release lock
```

Un nodo reclamado por otra IA se salta.

## Estado actual

- 27 nodos registrados.
- 5 nodos originales: Paso 3/revalidación.
- 15 nodos originales: Paso 2/FABLES.
- 7 componentes nuevos: Paso 1 — Dagu, Hatchet, PostgreSQL, Redis, Workalendar, gVisor, pgvector.
- APScheduler y Celery encontrados también en Core no se duplican porque ya son nodos originales.

## Intake automático

```text
SCAN Core kernel Yaiwes/
→ componente nuevo real?
→ ya existe nodo? YES = no duplicar
→ NO = crear nodo FREE/current_step=1
```

## Watchdog loop

```text
SCAN
→ REGISTER
→ CHECK LOCKS
→ REQUIRE BEFORE CHECKPOINT
→ SUPERVISE STEP 1|2|3
→ REQUIRE AFTER CHECKPOINT + EVIDENCE
→ ADVANCE | GAP
→ RELEASE
→ REPEAT
```

El Watchdog no crea documentos, motores o fases nuevas por iniciativa propia.

## Componentes mínimos disponibles para el propio Watchdog

Se reutilizan solamente cuando hagan falta: APScheduler (tiempo), Workalendar (calendario), Celery/Taskiq (cola), Redis (eventos/locks), Hatchet (durable), Dagu (multi-step), PostgreSQL (estado), pgvector (memoria), gVisor (sandbox). No son pasos nuevos.

## Anti-dilatación

- sin nuevas fases;
- sin refactor global antes de un error real;
- sin motor sustituto sin GAP demostrado;
- sin poda ciega;
- sin duplicar componentes;
- sin editar nodo de otro owner;
- sin PASS sin prueba real;
- sin afirmaciones `100x` sin benchmark.

## Enlaces

- Handoff: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
- Recovery: https://github.com/maxbry123-commits/agentes/blob/main/PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md
- Crazy Wall: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Bit%C3%A1cora%20stated%20JSON%20Craxy%20wall.json
- Machine plan: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/PLAN-WATCHDOG-PROGRAMMING-V2.json
