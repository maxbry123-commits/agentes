# BLOCKER-T-GAP — G6

**Gap:** real intelligence adapters
**Status:** BLOCKED / OPEN

## Problem
The task requires a real adapter only when a real client/SDK/source exists in the repository. The audited `gateway/intelligence.py` exposes the existing gateway contract, but no provider SDK/client implementation sufficient to create a production Claude Code/Codex/OpenHands/OpenCode/Aider/Cline adapter was verified.

## Source evidence
- Existing gateway contract: `extensions/wordflow_kernel/gateway/intelligence.py`
- Existing destination: `agente-yaiwes/execution-engine-pool/adapter-layer/`
- Existing work product: `Refactoria/G6/new/intelligence_adapter_contract.json`

## Impact
Creating an adapter without provider source would violate REUSE > PATCH > ADAPT > GENERATE and NO_INVENTAR.

## Recommended action
Acquire/commit a real provider client/SDK source under the repository with a pinned version/commit, then repeat Refactoria source→new, triple verification, integration test and cross-check.

## Decision
Do not integrate a fake provider adapter. G6 remains OPEN until source/SDK evidence exists.
