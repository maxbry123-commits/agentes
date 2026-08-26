# README PLAN MODELO UNIVERSAL — GUÍA + FORMULARIO EJECUTABLE

**Repo:** `maxbry123-commits/agentes` · **rama:** `main`  
**Qué es:** cómo se escribe un plan de trabajo y el formulario para instanciarlo.  
**Modelo de secciones (no se reescribe):** `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md`  
**GitHub = única verdad.** 1 tarea = 1 salida. PASS solo con evidencia + read-back. FAIL-CLOSED. LLM no declara PASS.

Instanciar: copiar este archivo a `PIPELINE/PLAN_<PLAN_ID>.md` y rellenar `{{ }}`.  
Mejora de este molde: parche `PIPELINE/PLAN_MODELO_UNIVERSAL/Readme1.md` (no vacuum).

Sandbox X-Ray 5: PASS (34 checks) antes de este commit.

---

## INPUT BLOCK (contrato — pegar literal del Director)

```text
TAREA:
OBJETIVO:
FUENTE:
DESTINOS:
ALCANCE:
FUERA DE ALCANCE:
REGLAS ESPECIALES:
CRITERIO PASS:
CRITERIO 100%:
PLAN_ID:
N_DESPLEGAR:          # WAIT si el Director no subió lote. No crear carpeta vacía.
```

No reinterpretar a mitad. Tarea nueva = otro PLAN_ID.

---

## IDENTIDAD

| Campo | Valor |
|---|---|
| PLAN_ID | `{{PLAN_ID}}` |
| Título | `{{TITULO}}` |
| Agente ejecutor | `{{GPT|Grok}}` |
| Estado | QUEUED |

---

## CABLEADO — de / a / función

N es el número de ESTE plan. `Desplegar 1` es solo el ejemplo del lote 1.

```text
Plan {{PLAN_ID}}
  → Desplegar/Desplegar {{N}}/                      inbox lote Director
  → Refactoria/refactoria-plan-{{PLAN_ID}}/source/  copia exacta a modificar
  → Refactoria/refactoria-plan-{{PLAN_ID}}/new/     versión nueva
  → destino canónico                                Yaiwes wordflow | Wordflow Code
  → PIPELINE/PLAN_{{PLAN_ID}}.md                    este plan
  → PIPELINE/checkpoints/{{PLAN_ID}}/S<n>.md        cierre 100%
```

| De | A | Función |
|---|---|---|
| Director | `Desplegar/Desplegar N/` | subir docs y code del plan N |
| Plan | `Desplegar/Desplegar N/` | no mezclar lotes de planes distintos |
| Plan | `Refactoria/refactoria-plan-ID/source/` | aislar viejo; no editar origen |
| Plan | `Refactoria/refactoria-plan-ID/new/` | implementar |
| `new/` | `Yaiwes wordflow/` o `Wordflow Code/` | integrar solo si sheriff+watchdog+guardian+×3 PASS |
| Plan | `PIPELINE/checkpoints/ID/` | anotar cierre sin reescribir el plan |
| Plan | `Método de trabajo/` | reglas; si falta gía = copiar archivo, no link |
| Plan | `notas-trabajo-grock/` | estado Grok |
| Capacidad nueva | Plugin Registry + `wordflow/abi.py` | cablear sin editar archivo base |
| Sheriff | cada salida | ¿permitido? ¿raíz viva? ¿hot path? |
| Watchdog | LOOP | stop determinista si estanca o rompe |
| Guardián | post-verify | DENY/PASS de autoridad, no del LLM |

Paths reales:

- Sheriff: `extensions/wordflow/standards/sheriff.py`, `extensions/wordflow/standards/checklist_sheriff.py`, `extensions/wordflow/engine/control_sheriff_bridge.py`
- Watchdog: `extensions/wordflow/engine/watchdog.py` (`check_watchdog`)
- Guardián: mount-guard en `agente-yaiwes/kernel-principal/extension-kernel/mount-guard/`; sentinel; VerdictAuthority en post_verify de `code_path_runner`
- Validación schema: `extensions/wordflow/schemas/`
- `extension-kernel` = nodo ejemplo. No dump de archivos nuevos.

