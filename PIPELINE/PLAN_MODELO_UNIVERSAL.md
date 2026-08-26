# PLAN MODELO UNIVERSAL — MOLDE DE TRABAJO

**Repo:** `maxbry123-commits/agentes` · **rama:** `main`  
**Qué es:** molde. Copia este archivo a `PIPELINE/PLAN_<ID>.md`. Rellena los campos `{{ }}`. No reescribas este molde; mejora = parche `PIPELINE/PLAN_MODELO_UNIVERSAL/Readme1.md`.
**Origen del molde:** copia de estructura de `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md` con tareas de esa misión vaciadas.
**GitHub = única verdad.** 1 tarea = 1 salida. PASS solo con evidencia. FAIL-CLOSED.

---

## 0. IDENTIDAD DEL PLAN (rellenar)

| Campo | Valor |
|---|---|
| PLAN_ID | `{{PLAN_ID}}` ejemplo `X-2` |
| Título | `{{TITULO}}` |
| Agente ejecutor | `{{GPT\|Grok\|otro}}` |
| Estado | `{{QUEUED\|RUNNING\|PASS\|OPEN\|BLOCKED}}` |

### Cableado obligatorio (N = número de ESTE plan, no fijo)

```text
Plan {{PLAN_ID}}
    → Desplegar/Desplegar {{N}}/                  inbox lote de este plan
    → Refactoria/refactoria-plan-{{PLAN_ID}}/     versiones VIEJAS a modificar
         source/   copia exacta origen
         new/      versión nueva
    → raíz destino canónica                      Yaiwes wordflow  |  Wordflow Code
    → PIPELINE/PLAN_{{PLAN_ID}}.md                este plan instanciado
    → PIPELINE/checkpoints/{{PLAN_ID}}/           cierre 100% por tarea
```

`Desplegar 1` es solo ejemplo de N=1. Cada plan nuevo usa su N.

### Schema de cada nodo / salida

```yaml
id: S{{n}}
objetivo: ""
inputs: []
outputs: []
desplegar: Desplegar/Desplegar {{N}}/
refactoria: Refactoria/refactoria-plan-{{PLAN_ID}}/
destino_canonico: ""
dependencias: []
pass: "evidencia GitHub: path + commit + read-back"
estado: QUEUED
checkpoint: PIPELINE/checkpoints/{{PLAN_ID}}/S{{n}}.md
```

### Checkpoint 100% (Grok y GPT escriben aquí, no en el plan base)

`PIPELINE/checkpoints/{{PLAN_ID}}/S{{n}}.md`

```text
PLAN_ID:
SALIDA:
PATHS:
COMMIT:
READBACK: PASS|FAIL
GAPS:
STATUS: PASS|FAIL|OPEN|BLOCKED
```

El plan base no se reescribe para anotar cierre. Se escribe el checkpoint.

---

## ESTADO AUDITADO

| Salida | Estado | Checkpoint | Nota |
|---|---|---|---|
| S1 | {{ }} | checkpoints/{{PLAN_ID}}/S1.md | |
| S2 | {{ }} | checkpoints/{{PLAN_ID}}/S2.md | |
| SN | {{ }} | checkpoints/{{PLAN_ID}}/SN.md | |

Gap técnico OPEN→CLOSED solo con evidencia real en `main`.

---

## SISTEMA REFACTORIA — OBLIGATORIO

### Paso 1 — Aislar (copiar, no editar in-place)

```text
Refactoria/refactoria-plan-{{PLAN_ID}}/source/
```

Nunca modificar primero el original en `Yaiwes wordflow/`, `Wordflow Code/`, `extensions/wordflow/` o destinos canónicos.

### Paso 2 — Implementar en LOOP

```text
Refactoria/refactoria-plan-{{PLAN_ID}}/new/
```

Usar `source/` como referencia. Bucle hasta acceptance (contratos, tests, sin pérdida de API pública).

### Paso 3 — Verificación cruzada ×3

1. Diff source/ vs new/
2. Tests contra new/
3. Checklist + evidencia + checkpoint

Solo si las 3 PASS: integrar `new/` al path canónico.  
Borrar original solo con autorización Director + 3 verificaciones.  
Nunca borrar `source/` en el mismo task.

### Prohibido

- Editar hot path sin paridad de tests
- PASS sin las 3 verificaciones
- Inventar body/adapters/schemas para cerrar gaps
- Reescribir archivo base (docs o code): parche + enlace + Plugin Registry

---

## EXTENSIÓN / PLUGIN (no tocar base)

El sistema sigue el patrón de **Microkernel Architecture** (también conocido como Plugin Architecture): un núcleo mínimo (`kernel-principal`) que expone puntos de extensión y un registro de plugins, permitiendo añadir capacidades nuevas sin modificar el núcleo. `wordflow/abi.py` (`ExtensionABI`) es la implementación concreta de ese punto de extensión en este repositorio.

`extension-kernel` es un nodo ejemplo. No es destino de todo archivo nuevo.

Docs: `.../Readme/` → `Readme1/` → `Readme2/`.  
Code: fila nueva en Plugin Registry. No reeditar `workflow.py` / runner.

---

## 1. FUENTES CANÓNICAS (rellenar + estas siempre)

Siempre:

