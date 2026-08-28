# MÉTODO DE TRABAJO — wordflow-code-deploy-router

Usar este bloque completo como prompt de arranque. No pegar valores de token (`ghp_...`) en ningún mensaje ni archivo — solo nombres de secreto. Seguir el skill `wordflow-code-deploy-router` para el detalle de cada PASO; este documento es el mapa corto para no perder el hilo entre pasos.

## DSL / DAG del pipeline

```
PREFLIGHT(leer contratos, token_ref only, no ghp_)
  -> ITEM3 DESTINO(diseñar repo GitHub -> montar Action -> extraer zip en la
                    misma raíz del zip -> auditar el mismo Action)
  -> P01 DOWNLOAD(Actions + py lock, GATE manifest 20 COMPLETE)
  -> P01b EXTRACT_AGRUPADO(unir partes del MISMO repo en UNA carpeta,
                    NUNCA una carpeta por ZIP -- X-Ray reconstruct)
  -> P02 BANDEJA(Download code/Download N)
        |-- OP1 PARTIAL copy selected -> Download N
        `-- OP2 FULL fork|new_root + CROSSCHECK SHA
  -> P03 EXTRACT(.staging) COPY+sha256 + PLUGIN I/O
        JSON|prompt -> .py EXTRACT_LITERAL
        rules|skill -> .yaml
  -> P04 ACTIONS_QUEUE(cp mapped src/config/scripts/tests; 1 commit 1 push)
  -> P05 STATE_NAME + atomic rewrite(temp,hash,validate,rename)
  -> P06 WORDFLOW_TAIL(code_path_runner -> evidence -> deploy)
  -> P07 STANDARDS load (no improve source)
  -> P08 ROUTER A|B|C (C HOLD)
  -> P09 OUT1 chat UOOS | OUT2 dest create_repo | OUT3 A root+evidence
  -> P10 XRAY then council12