---

## DSL

```text
PLAN_ID N S<n> G<n>
Desplegar/Desplegar N/
Refactoria/refactoria-plan-<PLAN_ID>/{source,new}
Yaiwes wordflow/ Wordflow Code/ Método de trabajo/ PIPELINE/ Refactoria/ Desplegar/
QUEUED RUNNING WAITING GAP PASS BLOCKED HOLD OPEN CLOSED
COPY MOVE REUSE PATCH ADAPT GENERATE
WRITE COMMIT WAIT READ-BACK COMPARE
SHERIFF WATCHDOG GUARDIAN VALIDATE CROSSCHECK
```

```text
PLAN <PLAN_ID> BINDS
  lote=Desplegar/Desplegar <N>
  old=Refactoria/refactoria-plan-<PLAN_ID>/source
  new=Refactoria/refactoria-plan-<PLAN_ID>/new
  dest=<raiz-viva>/<path>
  check=PIPELINE/checkpoints/<PLAN_ID>/S<n>.md
```

---

## DAG (no saltar nodo)

```text
INPUT_BLOCK
  → LEER método + este molde + PLAN_YAIWES + README 2 wordflows + notas
  → XRAY_20
  → BIND_DESPLEGAR_N
  → BIND_REFACTORIA
  → WRITE_PLAN_FILE
  → SCHEMA_CADA_S
  → LOOP_S → SHERIFF → WATCHDOG → COPY source/ → IMPLEMENT new/
       → VALIDATE → CROSSCHECK_x3 → GUARDIAN → INTEGRATE
       → WRITE COMMIT WAIT READ-BACK COMPARE → CHECKPOINT
  → SEGUNDA_PASADA
  → XRAY_5
  → DONE | BLOCKER
```

---

## SCHEMA de cada salida

```yaml
id: S1
objetivo: ""
inputs: []
outputs: []
desplegar: Desplegar/Desplegar N/
refactoria_source: Refactoria/refactoria-plan-<ID>/source/
refactoria_new: Refactoria/refactoria-plan-<ID>/new/
destino_canonico: ""
sheriff: "path en raíz viva; hot path solo con paridad tests"
watchdog: "no mismo fallo ×2 sin cambiar mecanismo"
guardian: "VerdictAuthority / sentinel no DENY"
validacion: "I/O + SHA"
verificacion_cruzada: ["diff source/new", "tests", "checklist"]
dependencias: []
pass: "commit + read-back + checkpoint"
estado: QUEUED
checkpoint: PIPELINE/checkpoints/<ID>/S1.md
```

Checkpoint (no reescribir el plan):

```text
PLAN_ID:
SALIDA:
PATHS:
COMMIT:
READBACK:
SHERIFF:
WATCHDOG:
GUARDIAN:
CROSSCHECK_1:
CROSSCHECK_2:
CROSSCHECK_3:
GAPS:
STATUS:
```

---

## ESTADO AUDITADO

| Salida | Estado | Checkpoint | Nota |
|---|---|---|---|
| S1 | QUEUED | PIPELINE/checkpoints/{{PLAN_ID}}/S1.md | |
| SN | QUEUED | PIPELINE/checkpoints/{{PLAN_ID}}/SN.md | |

---

## SISTEMA REFACTORIA — OBLIGATORIO

```text
Paso 1: Refactoria/refactoria-plan-{{PLAN_ID}}/source/
Paso 2: Refactoria/refactoria-plan-{{PLAN_ID}}/new/
Paso 3 ×3: diff + tests + checklist
```

