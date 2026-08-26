# GUÍA + MOLDE — CÓMO HACER UN PLAN DE TRABAJO

**Repo:** `maxbry123-commits/agentes` · **rama:** `main`  
**Qué es este archivo:** la guía para *escribir* un plan y el formulario para *instanciarlo*.  
**Modelo de plan ya aprobado:** `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md` — no se reescribe.  
**Este molde:** si hay que mejorarlo, parche `PIPELINE/PLAN_MODELO_UNIVERSAL/Readme1.md`. El Director pidió rehacerlo porque la versión corta no era guía.

**GitHub = única verdad.** PASS = evidencia + read-back. FAIL-CLOSED. LLM no declara PASS.

---

# PARTE I — QUÉ ES UN PLAN (como el que te pasé)

Un plan de trabajo en este repo **no es un resumen**. Es un documento ejecutable que una AI (Grok o GPT) puede seguir sin reinterpretar el chat.

El modelo `PLAN_YAIWES_AGENTE_WORDFLOW.md` ya demuestra las piezas que todo plan debe tener:

1. Cabecera: repo, rama, agente, regla GitHub=verdad, 1 tarea=1 salida, FAIL-CLOSED.
2. Documento de producción / fuentes (si existen).
3. Tabla ESTADO AUDITADO (cada salida con estado y nota).
4. SISTEMA REFACTORIA (source/ + new/ + verificación ×3).
5. FUENTES CANÓNICAS numeradas (paths reales, no ideas).
6. REGLAS GLOBALES (prohibido / obligatorio) + regla LEGO.
7. TOTAL DE SALIDAS (número cerrado).
8. GAPS con ID, destino canónico y OPEN/CLOSED/BLOCKED.
9. DEPLOYMENT (remote_apply / read-back explícito; no afirmar apply).
10. HOT PATH nombrado y protegido.
11. Cómo crece el sistema (ACQUIRE → REUSE → registry) si aplica.

Si un “plan” no tiene esas piezas, **no es un plan de este sistema**. Es una nota.

Este molde añade lo que el modelo YAIWES aún no traía (pedido Director):

- INPUT BLOCK literal al inicio.
- Schema YAML en cada salida.
- Checkpoint fuera del plan (`PIPELINE/checkpoints/<PLAN_ID>/`).
- Cableado Plan ↔ `Desplegar/Desplegar N/` ↔ `Refactoria/refactoria-plan-<ID>/` (N variable; `Desplegar 1` solo ejemplo).
- Extensión/plugin: no reescribir base.
- Cómo copiar, cómo ZIP, cómo borrar duplicado, X-Ray, NO-STOP.
- Enlaces a guías de `agentes` y de `Grupo-Trabajo-1`.

---

# PARTE II — CÓMO SE CONSTRUYE UN PLAN NUEVO (ORDEN FIJO)

No empieces escribiendo salidas. Sigue este DAG.

```text
P0  LEER INPUT BLOCK DEL DIRECTOR (literal)
P1  LEER este molde + PLAN_YAIWES + método + README de las 2 raíces Wordflow + notas-trabajo-grock
P2  X-RAY del repo destino (qué existe, qué falta, qué es basura, qué es HOLD)
P3  ASIGNAR PLAN_ID y N de Desplegar (no inventar carpeta N vacía)
P4  CREAR archivo NUEVO PIPELINE/PLAN_<PLAN_ID>.md  (copia secciones de PARTE V)
    no reescribir PLAN_YAIWES ni este molde
P5  RELLENAR identidad + cableado + fuentes reales
P6  PARTIR el trabajo en salidas (1 salida = 1 resultado verificable)
P7  POR CADA SALIDA: schema YAML + fila en ESTADO AUDITADO + path de checkpoint
P8  LISTAR GAPS OPEN (destino canónico). Sin source → BLOCKER no code inventado
P9  NOMBRAR hot path y raíces que no se tocan
P10 ENLAZAR guías que esa misión usa (ZIP / copia / cuentas / forense)
P11 DEFINITION OF DONE + BLOCKER path
P12 COMMIT del plan + READ-BACK del archivo en GitHub
P13 SOLO ENTONCES ejecutar salidas
```

