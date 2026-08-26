# PLAN S2 DEPURACIÓN MAIN — INSTANCIA DEL MOLDE

**Molde:** `PIPELINE/PLAN_MODELO_UNIVERSAL.md`  
**Repo:** `maxbry123-commits/agentes` · **rama:** `main`  
**PLAN_ID:** `S2`  
**Título:** Depurar main a raíces vivas  
**Agente ejecutor:** GPT  
**Grok:** solo autor del plan. No ejecuta borrados.  
**GitHub = única verdad.** 1 tarea = 1 salida. PASS solo con evidencia. FAIL-CLOSED.

No reescribir este plan para anotar cierre. Checkpoint: `PIPELINE/checkpoints/S2/`.

---

## 0. IDENTIDAD / CABLEADO

| Campo | Valor |
|---|---|
| PLAN_ID | S2 |
| N Desplegar | N de este plan cuando el Director suba lote. Si no hay lote, no inventar `Desplegar 1/`. |
| Refactoria | `Refactoria/refactoria-plan-S2/` |
| Destinos | `Yaiwes wordflow/` · `Wordflow Code/` · `Método de trabajo/` · `Desplegar/` |

```text
Plan S2
    → Desplegar/Desplegar N/                 solo si existe lote real
    → Refactoria/refactoria-plan-S2/source/  archivos a mover/clasificar
    → Refactoria/refactoria-plan-S2/new/
    → raíz viva destino
    → PIPELINE/checkpoints/S2/
```

### Schema nodos

```yaml
- id: S2-A
  objetivo: inventario X-Ray main
  inputs: [tree main, ORIGIN_MAP, PASO3, PLAN_YAIWES, NOTAS-1, NOTAS-2, molde]
  outputs: [PIPELINE/checkpoints/S2/S2-A.md tabla VIVO/HOLD/MOVE/BASURA/GAP]
  destino_canonico: PIPELINE/checkpoints/S2/
  dependencias: []
  pass: cada path de main clasificado; 0 path sin etiqueta
  estado: QUEUED
- id: S2-B
  objetivo: mover guías sueltas a Método de trabajo
  inputs: [GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md, GUIA_CUENTAS_REMOTE.md, GUIA_CUENTA_B_REMOTE.md, METODO_ZIP_COPY_DETERMINISTA.md, README_FORENSIC_HANDOFF.md]
  outputs: [Método de trabajo/<mismo nombre>]
  refactoria: Refactoria/refactoria-plan-S2/
  pass: SHA origen=destino + origen 404 + checkpoint
  estado: QUEUED
- id: S2-C
  objetivo: mover docs canónicos citados por el plan vivo (no borrar el plan vivo)
  inputs: [PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md, PIPELINE/Agente_YAIWES_v.1_en_PRODUCCION.md, PIPELINE/ARQUITECTURA_03_WORDFLOW.md]
  outputs: [Yaiwes wordflow/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md, Yaiwes wordflow/Agente_YAIWES_v.1_en_PRODUCCION.md, Wordflow Code/ARQUITECTURA_03_WORDFLOW.md]
  pass: SHA + read-back; PLAN_YAIWES intacto
  estado: QUEUED
- id: S2-D
  objetivo: cutover agente-yaiwes/ → Yaiwes wordflow/
  inputs: [agente-yaiwes/**]
  outputs: [Yaiwes wordflow/** mismo árbol]
  pass: conteo + sample SHA ×3; parche Readme1 SOURCE; borrar origen solo si 3 PASS
  estado: QUEUED
- id: S2-E
  objetivo: HOLD hot path
  inputs: [extensions/wordflow/engine/code_path_runner.py]
  outputs: [checkpoint HOLD explícito]
  pass: path original existe; no move; tests no rotos por este lote
  estado: QUEUED
- id: S2-F
  objetivo: borrar solo BASURA del inventario S2-A
  inputs: [tabla S2-A etiqueta BASURA]
  outputs: [404 de esos paths]
  pass: canónicos siguen; extras no clasificados = GAP no borrar
  estado: QUEUED
- id: S2-G
  objetivo: X-Ray final
  inputs: [tree main post F]
  outputs: [PIPELINE/checkpoints/S2/S2-G.md]
  pass: main = VIVO+HOLD+excepciones; 0 missing canónico
  estado: QUEUED
```

---

## ESTADO AUDITADO

| Salida | Estado | Checkpoint |
|---|---|---|
| S2-A | QUEUED | PIPELINE/checkpoints/S2/S2-A.md |
| S2-B | QUEUED | PIPELINE/checkpoints/S2/S2-B.md |
| S2-C | QUEUED | PIPELINE/checkpoints/S2/S2-C.md |
| S2-D | QUEUED | PIPELINE/checkpoints/S2/S2-D.md |
| S2-E | QUEUED | PIPELINE/checkpoints/S2/S2-E.md |
| S2-F | QUEUED | PIPELINE/checkpoints/S2/S2-F.md |
| S2-G | QUEUED | PIPELINE/checkpoints/S2/S2-G.md |

