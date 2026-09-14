# PLAN DE ADQUISICIÓN DE COMPONENTES — extensión del Crazy Wall
**No reemplaza `📂 Bitácora stated JSON Craxy wall.json` — es un registro paralelo,
específico de componentes open source, para no perder nada mientras se decide.**
**Última actualización: 2026-09-14, Claude (orquestador)**

---

## FASE 1 — Prioridad alta (aprobado por Director, listo para Salida 4 → Sol GPT)

### A) Confirmados en documentos propios del Director (R24 / Persistencia Cognitiva)
1. Ray — `github.com/ray-project/ray`
2. OpenTelemetry — `github.com/open-telemetry/opentelemetry-python`
3. NATS JetStream — `github.com/nats-io/nats-server` + `nats-py`
4. Reflexion — `github.com/noahshinn/reflexion`
5. OpenEvolve (equivalente abierto de AlphaEvolve) — `github.com/codelion/openevolve`
6. Letta — `github.com/letta-ai/letta`
7. GPT Researcher — `github.com/assafelovic/gpt-researcher`
8. DeerFlow — `github.com/bytedance/deer-flow`
9. CrewAI — `github.com/crewAIInc/crewAI`
10. OpenAI Agents SDK — `github.com/openai/openai-agents-python`
11. FAISS — `github.com/facebookresearch/faiss`

### B) Propuestos por Claude, pendiente aprobación individual del Director
12. MABWiser (bandit, corrige recomendación anterior de `river`) — `github.com/fidelity-com/mabwiser`
13. DSPy — `github.com/stanfordnlp/dspy`
14. Graphiti — `github.com/getzep/graphiti`
15. Mem0 — `github.com/mem0ai/mem0`
16. py_trees (Behavior Trees) — `github.com/splintered-reality/py_trees`
17. pyhop/GTPyhop (HTN) — pendiente verificación de URL exacta
18. semantic-router — `github.com/aurelio-labs/semantic-router`
19. simple-pid — `github.com/m-lundberg/simple-pid`
20. Rebuff — `github.com/protectai/rebuff`
21. LLM Guard — `github.com/protectai/llm-guard`
22. Schemathesis — `github.com/schemathesis/schemathesis`
23. cyclonedx-python / detect-secrets / Semgrep — higiene de repo, no kernel

### ❌ Descartado en la auditoría (sin evidencia de necesidad real hoy)
etcd, pymerkle, Dify, Flowise — quedan registrados aquí para no reconsiderarlos sin motivo nuevo.

---

## FASE 2 — Reserva (NO descargar todavía — solo cuando el Selector/Rotador esté cableado)

Destino cuando se active: `Core kernel Yaiwes/reserva-algoritmos-105/`

| Librería | Algoritmo del catálogo 105 |
|---|---|
| scikit-opt | ACO, Tabu Search |
| pyswarms | Particle Swarm Optimization |
| cma | CMA-ES |
| DEAP | Algoritmos genéticos |
| neat-python | Novelty Search |
| pysat | SAT solver |
| python-constraint | CSP solver |
| scikit-fuzzy | Lógica difusa |
| Hypothesis | Property-based testing |
| rank_bm25 | BM25 ranking |
| sumy | TextRank |
| VADER | Sentiment sin LLM |
| statsmodels | Series de tiempo |
| pynboids | Flocking/Boids |
| DMTCP | Checkpoint/restart HPC |
| XTDB | Base de datos bitemporal |
| pybreaker | Circuit breaker |
| dynaconf | Config cascade |
| croniter | Cron en lenguaje natural |
| PuLP / OR-Tools | Programación lineal/entera |
| Optuna | Optimización bayesiana |
| Stockfish | Referencia minimax/alfa-beta |

---

## Ya confirmado en `Core kernel Yaiwes/` (no volver a descargar — evidencia: Crazy Wall nodos 1-35)
APScheduler, Temporal, Azure-Durable-Functions, AWS-Step-Functions-DS-SDK, Dagu, Camunda, Hatchet, Apache-Airflow, Argo-Workflows, Burr, Apache-APISIX, Caddy, Cloudflare-Workers-SDK, Celery, BullMQ(⚠️reparando), Cedar, Casbin, Cerbos, Ajv, Cerberus, BAML, Chroma, pgvector, PostgreSQL, Redis, gVisor, ClawHub, Anthropic-Skills, AG2, Agno, Agenta, CodeUltraFeedback, AI-Scientist, AI-Scientist-v2, Coconut, Workalendar.

## Estado
Fase 1 (A+B, 23 componentes): **aprobada, lista para Salida 4**
Fase 2 (22 componentes): **en reserva, no tocar hasta activación explícita**
