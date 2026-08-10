# PIPELINE 25 — MVP 4 Objetivos · Status consolidado

**Fecha claim:** 2026-08-10  
**Repo:** maxbry123-commits/agentes  
**llm_control:** DENY en todas las extensiones

---

## Objetivo 1 — Extensión kernel / capa de control

| Pieza | Path | Estado |
|-------|------|--------|
| Control layer motor | `control-layer/` | DONE (Fase1 A1–A11) |
| project_bootstrap (docs nativos KTP) | `extensions/project_bootstrap/` | DONE |
| Enchufe v2 / ficha | control-layer ficha.v2 + manifests | DONE |
| Audit forensic | `extensions/audit_forensic/` | DONE (75 tests) |

## Objetivo 2 — Wordflow (InputBlock → Council → main_12)

| Pieza | Path | Estado |
|-------|------|--------|
| InputBlock + quality_bar | `extensions/wordflow/` | DONE |
| Goals 12IN/12OUT | store/goals_catalog.yaml | DONE |
| Refute L1-L3 + Repair R1-R6 | engine/refute_repair.py | DONE |
| Sentinel + Council 12 | engine/sentinel.py, council.py | DONE |
| main_12 loop | engine/main_loop.py | DONE |
| VersionSelector + Cursor hooks | DONE |
| Tests | 57 PASSED | DONE |
| PIPELINE | 22_WORDFLOW_CORE_STATUS.md | DONE |

## Objetivo 3 — Adquisición determinista de sources

| Pieza | Path | Estado |
|-------|------|--------|
| VersionPin + Registry | `extensions/source_evolution/` | DONE |
| Fetch planner + FakeFetcher | DONE |
| License gate PASS/DIRECTOR/STOP | DONE |
| Install planner (LOCAL_ARTIFACT) | DONE |
| Provenance (no secrets) | DONE |
| Tests | 30 PASSED | DONE |
| PIPELINE | 23_SOURCE_EVOLUTION_STATUS.md | DONE |

## Objetivo 4 — Publicación GitHub controlada por Wordflow

| Pieza | Path | Estado |
|-------|------|--------|
| Publish contract token_ref | `extensions/github_publisher/` | DONE |
| FakeGitHubPort + run_publish | DONE |
| BUILD → publish bridge | engine/bridge.py | DONE |
| Tests | 9 PASSED | DONE |
| PIPELINE | 24_GITHUB_PUBLISHER_STATUS.md | DONE |

---

## Flujo transversal

```
InputBlock → Wordflow main_12 → tasks/BUILD
    → SourceEvolution (si falta capability)
    → GitHubPublisher (token_ref → commit)
    → AuditForensic (EvidencePacket → P0-P3 → verdict)
```

## CI workflows

- test-control-layer.yml
- test-project-bootstrap.yml
- test-audit-forensic.yml
- test-wordflow.yml
- test-source-evolution.yml
- test-github-publisher.yml

## Fuera de este MVP (explícito)

- Fase 4 loops Minimax/Kimi (diferido)
- Real git/hf/GitHub API adapters (runtime)
- L2–L8 contracts formales (Fase2 B0–B8)
- 85 contratos completos

## Veredicto interno

MVP de los 4 objetivos **materializado en código + tests offline + CI yaml**.  
Pendiente solo adapters de red reales y evidencia CI run independiente.
