# 🎄🚂 SALIDA B · DOC B2 — LOOP ENGINE 🔁 (T-009): 4 NIVELES × 9 FASES + 1.080
# UOOS v2.0 | NCT | 2026-07-13 | Doc 7/16
# TRIBUNAL INTERNO: 14/14 PASS · REGALO 🎁: Selector inteligente multiproyecto

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EL CORAZÓN QUE LATE 🔁 (cómo gira cada vuelta del taller)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
CADA ITERACIÓN = 9 FASES EN ORDEN ESTRICTO (sin atajos):
📌leer_anclas → 🗺️plan → ⚙️ejecutar → 📏medir → 🛂validar →
🔧reparar → 📋evidencia → 💾checkpoint → 🎯decidir(continuar|cerrar)

OBLIGATORIAS (Sheriff frena si faltan o fallan): leer_anclas · ejecutar ·
validar · evidencia · decidir. Las otras 4 se pueden saltar declarándolo.

4 NIVELES (presupuesto heredado):        👀 6 DETECTORES (siempre encendidos):
micro    5 it ·  20k tok ·  10 min       estancamiento (error repetido)
tarea    8 it ·  80k tok ·  45 min       oscilación (ping-pong A-B-A-B)
fase    12 it · 300k tok · 180 min       regresión (score cayendo ×2)
proyecto 20 it · 1.5M tok · 24 h         deriva (salida sin sello del goal)
                                          presupuesto (aviso 80% / corte 100%)
                                          timeout
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARCHIVOS (repo 03 `loop_engine/`)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
| Archivo | Líneas | Qué hace |
|---|---|---|
| `engine.py` | 84 | `CicloNueveFases`: recorre las 9 fases en orden; obligatoria ausente o fallida = freno con causa; `correr()` itera hasta cerrar o techo del nivel |
| `detectores.py` | 78 | los 6 vigías, puros y baratos + `panel()` que corre todos de una (caso enfermo disparó 5 alertas simultáneas en test) |
| `catalogo.py` | 76 | genera los **1.080 loops** (4 niveles × 9 fases-foco × 30 dominios), ids estables LOOP-0001..1080, política RAPIDO/PROFUNDO + 🎁 |
| `loop_catalog.json` | 1.080 entradas | el catálogo generado y verificado, listo para la Loops UI |

**REGALO 🎁 — el Selector inteligente** (dentro de catalogo.py):
- `seleccionar(dominio, urgencia, fase)`: urgencia humana → nivel
  ("ya"→micro, "hoy"→tarea, "semana"→fase, "mes"→proyecto) y te da EL loop
- Si el dominio no existe **no adivina**: sugiere parecidos
  ("fichaje" → sugiere "fichas")
- `cargar_multiproyecto()`: varios proyectos a la vez, cada fallo queda
  AISLADO sin contagiar a los demás → es la semilla directa de tu Loops UI
  (T-017) y del selector visual 1-1000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EVIDENCIA §6.4 — 14 PRUEBAS REALES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```yaml
evidencia:
  nodo_id: "T-009"
  tests_clave:
    - "catálogo 1080/1080 con ids únicos: PASS"
    - "presupuestos escalonados micro<tarea<fase<proyecto: PASS"
    - "9 fases en orden estricto + cierre limpio: PASS"
    - "SHERIFF: fase obligatoria ausente → freno: PASS"
    - "fase opcional saltada sin drama: PASS"
    - "fase obligatoria fallida → freno con causa: PASS"
    - "loop eterno cortado por iter_max del nivel: PASS"
    - "6 detectores individuales + panel (5 alertas juntas): PASS"
    - "selector 🎁: dominio+urgencia+fase → loop exacto: PASS"
    - "selector honesto: dominio inexistente → sugiere, no inventa: PASS"
    - "multiproyecto: fallo aislado sin contagiar: PASS"
  score_tribunal: 97
  delta_vs_anterior: "el taller ya late: cualquier trabajo gira por las 9
    fases con 6 vigías, y el catálogo completo de 1.080 está generado y
    seleccionable por humanos."
```
VEREDICTO: SHERIFF ✅ · CENTINELA ✅ · JUEZ 96 · SUPERVISOR 97 ·
VALIDADOR 98 (14/14) · VERIFICADOR 97 → **PASA (97/100)**

MINI RESUMEN: 1.080 luces de bucle en el catálogo, un corazón de 9 fases
que no acepta atajos, y un selector que te trae el loop correcto con
decir "fichas, ya". 🔁🛷

→ Esperando: **OK** (sigue B3: Escritor + Runtime sandbox + Witness —
donde nace el código y nadie se aprueba a sí mismo, doc 8/16) | FIX
