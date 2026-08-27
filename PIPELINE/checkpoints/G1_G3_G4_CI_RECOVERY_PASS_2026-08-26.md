# CHECKPOINT + PARCHE DE RECUPERACIÓN — G1 / G3 / G4

## 0. Identidad
- Repository: `maxbry123-commits/agentes`
- Branch: `main`
- Verified head: `5ded92190dfa47ec427ea2566b309fcd1698d8f7`
- CI workflow: `.github/workflows/verify-gap-indexes.yml`
- Workflow run: `33032745705`
- Verify job: `98388725584`
- Evidence artifact: `g1-g3-verified-evidence-33032745705`
- Artifact ID: `9630853631`
- Artifact digest: `sha256:2d75ed90824e9dd8b91c4da234d279a5fcd7e023d8faf6b99d8df6285ef9465a`
- Artifact expiration: `2026-11-25T02:16:03Z`

## 1. Incidente detectado y causa raíz
`verify-gap-indexes #6` terminó con exit code 1.
El log real del job identificó exactamente:
`ModuleNotFoundError: No module named 'extensions'`

La causa era el `sys.path` de Python al ejecutar directamente un script ubicado en `Refactoria/G1/new/`. El script no registraba la raíz del repositorio antes de importar el índice canónico.

## 2. Parches aplicados
### G1 — bootstrap de importación
- Source conservado en `Refactoria/G1/source/build_programming_symbol_index.py`.
- `Refactoria/G1/new/build_programming_symbol_index.py` registra la raíz del repositorio antes del import.

### G1 — determinismo cross-run
La primera ejecución PASS generaba paths absolutos del runner (`/home/runner/...`). Eso no era suficientemente reproducible.

Se conservó otro source exacto en:
`Refactoria/G1/source/build_programming_symbol_index_pre_normalize.py`.

El `new/` ahora normaliza todos los paths de símbolos a paths POSIX relativos al repositorio, manteniendo el `build_symbol_index()` canónico.

### CI — recuperación
`.github/workflows/verify-gap-indexes.yml` ahora es read-only:
- `permissions: contents: read`
- no hace `git push` con `GITHUB_TOKEN`
- genera G1/G3
- verifica los artefactos
- crea evidencia con `run_id`
- sube un artifact real con `actions/upload-artifact@v4`
- verifica que `extensions/wordflow/engine/code_path_runner.py` no cambió.

## 3. Verificación cruzada ×3
### V1 — Source → New
PASS. Los sources pre-cambio están conservados en `Refactoria/G1/source/` y la modificación está limitada al bootstrap de importación y normalización de paths.

### V2 — CI real
PASS — run `33032745705`, job `98388725584`:
- Export G1 symbol index: PASS
- Verify G1 artifact: PASS
- Export G3 test assert index: PASS
- Verify G3 artifact: PASS
- Build verified evidence: PASS
- Upload G1/G3 evidence artifact: PASS
- Verify protected hot path unchanged: PASS

### V3 — evidencia/integridad
PASS — artifact real `9630853631` existe, no está expirado y tiene digest:
`sha256:2d75ed90824e9dd8b91c4da234d279a5fcd7e023d8faf6b99d8df6285ef9465a`

La inspección del artifact confirmó que el índice G1 contiene paths relativos como `extensions/wordflow/engine/code_path_runner.py`, no paths absolutos del runner.

## 4. Resultados
- G1: **CLOSED / PASS** — AST index real, 462 símbolos, paths relativos deterministas y runner/pipeline symbols presentes.
- G3: **CLOSED / PASS** — test→assert index real y todos los archivos indexados pasan parse.
- G4: **CLOSED / PASS** — run/log/artifact reales registrados.

## 5. Hot path
`extensions/wordflow/engine/code_path_runner.py`:
**INTACTO**.
El workflow ejecutó `Verify protected hot path unchanged` con PASS.

## 6. Reglas activas
- GitHub = truth.
- FAIL-CLOSED.
- NO_INVENTAR.
- NO_FAKE_PASS.
- NO_APAGAR_MONOLITO.
- REUSE > PATCH > ADAPT > GENERATE.
- No duplicar `goal_lock`, `cognitive_loop`, `evidence_packet`.
- Método de trabajo/plugin aplicado.
- Hermes permanece excluido por instrucción del Director.

## 7. Plan y guía
Plan: `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md`

Guía: `Método de trabajo/GUIA_REGISTRO_PLUGINS_Y_CABLEADO.md`

## 8. Parche de recuperación
Si G1/G3 vuelven a fallar:
1. conservar el último artifact real;
2. comparar el último `Refactoria/G1/source/` con `Refactoria/G1/new/`;
3. ejecutar `verify-gap-indexes`;
4. validar digest del artifact;
5. no tocar `extensions/wordflow/engine/code_path_runner.py`;
6. no declarar PASS sin run y artifact reales.

## 9. Prompt G1–G7 en resolución
G1: export AST real con `build_symbol_index()`.
G2: schemas C-19 solo para stages nombrados por código.
G3: índice test→assert reproducible.
G4: evidencia CI real.
G5: p01→p12 solo con source real.
G6: adapters solo con source/SDK real.
G7: bodies solo con source real; Hermes excluido en este loop.

## 10. Estado
G1 = CLOSED
G3 = CLOSED
G4 = CLOSED
G2 = OPEN residual
G5 = OPEN/BLOCKER si falta source
G6 = CLOSED
G7 = CLOSED