### P0 — INPUT BLOCK (obligatorio, se pega literal)

```text
TAREA:
OBJETIVO:
FUENTE: repo / path / commit / chat
DESTINOS: raíces autorizadas
ALCANCE:
FUERA DE ALCANCE:
REGLAS ESPECIALES:
CRITERIO PASS:
CRITERIO 100%:
PLAN_ID:
N_DESPLEGAR:  (solo si el Director ya subió lote; si no = WAIT)
```

El INPUT BLOCK no se reinterpretar a mitad de ejecución. Tarea nueva ≠ mezclar: se registra otro PLAN_ID.

### P3 — Cableado (ejemplo; N no es siempre 1)

```text
Plan X-2
    → Desplegar/Desplegar 2/                    lote que subió el Director
    → Refactoria/refactoria-plan-x-2/source/    archivos VIEJOS a modificar
    → Refactoria/refactoria-plan-x-2/new/       archivos NUEVOS
    → destino canónico                         Yaiwes wordflow | Wordflow Code
    → PIPELINE/PLAN_X-2.md
    → PIPELINE/checkpoints/X-2/S1.md … SN.md
```

Si el Director no subió lote: no crear `Desplegar N/` vacío. Estado WAIT en esa punta.

### P6 — Cómo salen las salidas

Una salida es cerrable con evidencia. Ejemplos válidos: “ commitear README ancla”, “mover guía X y verificar SHA”.  
Inválido: “organizar el repo” sin lista de paths.

Número de salidas = el trabajo real, no un número mágico. El modelo YAIWES usó 12 porque esa misión tenía 12. Un plan de depuración puede tener 7. Se declara el total y no se inventan salidas después sin nuevo plan/parche.

### Schema obligatorio por salida

```yaml
id: S1
objetivo: una frase
inputs: [paths reales]
outputs: [paths reales]
desplegar: Desplegar/Desplegar N/   # o N/A
refactoria: Refactoria/refactoria-plan-<ID>/
destino_canonico: Yaiwes wordflow/… | Wordflow Code/… | Método de trabajo/…
dependencias: [S0]
pass: "qué se ve en GitHub para declarar PASS"
estado: QUEUED
checkpoint: PIPELINE/checkpoints/<PLAN_ID>/S1.md
```

### Checkpoint (Grok/GPT escriben aquí, no en el plan)

`PIPELINE/checkpoints/<PLAN_ID>/S<n>.md`

```text
PLAN_ID:
SALIDA:
INPUTS_USADOS:
PATHS_TOCADOS:
COMMIT:
READBACK: PASS|FAIL
DIFF_SOURCE_NEW:
TESTS:
GAPS:
STATUS: PASS|FAIL|OPEN|BLOCKED
```

Reescribir el plan para “anotar que S1 pasó” está prohibido. Se escribe el checkpoint. Si el ESTADO AUDITADO debe cambiar, parche `PLAN_<ID>/Readme1.md` o una tabla en el checkpoint índice, no vacuum del plan.

---

# PARTE III — CÓMO SE RELLENA CADA SECCIÓN DEL MODELO YAIWES

Usa los mismos títulos que el plan modelo. Así GPT no se pierde.

## Cabecera

Copiar el estilo:
`# README PLAN <NOMBRE> — PLAN EJECUTABLE COMPLETO`  
Repo, rama, agente, GitHub=verdad, 1 tarea=1 salida.

## ESTADO AUDITADO

Tabla: Salida | Estado | Checkpoint | Nota.  
Estados permitidos: QUEUED, RUNNING, WAITING, GAP, PASS, BLOCKED.  
OPEN de gap técnico no se pinta PASS documental.

## SISTEMA REFACTORIA

Pegar el protocolo del modelo, cambiando el path a:

```text
Refactoria/refactoria-plan-<PLAN_ID>/source/
Refactoria/refactoria-plan-<PLAN_ID>/new/
```

