# GITHUB — ESTRUCTURA, DESTINOS Y COPIA DETERMINISTA V1.1

**COPIA** desde `maxbry123-commits/Grupo-Trabajo-1` path `GITHUB-ESTRUCTURA-DESTINOS-Y-COPIA-V1.1.md` SHA `737dfe55fa1ecc43bc09cc1df8983d8955ffe4d6`. No reescrito.

**TASK_ID:** GITHUB-STRUCTURE-001  
**ESTADO:** ACTIVO  
**MODO:** determinista / fail-closed / COPY-FIRST / REUSE-FIRST  
**FUENTE:** PIPELINE.1.1 — ARQUITECTURA CODE + guías de `agentes/main`  

## 0. OBJETIVO

Evitar que una AI mezcle software, componentes, archivos temporales o código de proyectos distintos en `main`.

La AI **no escribe software desde cero** cuando exista código open source reutilizable. Debe leer la gía de `main`, recibir/inspeccionar el ZIP o fuente autorizado, comparar, copiar/reutilizar, cablear y verificar.

Cada software o componente independiente debe tener una **raíz propia** dentro de su repositorio de destino. No se permite volcar todos los archivos de varios proyectos directamente en la raíz `main`.

---

# 1. MAPA CANÓNICO DE DESTINOS

| Función | Repositorio destino | Regla |
|---|---|---|
| Router inteligente universal | `maxbry123-commits/router-universal-router-inteligente-` | Todo software de router/gateway/routing va bajo una raíz propia del componente. |
| Frontend / UI / control plane | `maxbry123-commits/frontend` | Todo código exclusivamente frontend/UI va aquí, separado por software/componente. |
| Orquestador + auditoría + memoria/almacenamiento | `maxbry123-commits/osquestador-auditor` | Código de orquestación, auditoría, memoria y almacenamiento va aquí, cada software en su propia raíz. |
| Pipeline / planes de trabajo | `maxbry123-commits/Grupo-Trabajo-1` | Solo planificación, trazabilidad, guías, índices y evidencia del trabajo. |
| Motor/agentes Wordflow base | `maxbry123-commits/agentes` | Fuente base y guías canónicas del método; no usarlo como cajón para componentes nuevos. |

---

# 2. REGLA DE RAÍCES — NO MEZCLAR SOFTWARE

Incorrecto: soltar router.py, memory.py, frontend.jsx en main.  
Correcto: `software/<componente>/` con SOURCE.md + MANIFEST.json.

**Un software/componente independiente = una raíz identificable y trazable.**

# 3. DESTINO POR FUNCIÓN

Router → repo router. Frontend → repo frontend. Orquestador/auditor/memoria → osquestador-auditor. No mezclar UI en router ni memoria en frontend.

# 4. PROTOCOLO ZIP

`ZIP → HASH → EXTRACT SIN MODIFICAR → INVENTARIO → HASH ARCHIVOS → COMPARAR → SELECT → COPY/REUSE → VERIFY → COMMIT → READ-BACK`

Excluir solo `__MACOSX/`, `.DS_Store`, `Thumbs.db` con evidencia.

# 5. CINCO MÉTODOS DE COPIA

1. Contents API: GET → PUT → READ-BACK → VERIFY  
2. Git Data API: blob → tree → commit → ref, sin force  
3. GitHub Actions  
4. Transfer/fork — repo entero  
5. Clone local + push

# 6. BORRADO DUPLICADOS

Identificar canónico → borrar solo duplicado → 404 duplicado → canónico sigue. Si no sabes canónico: HOLD.

# 7. COPY-FIRST

COPY/MOVE/REUSE → LINK/CONNECT → PATCH → ADAPT → GENERATE LAST

# 8. TRAZABILIDAD

SOURCE_REPO, SOURCE_COMMIT/TAG, SOURCE_LICENSE, SOURCE_ZIP_SHA256, MANIFEST, DEST_REPO, DEST_ROOT, DEST_COMMIT, FILES_COPIED/EXCLUDED/ADAPTED, VERIFY, EVIDENCE.

# 9. PROTOCOLO AI

G0 READ_GUIDES → G1 DEST → G2 INVENTORY → G3 HASH → G4 DUP → G5 ROOT → G6 COPY → G7 VERIFY → G8 COMMIT → G9 READ-BACK → G10 EVIDENCE → G11 VERDICT

# 10. MAIN

No ZIP temporales, no caches, no duplicados, no mezclar software.

# 12. DONE

Raíz propia + destino + fuente + hash + copy + verify + commit + read-back + evidencia. PASS sin verify = FAIL.