GATE: EvidenceGate exit 0 else STOP
```

Regla de lectura: cada nodo del DAG tiene su tarjeta IN/DO/FORBID/GATE/OUT/NEXT completa en `SKILL.md`. Este documento solo enruta — no repite el detalle para no duplicar fuente de verdad.

Nota de auditoría: los nombres de skill `wordflow-paso-control`, `wordflow-paso-full` y `wordflow-paso-v3` quedan retirados — eran variantes divergentes del mismo pipeline generadas por regeneraciones inconsistentes. El nombre único y canónico es **`wordflow-code-deploy-router`**.

## Skills (canónicos — no confundir con nombres retirados)
- https://github.com/maxbry123-commits/agentes/tree/main/skills/wordflow-code-deploy-router
- https://github.com/maxbry123-commits/agentes/tree/main/skills/research-download-chain
- https://github.com/maxbry123-commits/agentes/blob/main/skills/research-download-chain/references/RESEARCH-DOWNLOAD-CHAIN-AI-PLAYBOOK.json
- https://github.com/maxbry123-commits/agentes/blob/main/skills/wordflow-code-deploy-router/references/METODO-DE-TRABAJO.md

## Download + ZIP
- https://github.com/maxbry123-commits/agentes/tree/main/Download%20code/archivos
- https://github.com/maxbry123-commits/agentes/tree/main/Download%20code/Download%201
- https://github.com/maxbry123-commits/agentes/tree/main/Download%20code/Download%202
- https://github.com/maxbry123-commits/agentes/tree/main/Download%20code/Download%203
- https://github.com/maxbry123-commits/agentes/blob/main/METODO_ZIP_COPY_DETERMINISTA.md
- https://github.com/maxbry123-commits/agentes/blob/main/GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md
- https://github.com/maxbry123-commits/TAREA-1/blob/main/GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md
- https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/main/GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md
- https://github.com/maxbry123-commits/agentes/actions/runs/33134420445/job/98731080894

## Wordflow Code (raíz de programación)
- https://github.com/maxbry123-commits/agentes/tree/main/Wordflow%20Code
- https://github.com/maxbry123-commits/agentes/blob/main/Wordflow%20Code/Readme/README.md
- https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/code_path_runner.py
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/ARQUITECTURA_03_WORDFLOW.md
- https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow

## Despliegue
- https://github.com/maxbry123-commits/agentes/tree/main/Desplegar
- https://github.com/maxbry123-commits/agentes/tree/main/Desplegar/Desplegar%201
- https://github.com/maxbry123-commits/agentes/tree/main/Desplegar/Desplegar%202
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/08_DESPLIEGUE_DETERMINISTA_v2.md
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/08_DESPLIEGUE_APPLY_PUSH.md
- https://github.com/maxbry123-commits/agentes/blob/main/extensions/github_deploy/apply_push.py
- https://github.com/maxbry123-commits/agentes/tree/main/despliegue
- https://github.com/maxbry123-commits/agentes/tree/main/.github/workflows

## Enchufe / plugins / Fables (alias)
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/07_ENCHUFE_UNIVERSAL_v2.md
- https://github.com/maxbry123-commits/agentes/blob/main/M%C3%A9todo%20de%20trabajo/GUIA_REGISTRO_PLUGINS_Y_CABLEADO.md
- https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/ficha.v2.json

## UOOS + Extract + X-Ray
- https://github.com/maxbry123-commits/agentes/blob/main/UOOS_v2_%20PARTE%201%20con%20este%20docimentl%20clude%20o%20minimax%20o%20cualquier%20Ai%20me%20da%20los%20documentos%20para%20yo%20ejecutar%20con%20el%20agente%20que%20yo%20quiero%20clude%20code%20o%20Open%20claw%20AUTORUN-1.md
- https://github.com/maxbry123-commits/agentes/blob/main/UOOS_PARTE2_v3_%20%20con%20este%20documento%20es%20el%20promt%20DSL%20universal%20para%20que%20el%20agente%20ejecute%20los%20documentos%20del%20c%C3%B3digo%20de%20ouss%20parte%201%20RUNTIME.md
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/57_MARKDOWN_TO_CODE_EXTRACTION.md
- https://github.com/maxbry123-commits/agentes/tree/main/extensions/audit_forensic
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSIC_CODE_AUDIT.md

## Tokens + cuentas (SOLO nombres — nunca valores)
- https://github.com/maxbry123-commits/agentes/settings/secrets/actions  (ver nombres existentes)
- https://github.com/maxbry123-commits/agentes/settings/secrets/actions/new  (crear uno nuevo)
- https://github.com/settings/personal-access-tokens/new
- https://github.com/maxbry123-commits/agentes/blob/main/GUIA_CUENTAS_REMOTE.md
- https://github.com/maxbry123-commits/agentes/blob/main/SETUP_TOKEN_MOVIL.md
- https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/connectors/external_accounts.yaml
- https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/check-external-token-secret.yml

Alias confirmados: `Maxbry_123_tokens` (cuenta A, acceso nativo agente↔repo `agentes`), `EXTERNAL_GH_B_TOKEN` (cuenta B), `EXTERNAL_GH_C_TOKEN` (cuenta C, HOLD), `TARGET_REPO_TOKEN` (genérico PASO 4), `HF_TOKEN` (Hugging Face Spaces).

## Refactoría + Método + Wordflow Code (parche)
- https://github.com/maxbry123-commits/agentes/tree/main/Refactoria
- https://github.com/maxbry123-commits/agentes/tree/main/M%C3%A9todo%20de%20trabajo
- https://github.com/maxbry123-commits/agentes/tree/main/M%C3%A9todo%20de%20trabajo/wordflow-code-deploy-router

## Tarea 3 — destinos cableados (post-evidencia)
```
canonical  skills/wordflow-code-deploy-router/
copia      Método de trabajo/wordflow-code-deploy-router/
copia      Download code/wordflow-code-deploy-router/
copia      Desplegar/wordflow-code-deploy-router/
copia      Refactoria/wordflow-code-deploy-router/
parche     Wordflow Code/Readme/Readme1/  (cable only)
```
