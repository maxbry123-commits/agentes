# Wordflow LOOP YAIWES — layered runtime

A small, non-monolithic workflow runtime for YAIWES. The control path is mostly deterministic Python; LLM use is optional, isolated and capped at 5%.

## Why this exists
The YAIWES sources require modular growth, fail-closed evidence, reuse before generation, exact destinations before mutation, and no monolithic kernel fusion. This runtime turns those rules into separate layers and separate governance gates.

## Architecture

```text
INPUT BLOCK literal
      │
      ▼
SHERIFF → VALIDATOR
      │
      ▼
┌──────────────────────────────────────────┐
│ L01 Research                             │
│ L02 X-Ray documents                     │
│ L03 X-Ray code/repos                    │
│ L04 Copy/Move                           │
│ L05 Download/Extract OSS                │
│ L06 Source Evolution                    │
└──────────────────────────────────────────┘
      │
      ▼
SENTINEL → VERIFY → SUPERVISOR → JUDGE → GUARDIAN
      │
      ▼
PASS + EVIDENCE | GAP → reinject failed delta
```

Each layer is a separate Python file. Governance is also split by role.

## Tree

```text
wordflow_loop/
├── README.md
├── pyproject.toml
├── contracts/
│   ├── workflow.dsl.yaml
│   └── workflow.schema.json
├── prompts/
│   └── SYSTEM_PROMPT.md
├── skills/
│   └── SKILL-WORDFLOW-LOOP.md
├── wordflow_loop/
│   ├── contracts.py
│   ├── ledger.py
│   ├── llm_gate.py
│   ├── runner.py
│   ├── governance/
│   │   ├── sheriff.py
│   │   ├── validator.py
│   │   ├── sentinel.py
│   │   ├── verifier.py
│   │   ├── supervisor.py
│   │   ├── judge.py
│   │   └── guardian.py
│   └── layers/
│       ├── layer_01_research.py
│       ├── layer_02_xray_documents.py
│       ├── layer_03_xray_code.py
│       ├── layer_04_copy_move.py
│       ├── layer_05_download_extract.py
│       └── layer_06_source_evolution.py
└── tests/
    ├── test_core.py
    └── test_layers.py
```

## Determinism 95 / LLM 5

The runtime does not require an LLM. `LLMGate` is injected only for:
- ambiguity resolution;
- semantic ranking after deterministic filtering;
- bounded summary.

It is denied when the declared work ratio would exceed 5%. LLM output cannot authorize writes or supply missing evidence.

## The two YAIWES systems reused as README-level patterns

### 1. Deterministic download + extraction
Source: `Readme arquitectura Yaiwes/Documentos arquitectura Yaiwes lote 1/Descargar y integrar la capacidades del agente rufo con el agente TEAM.md`.

Pattern adopted:

```text
SOURCE LOCK (repo + immutable commit + tree)
→ complete tree/inventory
→ X-Ray
→ selective extraction
→ adapter
→ test
→ evidence
→ publish
```

This Wordflow copies the **system pattern**, not Ruflo or another foreign kernel.

### 2. Source evolution
Source: `Readme arquitectura Yaiwes/Documentos arquitectura Yaiwes lote 1/PLAN_YAIWES_AGENTE_WORDFLOW.md`.

The plan maps:

```text
acquire_12 + analyze_12 + reuse_12
→ extensions.source-evolution-module
```

This becomes `L06_SOURCE_EVOLUTION`: reuse first, then small patch, then adapter, and only then generate the missing delta.

## Layer responsibilities

### L01 — Research
Accept candidates from injected search adapters, require real URL+snippet+source class, deduplicate and rank official code / Maxbry repos before secondary sources.

### L02 — Document X-Ray
Four passes: literal requirements → architecture/path anchors → code anchors → cross-check queue. It never invents semantics when deterministic extraction is insufficient.

### L03 — Code X-Ray
Python AST only: symbols, imports, stubs and dangerous calls. Candidate code is not executed during inspection.

Repository search adapters should prioritize:
1. `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`;
2. Router Inteligente repository once exact repository identity is resolved;
3. `maxbry123-commits/agentes`;
4. remaining authorized Maxbry repositories.

### L04 — Copy / Move
No approval = `BLOCKED`. With approval: read source → verify hash → write destination → verify destination hash → optional source delete for move → evidence.

### L05 — OSS Download / Extract
No floating `main/latest` as identity. Requires immutable commit/tree SHA. Builds a normalized tree and selective extraction manifest. GitHub Action dispatch remains blocked until authorization.

### L06 — Source Evolution
Deterministic ladder: `REUSE → PATCH_SMALL → ADAPTER → GENERATE_DELTA`; unsafe existing code is rejected.

## Governance roles

- **Sheriff:** freezes literal+hash and mutation authority.
- **Validator:** validates DAG dependencies and allow/deny rules.
- **Sentinel:** runtime timeout and action scope.
- **Verifier:** blocks PASS without real evidence.
- **Supervisor:** cross-checks node/layer/path scope.
- **Judge:** binary closure logic; open gaps cannot PASS.
- **Guardian:** ledger integrity and mutation policy.

## Safety
- No `exec()` of candidate source for X-Ray.
- No blind import of an OSS repository.
- No cross-repo write without exact allowlist + Director approval.
- No `VERIFIED_CLOSED` from documents, folders, mocks or stubs.
- Legacy/hot path remains untouched until parity tests exist.

## Current status
`INITIAL_LAYERED_RUNTIME / NOT_YET_CONNECTED_TO_REAL_GITHUB_ACTIONS_OR_LLM_PROVIDER`.

The code establishes the contracts and deterministic mechanics. Real repository adapters, Action dispatch and any provider LLM connection must be added as separately authorized layers/adapters and verified with runtime evidence.
