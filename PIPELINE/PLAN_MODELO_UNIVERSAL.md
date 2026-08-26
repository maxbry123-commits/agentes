# README PLAN MODELO UNIVERSAL — PLAN EJECUTABLE (MOLDE)

**Repo:** `maxbry123-commits/agentes` · **rama:** `main`  
**Agente:** `{{AGENTE}}`  
**PLAN_ID:** `{{PLAN_ID}}`  
**GitHub = única verdad.** 1 tarea = 1 salida. PASS solo con evidencia. FAIL-CLOSED. LLM no declara PASS. HTTP 200 ≠ PASS.

**Copia de estructura de:** `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md`  
Ese archivo **no se reescribe**. Este molde es otro path. Instanciar: copiar a `PIPELINE/PLAN_{{PLAN_ID}}.md` y rellenar `{{ }}`. Vaciar tablas de misión; no copiar G1–G7 ni S1–S12 de YAIWES.

**Documento de producción (si existe):** `{{DOC_PRODUCCION}}`

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

Sin lote subido: `N_DESPLEGAR=WAIT`. No crear carpeta vacía.

---

## ENLACES DEL PLAN — PARA QUÉ, CÓMO, DÓNDE

Van **aquí**, en cabecera, no al final.

```text
ENLACE_DESPLEGAR:  Desplegar/Desplegar {{N}}/
ENLACE_REFACTORIA: Refactoria/refactoria-plan-{{PLAN_ID}}/
ENLACE_DESTINO:    Yaiwes wordflow/  |  Wordflow Code/
ENLACE_CHECKPOINT: PIPELINE/checkpoints/{{PLAN_ID}}/
ENLACE_PLAN:       PIPELINE/PLAN_{{PLAN_ID}}.md
```

`despliegue/` (minúsculas, motor) **no** es `Desplegar/`.

### Desplegar — para qué
Inbox. El Director sube los documentos y el code de **este** plan. Es la fuente de verdad del lote. No es el Wordflow. No es Refactoria.

### Desplegar — cómo
1. N = número de este plan (el plan 2 usa `Desplegar 2`, no `Desplegar 1`).
2. El Director crea/usa `Desplegar/Desplegar {{N}}/` al subir archivos.
3. El ejecutor solo lee ese path. No mezcla lotes de otro N.
4. Si el archivo del lote **no existe** en el Wordflow: copiar al destino canónico.
5. Si el archivo del lote **cambia** un archivo que ya existe: usar Refactoria (abajo).
6. ZIP en el lote: hash → extraer a staging (el ZIP no se vacía) → inventario → misma regla 4 o 5.

### Desplegar — dónde
Raíz main `Desplegar/`. Extensiones: `Desplegar 1/`, `Desplegar 2/`, `Desplegar N/`. No son raíces nuevas de main.

### Refactoria — para qué
Mesa de reescritura. Evita editar el archivo vivo y perder código. Se coloca la **versión vieja** y se escribe la **nueva** al lado para cruzarlas.

### Refactoria — cómo (igual que el plan modelo YAIWES, path por plan)

**Paso 1 — Aislar (copiar, no editar in-place)**
```text
Refactoria/refactoria-plan-{{PLAN_ID}}/source/     ← copia exacta del archivo vivo
```
Nunca modificar primero el original en `extensions/` ni en destinos canónicos.

**Paso 2 — Implementar**
```text
Refactoria/refactoria-plan-{{PLAN_ID}}/new/        ← versión nueva
```
Usar `source/` como referencia. Se puede leer el lote `Desplegar/Desplegar {{N}}/` como spec. Bucle hasta acceptance.

**Paso 3 — Verificación cruzada ×3**
1. Diff `source/` vs `new/`
2. Tests contra `new/`
3. Checklist + evidencia + ficha de cierre + checkpoint

Solo si las 3 PASS: integrar `new/` al destino canónico.  
Borrar original solo con autorización Director + 3 verificaciones.  
Nunca borrar `source/` en el mismo task.

**Prohibido:** editar hot path sin paridad de tests; PASS sin las 3; inventar body/adapters/schemas para cerrar gaps.

### Path legado del plan YAIWES (misión G1–G7 ya abierta)
```text
despliegue/refactoria/<GAP_o_TASK_ID>/source/
Refactoria/<GAP_o_TASK_ID>/source/
Refactoria/<GAP_o_TASK_ID>/new/
```
Planes **nuevos** no usan esos paths. Usan solo `refactoria-plan-{{PLAN_ID}}/`.

### Cómo se usan juntos
```text
Desplegar/Desplegar N/          lote que el Director subió
        |
        |- archivo nuevo ----------------> destino canónico
        |- cambia un vivo
                > source/  (foto del vivo)
                > new/     (reescritura)
                > destino canónico
                > PIPELINE/checkpoints/PLAN_ID/
```

---

## ESTADO AUDITADO

| Salida | Estado | Checkpoint | Nota |
|---|---|---|---|
| S1 | QUEUED | PIPELINE/checkpoints/{{PLAN_ID}}/S1.md | |
| S{{K}} | QUEUED | PIPELINE/checkpoints/{{PLAN_ID}}/S{{K}}.md | |

Gap técnico OPEN→CLOSED solo con evidencia real en `main`.

---

## 1. FUENTES CANÓNICAS

