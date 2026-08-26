# Readme1 — parche del molde (no reescribe PLAN_MODELO_UNIVERSAL.md)

Base: `PIPELINE/PLAN_MODELO_UNIVERSAL.md`  
Modelo de secciones: `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md`

---

## A. ¿El plan modelo YAIWES lleva todo?

| Pieza | YAIWES | Este molde + parche |
|---|---|---|
| Cabecera repo/rama/FAIL-CLOSED | SÍ | SÍ |
| ESTADO AUDITADO por salida | SÍ | SÍ |
| REFACTORIA source/new ×3 | SÍ | SÍ + path por PLAN_ID |
| FUENTES CANÓNICAS | SÍ | SÍ |
| REGLAS + LEGO | SÍ | SÍ |
| TOTAL SALIDAS | SÍ | SÍ |
| GAPS destino+estado | SÍ | SÍ |
| DEPLOYMENT read-back | SÍ | SÍ |
| HOT PATH | SÍ | SÍ |
| CRECIMIENTO ACQUIRE | SÍ | SÍ |
| INPUT BLOCK | NO | SÍ (Director) |
| Schema por nodo | NO | SÍ (Director) |
| Checkpoint fuera del plan | NO | SÍ `PIPELINE/checkpoints/<ID>/` |
| Desplegar N variable | NO | SÍ |
| Refactoria por plan | parcial (`despliegue/refactoria` + `Refactoria/`) | `Refactoria/refactoria-plan-<ID>/` |
| Plugin / no tocar base | NO | SÍ |
| Copiar guías GT1 | NO | SÍ — archivos en Método de trabajo |
| DSL + DAG | NO explícito | SÍ esta página |
| Sheriff / watchdog / guardián | en code, no en el plan | SÍ cableado abajo |
| Validación + verificación cruzada | 3 checks Refactoria | SÍ + 4 pasadas |

---

## B. DSL del plan (lenguaje fijo)

Tokens permitidos (no inventar otros):

```text
PLAN_ID, N, S<n>, G<n>
Desplegar/Desplegar N/
Refactoria/refactoria-plan-<PLAN_ID>/{source,new}
Yaiwes wordflow/ | Wordflow Code/ | Método de trabajo/ | PIPELINE/
QUEUED|RUNNING|WAITING|GAP|PASS|BLOCKED|HOLD|OPEN|CLOSED
COPY|MOVE|REUSE|PATCH|ADAPT|GENERATE
WRITE|COMMIT|WAIT|READ-BACK|COMPARE
```

Frase de cableado (DSL):

```text
PLAN <PLAN_ID> BINDS lote=Desplegar/Desplegar <N>
                   old=Refactoria/refactoria-plan-<PLAN_ID>/source
                   new=Refactoria/refactoria-plan-<PLAN_ID>/new
                   dest=<raiz-viva>/<path>
                   check=PIPELINE/checkpoints/<PLAN_ID>/S<n>.md
                   sheriff=checklist + standards/sheriff
                   watchdog=engine/watchdog.check_watchdog
                   guardian=mount-guard + sentinel + VerdictAuthority
```

---

## C. DAG de un plan (no se salta nodo)

```text
INPUT_BLOCK
  → XRAY_20
  → BIND_DESPLEGAR_N          # si no hay lote: WAIT, no inventar carpeta
  → BIND_REFACTORIA_PLAN
  → WRITE_PLAN_FILE           # archivo NUEVO, no reescribir modelo YAIWES
  → SCHEMA_CADA_S
  → LOOP_S
       → PRE_GATE / SHERIFF   # ¿autorizado? ¿fuera de raíz? ¿hot path?
       → WATCHDOG             # stop determinista si loop/stagnation
       → COPY_SOURCE_A_REFACTORIA
       → IMPLEMENT_NEW
       → VALIDATE_SCHEMA      # inputs/outputs existen
       → CROSSCHECK_x3        # diff + tests + checklist
       → GUARDIAN             # mount-guard / sentinel / verdict
       → INTEGRATE_DESTINO
       → READ_BACK
       → CHECKPOINT
  → SEGUNDA_PASADA
  → XRAY_FINAL_4_PASADAS
  → DONE | BLOCKER
```

