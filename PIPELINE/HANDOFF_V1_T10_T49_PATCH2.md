# HANDOFF PATCH2 — re-auditoría (aditivo)
**Anclas (leer en orden):**
1. `PIPELINE/HANDOFF_V1_T10_T49.md` — **NO editar**
2. `PIPELINE/HANDOFF_V1_T10_T49_PATCH.md` — **NO editar**
3. Este archivo PATCH2

**Fecha:** 2026-08-18  
**Regla:** solo agregar; nunca borrar handoff ni patch1.

---

## Re-auditoría 4 pasadas

### Pasada 1 — ¿Siguen las 40 tareas + extras?
**PASS.** T10–T49 + extras siguen cubiertos entre HANDOFF + PATCH1.

### Pasada 2 — ¿PATCH1 cerró G-H1…G-H9?
| Gap | Estado tras PATCH1 |
|-----|--------------------|
| Inventario pre-code | Cerrado en texto |
| LOC | Cerrado |
| TAREAS_ACTUAL update | Cerrado en texto |
| Template forense | Cerrado (mínimo) |
| Firmas T13–T40 | Cerrado mínimo |
| Contrato T41 | Cerrado |
| PYTHONPATH / __init__ | Cerrado |

### Pasada 3 — 3 simulaciones nuevas (residual)
**Sim1 T10:** Agente no tiene el JSON de ficha embebido → debe **leer GH** `ficha.v2.json` antes de code.  
**Sim2 T13–T18:** Paths “o A o B” → debe **elegir un path existente** tras listar árbol; si ambos existen, ADAPT el más cableado.  
**Sim3 TAREAS_ACTUAL:** Archivo en GH aún puede decir SIGUIENTE T06 → **en la primera salida T10** corregir a T10 DONE / SIGUIENTE T11.

### Pasada 4 — ¿Bloquea ejecución T10?
**NO.** Residuales son operativos, no faltan IDs de tarea.

---

## RESIDUALES → cierre en PATCH2

### R1 — T10: leer ficha real antes de programar
Antes de editar `ficha_loader.py`:
1. Abrir en GH: `extensions/wordflow_kernel/ficha.v2.json` y/o `extensions/wordflow/ficha.v2.json`
2. Anotar claves reales presentes
3. `validate_ficha` exige al menos: identificador (`id` o `name`) + `version` si existe en el JSON; no inventar schema hostil al JSON real
4. Si el JSON está vacío/roto → fail_closed path (T12), no inventar ficha de producto

### R2 — Regla de path ambiguo (“A o B”)
Cuando HANDOFF dice dos paths posibles:
1. `list` dir en GH
2. Si **uno** existe → ADAPT ese
3. Si **los dos** existen → ADAPT el que ya importa el bootstrap/kernel
4. Si **ninguno** → CREATE en el path preferido de la ficha (el primero citado)
5. **Prohibido** crear `*_v2.py` / `*_new.py` paralelos

### R3 — Primera acción global al empezar T10
En el mismo ciclo T10 (o commit seguido):
- Actualizar `PIPELINE/TAREAS_ACTUAL.md` a: DONE T01–T10 (tras cerrar T10), SIGUIENTE T11
- Hasta que T10 no esté DONE, SIGUIENTE debe mostrar T10 (no T06)

### R4 — Dependencias mínimas (grafo corto)
```
T10 validate/load → T12 assert_ficha_or_fail
T07+T08+T09 → T11 bootstrap
T11+T12 → T13 bootstrap_fake
T06 → T18 kernel_list_connections
T26 → T27 GatewayModel
T13…T23 → T24 claim parcial
T13…T48 PASS → T49 claim V1
```
No ejecutar T49 si T48 tiene FAIL.

### R5 — Smoke commands de referencia
```bash
# desde repo root con código local
export PYTHONPATH=extensions
python -m wordflow_kernel.instance
python -m wordflow_kernel.instance_store
python -m wordflow_kernel.spawn
python -m wordflow_kernel.ficha_loader   # tras T10
python -m wordflow.engine.list_connections
```
Ajustar si el módulo no es `-m` ejecutable: `python path/al/archivo.py`.

### R6 — Forense: evidencia mínima aceptable
Para PASS de tarea con code hace falta **al menos una**:
- salida smoke en log de la salida, **y**
- enlace GH del archivo que abre el blob, **y**
- read-back remoto (mencionar size o ancla de contenido)
Sin eso → no DONE.

### R7 — Qué no está en handoff a propósito (no es gap V1)
- Fusión Kimi/Minimax runtime
- Fetch HF real
- 85 contratos L2–L8 completos
- DSL lexer completo
- Auto-recovery 200
(Ver PIPELINE 52 sección Fuera de V1.)

### R8 — Si aparece gap nuevo en ejecución
Crear `PIPELINE/HANDOFF_V1_T10_T49_PATCH3.md` (aditivo).  
**No** editar HANDOFF ni PATCH ni PATCH2 salvo orden explícita del Director.

---

## Veredicto re-auditoría
| Pregunta | Respuesta |
|----------|-----------|
| ¿Faltan tareas de las 40? | **No** |
| ¿Se puede empezar T10? | **Sí** |
| ¿Handoff original tocado? | **No** |
| ¿Gaps residuales documentados? | **Sí (R1–R8)** |

**Orden de lectura:** HANDOFF → PATCH → **PATCH2** → ejecutar T10.

Enlaces:
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/HANDOFF_V1_T10_T49.md
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/HANDOFF_V1_T10_T49_PATCH.md
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/HANDOFF_V1_T10_T49_PATCH2.md