Reglas idénticas al modelo YAIWES: no editar origen; 3 verificaciones; no borrar source/ en el mismo task; no inventar body; no tocar hot path sin paridad.

## FUENTES CANÓNICAS

Lista numerada de archivos que existen o que el Director subió a Desplegar N.  
Si no existe el path: no lo pongas como fuente. Ponlo en GAPS.

Siempre incluir:
1. este molde
2. el plan instanciado
3. `PLAN_YAIWES` si la misión toca YAIWES
4. README de `Yaiwes wordflow` y `Wordflow Code`
5. `Método de trabajo/` + `README_METHOD.md`
6. lote `Desplegar/Desplegar N/` si existe

## REGLAS GLOBALES

Bloque PROHIBIDO / OBLIGATORIO como el modelo. Añadir: no hardcodear Desplegar 1; no dump a `extension-kernel`; no reescribir bases.

Regla LEGO: tabla módulo → autoridad única. Del modelo:
`goal_lock.py` → execution-orchestration/goal-lock  
`cognitive_loop.py` → execution-orchestration/mission-planning  
`evidence_packet.py` → observability/evidence-packet

## TOTAL DE SALIDAS

Número + lista. Cada una con schema.

## GAPS

Tabla ID | Gap | Destino canónico | Estado.  
Sin source → BLOCKER en `Refactoria/refactoria-plan-<ID>/BLOCKER.md`.

## DEPLOYMENT

Escribir `NOT_CLAIMED` hasta read-back real. Nunca “done” por HTTP 200.

## HOT PATH

`extensions/wordflow/engine/code_path_runner.py`  
Raíz de nombre: `Wordflow Code/`. Cuerpo actual: `extensions/wordflow/`.

## CRECIMIENTO

Solo si la misión incorpora OSS: ACQUIRE → ANALYZE → REUSE/PATCH/ADAPT → ficha v2 → registry. No clonar agentes enteros.

---

# PARTE IV — CÓMO SE EJECUTA EL PLAN YA ESCRITO

Copiado operativo de Grupo-Trabajo-1 `METODO-DE-TRABAJO.md` (no se reescribió esa guía; aquí se resume el DAG para el autor del plan):

```text
INPUT BLOCK
 → LEER método + plan + checkpoints + notas-trabajo-grock
 → X-RAY (20 puntos: método, pipeline, bitácora/notas, commits, gaps, alcance, protegidos, evidencia)
 → ANOTAR tarea en checkpoint índice
 → LOTE de salidas
 → LOOP: ejecutar Si → WRITE → COMMIT → WAIT → READ-BACK → COMPARE
 → PASS → checkpoint → siguiente
 → GAP → diagnosticar → hasta 20 vías → resolver → verificar → no stop
 → segunda pasada
 → X-Ray final cruzado (plan ↔ GitHub ↔ checkpoints)
 → 100% solo si DoD
```

GAP no bloquea salidas independientes. Espera GitHub: trabajar otra salida, no idle + no PASS prematuro.

Sandbox ≠ DONE. DONE = publicado + read-back + forense cuando hay code.

---

# PARTE V — FORMULARIO VACÍO (copiar a PIPELINE/PLAN_<ID>.md)

