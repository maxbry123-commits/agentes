# FORENSE R3 — PASADA 01 STRUCTURE

**Ref:** `95eb881` (HEAD = commit de R2; no hay commit de code posterior)
**C100 = NO.** No sustituye R1 ni R2. Re-auditoría independiente.

## Alcance
Inventario declarativo vs tree GitHub. COPY-FIRST: no se regeneró code.

## Homes (reconfirmados en tree)

| Home | Path | Presente |
|------|------|----------|
| wordflow.core | `extensions/wordflow/` | SÍ |
| wordflow.reception inbox | `extensions/wordflow/reception/` | SÍ |
| wordflow_kernel | `extensions/wordflow_kernel/` | SÍ |
| kernel.reception LINK | `extensions/wordflow_kernel/reception/convert.py` | SÍ (9160 B) |
| maxbry_loop | `extensions/maxbry_loop/` | SÍ |
| github_deploy | `extensions/github_deploy/` | SÍ |
| C-19 / forensic_core | `extensions/wordflow/standards/` | SÍ |
| CI | `.github/workflows/test-wordflow-code-path.yml` | SÍ (re-verificado R3) |
| fusion slot | `extensions/wordflow_kernel/slots/kimi_minimax.ficha.v2.json` | SÍ PLACEHOLDER |
| acquire | `extensions/source_evolution/` | SÍ (no `control-layer/subsheriffs/acquire_os`) |

## Catálogos vs tree

- `component_catalog.json` v1.1.0: kernel/loop/reception `materialized` — coincide.
- `connect_catalog.json` v1.3.0: paths citados existen; `CONN.ingest_writes_phase` y `CONN.audit_to_plan` y `CONN.path_gateway` siguen GAP (declarado).
- Dual homes: siguen existiendo. Consumidor único documentado en `PIPELINE/HOMES_CONSUMIDOR_UNICO.md`.

## Delta vs R2 P1

| Ítem R2 | R3 |
|---------|----|
| CI path no re-verificado | CERRADO — workflow existe, unittest discover wordflow + kernel + loop |
| dual homes | IGUAL — documentados, no merge |
| catalogs alineados | IGUAL |
| engines stub files | IGUAL — `openclaw_stub.py` / `hermes_stub.py` existen |

## Residual STRUCTURE

- Dual homes no mergeados (no es mismatch de path).
- `intelligence_gateway` status=`stub` (archivo gateway sí existe).
- Tests de ingest/motor existen como blobs; no es evidencia de ejecución.

## Veredicto R3 P1

**STRUCTURE = PASS**
No implica CONNECTIVITY ni BEHAVIOR.
