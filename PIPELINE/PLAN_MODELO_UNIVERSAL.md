# README PLAN MODELO UNIVERSAL — PLAN EJECUTABLE (MOLDE)

**Repo:** `maxbry123-commits/agentes` · **rama:** `main`  
**Agente:** `{{AGENTE}}`  
**PLAN_ID:** `{{PLAN_ID}}`  
**GitHub = única verdad.** 1 tarea = 1 salida. PASS solo con evidencia. FAIL-CLOSED. LLM no declara PASS. HTTP 200 ≠ PASS.

**Forma:** PIPELINE-HUGGINGFACE.md sin tareas HF.  
**Segmentos:** PLAN_YAIWES sin S1–S12 ni G1–G7. Ese YAIWES no se reescribe.

Instanciar: `PIPELINE/PLAN_{{PLAN_ID}}.md`

---

## INPUT BLOCK

```text
TAREA: {{TAREA}}
OBJETIVO: {{OBJETIVO}}
FUENTE: {{FUENTE}}
DESTINOS: {{DESTINOS}}
ALCANCE: {{ALCANCE}}
FUERA DE ALCANCE: {{FUERA}}
CRITERIO PASS: {{PASS}}
CRITERIO 100%: {{CIERRE}}
PLAN_ID: {{PLAN_ID}}
N_DESPLEGAR: {{N}}
```

Sin lote: `N_DESPLEGAR=WAIT`. No crear carpeta vacía.

---

## REGLA UNIVERSAL (forma HF)

Cada salida: investigar → verificar → deduplicar → resolver GAP → segunda pasada → X-Ray → registrar → PASS → siguiente.
NO-STOP. No mezclar bloques. No inventar.

**Anotar = aditivo:** leer → SHA → append → commit → leer → el viejo sigue + lo nuevo está.

**Tags:** `CHAT_APROBADO` · `PIPELINE_EXISTENTE` · `INVESTIGACION_NUEVA` · `GAP` · `DESCARTADO`

---

## ENLACES — PARA QUÉ, CÓMO, DÓNDE

```text
ENLACE_DESPLEGAR:  Desplegar/Desplegar {{N}}/
ENLACE_REFACTORIA: Refactoria/refactoria-plan-{{PLAN_ID}}/
ENLACE_DESTINO:    Yaiwes wordflow/ | Wordflow Code/
ENLACE_CHECKPOINT: PIPELINE/checkpoints/{{PLAN_ID}}/
```

**Ejemplo:** Plan X número 2 → `Desplegar/Desplegar 2/` → `Refactoria/refactoria-plan-x-2/`

`despliegue/` ≠ `Desplegar/`.

### Desplegar — para qué
Inbox. El Director sube docs y code de este plan. No es Wordflow. No es Refactoria.

### Desplegar — cómo
1. N = número de este plan.
2. Solo se lee `Desplegar/Desplegar {{N}}/`.
3. No mezclar lotes.
4. Archivo nuevo → destino canónico.
5. Archivo que pisa un vivo → Refactoria.
6. ZIP: hash → extract staging (el ZIP no se vacía) → inventario → 4 o 5.

### Desplegar — dónde
Raíz `Desplegar/`. Extensiones `Desplegar 1/`, `Desplegar 2/`, `Desplegar N/`.

### Refactoria — para qué
Mesa. Versión vieja al lado de la nueva. No editar el vivo primero.

### Refactoria — cómo

**Paso 1 — Aislar**
```text
Refactoria/refactoria-plan-{{PLAN_ID}}/source/     ← copia exacta del vivo
```

**Paso 2 — Implementar**
```text
Refactoria/refactoria-plan-{{PLAN_ID}}/new/        ← versión nueva
```

**Paso 3 — Cruzada ×3**
1. Diff source/ vs new/
2. Tests contra new/
3. Checklist + ficha + checkpoint

Solo si 3 PASS: new → destino. No borrar source/ en el mismo task.

Legado YAIWES: `despliegue/refactoria/<GAP>/` y `Refactoria/<GAP>/`. Plan nuevo: solo `refactoria-plan-{{PLAN_ID}}/`.

