# CHECKPOINT + PARCHE DE RECUPERACIÓN — G1 / G3 / G4

## 0. Identidad
- Repository: `maxbry123-commits/agentes`
- Branch: `main`
- Closing commit: `4f7edfdcd21d0b482be8b814242b0205ca34a5c6`
- CI workflow: `.github/workflows/verify-gap-indexes.yml`
- Workflow run: `33032630757`
- Verify job: `98388384120`
- Evidence artifact: `g1-g3-verified-evidence-33032630757`
- Artifact ID: `9630814224`
- Artifact digest: `sha256:f2f1ae8163676eeefe6dbe333c31e078ef416e965e51a03b1fe565e4e60746a2`
- Artifact expiration: `2026-11-25T02:13:56Z`

## 1. Incidente detectado
Run manual anterior `verify-gap-indexes #6` terminó con exit code 1.
La evidencia real del job mostró que el fallo ocurría en `Export G1 symbol index`:
`ModuleNotFoundError: No module named 'extensions'`.
La causa fue el `sys.path` de Python al ejecutar directamente un script ubicado en `Refactoria/G1/new/`.
No fue un fallo del índice AST ni del hot path.

## 2. Parche de recuperación aplicado
### G1
Se preservó primero el source pre-parche en:
`Refactoria/G1/source/build_programming_symbol_index.py`

Luego `Refactoria/G1/new/build_programming_symbol_index.py` fue corregido para registrar explícitamente la raíz del repositorio en `sys.path` antes de importar:
`extensions.wordflow.standards.symbol_index`.

La implementación sigue reutilizando `build_symbol_index()` y conserva los roots reales:
- `extensions/wordflow/engine`
- `extensions/wordflow/standards`

### CI
`.github/workflows/verify-gap-indexes.yml` fue convertido a verificación read-only:
- `permissions: contents: read`
- elimina `git push` desde `GITHUB_TOKEN`
- conserva la ejecución real de G1/G3
- sube evidencia mediante `actions/upload-artifact@v4`

Esto elimina tanto el fallo de importación como la posibilidad de que la evidencia dependa de un push automatizado.

## 3. Verificación cruzada ×3
### V1 — Source vs New
PASS — el source pre-parche permanece conservado y el cambio de G1 se limita al bootstrap de importación.

### V2 — CI real
PASS — GitHub Actions run `33032630757`:
- Export G1 symbol index: PASS
- Verify G1 artifact: PASS
- Export G3 test assert index: PASS
- Verify G3 artifact: PASS
- Build verified evidence: PASS
- Upload G1/G3 evidence artifact: PASS
- Verify protected hot path unchanged: PASS

### V3 — Evidencia
PASS — artifact real `9630814224` existe, no está expirado y tiene digest SHA-256 registrado arriba.

## 4. Resultados
- G1: **CLOSED / PASS** — índice AST generado y validado; runner/pipeline symbols verificados.
- G3: **CLOSED / PASS** — índice test→assert generado y todos los archivos indexados pasan parse.
- G4: **CLOSED / PASS** — ejecución CI real, logs verificables y artifact real registrados.

## 5. Hot path
`extensions/wordflow/engine/code_path_runner.py`:
**INTACTO**.
La propia ejecución CI terminó `Verify protected hot path unchanged: success`.

## 6. Reglas que permanecen activas
- GitHub = truth.
- FAIL-CLOSED.
- NO_INVENTAR.
- NO_FAKE_PASS.
- NO_APAGAR_MONOLITO.
- REUSE > PATCH > ADAPT > GENERATE.
- No duplicar `goal_lock`, `cognitive_loop`, `evidence_packet`.
- Método de trabajo/plugin: los artefactos registrados no se editan para añadir cableados posteriores; se conectan mediante el contrato/plugin registrado.
- Hermes permanece excluido por instrucción del Director.

## 7. Plan y guía
Plan canónico:
`PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md`

Guía de método/plugin:
`Método de trabajo/GUIA_REGISTRO_PLUGINS_Y_CABLEADO.md`

## 8. Recuperación
Si G1/G3 vuelven a fallar:
1. conservar el último artifact real;
2. restaurar únicamente desde `Refactoria/G1/source/` para G1;
3. comparar `source/` → `new/`;
4. ejecutar el workflow;
5. no modificar `extensions/wordflow/engine/code_path_runner.py` para resolver el problema;
6. no declarar PASS sin un run y artifact reales.

## 9. Prompt de gaps en resolución
G1: export real AST reutilizando `build_symbol_index()`.
G2: schemas C-19 únicamente para stages realmente nombrados por el código.
G3: índice test→assert reproducible.
G4: evidencia CI real, sin logs inventados.
G5: p01→p12 solo con source real; sin módulos inventados.
G6: adapters solo con source/SDK real.
G7: bodies OpenClaw/Hermes solo con source real; Hermes excluido en este loop.

## 10. Estado al checkpoint
G1 = CLOSED
G3 = CLOSED
G4 = CLOSED
G2 = OPEN residual
G5 = OPEN/BLOCKER si falta source
G6 = CLOSED
G7 = CLOSED