Integrar solo si 3 PASS. No borrar source/ en el mismo task.  
Path legado YAIWES: `despliegue/refactoria/<GAP>/source/` y `Refactoria/<GAP>/source/`.  
Planes nuevos: solo `refactoria-plan-<PLAN_ID>/`.  
No editar in-place hot path. No inventar body.

---

## FUENTES CANÓNICAS

1. Este molde  
2. `PIPELINE/PLAN_{{PLAN_ID}}.md`  
3. `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md` si aplica (no reescribir)  
4. README Yaiwes wordflow y Wordflow Code  
5. Desplegar + lote N si existe  
6. Refactoria/README.md  
7. Método de trabajo/ + README_METHOD.md  
8. notas-trabajo-grock/

---

## REGLAS GLOBALES

```text
PROHIBIDO: inventar; reescribir code_path_runner sin paridad; duplicar lego;
PASS sin checkpoint; apply sin read-back; hardcodear Desplegar 1 como único N;
dump a extension-kernel; reescribir molde o PLAN_YAIWES para anotar cierre;
poner enlace donde se pidió copiar archivo.
OBLIGATORIO: INPUT BLOCK; schema; checkpoint; COPY-FIRST; Refactoria;
sheriff+watchdog+guardian; read-write-verify; X-Ray; FAIL-CLOSED.
```

### LEGO

| Módulo | Autoridad |
|---|---|
| goal_lock.py | execution-orchestration/goal-lock |
| cognitive_loop.py | execution-orchestration/mission-planning |
| evidence_packet.py | observability/evidence-packet |

---

## TOTAL DE SALIDAS = {{K}}

Una salida = un resultado verificable + schema + checkpoint.

---

## GAPS

| ID | Gap | Destino | Estado |
|---|---|---|---|
| G{{n}} | | | OPEN |

Sin source → `Refactoria/refactoria-plan-{{PLAN_ID}}/BLOCKER.md`.

---

## DEPLOYMENT

remote_apply / readback: NOT_CLAIMED hasta read-back. HTTP 200 ≠ PASS.

---

## HOT PATH

`extensions/wordflow/engine/code_path_runner.py`  
Raíz nombre: `Wordflow Code/`. Cuerpo: `extensions/wordflow/`.

---

## PLUGIN / MICROKERNEL

El sistema sigue el patrón de **Microkernel Architecture** (también conocido como Plugin Architecture): un núcleo mínimo (`kernel-principal`) que expone puntos de extensión y un registro de plugins, permitiendo añadir capacidades nuevas sin modificar el núcleo. `wordflow/abi.py` (`ExtensionABI`) es la implementación concreta de ese punto de extensión en este repositorio.

Docs: Readme/Readme1/Readme2. Code: registry. `extension-kernel` no es dump.

---

## CÓMO COPIAR / ZIP / DUPLICADO

1 Contents API GET→PUT→SHA  
2 Git Data blob→tree→commit→ref  
3 Actions  
4 Transfer repo entero  
5 Clone+push  

ZIP: hash → extract staging (no vacía ZIP) → inventario → guards → copy → 4 pasadas → commit → read-back.  
Duplicado: borrar solo el no canónico; si duda HOLD.

---

## RAÍCES VIVAS

Desplegar/ · PIPELINE/ · Método de trabajo/ · Refactoria/ · Yaiwes wordflow/ · Wordflow Code/ · notas-trabajo-grock/

---

## X-RAY 5

1 estructura 2 contenido 3 origen/copias 4 sheriff-watchdog-guardian 5 read-back

---

## CRECIMIENTO

OSS → ACQUIRE → ANALYZE → REUSE/PATCH/ADAPT → ficha v2 → registry.

---

## DoD documento plan

INPUT + secciones YAIWES + schema + checkpoint + cableado con función + DSL/DAG + control paths + fuentes reales + read-back.

## DoD misión

Cada S PASS o BLOCKER. Hot path intacto. 0 fake PASS.

## BLOCKER

`Refactoria/refactoria-plan-{{PLAN_ID}}/BLOCKER.md`
