# PIPELINE 23 — Source Evolution Status

**llm_control:** DENY  
**Extensión:** `extensions/source_evolution/`

## Entregado A-SE-01 … A-SE-05

| ID | Entrega | Estado |
|----|---------|--------|
| A-SE-01 | VersionPin + SourceRegistry | DONE |
| A-SE-02 | Fetch planner + FakeFetcher | DONE |
| A-SE-03 | License gate + install planner | DONE |
| A-SE-04 | run_acquire entrypoint + manifest | DONE |
| A-SE-05 | Provenance + CI workflow | DONE |

## Flujo

```
VersionPin → registry → fetch_plan → [FakeFetcher|real]
    → license_gate → install_plan → provenance
```

## Invariantes

- Nunca token en provenance/journal
- install usa LOCAL_ARTIFACT (no live registry)
- LICENSE STOP/DIRECTOR/PASS
- digest obligatorio (sha256 | git_commit)

## Tests

- source_evolution: 30 tests offline
- CI: `.github/workflows/test-source-evolution.yml`

## Pendiente (siguiente)

- A-DEP GitHub Publisher (objetivo 4)
- Real git/hf adapters (fuera offline)
