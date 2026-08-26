# PLAN S2 — DEPURACIÓN MAIN — EJECUTA GPT (no Grok)

**Repo:** maxbry123-commits/agentes · **rama:** `main`  
**Autor del plan:** Grok · **Ejecutor:** GPT  
**Grok no borra nada en S2.**

Leer ANTES:
- https://github.com/maxbry123-commits/agentes/blob/main/notas-trabajo-grock/NOTAS-1.md
- https://github.com/maxbry123-commits/agentes/blob/main/notas-trabajo-grock/NOTAS-2.md
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md
- https://github.com/maxbry123-commits/agentes/blob/main/Yaiwes%20wordflow/Readme/README.md
- https://github.com/maxbry123-commits/agentes/blob/main/Wordflow%20Code/Readme/README.md
- https://github.com/maxbry123-commits/agentes/blob/main/Desplegar/README.md

---

## 0. INPUT BLOCK

TAREA: depurar `main` hasta que solo queden las raíces vivas + excepciones HOLD.
OBJETIVO: basura fuera; code/docs canónicos no perdidos; hot path intacto.
ALCANCE: repo `agentes` rama `main`.
FUERA: no reescribir `PLAN_YAIWES_AGENTE_WORDFLOW.md`; no editar `code_path_runner.py`; no ejecutar Fase 2; no crear `Desplegar 1/` vacío; no inventar body.
PASS: inventario GitHub post-read-back = solo VIVO+HOLD+excepciones, con evidencia (commit + árbol).

---

## 1. RAÍCES VIVAS (no borrar nunca)

```text
Desplegar/
PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md
Método de trabajo/
README_METHOD.md
Refactoria/
Yaiwes wordflow/
Wordflow Code/
notas-trabajo-grock/
```

`.github/workflows/` = excepción física Actions. No borrar a ciegas.

---

## 2. REGLAS

1. COPY-FIRST. Si hay duda → HOLD + registrar GAP. No borrar.
2. No editar in-place. Mover = copiar a destino canónico + verify SHA + luego borrar origen.
3. Refactoria para todo archivo que se MODIFICA:
   `Refactoria/refactoria-plan-s2/<path>/source/` y `new/`.
4. Verificar ×3 antes de borrar origen: (1) destino existe (2) SHA/contenido (3) read-back GitHub.
5. Hot path NO SE MUEVE en S2 salvo tests PASS + autorización Director:
   `extensions/wordflow/engine/code_path_runner.py`
6. `extension-kernel` no es basurero. No tirar archivos ahí.
7. `Desplegar 1` no se inventa. `despliegue/` ≠ `Desplegar/`.
8. LLM ≠ PASS. PASS = evidencia.
9. Un GAP no para el lote independiente. GAP → OPEN + causa + acción. No fake CLOSE.
10. No force-push.

---

## 3. HOLD — no borrar (cutover o fuente del plan vivo)

### Cuerpo a cutover (mover DESPUÉS de verify; si riesgo → dejar y OPEN)

| Origen | Destino canónico | Nota |
|---|---|---|
| `agente-yaiwes/**` | `Yaiwes wordflow/` (mismo árbol interno) | cutover nombre |
| `extensions/wordflow/**` | `Wordflow Code/` | SOLO si tests C-19 PASS. Default S2 = HOLD en sitio |
| `wordflow/abi.py` + ABI docs | `Wordflow Code/` o dejar `wordflow/` HOLD | extension point |
| `extensions/wordflow_kernel/**` | HOLD | gateway/kernel; no borrar |
| `code-programming-engine/**` | HOLD | espejo C-19; clasificar no borrar |
| `Refactoria/G1`…`G7` | HOLD | misión YAIWES |
| `despliegue/INSTRUCCIONES_GROK_OPCION_A.md` | HOLD o mover a `Desplegar/` SOLO si Director confirma | fuente del plan vivo |
| `despliegue/**` resto | CLASSIFY | ≠ inbox Desplegar |

### Archivos citados por el plan vivo — MOVER no borrar

| Path | Destino propuesto |
|---|---|
| `PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md` | `Yaiwes wordflow/` |
| `PIPELINE/Agente_YAIWES_v.1_en_PRODUCCION.md` | `Yaiwes wordflow/` |
| `PIPELINE/ARQUITECTURA_03_WORDFLOW.md` | `Wordflow Code/` |
| `agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md` | via cutover |
| `agente-yaiwes/ORIGIN_MAP.md` | via cutover |
| `agente-yaiwes/COPY_MANIFEST.json` | via cutover |

