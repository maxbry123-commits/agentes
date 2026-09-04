# Checklist Sheriff — dataset → obligación determinista

## Idea
Los 500 puntos son **dataset**.  
Un **subset de programación** vive en `programming_points_catalog.py`.  
El **ChecklistSheriff** es sentinel/juez: sin checklist del agente con evidence → **BLOCK**.

## No se programa un gate por cada punto
Se programa:
1. Catálogo (ids + stage + required)
2. Claim del agente (`AgentChecklistClaim`)
3. Sheriff que valida cobertura de REQUIRED + evidence no vacía
4. Wire en pre_gate y post_verify

## Obligación del agente de programación
Antes de IMPLEMENT/APPLY debe enviar checklist con:
- action COPY|ADAPT|GENERATE
- sources si ADAPT/COPY
- files_touched
- claims[]: point_id, addressed, evidence

Si omite required o evidence vacía → no pasa.

## Propuestas adicionales
1. **Profiles:** `minimal` (solo required_default) vs `strict` (+ optional stages).
2. **Auto-fill measures:** post_verify rellena evidence de E151/E157 desde smoke/wiring (menos fricción).
3. **Scorecard:** coverage_ratio en bitácora por misión.
4. **Cursor skill:** “rellena AgentChecklistClaim desde plan”; el runtime solo sheriff.
5. **No expandir a 500 required** — solo subir required cuando un gap se repita 3 veces.

## Paths
- `extensions/wordflow/standards/programming_points_catalog.py`
- `extensions/wordflow/standards/checklist_sheriff.py`
- `extensions/wordflow/standards/executor_gates.py`
