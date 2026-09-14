# GRAPHIFY MVP INTEGRATION — WORDFLOW LOOP YAIWES

Status: `DIRECTOR_APPROVED_MVP / FAIL_CLOSED`

This file extends the mandatory agent prompt through `DIRECTOR-CODE-GRAPH-METHODS.md`. It does not replace DAGEngine, MavisPool, Graphiti, Fables, Sheriff, Validator, sandbox or final verification.

## 1. Purpose
Use Graphify as the project pre-analysis layer so agents read and relate less raw code manually.

Canonical acquired source:
- Source repo: `Graphify-Labs/graphify`
- Source commit: `23f2ffaa43fd12f25d9eabe91e6d184b5d89b474`
- Acquired/read-back location: `maxbry123-commits/osquestador-auditor/Graphify/`
- Acquisition commit: `8e1e0af23ae2114d7219dfc9fa91d20c9f9de737`
- Extracted files: `883`
- Extracted bytes: `17053233`
- Source/extracted tree SHA256: `4a60d754251731ac16b30e6e87ff44347477d6c55e24ac622d5a47ec3eda3735`
- Acquisition policy: canonical immutable download/extract motors, no LFS, read-back required.

## 2. Position in the LOOP

```text
INPUT files/repository/component
  -> Graphify deterministic project map
  -> graph.json + GRAPH_REPORT.md (+ graph.html for operator only)
  -> Sheriff/Validator source audit
  -> Ask Council against graph evidence
  -> architecture extraction
  -> generated_tasks + director_tasks
  -> DAGEngine dependencies/priorities
  -> placement A-G
  -> REUSE > PATCH > ADAPT > GENERATE
  -> adapter + Ficha v2 + Fables
  -> sandbox
  -> independent reviewer
  -> deterministic deploy/promote
  -> evidence + Crazy Wall
```

## 3. Allowed Graphify capabilities for MVP
1. Local deterministic code parsing through Tree-sitter/AST.
2. Map imports, calls, inheritance, references and cross-file relationships.
3. Generate/query `graph.json` instead of repeatedly grepping/re-reading the entire repository.
4. Use `graphify explain`, `graphify path` and scoped query functions where available.
5. Preserve distinction between `EXTRACTED` relations and `INFERRED` relations.
6. Use `GRAPH_REPORT.md` as untrusted analysis input, never as final proof by itself.
7. `graph.html` is optional operator visualization; it is not a source of truth.
8. Project-scoped Graphify skill may be used for supported coding agents only after the exact package/version/source is pinned and the sandbox gate passes.

## 4. Deterministic vs LLM boundary
- Code graph extraction is preferred in local/deterministic mode.
- If docs/PDF/media semantic processing needs an LLM/API, that output is tagged `INFERRED` and must not silently become executable truth.
- Scheduler, dependency ordering, authorization, placement gates, hashes, Fables validation, sandbox, deployment and final verification remain deterministic.

## 5. Separation of graph responsibilities
- `Graphify`: repository/document/code relationship map for pre-analysis and querying.
- `Graphiti`: temporal memory/context/provenance across agent/project history.
- `Graphology`: JS/TS in-memory graph structure for operator/UI use.
- `Sigma.js`: optional graph rendering.
- `DAGEngine`: authoritative task dependency graph and deterministic scheduling.
- `MavisPool`: execution pool / priority / dedup / parallel workers.

Graphify MUST NOT replace DAGEngine or become execution authority.

## 6. Fail-closed gates
Graphify output may enter the LOOP only when:
- source/version is pinned;
- graph generation completed without parser/runtime failure;
- `graph.json` exists and parses;
- input root/hash is recorded;
- no raw Graphify output grants authorization;
- inferred edges are distinguishable from extracted edges;
- the next Sheriff/Validator step independently checks claims required for mutation.

Failure result: `GRAPHIFY_PREANALYSIS_GAP` and continue with an authorized fallback analysis path; never fake PASS.

## 7. Minimal-code rule
Do not rewrite Graphify functionality inside YAIWES. Prefer:
1. package/CLI invocation;
2. a thin adapter only if required by Fables;
3. Ficha v2 registration;
4. sandboxed execution;
5. consume standard outputs.

Any custom parser/knowledge-graph code must prove a capability gap Graphify + existing Graphiti/Graphology/Tree-sitter cannot cover first.
