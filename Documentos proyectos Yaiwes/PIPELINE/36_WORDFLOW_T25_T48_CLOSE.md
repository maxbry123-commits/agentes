# PIPELINE/36 — Cierre plan numerado T25–T48

**Fecha:** 2026-08-14  
**Repo:** maxbry123-commits/agentes  
**Precondición:** Gaps G1–G9 cerrados (PIPELINE/35) · T0–T24 hechos

---

## 1 · WAVE-4 Sheriff + Mission + Evidence

| ID | Entrega | Commit |
|----|---------|--------|
| T25 | sheriff_adapter 5 estados + gate_lock | https://github.com/maxbry123-commits/agentes/commit/9c194cb17d577f43e1741fe9628643828281cd30 |
| T26 | mission = GoalLock enforce | https://github.com/maxbry123-commits/agentes/commit/07398be657809d5e8e44aceaa6f87c071c74c4bd |
| T27 | evidence_graph | https://github.com/maxbry123-commits/agentes/commit/a4ebb75903e95895db495b1dc27f2a45dea3ba76 |
| T28 | wave4_runtime glue | https://github.com/maxbry123-commits/agentes/commit/d6cbebf304cf6d9f3275c04f1827b7e30dba2291 |

## 2 · WAVE-5 Expert Panel + Router

| ID | Entrega | Commit |
|----|---------|--------|
| T29 | expert_panel | https://github.com/maxbry123-commits/agentes/commit/77a15c6ed249e4ac240e661fe0ee539b94331b33 |
| T30 | expert_decision YAIWES | https://github.com/maxbry123-commits/agentes/commit/824b669c105b4425deb8506287c7fd4bab70d640 |
| T31 | expert_router | https://github.com/maxbry123-commits/agentes/commit/0527f2c4752eb736e25fa22629248259a37c5ac8 |
| T32 | wave5_runtime | https://github.com/maxbry123-commits/agentes/commit/651cac556fdad74fd2cecca0fb263ceb5c8539a3 |

## 3 · WAVE-6 Recovery + Publish + HF + DNA

| ID | Entrega | Commit |
|----|---------|--------|
| T33 | recovery engine | https://github.com/maxbry123-commits/agentes/commit/501118b1538cbdad08fb5a3308043f2184787627 |
| T34 | github_publisher (Obj.4) | https://github.com/maxbry123-commits/agentes/commit/6caa6e09bcd18288972fb86a8c78c28c872a8504 |
| T35 | hf_index | https://github.com/maxbry123-commits/agentes/commit/3c0ddbfe049b24be878d107629ee1dcd5a865893 |
| T36 | workflow_dna | https://github.com/maxbry123-commits/agentes/commit/0f1d992b3046cac40088da2fdb2deacd0cb7b5a3 |

## 4 · WAVE-7 Intent + KER + Env + CI

| ID | Entrega | Commit |
|----|---------|--------|
| T37 | capability_intent | https://github.com/maxbry123-commits/agentes/commit/228a4234f679c176b68ff94897a47896d5c63f74 |
| T38 | extension_registry | https://github.com/maxbry123-commits/agentes/commit/46e57492ae0003e228806604f3e1c4355ab115ee |
| T39 | environment_scan | https://github.com/maxbry123-commits/agentes/commit/b6db09a33c9b010c30292ced7a1da27c4c9d60bc |
| T40 | CI test-wordflow | https://github.com/maxbry123-commits/agentes/commit/feda1263c38fc837f6b468e5087188fd66448e94 |

## 5 · WAVE-8 Bootstrap + Handoff + Publish path + Microkernel + Brain + State + Orch

| ID | Entrega | Commit |
|----|---------|--------|
| T41 | bootstrap Kernel.start | https://github.com/maxbry123-commits/agentes/commit/6105eea4e189d23dd3ab5a5ddab418462fe37518 |
| T42 | dna_handoff | https://github.com/maxbry123-commits/agentes/commit/29fc198b555dbc9b9cb71d4cc525d150c666be34 |
| T43 | publish_path | https://github.com/maxbry123-commits/agentes/commit/af38a02938dba0e78a8078cd9796ad4297d066c6 |
| T44 | microkernel_install planner | https://github.com/maxbry123-commits/agentes/commit/c90d8053224c05228441c539263f330eca52fac9 |
| T45 | capability_brain | https://github.com/maxbry123-commits/agentes/commit/a3ef5a39a0ca4aa959d51393f5b71b299bb5bad3 |
| T46 | state_authority | https://github.com/maxbry123-commits/agentes/commit/32f4a281467d0d112103160970d45137e016a14e |
| T47 | orchestrator | https://github.com/maxbry123-commits/agentes/commit/126d2232fca53a5e0a9fadc8aeffdce222767016 |
| T48 | este documento | (este commit) |

---

## 6 · Conteo

| Bloque | Hecho |
|--------|-------|
| T0a–T0q | 17 |
| T1–T24 (sin T3) | 23 |
| T25–T48 | 24 |
| **Total numerado hecho** | **~64** |
| T3 diferido | 1 |
| Post-Wordflow (HF real, OC/Hermes real, SSH real) | pendiente |

---

## 7 · Aún diferido (no numerado o T3)

1. T3 wire real OpenClaw/Hermes (solo puertos Fake hoy)  
2. HF fetch real + microkernel download  
3. SSH/Docker real workers  
4. control-layer CompilePlan Sheriff C00 full path from Wordflow  
5. CI run verde evidencia independiente (workflow existe)  

---

## 8 · Flujo canónico actual

```
InputContract → loop_bridge → GoalLock
  → Mission.enforce → SheriffAdapter
  → CapabilityBrain / ExpertRouter → YAIWES decide
  → ExecutionFacade (Bus|Resource)
  → ParallelFacadeRuntime
  → DNA handoff / GitHubPublisher (dry_run)
  → StateAuthority
Orchestrator.run_turn()  # glue
```

**T48 DONE — plan numerado T25–T48 cerrado en bitácora.**  