```markdown
# README PLAN {{NOMBRE}} — PLAN EJECUTABLE COMPLETO

**Repo:** maxbry123-commits/agentes · **rama:** main
**PLAN_ID:** {{ID}}
**Agente ejecutor:** {{GPT|Grok}}
**GitHub = única verdad.** 1 tarea = 1 salida. FAIL-CLOSED.
**Molde:** PIPELINE/PLAN_MODELO_UNIVERSAL.md
**Modelo de secciones:** PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md

## INPUT BLOCK
TAREA:
OBJETIVO:
FUENTE:
DESTINOS:
ALCANCE:
FUERA:
PASS:
N_DESPLEGAR:

## CABLEADO
Plan {{ID}} → Desplegar/Desplegar {{N}}/ → Refactoria/refactoria-plan-{{ID}}/

## ESTADO AUDITADO
| Salida | Estado | Checkpoint | Nota |
| S1 | QUEUED | PIPELINE/checkpoints/{{ID}}/S1.md | |

## SISTEMA REFACTORIA
Refactoria/refactoria-plan-{{ID}}/source/
Refactoria/refactoria-plan-{{ID}}/new/
Verificación ×3. No editar origen. No inventar body.

## SCHEMA S1
(id, objetivo, inputs, outputs, desplegar, refactoria, destino, dependencias, pass, estado, checkpoint)

## FUENTES CANÓNICAS
1.
2.

## REGLAS GLOBALES
PROHIBIDO / OBLIGATORIO
LEGO:

## TOTAL DE SALIDAS = {{K}}

## GAPS
| ID | Gap | Destino | Estado |

## DEPLOYMENT
remote_apply / readback: NOT_CLAIMED

## HOT PATH
extensions/wordflow/engine/code_path_runner.py

## GUÍAS USADAS
(links PARTE VI que apliquen)

## DEFINITION OF DONE
- checkpoints PASS o BLOCKER con causa
- hot path intacto salvo autorización
- cableado verificado
- read-back de cada path
- 0 fake PASS

## BLOCKER
Refactoria/refactoria-plan-{{ID}}/BLOCKER.md
```

---

# PARTE VI — GUÍAS (cómo se copia, ZIP, destinos, plugin)

No reescribir estas guías. Leerlas. Si falta en `agentes` y existe en Grupo-Trabajo-1: **copiar archivo** a `Método de trabajo/` (read→write→verify), no resumir de memoria.

## En este repo (agentes)

| Tema | Path |
|---|---|
| Plan modelo (secciones) | https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md |
| Método raíz | https://github.com/maxbry123-commits/agentes/blob/main/README_METHOD.md |
| Plugin / cableado | https://github.com/maxbry123-commits/agentes/blob/main/M%C3%A9todo%20de%20trabajo/GUIA_REGISTRO_PLUGINS_Y_CABLEADO.md |
| ZIP | https://github.com/maxbry123-commits/agentes/blob/main/GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md |
| ZIP determinista | https://github.com/maxbry123-commits/agentes/blob/main/METODO_ZIP_COPY_DETERMINISTA.md |
| Cuentas remote | https://github.com/maxbry123-commits/agentes/blob/main/GUIA_CUENTAS_REMOTE.md |
| Cuenta B | https://github.com/maxbry123-commits/agentes/blob/main/GUIA_CUENTA_B_REMOTE.md |
| COPY/MOVE/REUSE | https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/56_METODO_COPY_MOVE_REUSE_INDEX.md |
| PATCH git | https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/59_PATCH_GIT_01.md |
| Transfer repos | https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/58_CROSS_REPOSITORY_TRANSFER.md |
| Extract MD→code | https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/57_MARKDOWN_TO_CODE_EXTRACTION.md |
| REUSE-FIRST | https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/60_REUSE_FIRST.md |
| Método + arquitectura | https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md |
| Apply/push | https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/08_DESPLIEGUE_APPLY_PUSH.md |
| Yaiwes README | https://github.com/maxbry123-commits/agentes/blob/main/Yaiwes%20wordflow/Readme/README.md |
| Wordflow Code README | https://github.com/maxbry123-commits/agentes/blob/main/Wordflow%20Code/Readme/README.md |
| Desplegar | https://github.com/maxbry123-commits/agentes/blob/main/Desplegar/README.md |
| Refactoria | https://github.com/maxbry123-commits/agentes/blob/main/Refactoria/README.md |

## Grupo-Trabajo-1 (investigado 2026-08-26 — copiar lo que no esté en método agentes)