---

## SISTEMA REFACTORIA

```text
Refactoria/refactoria-plan-S2/source/
Refactoria/refactoria-plan-S2/new/
```

3 verificaciones antes de integrar o borrar. source/ no se borra en el mismo task.

---

## EXTENSIÓN / PLUGIN

No reescribir README base de las raíces. Cutover SOURCE = `Yaiwes wordflow/Readme/Readme1/`.  
Microkernel: no dump a `extension-kernel`.

---

## 1. FUENTES CANÓNICAS

1. `PIPELINE/PLAN_MODELO_UNIVERSAL.md`
2. Este plan
3. `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md` (no tocar)
4. `Yaiwes wordflow/Readme/README.md`
5. `Wordflow Code/Readme/README.md`
6. `Desplegar/README.md`
7. `notas-trabajo-grock/NOTAS-1.md` + `NOTAS-2.md`
8. `agente-yaiwes/ORIGIN_MAP.md` + `COPY_MANIFEST.json` + `PLAN_100_ESTRUCTURA_DEFINITIVA.md`
9. `PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md`

---

## 2. REGLAS GLOBALES

```text
PROHIBIDO: inventar; mover/editar code_path_runner; fake PASS; borrar si duda;
hardcodear Desplegar 1; force-push; reescribir PLAN_YAIWES; reescribir este plan para cierre.
OBLIGATORIO: S2-A antes de borrar; COPY-FIRST; SHA+read-back; HOLD si ORIGIN_MAP/PASO3 REF.
```

---

## 3. TOTAL DE SALIDAS = 7 (S2-A … S2-G)

---

## 4. GAPS / HOLD / BASURA (semilla — S2-A confirma)

### VIVO

`Desplegar/` · `Yaiwes wordflow/` · `Wordflow Code/` · `Refactoria/` · `Método de trabajo/` · `README_METHOD.md` · `notas-trabajo-grock/` · `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md` · `PIPELINE/PLAN_MODELO_UNIVERSAL.md` · este plan · `PIPELINE/checkpoints/`

### HOLD

| Path | Por qué |
|---|---|
| `extensions/wordflow/**` | hot path |
| `extensions/wordflow_kernel/**` | gateway |
| `wordflow/abi.py` | extension point |
| `code-programming-engine/**` | espejo C-19 |
| `Refactoria/G1`…`G7` | misión YAIWES |
| `despliegue/INSTRUCCIONES_GROK_OPCION_A.md` | fuente plan vivo |
| `.github/workflows/` | Actions |
| `agente-yaiwes/**` | hasta S2-D PASS |

### MOVE (no borrar hasta verify)

Guías raíz → `Método de trabajo/`  
3 docs PIPELINE §S2-C  
`agente-yaiwes/` → `Yaiwes wordflow/`

### BASURA candidata (solo si S2-A no la pasa a HOLD)

`.cursor/` `TASK-GAPS/` `agents/` `control-layer/` `docs/` `groups/` `memory/` `scripts/` `tools/`  
`extensions/{adapters,audit_forensic,github_deploy,github_publisher,knowledge,maxbry_loop,project_bootstrap,source_evolution}/`  
`PIPELINE/*` histórico excepto VIVO/MOVE  
`AGENTS.md` `README_ARQUITECTURA.md` `RENAME_NOTE.md` `SETUP_TOKEN_MOVIL.md`  
`despliegue/**` resto tras clasificar ≠ `Desplegar/`

---

## 5. DEPLOYMENT

remote_apply / readback: NOT_CLAIMED hasta S2-G.

---

## 6. HOT PATH

`extensions/wordflow/engine/code_path_runner.py` — S2-E HOLD. No move.

---

## 7. GUÍAS (cómo copiar / ZIP / borrar)

Igual que molde §7. Read → write → verify. ZIP no aplica salvo que aparezca lote en Desplegar N.

---

## 8. DEFINITION OF DONE

- S2-A…G con checkpoint PASS o BLOCKER con causa
- PLAN_YAIWES intacto
- hot path en el mismo path
- 6 raíces + notas + molde + este plan vivos
- `agente-yaiwes/` ausente solo si S2-D ×3 PASS; si no OPEN
- BASURA S2-A en 404
- 0 fake PASS

## 9. BLOCKER

`Refactoria/refactoria-plan-S2/BLOCKER.md`  
problem / source / impact / action. No code inventado.

## 10. CRECIMIENTO

No aplica a depuración. No clonar repos para “limpiar”.
