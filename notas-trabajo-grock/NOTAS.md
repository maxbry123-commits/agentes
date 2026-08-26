# notas-trabajo-grock — NOTAS (base)

**Repo:** maxbry123-commits/agentes · **rama:** main  
**Rol:** block de estado Grok (state JSON / crazy wall).  
**Regla:** este archivo NO se reescribe. Input aprobado nuevo = archivo nuevo enlazado. Tarea 100% PASS → borrar ESE archivo de notas (no este base mientras siga vivo el ciclo).

**Siguiente parche:** `notas-trabajo-grock/NOTAS-1.md`

---

## INPUT BLOCK (leer literal)

TAREA EN CURSO: organizar main a 6 raíces + 3 salidas + anotar Fase 2 para DESPUÉS.
OBJETIVO: no ejecutar Fase 2 ahora. Ejecutar S1 → S2 → S3 → 2 simulaciones + 3 council sobre el molde → luego Fase 2.
FUENTE: chat Director 2026-08-26 + PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md
ALCANCE DE ESTE ARCHIVO: anotar estado aprobado.
FUERA: no limpiar main aquí; no diseñar code aquí; no reescribir el plan vivo.

---

## 6 raíces vivas (autorizadas)

1. Desplegar/ — raíz inbox. Desplegar N = docs de Plan X-N. NO hardcodear Desplegar 1.
2. PIPELINE/ — plan vivo intacto + molde universal (S3).
3. Método de trabajo — base no se toca; falta = parche nuevo.
4. Refactoria/refactoria-plan-x-N/ — solo versión vieja a modificar de ese plan.
5. Yaiwes wordflow/
6. Wordflow Code/

Cableado ejemplo (no fijo):
Plan X-2 → Desplegar/Desplegar 2/ → Refactoria/refactoria-plan-x-2/

7º autorizado solo Grok: esta raíz `notas-trabajo-grock/`.

Patrón cableado = plugin/extensión (Microkernel). `extension-kernel` es UN nodo ejemplo. NO dump de todo lo nuevo.

---

## Salidas pendientes (orden)

S1 Grok: 2 README (enlace + mapa 6 raíces + prohibido crear fuera) + rename/crear 6 raíces + X-Ray notice.
S2 Grok escribe plan; GPT depura basura.
S3 Grok: copiar plan exacto → vaciar TAREAS → molde en PIPELINE. Schema/nodo. Checkpoint 100% Grok/GPT. Enlaces Desplegar N + Refactoria de ese plan. Copiar de Grupo-Trabajo-1 solo lo que falte en método agentes. No reescribir plan original.

LUEGO (sin dañar el molde): 2 simulaciones + 3 ask-council → anotar mejoras en parche de notas / parche del molde.

---

## FASE 2 — ANOTADA · NO EJECUTAR HASTA CERRAR S1 S2 S3 + simulaciones/council

Paso 1. Director sube lote docs + code a Desplegar/Desplegar N.
Paso 2. X-Ray cruzado docs vs code fuente Wordflow. 4 u 8 pasadas. Checkpoint dentro del plan nuevo. Goals ×12:
- ¿Qué está en Desplegar N y no en code Wordflow?
- ¿Qué está incompleto / mejorable?
- ¿Dónde y por qué?
- ¿Existe / rompe / bloquea / falta?
- ¿Cómo se soluciona?
- + resto hasta 12 goals.
Paso 3. Grok usa prompt chat 1 SOLO para diseñar el code que falta (estándares del prompt + sistema plugins/extensión). Entregar al Director para mandar a diseñar.
Paso 4. Director sube code nuevo. Debate y aprobación.
Paso 5. Grok revisa, crea plan nuevo, usa code de Desplegar N, crea Refactoria/refactoria-plan-x-N si hay que modificar, cablea: Refactoria + Desplegar + Plan + trazabilidad + guías + método + raíz destino de cada archivo. GPT no se sale de esa ruta.

Fase 3, 4, 5 = mismo método.

---

## Estado

FASE_2 = ANOTADA_NO_INICIADA
SALIDAS = PENDIENTES
NOTAS_BASE = VIVO
