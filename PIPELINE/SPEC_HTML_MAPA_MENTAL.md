# Spec HTML mapa mental cascada — S05 / T05
**Fecha:** 2026-08-18  
**Estilo:** NCT/APEX cascada  
**Objetivo T05:** contrato del HTML final (implementación HTML = **T41**)  
**IDs:** ROOT_MAP_IDS · XRAY_SEED_STATUS

## Requisitos del HTML final (T41)
1. Cascada vertical: Visión → Kernel → Instance → Extensions → Path → Recursos → UI
2. Cada bloque lleva ID canónico (ROOT_MAP_IDS)
3. Cada bloque muestra: `→ Para qué` / `→ Sin esto`
4. Estados de color: IMPLEMENTED (verde) | PARTIAL (ámbar) | MISSING (rojo) | PENDING (gris)
5. Enlaces directos a path GitHub cuando exista archivo
6. Sin dependencias externas pesadas (HTML + CSS mínimo inline o un solo archivo)
7. Responsive básico
8. **Visión en ≤5 s:** título + 3 bullets de sistema vivo (multi-instancia, COPY-FIRST, GitHub=verdad)
9. Fuente de STATUS: `PIPELINE/XRAY_SEED_STATUS.md` (seed) → T43 matriz post-code
10. No claim C100 100% en UI hasta T49

## Estructura de secciones
```
1. Visión (OBJETIVO V1)
2. Kernel (WF.00)
3. WordflowInstance (INST.*)
4. Extensions wordflow (WF.01)
5. Extensions wordflow_kernel (WF.02)
6. Control-layer (WF.03)
7. Code path / loops
8. Recursos HF / cuentas
9. UI / Gateway
10. PIPELINE docs
```

## Contrato de bloque (cada nodo)
| Campo | Obligatorio | Ejemplo |
|-------|-------------|---------|
| id | sí | WF.01 |
| title | sí | extensions/wordflow |
| status | sí | IMPLEMENTED \| PARTIAL \| … |
| para_que | sí | Motor code_path + accounts |
| sin_esto | sí | Sin path de programación |
| github_path | si existe | extensions/wordflow/engine/ |
| children | opcional | FILE.* / CONN.* |

## Cascada (orden de render)
1. Visión  
2. Kernel (WF.00)  
3. Instance (INST.v1 / INST.*)  
4. WF.01 wordflow  
5. WF.02 kernel package  
6. WF.03 control-layer  
7. Hot path (code_path_runner, programming_pipeline, goal_lock)  
8. maxbry_loop (WF.05)  
9. Recursos / accounts / HF  
10. UI gateway / router_slot / memory_slot  
11. PIPELINE (00, 52, ROOT_MAP, XRAY)

## CSS mínimo (contrato)
- `.status-IMPLEMENTED { }` verde  
- `.status-PARTIAL { }` ámbar  
- `.status-MISSING { }` rojo  
- `.status-PENDING { }` gris  
- Layout: columna única, bloques apilados, indent hijos

## Fuera de alcance T05
- No generar el HTML final aquí (eso es **T41**)  
- No inventar STATUS distintos de XRAY/ROOT_MAP  
- No dependencias React/Vue/CDN obligatorias

## Criterio de cierre T05
- Este documento en `PIPELINE/SPEC_HTML_MAPA_MENTAL.md` con requisitos 1–10 + contrato de bloque + cascada  
- T41 debe poder implementarse **solo** con esta spec + ROOT_MAP + XRAY_SEED

## Anclas
SPEC_HTML · T05 · T41 · NCT_APEX · ROOT_MAP_IDS · XRAY_SEED · NO_C100_CLAIM
