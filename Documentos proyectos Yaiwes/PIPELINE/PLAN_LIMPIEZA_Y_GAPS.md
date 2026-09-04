# PLAN_LIMPIEZA_Y_GAPS — GPT ejecuta esto

X-Ray raíz main 2026-08-26. Molde usado por Grok. Docs de Guia-plan NO se editan.
FAIL-CLOSED. LLM no declara PASS. HTTP 200 ≠ PASS. Cero borrados sin SI del Director.

## INPUT BLOCK
```text
PLAN_ID: LIMPIEZA_GAPS
AGENTE: GPT
TAREA: Gaps G1-G7 con evidencia; inventario basura; borrar solo líneas SI
N_DESPLEGAR: WAIT
HOT_PATH_SE_TOCA: NO
FUERA: editar Guia-plan; fabricar p01-p12; crear G1_G3_CI_PASS.md a mano; force-push; tocar hot path
```

ENLACE_DESPLEGAR: WAIT
ENLACE_REFACTORIA: Refactoria/refactoria-plan-LIMPIEZA_GAPS/
ENLACE_CHECKPOINT: PIPELINE/checkpoints/LIMPIEZA_GAPS/

---

## NO TOCAR (prohibido borrar, mover, reescribir)

### Docs que subió el Director
- PIPELINE/Guia-plan/MOLDE_MAESTRO_UNIVERSAL_v2.md
- PIPELINE/Guia-plan/MOLDE_MAESTRO_UNIVERSAL_v2_PARCHE_1.md
- PIPELINE/Guia-plan/MOLDE_MAESTRO_UNIVERSAL_v2_PARCHE_1-1.md
- PIPELINE/Guia-plan/DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2.md
- PIPELINE/Guia-plan/PROMPT_MAESTRO_CHAT_A_CHAT_B_VERSION_MADURA.md
- PIPELINE/Guia-plan/UOOS_v2_ PARTE 1 ... AUTORUN-1.md
- PIPELINE/Guia-plan/UOOS_PARTE2_v3_ ... RUNTIME.md

### Planes y misión
- PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md
- PIPELINE/PLAN_LIMPIEZA_Y_GAPS.md
- PIPELINE/planes/PLAN_01.md … PLAN_05.md
- PIPELINE/Guia-plan/plugins-extension/
- PIPELINE/Guia-plan/Readme/

### Raíces / hot path
- Desplegar/
- Refactoria/
- Método de trabajo/
- Yaiwes wordflow/
- Wordflow Code/
- extensions/wordflow/   ← hot path code_path_runner.py VIVE AQUÍ
- .github/workflows/verify-gap-indexes.yml
- .github/workflows/  (no borrar workflows)

`despliegue/` ≠ `Desplegar/`. No borrar `despliegue/` en este plan (legado YAIWES / motor). Solo listar.

---

## X-RAY RAÍZ main (32 entradas)

### Canónico / vivo
Desplegar | PIPELINE | Método de trabajo | Refactoria | Yaiwes wordflow | Wordflow Code | extensions (hot path) | .github

### Candidatos a basura — SOLO LISTAR. Borrar = SI del Director
| Path | Por qué |
|---|---|
| agente-yaiwes/ | duplicado del wordflow Yaiwes |
| agents/ | extra |
| TASK-GAPS/ | extra |
| code-programming-engine/ | posible duplicado PASO3 |
| control-layer/ | extra |
| docs/ | extra |
| groups/ | extra |
| memory/ | extra |
| wordflow/ | posible duplicado de extensions/wordflow |
| scripts/ tools/ | extra salvo que Director marque NO |
| PIPELINE/00_* … 64_* y históricos | PIPELINE solo vivo: YAIWES + Guia-plan + planes + este plan |
| GUIA-*.md GUIA_*.md METODO_ZIP*.md README_*.md RENAME_NOTE SETUP_TOKEN AGENTS.md en raíz | no son raíz canónica |
| .cursor/ | extra |

### HOLD (no clasificar PASS ni borrar)
- despliegue/
- extensions/
- agente-yaiwes/ hasta que G1/G3 artifacts no dependan de esos paths (el workflow escribe en agente-yaiwes/...)

NOTA X-Ray: verify-gap-indexes.yml escribe en `agente-yaiwes/control-governance/...` y `agente-yaiwes/code-programming-engine/...`. Por eso agente-yaiwes es HOLD hasta cerrar G1/G3, no basura aún.

---

## S1 G1/G3 CI
Pedir Run: https://github.com/maxbry123-commits/agentes/actions/workflows/verify-gap-indexes.yml
PASS solo: run verde + URL + archivo escrito por Actions. No fabricar G1_G3_CI_PASS.md.

## S2 G4
Mismo run. Log/URL. Sin run = OPEN.

## S3 G2
PARCIAL + residual. No forzar PASS.

## S4 G5 G6 G7
G5 BLOCKER sin source p01-p12. No inventar. G6/G7 no reabrir si OpenClaw sigue.

## S5 Inventario
Tabla path | por qué | SI/NO Director. Cero deletes sin SI.
Checkpoint: PIPELINE/checkpoints/LIMPIEZA_GAPS/S5.md

## Ficha Sn
SALIDA / COMMIT / READBACK / URL / STATUS PASS|FAIL|OPEN|BLOCKED