1. Este molde `PIPELINE/PLAN_MODELO_UNIVERSAL.md`
2. El plan instanciado `PIPELINE/PLAN_{{PLAN_ID}}.md`
3. `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md` si la misión toca YAIWES (no reescribir)
4. `Yaiwes wordflow/Readme/README.md`
5. `Wordflow Code/Readme/README.md`
6. `Desplegar/README.md` + `Desplegar/Desplegar {{N}}/` si existe
7. `Refactoria/README.md`
8. `Método de trabajo/` + `README_METHOD.md`
9. `notas-trabajo-grock/`
10. `{{FUENTE_EXTRA}}`

---

## 2. REGLAS GLOBALES

```text
PROHIBIDO: inventar; reescribir code_path_runner sin paridad; duplicar lego;
PASS sin checkpoint ni ficha; afirmar apply sin read-back; hardcodear Desplegar 1
como único N; dump a extension-kernel; reescribir PLAN_YAIWES o este molde
para anotar un cierre; poner URL donde se pidió copiar archivo;
mezclar lotes N; crear Desplegar N vacío.
OBLIGATORIO: INPUT BLOCK; enlaces en cabecera; schema; checkpoint;
COPY-FIRST; Refactoria en cambios de code; sheriff+watchdog+guardian;
anotar=aditivo; FAIL-CLOSED.
```

### Regla LEGO
| Módulo | Autoridad única |
|---|---|
| goal_lock.py | execution-orchestration/goal-lock |
| cognitive_loop.py | execution-orchestration/mission-planning |
| evidence_packet.py | observability/evidence-packet |

### Anotar = aditivo
Leer archivo → SHA → append → commit → leer de nuevo → el texto viejo sigue y lo nuevo está. Nunca vacuum.

### Tags
`CHAT_APROBADO` · `EXISTENTE` · `NUEVO` · `GAP` · `DESCARTADO`

### Plugin
Microkernel / Plugin Architecture. Núcleo mínimo. `wordflow/abi.py` (`ExtensionABI`) = extension point. `extension-kernel` = abi-mount + registry + mount-guard. No es carpeta de dump.

---

## 3. TOTAL DE SALIDAS = {{K}}

Molde: K vacío. Cada salida = 1 schema + 1 fila ESTADO + 1 checkpoint + 1 ficha.

### Schema
```yaml
id: S1
objetivo: ""
enlace_desplegar: Desplegar/Desplegar N/
enlace_refactoria: Refactoria/refactoria-plan-{{PLAN_ID}}/
destino_canonico: ""
tag: GAP
sheriff: raiz viva / hot path
watchdog: no stagnation x2
guardian: no DENY
verificacion_cruzada: [diff, tests, checklist]
pass: commit + read-back + ficha + checkpoint
estado: QUEUED
checkpoint: PIPELINE/checkpoints/{{PLAN_ID}}/S1.md
```

### Preflight 1.a.1 (antes de cada salida)
1. repo/rama main
2. leer este plan + INPUT checklist
3. ENLACE_DESPLEGAR existe o WAIT
4. hot path
5. alcance
6. evidencia previa
7. no pintar PASS un GAP

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

### Sheriff / watchdog / guardian
- Sheriff: `extensions/wordflow/standards/sheriff.py`
- Watchdog: `extensions/wordflow/engine/watchdog.py`
- Guardian: mount-guard + sentinel + VerdictAuthority (`code_path_runner` post_verify)

DAG: BIND enlaces → SHERIFF → source → new → ×3 → GUARDIAN → destino → READ-BACK → FICHA → CHECKPOINT.

---

## 4. GAPS

| ID | Gap | Destino canónico | Estado |
|---|---|---|---|
| G{{n}} | | | OPEN |

Sin source → `Refactoria/refactoria-plan-{{PLAN_ID}}/BLOCKER.md` (problem / source / impact / action). No inventar implementación.

---

## 5. DEPLOYMENT

remote_apply / readback: `NOT_CLAIMED` hasta read-back real.

---

## 6. HOT PATH

`extensions/wordflow/engine/code_path_runner.py` — operativo.  
Raíz de nombre: `Wordflow Code/`. Cuerpo actual: `extensions/wordflow/`.

---

## 7. CRECIMIENTO DE CAPACIDADES

OSS → ACQUIRE → ANALYZE gap → REUSE/PATCH/ADAPT → ficha v2 + enchufe → catalog → registry.  
No clonar agentes enteros. No escribir de cero lo reciclable.

---

## COPIAR / ZIP / DUPLICADO

1. Contents API GET→PUT→SHA
2. Git Data blob→tree→commit→ref
3. Actions
4. Transfer/fork (repo entero)
5. Clone + push

ZIP: HASH → EXTRACT staging → INVENTARIO → COPY raíz destino → 4 pasadas → COMMIT → READ-BACK. Extraer no vacía el ZIP.
Duplicado: identificar canónico → borrar solo el otro → 404 duplicado → canónico sigue.

---

## RAÍCES MAIN

1. `Desplegar/`
2. `PIPELINE/`
3. `Método de trabajo/` + `README_METHOD.md`
4. `Refactoria/`
5. `Yaiwes wordflow/`
6. `Wordflow Code/`
7. `notas-trabajo-grock/`

`.github/workflows/` excepción Actions.

---

## DEFINITION OF DONE

Documento: misma estructura que YAIWES + INPUT + enlaces Desplegar/Refactoria explicados + schema + ficha + checkpoint.
Misión: cada S con ficha PASS o BLOCKER. 0 fake PASS.
