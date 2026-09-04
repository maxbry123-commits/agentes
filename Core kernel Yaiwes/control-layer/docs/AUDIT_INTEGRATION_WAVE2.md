# Wave 2 integration · Research / Opportunity / Watchdog / Genome / CodeWorker

## Dónde vive cada pieza
| Módulo | Path | Rol en pipeline |
|--------|------|-----------------|
| Research | evolution/research/ | candidatos → evolve_path |
| Opportunity | evolution/opportunity/ | gaps post-register |
| Watchdog | evolution/watchdog/ | fail count → ledger rollback |
| Genome | evolution/genome/ | PROMOTE/HOLD/REJECT |
| CodeWorker | evolution/workers/ | rellena adapter.py |

## Pipeline actualizado
```
license → acquire → AST → IR → policy → simulate
  → package write → CodeWorker.fill_adapter
  → Genome.evaluate (REJECT aborta)
  → ledger EV-#### → registry
  → Opportunity.scan_registry
  → events absorb.*
```

## ABI extension capabilities nuevas
- evolution.research
- evolution.research_and_evolve
- evolution.opportunities
- evolution.safe_invoke
- evolution.watchdog

## Test e2e
evolve True REGISTERED · genome PROMOTE 1.0 · worker deterministic · safe_invoke True · research graphiti/playwright

## Nota
controller.py local (artifacts/evo_v3) incluye wiring completo; si GH controller aún no sincroniza 100%, usar package local o re-push controller.