1. Este molde `PIPELINE/PLAN_MODELO_UNIVERSAL.md`
2. El plan instanciado `PIPELINE/PLAN_{{PLAN_ID}}.md`
3. `Desplegar/Desplegar {{N}}/` (lote de este plan; si aún no subieron archivos, estado WAIT no inventar)
4. README `Yaiwes wordflow/Readme/README.md`
5. README `Wordflow Code/Readme/README.md`
6. `Método de trabajo/` + `README_METHOD.md`
7. `notas-trabajo-grock/` (estado Grok)

Misión específica: listar ORIGIN_MAP / PASO3 / docs del lote N.

---

## 2. REGLAS GLOBALES

```text
PROHIBIDO: inventar; reescribir code_path_runner sin paridad; duplicar lego;
PASS sin checkpoint; afirmar remote apply sin evidencia; hardcodear Desplegar 1;
tirar todo a extension-kernel; reescribir este molde o el plan base para anotar cierre.
OBLIGATORIO: schema por nodo; checkpoint; COPY-FIRST; Refactoria en cambios;
INPUT BLOCK literal; X-Ray antes de borrar; read-back GitHub; FAIL-CLOSED.
```

### Regla LEGO (autoridad única — no duplicar módulo)

| Módulo | Autoridad |
|---|---|
| {{modulo}} | {{path canónico}} |

---

## 3. TOTAL DE SALIDAS = {{K}}

Cada salida = una fila de schema §0 + un checkpoint.

---

## 4. GAPS

| ID | Gap | Destino canónico | Estado |
|---|---|---|---|
| G{{n}} | {{ }} | {{path}} | OPEN\|CLOSED\|BLOCKED |

Sin source → BLOCKER, no inventar implementación.

---

## 5. DEPLOYMENT

remote_apply / readback: `{{NOT_CLAIMED\|PASS\|FAIL}}`  
No afirmar apply remoto sin read-back.

---

## 6. HOT PATH

`extensions/wordflow/engine/code_path_runner.py` — operativo. No mover/apagar sin tests + Director.
Raíz autorizada nombre: `Wordflow Code/`. Cuerpo actual: `extensions/wordflow/`.

---

## 7. CÓMO SE TRABAJA (enlaces — no reescribir las guías)

### Copiar archivo (5 vías)

Fuente: `Método de trabajo/` y `README_METHOD.md` + Grupo-Trabajo-1 `METODO-DE-TRABAJO.md`  
https://github.com/maxbry123-commits/Grupo-Trabajo-1/blob/main/METODO-DE-TRABAJO.md

1. Contents API (1 archivo): GET origen → PUT destino → verify SHA  
2. Git Data API (lote): blob → tree → commit → ref, sin force  
3. Actions Cuenta A → token destino  
4. Transfer/fork solo repo entero  
5. Clone local + push (humano/CI)

Contrato: read → write → verify. Idempotente si destino ya igual.

### ZIP → raíz

- https://github.com/maxbry123-commits/agentes/blob/main/GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md
- https://github.com/maxbry123-commits/agentes/blob/main/METODO_ZIP_COPY_DETERMINISTA.md
- https://github.com/maxbry123-commits/Grupo-Trabajo-1/blob/main/GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md

`ZIP → binario → extraer staging → inventario → raíz → 4 pasadas → commit → read-back`  
Extraer ≠ vaciar ZIP. Extraer ≠ borrar ZIP.

### Borrar duplicado

Canónico se queda. DELETE solo el path duplicado + verify 404 + canónico sigue. Si no sabes cuál es canónico: no borrar.

### Cuentas remote

- https://github.com/maxbry123-commits/agentes/blob/main/GUIA_CUENTAS_REMOTE.md
- https://github.com/maxbry123-commits/agentes/blob/main/GUIA_CUENTA_B_REMOTE.md

### LOOP / X-Ray / NO-STOP

INPUT BLOCK → leer método + plan + bitácora/notas → X-Ray → lotes → ejecutar → verify → GAP×20 → checkpoint → siguiente.  
No stop por GAP. No PASS por HTTP 200. WRITE → WAIT → READ-BACK → COMPARE.

Referencia de PIPELINE vivo (no copiar contenido HF):  
https://github.com/maxbry123-commits/Grupo-Trabajo-1/blob/main/PIPELINE-HUGGINGFACE.md

### Estructura destinos / copia

https://github.com/maxbry123-commits/Grupo-Trabajo-1/blob/main/GITHUB-ESTRUCTURA-DESTINOS-Y-COPIA-V1.1.md

---

## 8. DEFINITION OF DONE

- Todas las salidas con checkpoint PASS o BLOCKER con causa
- Hot path intacto salvo autorización
- Cableado Plan ↔ Desplegar N ↔ Refactoria de este plan
- Ningún archivo base reescrito para “anotar”
- Read-back GitHub de cada path tocado
- 0 fake PASS

## 9. BLOCKER

`Refactoria/refactoria-plan-{{PLAN_ID}}/BLOCKER.md`  
problem / source / impact / recommended_action. No sustituir BLOCKER por code inventado.

## 10. CRECIMIENTO

OSS → ACQUIRE → ANALYZE gap → REUSE/PATCH/ADAPT → ficha v2 + enchufe → catalog → registry.  
No clonar agentes enteros. No escribir de cero lo reciclable.
