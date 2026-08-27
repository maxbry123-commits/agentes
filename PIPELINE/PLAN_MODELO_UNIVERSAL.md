# PIPELINE PLAN MODELO UNIVERSAL

**Proyecto:** maxbry123-commits/agentes  
**Forma:** PIPELINE-HUGGINGFACE.md (sin tareas HF)  
**Segmentos de misión:** PLAN_YAIWES (sin S1–S12 ni G1–G7)  
**Estado:** MOLDE / NO es una misión  
**PLAN_ID:** {{PLAN_ID}} · **N_DESPLEGAR:** {{N}}

GitHub = verdad. 1 salida = 1 resultado. FAIL-CLOSED. LLM no declara PASS. HTTP 200 ≠ PASS.  
YAIWES original no se toca: `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md`

Instanciar: copiar este archivo a `PIPELINE/PLAN_{{PLAN_ID}}.md`.

---

## REGLA UNIVERSAL (forma HF)

Cada salida: investigar → verificar → GAP → 2ª pasada → X-Ray → registrar → PASS → siguiente.  
NO-STOP. No mezclar bloques. Anotar = aditivo.

Tags: `CHAT_APROBADO` · `EXISTENTE` · `NUEVO` · `GAP` · `DESCARTADO`

---

## BLOQUE A — INPUT + ENLACES

```text
TAREA / OBJETIVO / FUENTE / DESTINOS / ALCANCE / FUERA / PASS / PLAN_ID
N_DESPLEGAR: {{N}}     # WAIT si no hay lote
ENLACE_DESPLEGAR:  Desplegar/Desplegar {{N}}/
ENLACE_REFACTORIA: Refactoria/refactoria-plan-{{PLAN_ID}}/
ENLACE_DESTINO:    Yaiwes wordflow/ | Wordflow Code/
ENLACE_CHECKPOINT: PIPELINE/checkpoints/{{PLAN_ID}}/
```

Ejemplo (N no es siempre 1):
`Plan X número 2 → Desplegar/Desplegar 2/ → Refactoria/refactoria-plan-x-2/`

`despliegue/` ≠ `Desplegar/`.

### Desplegar — para qué / cómo / dónde
Inbox del lote que el Director sube para ESE plan. Extensión de la raíz `Desplegar/`. Sin lote = no crear carpeta. Archivo nuevo → destino. Archivo que pisa un vivo → Refactoria.

### Refactoria — para qué / cómo / dónde (segmento YAIWES)
Paso 1 source/ = copia exacta del vivo.  
Paso 2 new/ = reescritura.  
Paso 3 ×3 diff + tests + checklist.  
Integrar solo si 3 PASS. No borrar source/ en el mismo task.  
Legado YAIWES: `despliegue/refactoria/<GAP>/` y `Refactoria/<GAP>/`. Plan nuevo: solo `refactoria-plan-{{PLAN_ID}}/`.

extension-kernel = ejemplo (abi-mount, registry, mount-guard). No dump.

---

## BLOQUE B — SEGMENTOS YAIWES (tablas vacías)

### ESTADO AUDITADO
| Salida | Estado | Checkpoint | Nota |
|---|---|---|---|
| S1 | QUEUED | PIPELINE/checkpoints/{{PLAN_ID}}/S1.md | |

### FUENTES
Molde + plan instanciado + YAIWES si aplica + README 2 wordflows + Desplegar N + Refactoria + Método + notas-trabajo-grock

### REGLAS + LEGO
PROHIBIDO inventar; tocar hot path sin paridad; PASS sin ficha; hardcodear solo Desplegar 1; vacuum.  
LEGO: goal_lock / cognitive_loop / evidence_packet en sus autoridades.

### TOTAL SALIDAS = {{K}}
Schema + ficha + checkpoint por salida.

```yaml
id: S1
enlace_desplegar: Desplegar/Desplegar N/
enlace_refactoria: Refactoria/refactoria-plan-{{PLAN_ID}}/
destino_canonico: ""
tag: GAP
sheriff / watchdog / guardian: ""
estado: QUEUED
checkpoint: PIPELINE/checkpoints/{{PLAN_ID}}/S1.md
```

Ficha: SALIDA / COMMIT / READBACK / ENLACE_GITHUB / ERRORES / TAG / STATUS

Sheriff `extensions/wordflow/standards/sheriff.py`  
Watchdog `extensions/wordflow/engine/watchdog.py`  
Guardian mount-guard + VerdictAuthority

Preflight 1.a.1: rama · plan · enlace o WAIT · hot path · alcance · no pintar PASS.

### GAPS
| ID | Gap | Destino | Estado |
|---|---|---|---|
| G{{n}} | | | OPEN |

### DEPLOYMENT
NOT_CLAIMED hasta read-back.

### HOT PATH
`extensions/wordflow/engine/code_path_runner.py`

### CRECIMIENTO
ACQUIRE → REUSE/PATCH/ADAPT. No clonar agentes.

---

## BLOQUE C — COPIA / ZIP / RAÍCES

GET→PUT→SHA · blob→tree→commit · ZIP: extract no vacía el ZIP.  
Raíces: Desplegar · PIPELINE · Método de trabajo · Refactoria · Yaiwes wordflow · Wordflow Code · notas-trabajo-grock

---

## BLOQUE D — FASE 2 (después de salidas de esta guía, no ahora)

1 Director sube lote a Desplegar N  
2 X-Ray docs vs code Wordflow (4 u 8) + checkpoint 12 goals  
3 Grok diseña code faltante con plugin  
4 Director sube code nuevo; debate  
5 Grok cablea plan + Desplegar + Refactoria

---

## LOOP
INPUT → BIND enlaces → SHERIFF → source → new → ×3 → GUARDIAN → destino → READ-BACK → FICHA → CHECKPOINT → siguiente.
