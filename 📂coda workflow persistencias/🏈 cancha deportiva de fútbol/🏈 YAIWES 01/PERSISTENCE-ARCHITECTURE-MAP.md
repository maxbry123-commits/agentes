# 01 — DeepAudit → CODA persistence link

## Source provenance

- Source: `lintsinghua/DeepAudit`
- Source commit: `324133fe60b540327d182fbb8c800aa65a613349`
- Download/extract tree SHA-256: `bcb29183c573e82813cfc2df623d20b2ad412b0abe6788de9607675f866a5f4c`
- Source files verified by download motor: 507

## Reusable architecture retained

The useful control-plane is the dynamic-agent core under `backend/app/services/agent/core/`. In particular the downloaded copy contains an executor with sequential/parallel/dependency-aware execution, a graph controller, persistent state support, circuit-breaker/fallback logic, messaging, registry and event/telemetry infrastructure.

These patterns are retained as design inputs for CODA task persistence. The benign link runtime is intentionally independent of the original security execution stack so persistence can be tested without loading the offensive tool surface.

## Surgical quarantine

`backend/app/services/agent/tools/__init__.py` was changed from a broad security-tool export surface to a fail-closed persistence-only surface. It no longer imports or exports sandbox execution, HTTP sandboxing, vulnerability-validation payloads, injection-specific test tools, fuzzing/generic code execution, external scanners, smart-scan functionality or vulnerability reporting.

`backend/app/services/agent/__init__.py` was also changed so importing the agent package does not automatically import the original reconnaissance, vulnerability-analysis or verification agents. It now exposes reusable state/message/event/collaboration primitives only.

The original downloaded files remain inside the provenance tree for inspection, but the transformed CODA path does not execute them.

## Persistence link

`code/coda_persistence/link.py` implements:

`LOAD STATE → VALIDATE → CHECKPOINT → SAFE TASK → VERIFY/RESULT → HANDOFF`

State writes are atomic JSON replacements, raw workflow/link identifiers are hashed before becoming filesystem paths, retries are bounded, completed work is idempotent on replay, and the only accepted task categories are research, code review, documentation, data transformation, mock/unit tests, reporting, checkpoint and handoff.

The next link is `02-CyberStrikeAI`.

## Test evidence

GitHub Actions run `34810287658`, job `103870094620`: **PASS**.

Four checks passed: checkpoint round-trip + handoff, idempotent resume, fail-closed rejection of an offensive task type after bounded retries, and state-path containment.