extension-kernel = ejemplo (abi-mount, registry, mount-guard). No dump.

---

## ESTADO AUDITADO

| Salida | Estado | Checkpoint |
|---|---|---|
| S1 | QUEUED | PIPELINE/checkpoints/{{PLAN_ID}}/S1.md |
| S{{K}} | QUEUED | PIPELINE/checkpoints/{{PLAN_ID}}/S{{K}}.md |

---

## 1. FUENTES CANÓNICAS

1. Este molde
2. Plan instanciado
3. PLAN_YAIWES si aplica (no reescribir)
4. README de los 2 wordflows
5. Desplegar/Desplegar {{N}}/
6. Refactoria/README.md
7. Método de trabajo
8. notas-trabajo-grock

---

## 2. REGLAS GLOBALES + LEGO

PROHIBIDO: inventar; hot path sin paridad; PASS sin ficha; hardcodear solo Desplegar 1; vacuum.

| Módulo | Autoridad |
|---|---|
| goal_lock.py | execution-orchestration/goal-lock |
| cognitive_loop.py | execution-orchestration/mission-planning |
| evidence_packet.py | observability/evidence-packet |

---

## 3. TOTAL DE SALIDAS = {{K}}

```yaml
id: S1
objetivo: ""
enlace_desplegar: Desplegar/Desplegar N/
enlace_refactoria: Refactoria/refactoria-plan-{{PLAN_ID}}/
destino_canonico: ""
tag: GAP
sheriff: extensions/wordflow/standards/sheriff.py
watchdog: extensions/wordflow/engine/watchdog.py
guardian: mount-guard + VerdictAuthority
verificacion_cruzada: [diff, tests, checklist]
pass: commit + read-back + ficha + checkpoint
estado: QUEUED
checkpoint: PIPELINE/checkpoints/{{PLAN_ID}}/S1.md
```

### Preflight 1.a.1
1 rama main  2 plan+checklist  3 enlace o WAIT  4 hot path  5 alcance  6 evidencia  7 no pintar PASS

### Ficha de cierre
```text
SALIDA:
COMMIT:
READBACK:
ENLACE_GITHUB:
ERRORES:
TAG:
STATUS: PASS|FAIL|OPEN|BLOCKED
```

DAG: BIND → SHERIFF → source → new → ×3 → GUARDIAN → destino → READ-BACK → FICHA → CHECKPOINT

---

## 4. GAPS

| ID | Gap | Destino | Estado |
|---|---|---|---|
| G{{n}} | | | OPEN |

Sin source → BLOCKER.md (problem / source / impact / action).

---

## 5. DEPLOYMENT
NOT_CLAIMED hasta read-back.

## 6. HOT PATH
`extensions/wordflow/engine/code_path_runner.py`

## 7. CRECIMIENTO
ACQUIRE → REUSE/PATCH/ADAPT. No clonar agentes.

---

## COPIAR / ZIP / RAÍCES

1 GET→PUT→SHA  2 blob→tree→commit  3 Actions  4 fork  5 clone+push  
ZIP: HASH → EXTRACT staging → INVENTARIO → COPY → COMMIT → READ-BACK. El ZIP no se vacía.

1 Desplegar  2 PIPELINE  3 Método de trabajo  4 Refactoria  5 Yaiwes wordflow  6 Wordflow Code  7 notas-trabajo-grock

README parches `Readme/Readme1/`. Prohibido crear fuera.
METODO-DE-TRABAJO.md GT1 54KB = OPEN.

---

## FASE 2 (no ahora)
1 subir lote Desplegar N  2 X-Ray 4 u 8 + 12 goals  3 Grok diseña code plugin  4 debate  5 cablear plan+Desplegar+Refactoria

## OPERADOR
RECIBIR → LEER → PLANIFICAR → COMPROBAR → PREPARAR → ENVIAR → SHA → MONITOR → GAP → REINTENTAR → VALIDAR → FICHA → CERRAR
