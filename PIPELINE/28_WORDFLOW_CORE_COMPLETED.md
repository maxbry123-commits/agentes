# PIPELINE 28 — Wordflow Core COMPLETED (W1–W9)

**Fecha claim:** 2026-08-14  
**Repo:** maxbry123-commits/agentes  
**Extensión:** `extensions/wordflow/`  
**llm_control:** DENY  
**Alcance:** Wordflow **core** 100% (no incluye retry/recovery/evolution, C10, skill_compiler)

---

## Commits del bloque W1–W9

| ID | Commit | Entrega |
|----|--------|--------|
| W1 | `9184dce0…` | architecture_output + code_output schemas |
| W2 | `da2f0a96…` | evidence_bridge + S10 formal |
| W3 | `50eb92ce…` | watchdog.py |
| W4 | `b6e37a40…` | supervisor.py |
| W5 | `7abc0a7e…` | policies/sheriff + sentinel |
| W6 | `9681790e…` | wire main_loop S05/S11 |
| W7 | `294089a1…` | ficha.v2.json |
| W8 | `1a38c344…` | tests/test_w_gaps.py |
| W9 | *(este commit)* | claim + PIPELINE 28 |

**BASE pre-W1:** `7c1c2070…`  
**FINAL (W8):** `1a38c344cef7b2a9e3afb3ed3472498817983660`

---

## Tree verificado (45 blobs bajo extensions/wordflow/)

### Engine
- evidence_bridge.py · watchdog.py · supervisor.py · main_loop.py (wired)
- input_normalizer · goals_extractor · refute_repair · sentinel · council
- entrypoint · state_store · version_selector · cursor_hooks

### Schemas
- input_block.schema.json
- architecture_output.schema.json
- code_output.schema.json

### Policies + ABI
- policies/sheriff.yaml · policies/sentinel.yaml
- ficha.v2.json (abi_version 2.0, mount_mode sidecar, llm_control DENY)
- manifest.yaml

### Tests
- test_w_gaps.py (schemas, evidence, watchdog, supervisor, ficha, main_loop)
- tests previos (11 módulos)

---

## Gaps W1–W9 — estado

| Gap | Estado |
|-----|--------|
| Arch/Code schemas | CERRADO W1 |
| EvidencePacket formal | CERRADO W2 |
| watchdog | CERRADO W3 |
| supervisor TTL | CERRADO W4 |
| policies fail_closed | CERRADO W5 |
| wire main_loop | CERRADO W6 |
| ficha.v2 | CERRADO W7 |
| tests gaps | CERRADO W8 |
| claim | ESTE DOC |

---

## Fuera de este claim (explícito)

- loops/retry.yaml · recovery.yaml · evolution.yaml
- github_deploy C10 (Obj4)
- skill_compiler / acquire_12 (Obj3)
- CI run independiente de test_w_gaps (tests presentes; run = claim ejecutor)

---

## Veredicto

```
STATUS: COMPLETED (Wordflow core)
MIENTE: NO — paths y commits listados
Tests W8: materializados en GH; ejecución CI pendiente evidencia independiente
```

**Sustituye** el estado PARTIAL de PIPELINE 22 (SUPERSEDED) para el **core** Wordflow.  
PIPELINE 27 residual E2–E27 (SE / C10 / resource_brain) **sigue vigente** fuera de Wordflow.
