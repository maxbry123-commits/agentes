# GUÍA + MOLDE DE PLAN DE TRABAJO

**Repo:** maxbry123-commits/agentes · **rama:** main  
**Modelo:** PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md (no se reescribe)  
**Instancia:** copiar a PIPELINE/PLAN_<PLAN_ID>.md y rellenar {{ }}.  
GitHub = verdad. 1 tarea = 1 salida. FAIL-CLOSED. LLM no declara PASS. HTTP 200 ≠ PASS.

**NÚMERO DE SALIDAS DEL MOLDE = 0.** El molde no ejecuta misión. El plan instanciado declara su K.

---

# BLOQUE A — CABLEADO (no mezclar con B/C)

## Para qué son los dos enlaces

| Enlace | Carpeta | Para qué |
|---|---|---|
| ENLACE_DESPLEGAR `Desplegar/Desplegar {{N}}/` | inbox plan N | El Director sube docs/code de ese plan. Fuente del lote. |
| ENLACE_REFACTORIA `Refactoria/refactoria-plan-{{PLAN_ID}}/` | mesa | Versión vieja del archivo que ya existe y se va a cambiar. |

`despliegue/` ≠ `Desplegar/`.

## Dónde va en el plan (cabecera, no anexo)

```text
PLAN_ID: {{PLAN_ID}}
ENLACE_DESPLEGAR:  Desplegar/Desplegar {{N}}/
ENLACE_REFACTORIA: Refactoria/refactoria-plan-{{PLAN_ID}}/source/ y /new/
ENLACE_DESTINO:    Yaiwes wordflow/… | Wordflow Code/…
ENLACE_CHECKPOINT: PIPELINE/checkpoints/{{PLAN_ID}}/
```

## Cómo se usa Desplegar
1. N = número de este plan. 2. Director sube a Desplegar/Desplegar N/. 3. El plan apunta solo ahí. 4. Sin lote = WAIT; no crear vacío. 5. Archivo nuevo del lote → destino canónico. Archivo que pisa uno vivo → Bloque B / Refactoria.

## Cómo se usa Refactoria
1. Copiar vivo → source/. 2. No editar source ni vivo. 3. Escribir new/. 4. Diff + tests + checklist. 5. Sheriff → watchdog → guardian. 6. new/ → canónico. 7. Read-back. 8. source/ no se borra en el mismo task.

Legado YAIWES: `despliegue/refactoria/<GAP>/source/` y `Refactoria/<GAP>/source/`. Planes nuevos: solo refactoria-plan-ID.

## Triángulo
Desplegar N (lote) → si muta vivo: Refactoria source/new → destino Wordflow → checkpoint.

---

# BLOQUE B — FORMA DEL PLAN (secciones YAIWES)

INPUT BLOCK literal. ESTADO AUDITADO. REFACTORIA. FUENTES. REGLAS + LEGO (goal_lock / cognitive_loop / evidence_packet). TOTAL SALIDAS = {{K}}. GAPS. DEPLOYMENT NOT_CLAIMED. HOT PATH `extensions/wordflow/engine/code_path_runner.py`. CRECIMIENTO ACQUIRE/REUSE.

### Schema salida
```yaml
id: S1
objetivo: ""
enlace_desplegar: Desplegar/Desplegar N/
enlace_refactoria: Refactoria/refactoria-plan-ID/
destino: ""
tag: CHAT_APROBADO | EXISTENTE | NUEVO | GAP | DESCARTADO
sheriff / watchdog / guardian: ""
pass: commit + read-back + ficha
checkpoint: PIPELINE/checkpoints/ID/S1.md
estado: QUEUED
```

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

### Anotar = aditivo
Leer → SHA → append → commit → leer → el viejo sigue + lo nuevo está. Nunca vacuum.

### Preflight 1.a.1
1 repo/rama 2 plan+checklist 3 enlaces o WAIT 4 hot path 5 alcance 6 evidencia 7 GAP no se pinta PASS.

### DSL / DAG
BIND enlaces → SHERIFF → source → new → ×3 → GUARDIAN → destino → READ-BACK → FICHA.
Sheriff `extensions/wordflow/standards/sheriff.py`. Watchdog `extensions/wordflow/engine/watchdog.py`. Guardian mount-guard + VerdictAuthority.

---

# BLOQUE C — COPIA / ZIP / RAÍCES / PLUGIN

Copy: GET→PUT→SHA | blob→tree→commit | Actions | fork | clone+push.  
ZIP: hash→extract staging (ZIP no se vacía)→inventario→raíz.  
Duplicado: borrar solo no-canónico.

Raíces: Desplegar · PIPELINE · Método de trabajo · Refactoria · Yaiwes wordflow · Wordflow Code · notas-trabajo-grock.

Plugin: Microkernel. `wordflow/abi.py`. extension-kernel no dump. README Readme/Readme1.

GT1: GITHUB-ESTRUCTURA ya en Método de trabajo. METODO-DE-TRABAJO.md 54KB = OPEN GET+PUT.

---

# BLOQUE D — NO MEZCLAR

A cableado. B forma. C copia. D esta regla.  
No meter contenido HF (modelos/Spaces) en planes de agentes.  
Tags: CHAT_APROBADO · EXISTENTE · NUEVO · GAP · DESCARTADO.

---

# DoD
Enlaces Desplegar/Refactoria con para qué / cómo / dónde. Secciones YAIWES. Ficha. Aditivo. Preflight. Tags. METODO GT1 OPEN explícito.