| Tema | Path |
|---|---|
| Método completo (INPUT BLOCK, X-Ray 20, NO-STOP, GAP×20, 5 copias, borrar duplicado, ZIP DAG, sandbox→GitHub→forense) | https://github.com/maxbry123-commits/Grupo-Trabajo-1/blob/main/METODO-DE-TRABAJO.md |
| Destinos + copia V1.1 | https://github.com/maxbry123-commits/Grupo-Trabajo-1/blob/main/GITHUB-ESTRUCTURA-DESTINOS-Y-COPIA-V1.1.md |
| Tarea GitHub final (autoridad, ficha repo, DAG G0–G12, X-Ray 14, fail-closed) | https://github.com/maxbry123-commits/Grupo-Trabajo-1/blob/main/TAREAS-EN-CURSO-HUGGINGFACE/TAREA-GITHUB-FINAL-V1.1.md |
| ZIP universal (copia allá) | https://github.com/maxbry123-commits/Grupo-Trabajo-1/blob/main/GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md |
| PIPELINE HF (ejemplo de PIPELINE vivo aditivo; no copiar contenido HF a agentes) | https://github.com/maxbry123-commits/Grupo-Trabajo-1/blob/main/PIPELINE-HUGGINGFACE.md |
| Pipeline.1.x | https://github.com/maxbry123-commits/Grupo-Trabajo-1/tree/main/Pipeline/pipeline1 |

### Destinos de cuenta (de esa guía — no mezclar software en main de agentes)

| Función | Repo |
|---|---|
| Wordflow / método base | maxbry123-commits/agentes |
| Planes / evidencia de otras líneas | maxbry123-commits/Grupo-Trabajo-1 |
| Router | maxbry123-commits/router-universal-router-inteligente- |
| Frontend | maxbry123-commits/frontend |
| Orquestador / auditor / memoria | maxbry123-commits/osquestador-auditor |

Un software = una raíz. agentes no es cajón de componentes nuevos.

### 5 vías de copia (obligatorio en cada plan que mueva archivos)

1. Contents API — 1 archivo: GET → PUT → verify SHA  
2. Git Data API — lote: blob → tree → commit → ref, sin force  
3. Actions — repetible  
4. Transfer/fork — repo entero no un path  
5. Clone+push — runner con git  

ZIP entregado: hash → extract staging → inventario → copy → 4 pasadas → commit → read-back. Extraer ≠ vaciar ZIP.

### Borrar duplicado

Canónico se queda. DELETE solo duplicado → 404 → canónico sigue. Si no sabes cuál es canónico: HOLD.

### Plugin / Microkernel

Texto citable:

> El sistema sigue el patrón de Microkernel Architecture (también conocido como Plugin Architecture): un núcleo mínimo (`kernel-principal`) que expone puntos de extensión y un registro de plugins, permitiendo añadir capacidades nuevas sin modificar el núcleo. `wordflow/abi.py` (`ExtensionABI`) es la implementación concreta de ese punto de extensión en este repositorio.

Guía local: `Método de trabajo/GUIA_REGISTRO_PLUGINS_Y_CABLEADO.md`  
`extension-kernel` = un nodo ejemplo. No dump.

Docs: `Readme/` → `Readme1/` → `Readme2/`.  
Code: registry / adapter / cable. Refactoria si el componente mismo cambia.

---

# PARTE VII — RAÍCES VIVAS DE agentes/main (todo plan las respeta)

1. `Desplegar/` — inbox; `Desplegar N/` = lote del plan N  
2. `PIPELINE/` — plan vivo de misión + este molde + planes instanciados + checkpoints  
3. `Método de trabajo/` + `README_METHOD.md`  
4. `Refactoria/refactoria-plan-<ID>/`  
5. `Yaiwes wordflow/`  
6. `Wordflow Code/`  
7. `notas-trabajo-grock/` — estado Grok, no Wordflow  

`.github/workflows/` excepción Actions.

---

# PARTE VIII — DEFINITION OF DONE DE UN PLAN (el documento)

El *documento plan* está listo para ejecutar cuando:

- tiene INPUT BLOCK literal;
- tiene las secciones del modelo YAIWES;
- cada salida tiene schema + checkpoint path;
- cableado Desplegar N + Refactoria de ESE plan;
- fuentes son paths reales;
- gaps tienen destino o BLOCKER;
- hot path nombrado;
- guías enlazadas;
- el archivo existe en GitHub (read-back).

La *misión* está DONE cuando cada salida tiene checkpoint PASS o BLOCKER explícito y el X-Ray final cruza plan ↔ GitHub.
