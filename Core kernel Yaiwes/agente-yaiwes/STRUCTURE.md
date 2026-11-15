# agente-yaiwes — estructura materializada (S1 2026-08-26)

Scaffold ampliado según PLAN_100 + nodos Paso 3.  
ESQ/MIX = PLACEHOLDER.md + PENDIENTE_CODE. REF = SOURCE.md.  
Wordflow: `extensions/wordflow` = LEGACY operativo en main.

```text
agente-yaiwes/
├── README.md
├── STRUCTURE.md
├── PLAN_100_ESTRUCTURA_DEFINITIVA.md
├── code-programming-engine/
│   ├── SOURCE.md
│   ├── engine-modules/
│   ├── code-path-execution/
│   ├── standards-forensic/
│   ├── schema-contracts-io/
│   ├── external-motor-bridge/
│   ├── multi-account-bridge/
│   ├── inbox-normalization/
│   └── module-tests/
├── kernel-principal/
│   ├── control-layer/SOURCE.md
│   ├── extension-kernel/ (abi-mount, capability-registry, capability-passport, native-learning, mount-guard)
│   ├── reasoning-kernel/ (decision-on-demand, expert-panel-router, consensus-trigger, goal-dual-driver, workflow-capacity)
│   ├── resource-governance/ (resource-broker-gate, lease-management, watchdog, circuit-breaker, retry-policy)
│   ├── internal-bus/
│   └── execution-manifest/
├── input-layer/ (cli-entry, route-entry, cross-tool-session-import, reception)
├── definition-registry/ (workflow-definition/*, schema-contracts, domain-specific-contracts, declared-dependency-catalog, authorization-model, agent/task/tool/skill-definition)
├── control-governance/ (sheriff-bridge, sentinel, council, forensic-core, verdict-authority, symbol-index-wiring-graph, pre-post-gates, closure-engine, quality-dag, gap_*, llm-control-deny, …)
├── multi-workflow-engine/ (shared-services/*, instances/workflow-1/*)
├── execution-orchestration/ (goal-lock, mission-planning, dag-executor, …)
├── execution-engine-pool/ (adapter-layer, auxiliary-role-agents, …)
├── deploy-publish/ (multi-account-registry, push-injection, deployment-target-selector, …)
├── state-events-durability/
├── observability/
├── agent-fleet-parallelism/
├── human-in-the-loop/
├── communication-notifications/
├── control-plane-ui/
├── tools-models-memory-knowledge/
├── security-auth/
├── codebase-intelligence/
├── artifact-output-storage/
├── extensions/ (wordflow-engine-module SOURCE, wordflow-kernel-module SOURCE, source-evolution-module)
├── PIPELINE/SOURCE.md
└── agents/SOURCE.md
```

**S1 PASS** — estructura raíz materializada. Organización de código real = S4–S10.
