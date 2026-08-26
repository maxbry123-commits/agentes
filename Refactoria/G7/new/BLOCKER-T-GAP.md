# BLOCKER-T-GAP — G7

**Gap:** OpenClaw/Hermes real bodies
**Status:** BLOCKED / OPEN

## Problem
The task requires a real OpenClaw/Hermes body only when acquire source or equivalent implementation is actually present in the repository. The audited engine layer currently provides `EnginePort` plus `openclaw_stub.py` and `hermes_stub.py`; no acquired body is materialized under `agents/OpenClaw` or `agents/Hermes` on `main`.

## Source evidence
- Engine contract: `extensions/wordflow_kernel/engines/port.py`
- Current bodies: `extensions/wordflow_kernel/engines/openclaw_stub.py`, `extensions/wordflow_kernel/engines/hermes_stub.py`
- Acquisition workflows exist: `.github/workflows/acquire-openclaw.yml`, `.github/workflows/acquire-hermes.yml`
- Current `agents/` tree contains only `.gitkeep`; therefore acquisition has not materialized the source on `main`.
- Existing work product: `Refactoria/G7/new/engine_port_contract.json`

## Impact
Implementing a body without acquired source would violate NO_INVENTAR and the explicit source-only requirement.

## Recommended action
Run the existing acquisition workflows externally through GitHub Actions, verify the resulting pinned source snapshots are committed to `main`, then repeat Refactoria source→new, triple verification, integration tests, and cross-check. Do not treat the workflow definition itself as body source.

## Decision
Do not fabricate OpenClaw/Hermes bodies. G7 remains OPEN until the pinned source is actually materialized and verified in `main`.
