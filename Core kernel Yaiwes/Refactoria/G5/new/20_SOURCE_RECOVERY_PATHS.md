# G5 — 20 source-recovery paths audited

Purpose: close the p01→p12 E2E gap without fabricating modules.

1. Exact filename search `p01_*` in `agentes` — no source found.
2. Exact token `p01` in `agentes` — only gap/audit documentation, no module source.
3. Exact filename search `p12_*` in `agentes` — no source module found.
4. Exact token `p12` in `agentes` — only gap/audit documentation, no module source.
5. Branch-name search for `p01` — no matching branch.
6. Commit-history search for `p01` — no matching commit.
7. Search canonical `agente-yaiwes/code-programming-engine/code-path-execution/` — no verified p01–p12 source set.
8. Search `extensions/wordflow/engine/` — monolithic runner exists; it is protected and cannot be rewritten into fabricated modules.
9. Search `extensions/wordflow/codegen/` — no verified p01–p12 source set.
10. Search `extensions/wordflow_kernel/stages/` — no verified p01–p12 source set.
11. Search `agente-yaiwes/kernel-principal/stages/` — no verified p01–p12 source set.
12. Search `PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md` — architecture mapping does not supply the missing source modules.
13. Search `agente-yaiwes/ORIGIN_MAP.md` — no legitimate p01–p12 origin rows that can be materialized.
14. Search `agente-yaiwes/COPY_MANIFEST.json` — no source mapping that licenses fabricated p01–p12 files.
15. Search `maxbry123-commits/Agentes-motores-Wordflow-YAIWES` — no `p01_` source found.
16. Search sibling repository for `p01` — no p01 module source found.
17. Search OpenClaw source as a substitute — invalid for G5; OpenClaw is an external route/agent, not p01–p12 source.
18. Extract stages from `ProgrammingPipeline` and rename them p01–p12 — rejected because it invents the required module set.
19. Split `code_path_runner.py` into twelve generated files — rejected because it violates NO_INVENTAR and the hot-path/no-rewrite rule.
20. Acquire/attach the real p01–p12 source set, then copy-first into `Refactoria/G5/source`, implement in `Refactoria/G5/new`, parity-test, and integrate — **only compliant path capable of closing G5**.

## Result
The blocker is source absence, not an unresolved implementation choice. Until path 20 supplies real source, G5 MUST remain `OPEN/BLOCKER` under FAIL-CLOSED.