Guías de método sueltas en raíz — MOVER a `Método de trabajo/` (no borrar):
`GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md` · `GUIA_CUENTAS_REMOTE.md` · `GUIA_CUENTA_B_REMOTE.md` · `METODO_ZIP_COPY_DETERMINISTA.md` · `README_FORENSIC_HANDOFF.md`

---

## 4. CANDIDATO BASURA (borrar solo tras inventario + no-HOLD)

Raíz:
`.cursor/` · `AGENTS.md` · `README_ARQUITECTURA.md` · `RENAME_NOTE.md` · `SETUP_TOKEN_MOVIL.md` · `README.md` raíz (reescribir no; si se toca = parche nuevo en `Yaiwes wordflow/Readme/` y raíz vieja se evalúa)

Dirs:
`TASK-GAPS/` · `agents/` · `control-layer/` · `docs/` · `groups/` · `memory/` · `scripts/` · `tools/`

`extensions/` excepto HOLD:
`adapters/` · `audit_forensic/` · `github_deploy/` · `github_publisher/` · `knowledge/` · `maxbry_loop/` · `project_bootstrap/` · `source_evolution/`

Si un path de esos está REF-eado por `agente-yaiwes/ORIGIN_MAP.md` o PASO3 → HOLD + mover REF, no borrar.

`PIPELINE/**` excepto:
- `PLAN_YAIWES_AGENTE_WORDFLOW.md` (nunca)
- los 3 archivos de la tabla §3 (mover)
- `checkpoints/` → HOLD hasta S3 (sitio checkpoint del molde)

Default resto PIPELINE = basura documental histórica.

---

## 5. LOTES (orden fijo)

LOTE A — Inventario X-Ray
- Listar tree main.
- Marcar cada path: VIVO / HOLD / MOVE / BASURA / GAP.
- Cruzar ORIGIN_MAP + PASO3 + plan vivo.
- Entregar tabla. No borrar aún.

LOTE B — Mover guías a `Método de trabajo/`
- Copy + SHA + read-back + borrar origen.

LOTE C — Mover 3 docs PIPELINE canónicos (§3)
- Copy a raíz destino + SHA + read-back.
- No borrar el plan vivo.

LOTE D — Cutover `agente-yaiwes/` → `Yaiwes wordflow/`
- Copy árbol (Git Data API / mismos blob SHA).
- Verify conteo + sample SHA.
- Actualizar `Yaiwes wordflow/SOURCE.md` como parche `Readme/Readme1/` (no reescribir README base).
- Borrar `agente-yaiwes/` solo si verify ×3 PASS.

LOTE E — Hot path
- NO MOVER `extensions/wordflow/`.
- Registrar HOLD explícito + razón tests.
- `Wordflow Code/SOURCE.md` se queda apuntando al path real.

LOTE F — Borrar BASURA ya clasificada
- Solo paths BASURA del lote A.
- Un commit por grupo (PIPELINE histórico / dirs raíz / extensions no-HOLD).
- Read-back: path 404 + canónicos siguen.

LOTE G — X-Ray final
- Tree main vs lista VIVO+HOLD.
- Extra inesperado = GAP no “OK”.
- Missing canónico = FAIL. Restaurar.

---

## 6. CHECKPOINT

Escribir en `PIPELINE/checkpoints/S2_GPT.md` (crear si falta; no reescribir el plan vivo):

```text
LOTE:
PATHS_MOVED:
PATHS_DELETED:
COMMIT:
READBACK:
HOLD_REMAINING:
GAPS:
STATUS: PASS|FAIL|OPEN
```

---

## 7. DEFINITION OF DONE

- `PLAN_YAIWES_AGENTE_WORDFLOW.md` intacto (mismo rol; no vacuum).
- `code_path_runner.py` en el mismo path, tests no rotos por move.
- `Yaiwes wordflow/` + `Wordflow Code/` + `Desplegar/` + `Refactoria/` + `Método de trabajo/` + `notas-trabajo-grock/` vivos.
- Sin `agente-yaiwes/` SOLO si cutover verify PASS; si no, HOLD y OPEN.
- Basura del lote A ausente (404).
- Checkpoint S2 escrito.
- Ningún fake PASS.

## 8. BLOCKER

Si ORIGIN_MAP dice que un path “basura” es REF real → no borrar.  
`BLOCKER-S2.md` en `notas-trabajo-grock/` (archivo nuevo) con problem/source/impact/action.
