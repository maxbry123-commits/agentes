# SKILL — WORDFLOW LOOP YAIWES — LAYERED 95/5

**State:** initial implemented skeleton / fail-closed  
**Work root:** `➡️📂 Wordflow LOOP Yaiwes/`  
**Source basis used for this version:** only `Readme arquitectura Yaiwes/`.

## Objective
Build the Wordflow as replaceable layers, never a monolith. Each layer has one responsibility, a Python module, a contract, evidence rules and explicit handoff.

## 95/5 policy
- 95% target: deterministic Python, schemas, hashes, AST, manifests, allowlists, DAG, tests.
- 5% maximum: optional LLM for bounded ambiguity/ranking/summary.
- LLM cannot mutate repositories, grant authorization, fabricate evidence, or change architecture.

## Layer map
1. `L01_RESEARCH` — filter, dedup and rank evidence.
2. `L02_XRAY_DOCUMENTS` — four deterministic scans of documents.
3. `L03_XRAY_CODE` — static AST X-Ray of code; repository adapters search authorized Maxbry repos with priority to `Agentes-motores-Wordflow-YAIWES`.
4. `L04_COPY_MOVE` — hash-verified copy/move, blocked without Director approval.
5. `L05_DOWNLOAD_EXTRACT` — immutable source lock → tree inventory → selective extraction → GitHub Action request.
6. `L06_SOURCE_EVOLUTION` — `acquire → analyze → reuse` decision using REUSE/PATCH/ADAPTER/GENERATE_DELTA.

## Governance contract
`SHERIFF → VALIDATOR → SENTINEL → VERIFY → SUPERVISOR → JUDGE → GUARDIAN`.

## Source patterns reused, not copied as foreign code
- Download/extraction design: `Documentos arquitectura Yaiwes lote 1/Descargar y integrar la capacidades del agente rufo con el agente TEAM.md` (`f107fad7aff673516346ea3f04bed12808922801`): immutable commit/tree, complete inventory, selective extraction, adapters, tests.
- Evolution design: `PLAN_YAIWES_AGENTE_WORDFLOW.md` (`76db427aa5d3b45198e34697b4939a114553a03e`): `acquire_12, analyze_12, reuse_12 → extensions.source-evolution-module`.
- Core fail-closed contract: `Método obligatorio de trabajo para ai y agentes` (`aecbac8f6936ada9d61df9db83463be66bf1fe3d`) and `SKILL-ORQUESTACION-YAIWES.md` (`b3885e48e66749c0a695d0a305257e69588ea2eb`).

## Gate
This skill defines the runtime method. It does not authorize cross-repo moves or OSS extraction by itself. Those remain blocked until a literal node carries authorization and exact destination.
