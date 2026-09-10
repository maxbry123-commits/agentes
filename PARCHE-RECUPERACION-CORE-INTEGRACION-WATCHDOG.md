# PARCHE DE RECUPERACIÓN — GROK / SOL / ASTRA — YAIWES 27 NODOS

**Fecha:** 2026-09-10  
**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Estado:** `READY_TO_RESUME / 5X_REVIEWED`

## 1. Leer primero

```text
1. ESTE PARCHE
2. Readme arquitectura Yaiwes/HANDOFF-INTEGRACION-1-20.md
3. 📂 Bitácora stated JSON Craxy wall.json
4. estado físico fresco de main
5. PLAN-WATCHDOG-PROGRAMMING-V2.json
```

Si un documento contradice `main`, prevalece el estado físico. No inferir resultados.

## 2. Único contrato permitido

```text
PASO 1 — decidir A/B/C + destino + MOVE con Motor4
PASO 2 — podar solo si hace falta + cablear con FABLES obligatorio
PASO 3 — test real
```

**No Paso 4. No fases laterales.**

A/B/C es solo una decisión de destino:

- A = agente/subagente autónomo.
- B = workflow/DAG/scheduler/queue/workers/durable/loop.
- C = capacidad modular: schema/policy/storage/memory/routing/research/sandbox/validator/tool.

Si no se demuestra la clasificación/destino: `GAP_DESTINATION`. No adivinar.

## 3. Estado exacto

Total registrado: **27 nodos**.

- Nodos 1–5: `PENDING_STEP3_REVALIDATION`.
- Nodos 6–20: `PENDING_STEP2_FABLES`; su MOVE original NO se repite.
- Nodos 21–27: `PENDING_STEP1`: Dagu, Hatchet, PostgreSQL, Redis, Workalendar, gVisor, pgvector.

Evidencia del MOVE original 20/20:

- Run `34445710787`.
- Job `102771861495`.
- Commit `a3cf705f58f95cce65d1c230cb00abcab39732b2`.
- Motor4 blob `9a21facfe11327cf60a2afca8f415ad52f0ecbe5`.

Los destinos de los nuevos siete que figuran en Crazy Wall son **candidatos `VERIFY_BEFORE_MOVE`**; Grok debe confirmar función/código antes de Motor4.

## 4. Enchufe FABLES obligatorio

PASO 2 no se cierra sin estas dos piezas entregadas por el usuario:

```text
ficha_contract_v2.py
  entry: validar()
  sha256: 759d0d7855d8df106462b966bfc4ee543f24a3e789a27048f253159b58ff8d1a

universal_plugin_bus_v2_integrated.py
  entry: UniversalPluginBus.enchufar()
  sha256: 5e4595a86bfd68a3c1fde70ba614ce7b9ec6ea4d6c867912e836cca33c626fc3
```

**Auditoría 5×:** estas piezas exactas no quedaron demostradas en `main`. Estado: `PENDING_MATERIALIZATION`. No inventar sustituto. Esto no crea otro paso: es requisito interno de PASO 2.

## 5. Cómo empieza Grok sin pisar a nadie

```text
READ fresh Crazy Wall
→ buscar lock=FREE
→ elegir un nodo compatible con el trabajo posible
→ escribir owner=GROK
→ lock=CLAIMED
→ checkpoint.before
→ ejecutar SOLAMENTE current_step
→ guardar commit/run/test en evidence
→ checkpoint.after
→ avanzar step o dejar GAP
→ lock=FREE + owner=null
```

Si el nodo está `CLAIMED` por SOL o ASTRA: **no tocarlo**; tomar otro FREE.

## 6. Reglas de reparación

PASO 1 falla → corregir destino/MOVE dentro de PASO 1.  
PASO 2 falla → buscar código, podar solo si se demuestra necesario, escribir/corregir adapter o hacer fork si hace falta, volver a enchufar.  
PASO 3 falla → localizar causa, volver a PASO 2 solo si el cableado/código es la causa y repetir PASO 3.

Nunca convertir un error en una fase nueva.

## 7. Prohibido

- rehacer MOVE 1–20;
- crear Paso 4;
- clasificación A/B/C por intuición;
- poda masiva por nombre de carpeta;
- aceptar `source_probe()` o carpeta existente como PASS;
- reescribir upstream sin necesidad demostrada;
- descargar otro orquestador/motor para evitar resolver el nodo;
- modificar un nodo reclamado por otra IA;
- declarar cierre sin test/evidence/read-back.

## 8. Watchdog

El Watchdog solo supervisa:

```text
SCAN Core kernel Yaiwes/
→ REGISTER nodo nuevo STEP1 si no existe
→ CHECK Crazy Wall locks
→ REQUIRE checkpoint.before
→ OBSERVE current_step
→ REQUIRE checkpoint.after + evidence
→ ADVANCE | GAP
→ RELEASE
→ REPEAT
```

No introduce tareas adicionales. Backend disponible para su implementación progresiva: APScheduler, Workalendar, Celery/Taskiq, Redis, Hatchet, Dagu, PostgreSQL, pgvector y gVisor.

## 9. Punto inicial recomendado a Grok

1. Leer este parche + handoff + Crazy Wall.
2. Hacer read-back fresco de `main`.
3. Si FABLES aún no está materializado, puede tomar un nodo nuevo 21–27 de PASO 1 o una revalidación 1–5 que no altere el enchufe.
4. Para nodos 6–20, materializar/verificar FABLES exacto antes de cerrar PASO 2.
5. Actualizar siempre Crazy Wall antes y después.

## 10. Enlaces

- Handoff: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
- Crazy Wall: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Bit%C3%A1cora%20stated%20JSON%20Craxy%20wall.json
- STATE: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/STATE.json
- Watchdog machine plan: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/PLAN-WATCHDOG-PROGRAMMING-V2.json
- Este parche: https://github.com/maxbry123-commits/agentes/blob/main/PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md