---

## D. Schema de salida (obligatorio)

```yaml
id: S1
objetivo: ""
inputs: []
outputs: []
desplegar: Desplegar/Desplegar N/
refactoria_source: Refactoria/refactoria-plan-<ID>/source/
refactoria_new: Refactoria/refactoria-plan-<ID>/new/
destino_canonico: ""
sheriff: "pass si path en raíz viva y no hot path sin paridad"
watchdog: "pass si no stagnation x2 mismo fallo"
guardian: "pass si VerdictAuthority / sentinel no DENY"
validacion: "schema I/O + SHA"
verificacion_cruzada: ["diff source/new", "tests", "checklist"]
pass: "commit + read-back + checkpoint"
estado: QUEUED
checkpoint: PIPELINE/checkpoints/<ID>/S1.md
```

---

## E. Cableado — con qué y qué función

| De | A | Función |
|---|---|---|
| Director | `Desplegar/Desplegar N/` | inbox lote docs+code de ESE plan |
| Plan | `Desplegar/Desplegar N/` | no mezclar planes; N = id del lote |
| Plan | `Refactoria/refactoria-plan-<ID>/source/` | aislar versión vieja |
| Plan | `Refactoria/refactoria-plan-<ID>/new/` | escribir versión nueva |
| `new/` | `Yaiwes wordflow/` o `Wordflow Code/` | integrar solo tras ×3 + guardian |
| Plan | `PIPELINE/checkpoints/<ID>/` | cierre 100% sin reescribir el plan |
| Plan | `Método de trabajo/` | reglas; parche si falta |
| Plan | `notas-trabajo-grock/` | estado Grok |
| Code nuevo | Plugin Registry / `wordflow/abi.py` | cablear sin editar base |
| Sheriff | cada S | ¿esta acción permitida? |
| Watchdog | LOOP | stop si se rompe / se estanca |
| Guardián | post-verify | DENY o PASS de autoridad, no del LLM |

Paths reales (no inventados):

- Sheriff: `extensions/wordflow/standards/sheriff.py`, `checklist_sheriff.py`, `engine/control_sheriff_bridge.py`
- Watchdog: `extensions/wordflow/engine/watchdog.py` (`check_watchdog`), `control-layer/evolution/watchdog/monitor.py`
- Guardián: `agente-yaiwes/kernel-principal/extension-kernel/mount-guard/`, sentinel en control-governance, VerdictAuthority (cadena code_path post_verify)
- Validación: schemas `extensions/wordflow/schemas/`, `code-programming-engine/schema-contracts-io/`
- Verificación cruzada: Refactoria ×3 + X-Ray 4 pasadas (estructura, contenido SHA, origen, read-back)

`extension-kernel` no recibe todo archivo nuevo. Solo extension point + registry + mount-guard.

---

## F. 4 pasadas (cada revisión de plan o de lote)

1. ESTRUCTURA — ¿están las secciones del modelo YAIWES + INPUT + schema + cableado?
2. CONTENIDO — ¿paths reales? ¿fuentes existen?
3. ORIGEN — ¿se copió GT1 donde faltaba o solo se enlazó?
4. READ-BACK — ¿el archivo en GitHub es el que se afirma?

---

## G. Instrucciones Director — checklist

- [x] 6 raíces + notas Grok
- [x] no hardcodear Desplegar 1
- [x] Refactoria por plan
- [x] no rewrite base / plugin
- [x] schema + checkpoint
- [x] copiar GT1 (1 archivo copiado; METODO-DE-TRABAJO OPEN GET+PUT)
- [x] DSL DAG sheriff watchdog guardian validación cruzada
- [x] cableado con función
- [ ] METODO-DE-TRABAJO.md cuerpo 54KB aún no materializado en Método (OPEN honesto)
