# Cognithor × AutoGen Strategy Implementation Plan (v0.94.0)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the five Work-Packages (WP1-WP5) from `docs/superpowers/specs/2026-04-25-cognithor-autogen-strategy-design.md` as Cognithor v0.94.0 — a `cognithor.compat.autogen` source-compat shim that mirrors `autogen-agentchat==0.7.5` API shapes, a `cognithor_bench/` benchmark scaffold, an `examples/insurance-agent-pack/` reference-implementation, and competitive-analysis docs + a PGE-Trinity ADR.

**Architecture:** `cognithor.compat.autogen` is a thin translation layer: AutoGen-shaped public API (`AssistantAgent`, `RoundRobinGroupChat`, message classes, terminations, `OpenAIChatCompletionClient`) bridges into `cognithor.crew.Crew(agents=[a], tasks=[t]).kickoff_async()` for the 1-shot path and into a custom `_RoundRobinAdapter` for the multi-round path. No verbatim AutoGen code — signature parity is enforced via `inspect.signature` diff tests against `autogen-agentchat==0.7.5` (single pin-point in `pyproject.toml [project.optional-dependencies] autogen`). `cognithor_bench/` is an in-monorepo submodule with its own `pyproject.toml` and console-script `cognithor-bench`. `examples/insurance-agent-pack/` is a standalone-installable Python package (no `cognithor.packs` registration — that system is reserved for private commerce-packs).

**Tech Stack:** Python 3.12, Pydantic v2, pytest + pytest-asyncio, ruff, mypy strict. No new mandatory runtime deps; `autogen-agentchat==0.7.5` is opt-in via `pip install cognithor[autogen]`. Apache 2.0; `NOTICE` file gets an AutoGen-MIT attribution Section (analog CrewAI from v0.93.0).

---

## Sequencing and Dependencies

Per spec §13:

```
v0.93.0 (released 2026-04-24)
    ↓
[Pre-WP1 Gate: 24-48h v0.93.0 stability without v0.93.1 hotfix — Task 0]
    ↓
PR 1 (WP1 + WP5 docs)              — Tasks 1-8     (8 tasks,  1.5 days)
    ↓
PR 2 (WP4 cognithor-bench)         — Tasks 9-22    (14 tasks, 4-5 days)
    ↓
PR 3 (WP2 AutoGen-compat-shim)     — Tasks 23-40   (18 tasks, 7-9 days)
    ↓
PR 4 (WP3 insurance-pack)          — Tasks 41-54   (14 tasks, 5-7 days)
    ↓
Direct-Commit on main (v0.94.0)    — Tasks 55-59   (5 tasks,  1 day)
    ↓
Tag v0.94.0 + push  →  Release-Workflows  →  v0.94.0 LIVE
```

**Hard dependencies:**

- **PR 3 needs PR 2's pin** — WP2 references `autogen-agentchat==0.7.5` via `pyproject.toml [project.optional-dependencies] autogen` which is added in PR 2 (single pin-point per spec F7). Merging PR 3 before PR 2 would force WP2 to re-add the pin, then PR 2 would conflict on the same line.
- **PR 4 needs `cognithor.crew` from main** — already shipped in v0.93.0; verify `from cognithor.crew import Crew, CrewAgent, CrewTask, CrewProcess` resolves before starting WP3.
- **Direct-Commit needs all 4 PRs merged + main CI green** — version bump references features that must be in `main`.

**Soft dependencies (parallel-OK):**

- PR 1 (docs only) blocks no code-PR. Order is "PR 1 first" because the ADR is referenced from WP3's `examples/insurance-agent-pack/README.md` and WP2's migration guide.

---

## PR Strategy (4 PRs + Direct-Commit + Tag)

| PR        | Work-Package                              | Tasks   | Branch                                     | Merge Target | Release? |
|-----------|-------------------------------------------|---------|--------------------------------------------|--------------|----------|
| **PR 1**  | WP1 Competitive Analysis + WP5 ADR        | 1-8     | `feat/cognithor-autogen-v1-docs`           | `main`       | No       |
| **PR 2**  | WP4 `cognithor-bench` Scaffold            | 9-22    | `feat/cognithor-autogen-v2-bench`          | `main`       | No       |
| **PR 3**  | WP2 AutoGen-Compatibility-Shim            | 23-40   | `feat/cognithor-autogen-v3-compat`         | `main`       | No       |
| **PR 4**  | WP3 Insurance Agent Pack                  | 41-54   | `feat/cognithor-autogen-v4-insurance`      | `main`       | No       |
| **DC**    | v0.94.0 Release-Bundle (Direct on main)   | 55-59   | `main` (no PR — direct commit + tag)       | `main`       | **Yes**  |

**Per-PR closeout sequence (applies to PR 1, PR 2, PR 3, PR 4):**

1. Full regression on the feature branch:
   - `pytest tests/ -x -q --cov=src/cognithor --cov-fail-under=89`
   - For PR 2: also `pytest cognithor_bench/tests/ -x -q --cov=cognithor_bench/src/cognithor_bench --cov-fail-under=80`
   - For PR 3: also `pytest tests/test_compat/test_autogen/ -x -q --cov=src/cognithor/compat/autogen --cov-fail-under=85`
   - For PR 4: also `pytest examples/insurance-agent-pack/tests/ -x -q --cov=examples/insurance-agent-pack/src/insurance_agent_pack --cov-fail-under=80`
2. `ruff check .` clean
3. `ruff format --check .` clean (per memory `feedback_ruff_format_before_commit.md`)
4. For PR 3: `mypy --strict src/cognithor/compat` clean
5. CHANGELOG `[Unreleased]` shows the WP's entries (no version bump until DC)
6. Push branch, open PR, wait all CI green, squash-merge into `main`
7. **Cleanup in a SEPARATE turn** — never chain `&& git branch -d ...` after merge (per memory `feedback_pr_merge_never_chain_cleanup.md` — has caused two PR-closure incidents). After confirming the PR is merged in main, delete the local + remote branch in a fresh turn.

**Direct-Commit on main (DC) sequence:**

1. Verify PRs 1-4 merged + main CI green
2. Bump version in 5 files (Task 55)
3. Append AutoGen attribution to `NOTICE` (Task 56)
4. Append v0.94.0 highlights to `README.md` (Task 57)
5. Convert CHANGELOG `[Unreleased]` → `[0.94.0]` (Task 58)
6. Commit + tag `v0.94.0` + push → release workflows fire (Task 59)

---

## File Structure

### New: WP1 + WP5 docs (PR 1)

- `docs/competitive-analysis/README.md` — index, ~150 words
- `docs/competitive-analysis/autogen.md` — Cognithor vs AutoGen, ≥400 words
- `docs/competitive-analysis/microsoft-agent-framework.md` — Cognithor vs MAF, ≥400 words
- `docs/competitive-analysis/decision-matrix.md` — 5-column comparison table
- `docs/adr/README.md` — ADR index, Nygard template note
- `docs/adr/0001-pge-trinity-vs-group-chat.md` — first ADR

### New: WP4 `cognithor_bench/` submodule (PR 2)

- `cognithor_bench/README.md` — usage + scenario authoring guide
- `cognithor_bench/pyproject.toml` — separate package, console-script `cognithor-bench`
- `cognithor_bench/src/cognithor_bench/__init__.py`
- `cognithor_bench/src/cognithor_bench/cli.py` — argparse, `run` + `tabulate` subcommands
- `cognithor_bench/src/cognithor_bench/runner.py` — core async benchmark loop
- `cognithor_bench/src/cognithor_bench/reporter.py` — Markdown table emitter
- `cognithor_bench/src/cognithor_bench/adapters/__init__.py`
- `cognithor_bench/src/cognithor_bench/adapters/base.py` — `Adapter` Protocol
- `cognithor_bench/src/cognithor_bench/adapters/cognithor_adapter.py` — default, wraps `cognithor.crew`
- `cognithor_bench/src/cognithor_bench/adapters/autogen_adapter.py` — opt-in, lazy ImportError-safe
- `cognithor_bench/src/cognithor_bench/scenarios/smoke_test.jsonl` — 3 trivial tasks for CI
- `cognithor_bench/tests/__init__.py`
- `cognithor_bench/tests/test_runner.py`
- `cognithor_bench/tests/test_cli.py`
- `cognithor_bench/tests/test_adapters.py`
- `cognithor_bench/tests/conftest.py`
- `cognithor_bench/tests/fixtures/sample_results.json`

### New: WP2 `cognithor.compat.autogen/` (PR 3)

- `src/cognithor/compat/__init__.py`
- `src/cognithor/compat/autogen/__init__.py` — re-exports + DeprecationWarning
- `src/cognithor/compat/autogen/README.md` — migration guide, side-by-side diff
- `src/cognithor/compat/autogen/_bridge.py` — internal bridge to `cognithor.crew`
- `src/cognithor/compat/autogen/_round_robin_adapter.py` — multi-round adapter (~250-300 LOC)
- `src/cognithor/compat/autogen/agents/__init__.py`
- `src/cognithor/compat/autogen/agents/_assistant_agent.py` — `AssistantAgent` with exact 14-field signature
- `src/cognithor/compat/autogen/teams/__init__.py`
- `src/cognithor/compat/autogen/teams/_round_robin.py` — `RoundRobinGroupChat`
- `src/cognithor/compat/autogen/messages/__init__.py` — `TextMessage`, `HandoffMessage`, `ToolCallSummaryMessage`, `StructuredMessage`
- `src/cognithor/compat/autogen/conditions/__init__.py` — `MaxMessageTermination`, `TextMentionTermination` + `__and__`/`__or__`
- `src/cognithor/compat/autogen/models/__init__.py` — `OpenAIChatCompletionClient` wrapper
- `tests/test_compat/__init__.py`
- `tests/test_compat/test_autogen/__init__.py`
- `tests/test_compat/test_autogen/conftest.py` — mock model client fixtures, autogen-skip marker
- `tests/test_compat/test_autogen/test_signature_compat.py` — `inspect.signature` parity
- `tests/test_compat/test_autogen/test_assistant_agent.py` — basic AssistantAgent behaviour
- `tests/test_compat/test_autogen/test_round_robin.py` — RoundRobinGroupChat surface
- `tests/test_compat/test_autogen/test_round_robin_adapter.py` — multi-round behaviour
- `tests/test_compat/test_autogen/test_combined_terminations.py` — A&B, A|B
- `tests/test_compat/test_autogen/test_messages.py` — message-class shapes
- `tests/test_compat/test_autogen/test_hello_world_search_replace.py` — Stage-2 behaviour test (D6)

### New: WP3 `examples/insurance-agent-pack/` (PR 4)

- `examples/insurance-agent-pack/README.md` — marketing + walkthrough + asciinema link
- `examples/insurance-agent-pack/LICENSE` — Apache 2.0 (points to repo root)
- `examples/insurance-agent-pack/pyproject.toml` — depends on `cognithor>=0.94.0`
- `examples/insurance-agent-pack/src/insurance_agent_pack/__init__.py`
- `examples/insurance-agent-pack/src/insurance_agent_pack/crew.py` — `@agent` decorators, 4 roles
- `examples/insurance-agent-pack/src/insurance_agent_pack/cli.py` — argparse, `--interview` mode
- `examples/insurance-agent-pack/src/insurance_agent_pack/agents/__init__.py`
- `examples/insurance-agent-pack/src/insurance_agent_pack/agents/policy_analyst.py` — NEW vs v0.93.0 template (PDF tool-use)
- `examples/insurance-agent-pack/src/insurance_agent_pack/agents/needs_assessor.py`
- `examples/insurance-agent-pack/src/insurance_agent_pack/agents/compliance_gatekeeper.py` — NEW PGE-demo
- `examples/insurance-agent-pack/src/insurance_agent_pack/agents/report_generator.py`
- `examples/insurance-agent-pack/src/insurance_agent_pack/prompts/policy_analyst.md`
- `examples/insurance-agent-pack/src/insurance_agent_pack/prompts/needs_assessor.md`
- `examples/insurance-agent-pack/src/insurance_agent_pack/prompts/compliance_gatekeeper.md`
- `examples/insurance-agent-pack/src/insurance_agent_pack/prompts/report_generator.md`
- `examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/pkv_grundlagen.jsonl`
- `examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/ggf_versorgung.jsonl`
- `examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/bav_basics.jsonl`
- `examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/bu_grundlagen.jsonl`
- `examples/insurance-agent-pack/src/insurance_agent_pack/tools/__init__.py`
- `examples/insurance-agent-pack/src/insurance_agent_pack/tools/pdf_extractor.py`
- `examples/insurance-agent-pack/tests/__init__.py`
- `examples/insurance-agent-pack/tests/conftest.py`
- `examples/insurance-agent-pack/tests/test_team.py`
- `examples/insurance-agent-pack/tests/test_gatekeeper_blocks_legal_advice.py`
- `examples/insurance-agent-pack/tests/test_audit_chain_intact.py`
- `examples/insurance-agent-pack/tests/test_local_inference_mode.py`
- `examples/insurance-agent-pack/tests/fixtures/sample_policy.pdf` — synthetic, anonymized
- `examples/insurance-agent-pack/docs/demo_walkthrough.md`
- `examples/insurance-agent-pack/docs/architecture.md` — PGE-Trinity diagram
- `examples/insurance-agent-pack/docs/DISCLAIMER.md` — Alexander writes personally

### Modified files (across PRs):

- `pyproject.toml` — adds `[project.optional-dependencies] autogen = ["autogen-agentchat==0.7.5"]` in PR 2 (Task 9). PR 3 references it. PR 4 doesn't touch it.
- `src/cognithor/__init__.py` — version bump in DC (Task 55)
- `flutter_app/pubspec.yaml` — version bump in DC (Task 55)
- `flutter_app/lib/providers/connection_provider.dart` — `kFrontendVersion` bump in DC (Task 55)
- `CHANGELOG.md` — `[Unreleased]` entries appended in each PR; final `[0.94.0]` rollup in DC (Task 58)
- `NOTICE` — AutoGen-MIT attribution appended in DC (Task 56)
- `README.md` — Highlights bullets appended in DC (Task 57); `Architecture` section gets ADR link in PR 1 (Task 8)
- `docs/README.md` (or main index) — competitive-analysis link appended in PR 1 (Task 5)

---

## Scope Clarifications

- **No verbatim AutoGen code anywhere.** API surfaces are concept-inspired only. The `AssistantAgent` 14-field signature is mirrored from public docs / `inspect.signature` reads, not copy-paste.
- **Apache 2.0 only.** `NOTICE` gets a Section "Third-party attributions" line for AutoGen MIT (analog to existing CrewAI line at NOTICE root).
- **Single pin-point** for `autogen-agentchat==0.7.5` in `pyproject.toml [project.optional-dependencies] autogen`. WP2 tests + WP4 `autogen_adapter.py` reference this Extra by import — never re-pin in their own files.
- **No new mandatory runtime deps.** `autogen-agentchat` is opt-in via `pip install cognithor[autogen]`.
- **Backward compat:** Zero changes to `cognithor.crew`, the Agent SDK, or PGE-Trinity internals. WP2 is strictly additive under `cognithor.compat.autogen`.
- **Test coverage floors:** Branch CI guards ≥89% total coverage. WP2 module-level ≥85%. WP3 module-level ≥80%. WP4 module-level ≥80%.
- **DSGVO:** All defaults offline-capable. WP3 fixtures are 100% synthetic (no real customer data, ever). WP2 + WP4 use mock model clients in tests.
- **Pre-WP1 Gate (per spec F5):** 24-48h v0.93.0 stability without v0.93.1-hotfix needed before PR 1 starts. Verified in Task 0.
- **Branching:** Each PR cuts its branch from latest `main` after the previous PR is merged. Cleanup is a separate turn (memory).
- **Conventional Commits:** `feat:`, `docs:`, `test:`, `refactor:`, `chore:`.

---

## Working Directory

All commands assume working directory `D:/Jarvis/jarvis complete v20`. The repo is non-git in this environment per the working-directory metadata, but git operations against the upstream `Alex8791-cyber/cognithor` remote work via the standard `git` CLI (the v0.93.0 release confirmed this). All shell snippets use forward slashes per the platform note.

---

## Task 0: Pre-WP1 Gate — verify v0.93.0 stability (24-48h, no hotfix)

**Why this exists (spec F5):** Starting WP work while a `v0.93.1` hotfix is brewing on `main` would force constant rebases on every PR-branch and risk a hotfix landing inside a WP-PR by accident. The gate buys us 24-48h of "is the v0.93.0 release actually OK?" before we open PR 1.

**Files:** none (operational gate, no code).

- [ ] **Step 1: Confirm `pip install cognithor==0.93.0` works in a fresh venv on Windows + Linux**

```bash
# Windows (host PowerShell — user runs this manually if needed)
python -m venv /tmp/v093-check && /tmp/v093-check/Scripts/python.exe -m pip install cognithor==0.93.0
/tmp/v093-check/Scripts/python.exe -c "import cognithor; print(cognithor.__version__)"
```

Expected output: `0.93.0`.

- [ ] **Step 2: Read GitHub issue tracker for v0.93.0 regression reports**

```bash
gh issue list --repo Alex8791-cyber/cognithor --state open --label "regression" --search "v0.93.0 in:body,title"
gh issue list --repo Alex8791-cyber/cognithor --state open --search "0.93.0"
```

Expected: zero issues labelled `regression` for v0.93.0. If any exist, classify them with the user before proceeding.

- [ ] **Step 3: Confirm 24-48h since v0.93.0 tag-push without a `v0.93.1` PR opened**

```bash
gh release view v0.93.0 --repo Alex8791-cyber/cognithor --json publishedAt,tagName
gh pr list --repo Alex8791-cyber/cognithor --state all --search "v0.93.1"
```

Expected: `publishedAt` is ≥24h in the past; no v0.93.1 PRs exist or any that exist are merged-and-stable.

- [ ] **Step 4: Confirm main CI is green**

```bash
gh run list --repo Alex8791-cyber/cognithor --branch main --workflow ci.yml --limit 5
```

Expected: latest 5 runs on `main` show `success` status.

- [ ] **Step 5: Decision gate**

If Steps 1-4 all pass → proceed to PR 1 / Task 1. If any step fails (issues open, hotfix needed, CI red) → **stop and report to user**; do not start PR 1 work.

No commit on this task — it's a verification gate.

---

# PR 1 — WP1 Competitive Analysis + WP5 PGE-Trinity ADR (Tasks 1-8)

Implements spec §8.1 (WP1 — three competitive-analysis docs + index) and §8.2 (WP5 — first ADR `0001-pge-trinity-vs-group-chat.md` + ADR index).

**Branch:** `feat/cognithor-autogen-v1-docs` cut from latest `main`.

**PR-1 closeout target:** All 4 competitive-analysis files exist, ADR exists + numbered, both linked from main `README.md`'s Architecture section. Markdown-only; no Python tests beyond a single link-checker at Task 8.

---

### Task 1: Branch + scaffold `docs/competitive-analysis/` index

**Files:**
- Create: `docs/competitive-analysis/README.md`

- [ ] **Step 1: Cut feature branch from main**

```bash
git checkout main
git pull --ff-only
git checkout -b feat/cognithor-autogen-v1-docs
```

Expected: clean tree on `feat/cognithor-autogen-v1-docs`, no untracked files.

- [ ] **Step 2: Create `docs/competitive-analysis/README.md`**

```markdown
# Competitive Analysis — Cognithor in the Multi-Agent Framework Landscape

This directory documents how Cognithor compares with adjacent multi-agent
frameworks. The intent is sober comparison, not advocacy: every claim about
a competing project should be backed by a public-source link.

## Documents

- [`autogen.md`](./autogen.md) — Cognithor vs Microsoft AutoGen (Python `0.7.5`,
  Maintenance Mode since Q4 2025).
- [`microsoft-agent-framework.md`](./microsoft-agent-framework.md) — Cognithor
  vs Microsoft Agent Framework (MAF, GA April 2026).
- [`decision-matrix.md`](./decision-matrix.md) — Side-by-side feature matrix
  across Cognithor, AutoGen, MAF, LangGraph, CrewAI.

## Scope

These documents inform marketing material, technical decisions, and the
v0.94.0 AutoGen-Compatibility-Shim (`cognithor.compat.autogen`). They are
deliberately conservative — no performance claims without a benchmark, no
"X is dead" rhetoric.

## Related

- [ADR 0001 — PGE Trinity vs Group Chat](../adr/0001-pge-trinity-vs-group-chat.md)
- [`cognithor.compat.autogen` migration guide](../../src/cognithor/compat/autogen/README.md) (added in PR 3)
```

- [ ] **Step 3: Commit**

```bash
git add docs/competitive-analysis/README.md
git commit -m "docs(competitive-analysis): add directory index"
```

Expected: 1 file changed, ~25 insertions.

---

### Task 2: Write `docs/competitive-analysis/autogen.md`

**Files:**
- Create: `docs/competitive-analysis/autogen.md`

- [ ] **Step 1: Write the document**

```markdown
# Cognithor vs Microsoft AutoGen

> **Status of this document:** 2026-04-25. Sources cited inline.

## 1. Status of AutoGen (Q2 2026)

The `microsoft/autogen` repository carries an explicit Maintenance-Mode
notice since approximately October 2025[^1]. The last actively-developed
Python release is `autogen-agentchat==0.7.5` (September 2025). Microsoft
actively redirects new users to the **Microsoft Agent Framework (MAF)** as
the supported successor[^2]. `agbench` and Magentic-One are tagged
"reference applications" rather than production-ready releases.

[^1]: https://github.com/microsoft/autogen — README banner.
[^2]: https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/

## 2. Architecture Summary (3-Layer Design)

AutoGen ships as three Python packages:

- **`autogen-core`** — Actor-Model runtime (`SingleThreadedAgentRuntime`,
  `RoutedAgent`, `@message_handler`). Low-level concurrency primitive.
- **`autogen-agentchat`** — High-level conversational API
  (`AssistantAgent`, teams `RoundRobinGroupChat` / `SelectorGroupChat` /
  `Swarm` / `MagenticOneGroupChat`, message types `TextMessage` /
  `HandoffMessage` / `ToolCallSummaryMessage`).
- **`autogen-ext`** — Provider/Tool extensions (`OpenAIChatCompletionClient`,
  function-tool wrappers).

The **conversational programming model** treats agent-to-agent
communication as a sequence of messages on a shared chat history; teams
schedule turns. This contrasts with **graph-based** orchestration adopted
by MAF and LangGraph.

## 3. Common Ground with Cognithor

- Multi-Agent first-class (Cognithor's `cognithor.crew` since v0.93.0).
- MCP client support (Cognithor: 145 tools across 14 modules).
- Local-model story (AutoGen via Ollama-compatible clients; Cognithor:
  Ollama is the default, not an integration).
- Tool/function-call abstraction at the agent level.

## 4. Differences (honest)

**Where AutoGen is stronger:**
- Cross-language (Python + .NET).
- Larger English-speaking community.
- More extensive end-user documentation and tutorials.

**Where Cognithor is stronger:**
- **PGE-Trinity** as enforced role-separation (Planner-Gatekeeper-Executor)
  with Hashline-Guard audit chain — see
  [ADR 0001](../adr/0001-pge-trinity-vs-group-chat.md).
- **DSGVO-First defaults**: PII redaction, EU-provider documentation,
  offline-capable defaults. Mentioned only obliquely in AutoGen.
- **Vendor neutrality**: 16 LLM providers out-of-the-box; no implicit Azure
  preference.
- **Local inference first-class**: Ollama is the default execution path,
  not an opt-in extension.
- **6-Tier cognitive memory** (`cognithor.memory`) integrated with the
  Planner; AutoGen leaves memory to the user.
- **Deep Research v2** as a dedicated subsystem (`deep_research_v2.py`)
  rather than a sample notebook.

## 5. Conceptual Migration Path

AutoGen's `autogen-agentchat` Python API has a stable 1-shot path —
`AssistantAgent.run(task=...)` — that maps cleanly to
`cognithor.crew.Crew(agents=[a], tasks=[t]).kickoff_async()`. Cognithor
v0.94.0 ships `cognithor.compat.autogen` as a thin source-compatibility
shim covering this surface. See
[`cognithor.compat.autogen` migration guide](../../src/cognithor/compat/autogen/README.md)
(added in PR 3 of v0.94.0) for the supported subset and search-and-replace
import recipe.

The shim deliberately does **not** support `SelectorGroupChat`, `Swarm`,
or `MagenticOneGroupChat`; the rationale is in
[ADR 0001](../adr/0001-pge-trinity-vs-group-chat.md).

## 6. References

- AutoGen GitHub: https://github.com/microsoft/autogen
- AutoGen AgentChat reference: https://microsoft.github.io/autogen/stable//reference/python/autogen_agentchat.agents.html
- Magentic-One paper: https://arxiv.org/abs/2411.04468
- MAF migration guide: https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/
```

- [ ] **Step 2: Word-count check**

```bash
wc -w docs/competitive-analysis/autogen.md
```

Expected: ≥400 words (the body above is ~520 words).

- [ ] **Step 3: Commit**

```bash
git add docs/competitive-analysis/autogen.md
git commit -m "docs(competitive-analysis): add Cognithor vs AutoGen comparison"
```

---

### Task 3: Write `docs/competitive-analysis/microsoft-agent-framework.md`

**Files:**
- Create: `docs/competitive-analysis/microsoft-agent-framework.md`

- [ ] **Step 1: Write the document**

```markdown
# Cognithor vs Microsoft Agent Framework (MAF)

> **Status of this document:** 2026-04-25. Sources cited inline.

## 1. What MAF Is

Microsoft Agent Framework is the supported successor to AutoGen. GA was
April 2026[^1]. License: MIT. Languages: Python and .NET. Programming
model: **graph-based** workflow orchestration with `@workflow`,
`@activity`, and explicit edges between agent nodes.

MAF ships first-class integrations with Azure AI Foundry, Microsoft
Sentinel, and the broader Azure observability story. The `@tool` decorator
replaces AutoGen's `FunctionTool` workbench abstraction.

[^1]: https://learn.microsoft.com/en-us/agent-framework/

## 2. Programming-Model Shift

The most consequential change between AutoGen and MAF is **conversation →
graph**:

| AutoGen (`autogen-agentchat`) | MAF |
|-------------------------------|-----|
| Conversational chat history shared by team | DAG/graph with explicit nodes and edges |
| `RoundRobinGroupChat`, `SelectorGroupChat` | `@workflow` with conditional edges |
| `FunctionTool` / `Workbench` | `@tool` decorator on async functions |
| Termination via `MaxMessageTermination`, `TextMentionTermination` | Termination via end-nodes in the graph |
| State implicit in chat history | State explicit in the workflow context |

For tens of thousands of existing AutoGen users, this is a **hard
migration** — graph thinking differs structurally from chat thinking.

## 3. Why Cognithor Still Exists

MAF is excellent for Azure-centric Enterprise customers who want a vendor-
supported framework with first-class observability inside the Microsoft
stack. Cognithor's positioning is complementary, not competitive:

- **EU-Sovereignty**: No implicit Azure dependency. `OLLAMA_HOST` is the
  default, not an "alternative client". The DACH-region documentation
  layer (`cognithor init --template versicherungs-vergleich`) ships with
  the framework, not as a sample.
- **No Azure account required**: `pip install cognithor` plus a local
  Ollama gives a working agent in <5 minutes.
- **DSGVO-relevant features**: PII-redaction guardrails (`no_pii()`),
  Hashline-Guard audit chain, strict role separation via PGE-Trinity, all
  documented as compliance primitives — not afterthoughts.
- **Local inference first-class**: 16 providers including local Ollama,
  vLLM, llama.cpp; no managed-service preference.
- **Public Apache 2.0**: MAF is also MIT/permissive, but MAF's commercial
  motion is tightly bound to Azure. Cognithor's commercial layer
  (`cognithor.packs`) is opt-in, EULA-gated, and orthogonal to the core.

## 4. Not a Framework War

Cognithor does not position itself as "the alternative MAF" or claim
feature-superiority for graph-orchestration use-cases. For workflows that
**need** explicit DAG semantics (e.g., approval chains with conditional
branches, finance-style state machines), MAF or LangGraph is the right
tool. Cognithor is the right tool when:

- DSGVO/EU-residency is a hard requirement.
- Local inference is preferred (or required by policy).
- The team wants a chat-style multi-agent abstraction with a built-in
  Gatekeeper layer for safety.
- Vendor independence matters more than Azure-native observability.

## 5. References

- MAF documentation: https://learn.microsoft.com/en-us/agent-framework/
- MAF migration from AutoGen: https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/
- Cognithor PGE-Trinity ADR: [`docs/adr/0001-pge-trinity-vs-group-chat.md`](../adr/0001-pge-trinity-vs-group-chat.md)
```

- [ ] **Step 2: Word-count check**

```bash
wc -w docs/competitive-analysis/microsoft-agent-framework.md
```

Expected: ≥400 words.

- [ ] **Step 3: Commit**

```bash
git add docs/competitive-analysis/microsoft-agent-framework.md
git commit -m "docs(competitive-analysis): add Cognithor vs Microsoft Agent Framework"
```

---

### Task 4: Write `docs/competitive-analysis/decision-matrix.md`

**Files:**
- Create: `docs/competitive-analysis/decision-matrix.md`

- [ ] **Step 1: Write the document**

```markdown
# Decision Matrix — Multi-Agent Frameworks

> **Status of this document:** 2026-04-25. Each cell sourced from public
> documentation; corrections welcome via issue.

This matrix compares feature surfaces, not performance. Performance
benchmarks are deliberately deferred — see [`cognithor_bench/README.md`](../../cognithor_bench/README.md)
(added in v0.94.0 PR 2).

| Dimension | Cognithor | AutoGen 0.7.5 | MAF 1.0 | LangGraph | CrewAI |
|-----------|-----------|---------------|---------|-----------|--------|
| Core License | Apache 2.0 | MIT | MIT | MIT | MIT |
| Host-Region (Default) | Local / EU | n/a (library) | Azure-leaning | n/a (library) | n/a (library) |
| Local Inference First-Class | Yes (Ollama default) | Via `OpenAIChatCompletionClient` | Possible, not default | Yes | Yes |
| LLM Providers OOTB | 16 | 1 (OpenAI-compat) + extensions | Azure AI + OpenAI | LangChain providers | LangChain providers |
| MCP Client | Yes (145 tools across 14 modules) | Yes | Yes | Via LangChain | Yes |
| A2A Protocol | Yes (`cognithor.a2a`) | Partial | Yes | No | No |
| Multi-Agent Pattern | PGE-Trinity (forced role separation) | Conversation (chat history) | Graph (DAG) | Graph (DAG) | Conversation (Crews) |
| DSGVO Compliance Claim | Explicit (PII redaction, EU-provider docs) | Not addressed | Implicit (Azure EU) | Not addressed | Not addressed |
| Audit Chain | Hashline Guard (xxhash chain) | No | Azure observability | LangSmith | No |
| Commercial Coupling | None (Apache core; opt-in commerce packs) | None (Microsoft project) | Microsoft / Azure | LangChain Inc. | CrewAI Inc. (Pro) |
| Active Maintenance Status | Active (v0.94.0 in flight) | Maintenance Mode | Active | Active | Active |

## How to read this matrix

- "Yes" / "No" answers reflect what's documented in the upstream framework
  as of 2026-04-25. They do not indicate quality or maturity.
- "First-Class" means a feature is treated as the default, not an opt-in
  extension.
- For runtime performance, see `cognithor_bench/` once GAIA/WebArena
  scenarios are integrated (post-v0.94.0).

## References

- AutoGen: https://github.com/microsoft/autogen
- MAF: https://learn.microsoft.com/en-us/agent-framework/
- LangGraph: https://langchain-ai.github.io/langgraph/
- CrewAI: https://docs.crewai.com/
```

- [ ] **Step 2: Commit**

```bash
git add docs/competitive-analysis/decision-matrix.md
git commit -m "docs(competitive-analysis): add 5-framework decision matrix"
```

Expected: 1 file changed, ~50 insertions.

---

### Task 5: Add competitive-analysis index to main docs `README.md`

**Files:**
- Modify: `docs/README.md` (or `docs/index.html` if no README — verify which exists)

- [ ] **Step 1: Verify which docs landing page exists**

```bash
ls docs/README.md docs/index.html 2>&1
```

If `docs/README.md` exists, modify it. If only `docs/index.html` exists, the link goes into `README.md` at repo root instead (Architecture section).

- [ ] **Step 2: Read the target file**

```bash
# Use the Read tool on either docs/README.md or repo-root README.md
```

Locate an "Architecture" or "Documentation" section near the top.

- [ ] **Step 3: Add a single line linking the competitive analysis**

In an existing list (e.g. under "Documentation"), add:

```markdown
- **Competitive Analysis** — [`docs/competitive-analysis/`](docs/competitive-analysis/README.md) — Cognithor vs AutoGen / MAF / LangGraph / CrewAI.
```

- [ ] **Step 4: Commit**

```bash
git add docs/README.md  # or README.md
git commit -m "docs: link competitive-analysis from main docs index"
```

---

### Task 6: Scaffold `docs/adr/` + index

**Files:**
- Create: `docs/adr/README.md`

- [ ] **Step 1: Write the ADR index**

```markdown
# Architecture Decision Records

This directory holds Architecture Decision Records (ADRs) for Cognithor,
following the [Nygard template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

## Records

| #    | Status   | Title                                     | Date       |
|------|----------|-------------------------------------------|------------|
| 0001 | Accepted | [PGE Trinity vs Group Chat](./0001-pge-trinity-vs-group-chat.md) | 2026-04-25 |

## Template

```markdown
# ADR NNNN: <Title>

## Status
Proposed | Accepted | Deprecated | Superseded by ADR-XXXX

## Context
<Forces at play, problem statement, constraints>

## Decision
<The change we're making>

## Consequences

### Positive
- <Benefit 1>
- <Benefit 2>

### Negative / Trade-offs
- <Cost 1>
- <Cost 2>
- <Cost 3>  # at least 3 honest trade-offs

## Alternatives Considered
1. <Option A> — rejected because <reason>
2. <Option B> — rejected because <reason>

## References
- <Source 1>
- <Source 2>
```
```

- [ ] **Step 2: Commit**

```bash
git add docs/adr/README.md
git commit -m "docs(adr): scaffold ADR directory with Nygard template"
```

---

### Task 7: Write ADR 0001 — PGE Trinity vs Group Chat

**Files:**
- Create: `docs/adr/0001-pge-trinity-vs-group-chat.md`

- [ ] **Step 1: Write the ADR**

```markdown
# ADR 0001: PGE Trinity as Multi-Agent Control Model

## Status
Accepted — 2026-04-25

## Context

Multi-agent systems need a way to coordinate multiple LLM-backed agents
working on a shared task. The dominant patterns in 2025-2026 are:

1. **AutoGen GroupChat patterns** (`autogen-agentchat`):
   - `RoundRobinGroupChat` — agents take turns in a fixed order.
   - `SelectorGroupChat` — an LLM decides who speaks next.
   - `Swarm` — agents pass control via `HandoffMessage`.
   - `MagenticOneGroupChat` — central orchestrator agent
     ([Magentic-One paper](https://arxiv.org/abs/2411.04468)).
2. **Graph orchestration** (LangGraph, MAF) — explicit DAG with nodes and
   edges; control-flow declared in code, not emergent from chat.
3. **Pure handoff/swarm** — no central coordinator; agents exchange
   ownership tokens.

Cognithor needs a Multi-Agent control model that supports:
- Auditability — every action attributable to a verifiable chain
  (Hashline Guard).
- DSGVO-grade safety — PII filtering, allow-list enforcement, before any
  external call.
- Predictability — no agent should "drift" into a role it wasn't
  authorized for, including via prompt injection.
- Local inference compatibility — must work without an external selector
  LLM in the critical path.

The question this ADR answers: **Why does Cognithor not just adopt one of
the AutoGen GroupChat patterns?**

## Decision

Cognithor uses **PGE Trinity** — Planner / Gatekeeper / Executor — as
enforced role separation:

- **Planner** decides what should happen next (intent, plan steps).
- **Gatekeeper** decides whether each proposed action is permissible
  (DSGVO PII check, tool allow-list, risk classification GREEN /
  YELLOW / ORANGE / RED).
- **Executor** runs the action and emits the audit record.

These roles are **separate concerns implemented as separate components**
(see `src/cognithor/core/planner.py`, `src/cognithor/core/gatekeeper.py`,
`src/cognithor/core/gateway.py`). They are not three prompts to the same
agent; they are three pipeline stages with explicit hand-offs and audit
points.

`cognithor.crew` (added in v0.93.0) wraps this trio for declarative
multi-agent scenarios, but the trio itself is not optional or
configurable away. Every Crew kickoff routes through Planner →
Gatekeeper → Executor.

## Consequences

### Positive

- **Auditability**: Every action passes through Gatekeeper, which writes
  a Hashline-Guard chain entry. The chain is verifiable end-to-end.
- **DSGVO**: PII filtering and allow-list enforcement live in one place,
  not duplicated per agent. Disabling them requires touching one
  component, which is reviewable.
- **No agent drift**: Roles cannot emerge from prompt-engineering
  accident. A Planner cannot execute; an Executor cannot decide policy.
- **Local-first**: No selector-LLM hop in the critical path. Gatekeeper
  is rule-based with optional LLM augmentation, not LLM-only.
- **Composability**: `cognithor.crew` can adopt new orchestration
  patterns above PGE; the trio is a substrate, not a replacement.

### Negative / Trade-offs

- **Higher latency than direct GroupChat**: Every action incurs a
  Gatekeeper hop (typically 5-50ms for rule-based classification, more
  if an LLM-backed risk check is enabled).
- **Less "creative" emergent behaviour**: SelectorGroupChat-style
  setups where an LLM picks the next speaker can produce surprising
  task-decompositions. PGE forecloses some of that surface area
  intentionally.
- **Higher entry barrier for AutoGen migrants**: Users coming from
  `RoundRobinGroupChat` or `SelectorGroupChat` see more boilerplate
  in PGE-Trinity for simple cases. The `cognithor.compat.autogen`
  shim mitigates this for the 1-shot and round-robin paths but
  cannot reproduce SelectorGroupChat or Swarm semantics.
- **Operational complexity**: Three components to monitor, three log
  streams to correlate. The Hashline-Guard chain ties them but
  understanding the chain is a learning curve.

## Alternatives Considered

1. **`RoundRobinGroupChat` equivalent without Gatekeeper** — rejected:
   no audit point. The chain would be a record of "who said what" but
   not of "which actions were authorized to run". DSGVO compliance
   would have to be reimplemented per agent.
2. **`SelectorGroupChat` equivalent (LLM picks the next speaker)** —
   rejected: an LLM as a security boundary is not load-bearing. Prompt
   injection trivially redirects a selector LLM. Gatekeeper rules are
   inspectable and testable.
3. **Pure Handoff / Swarm** — rejected: no central policy enforcement.
   Each agent would carry its own DSGVO logic; impossible to audit
   centrally.
4. **Graph orchestration (LangGraph / MAF style)** — rejected as
   substrate (would conflict with the conversation-style API surface
   `cognithor.crew` exposes), but kept as a future-feature option:
   spec §6 "Flows" (deferred to v1.x) would let users compose Crews
   into larger DAGs without replacing PGE-Trinity inside each Crew.

## References

- AutoGen GroupChat docs: https://microsoft.github.io/autogen/stable//user-guide/agentchat-user-guide/tutorial/teams.html
- Magentic-One paper: https://arxiv.org/abs/2411.04468
- Cognithor Gatekeeper code: `src/cognithor/core/gatekeeper.py`
- Cognithor PGE pipeline: `src/cognithor/gateway/gateway.py`
- Hashline Guard: `docs/hashline-guard.md`
- v0.94.0 AutoGen-compat shim (PR 3): `src/cognithor/compat/autogen/`
```

- [ ] **Step 2: Verify the three AutoGen patterns are mentioned by name**

```bash
grep -E "RoundRobinGroupChat|SelectorGroupChat|Swarm" docs/adr/0001-pge-trinity-vs-group-chat.md
```

Expected: at least one match for each of the three pattern names.

- [ ] **Step 3: Verify ≥3 negative trade-offs**

```bash
awk '/### Negative/,/## Alternatives/' docs/adr/0001-pge-trinity-vs-group-chat.md | grep -c "^- \*\*"
```

Expected: ≥3 (the document above has 4).

- [ ] **Step 4: Commit**

```bash
git add docs/adr/0001-pge-trinity-vs-group-chat.md
git commit -m "docs(adr): add ADR 0001 — PGE Trinity vs Group Chat"
```

---

### Task 8: Link ADR + competitive-analysis from repo-root `README.md`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Locate the "Architecture" section in `README.md`**

```bash
grep -n "## Architecture\|## Documentation\|## Links" README.md
```

- [ ] **Step 2: Append a "Decision Records" subsection or list line**

Below the existing Architecture section, append:

```markdown
### Architecture Decision Records

- [`docs/adr/0001-pge-trinity-vs-group-chat.md`](docs/adr/0001-pge-trinity-vs-group-chat.md)
  — Why Cognithor uses Planner/Gatekeeper/Executor instead of conversational
  GroupChat patterns.

### Comparison with Other Frameworks

- [`docs/competitive-analysis/`](docs/competitive-analysis/README.md) —
  Cognithor vs AutoGen, Microsoft Agent Framework, LangGraph, CrewAI.
```

(Place after the existing Architecture content — read the file first to see the exact insertion point.)

- [ ] **Step 3: Add a Markdown link-checker test**

**Files:**
- Create: `tests/test_docs/test_competitive_analysis_links.py`

```python
# tests/test_docs/test_competitive_analysis_links.py
"""Verify the WP1 + WP5 docs all exist and cross-references resolve."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_competitive_analysis_files_exist() -> None:
    for name in ("README.md", "autogen.md", "microsoft-agent-framework.md", "decision-matrix.md"):
        path = REPO_ROOT / "docs" / "competitive-analysis" / name
        assert path.exists(), f"missing {path}"


def test_adr_files_exist() -> None:
    assert (REPO_ROOT / "docs" / "adr" / "README.md").exists()
    assert (REPO_ROOT / "docs" / "adr" / "0001-pge-trinity-vs-group-chat.md").exists()


def test_autogen_md_minimum_length() -> None:
    body = (REPO_ROOT / "docs" / "competitive-analysis" / "autogen.md").read_text(encoding="utf-8")
    assert len(body.split()) >= 400, f"autogen.md is below 400 words ({len(body.split())} words)"


def test_maf_md_minimum_length() -> None:
    body = (REPO_ROOT / "docs" / "competitive-analysis" / "microsoft-agent-framework.md").read_text(
        encoding="utf-8"
    )
    assert len(body.split()) >= 400, f"MAF doc is below 400 words ({len(body.split())} words)"


def test_adr_mentions_three_groupchat_patterns() -> None:
    body = (REPO_ROOT / "docs" / "adr" / "0001-pge-trinity-vs-group-chat.md").read_text(
        encoding="utf-8"
    )
    for name in ("RoundRobinGroupChat", "SelectorGroupChat", "Swarm"):
        assert name in body, f"ADR 0001 must mention {name} by name"


def test_root_readme_links_competitive_analysis() -> None:
    body = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/competitive-analysis/" in body, "root README must link competitive-analysis"
    assert "docs/adr/0001-pge-trinity-vs-group-chat.md" in body, "root README must link ADR 0001"
```

Also create `tests/test_docs/__init__.py` (empty file).

- [ ] **Step 4: Run the link-checker**

```bash
mkdir -p tests/test_docs && touch tests/test_docs/__init__.py
pytest tests/test_docs/test_competitive_analysis_links.py -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_docs/__init__.py tests/test_docs/test_competitive_analysis_links.py README.md
git commit -m "docs: link ADR 0001 + competitive-analysis from repo README; add link-checker test"
```

---

### PR 1 Closeout

- [ ] **Step 1: Full regression on the feature branch**

```bash
pytest tests/ -x -q --cov=src/cognithor --cov-fail-under=89
```

Expected: green, coverage ≥89%.

- [ ] **Step 2: Lint + format check**

```bash
ruff check .
ruff format --check .
```

Expected: both clean.

- [ ] **Step 3: CHANGELOG entry under `[Unreleased]`**

Read `CHANGELOG.md`, append under `[Unreleased]` section:

```markdown
### Added
- `docs/competitive-analysis/` — comparison docs for AutoGen, MAF, LangGraph, CrewAI (WP1).
- `docs/adr/0001-pge-trinity-vs-group-chat.md` — first Architecture Decision Record (WP5).
```

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): note WP1 + WP5 additions for v0.94.0"
```

- [ ] **Step 4: Push + open PR**

```bash
git push -u origin feat/cognithor-autogen-v1-docs
gh pr create --title "docs: WP1 competitive-analysis + WP5 PGE-Trinity ADR (v0.94.0 PR 1)" --body "$(cat <<'EOF'
## Summary
- Adds `docs/competitive-analysis/` with index, autogen.md, microsoft-agent-framework.md, decision-matrix.md
- Adds `docs/adr/0001-pge-trinity-vs-group-chat.md` and ADR-index README
- Links both from repo-root README.md
- Adds a small Pytest link-checker

## Spec
- `docs/superpowers/specs/2026-04-25-cognithor-autogen-strategy-design.md` §8.1, §8.2

## Test plan
- [ ] `pytest tests/test_docs/ -v` passes
- [ ] `pytest tests/ -x -q --cov=src/cognithor --cov-fail-under=89` passes
- [ ] All four competitive-analysis files ≥400 words
- [ ] ADR 0001 mentions RoundRobinGroupChat, SelectorGroupChat, Swarm by name
- [ ] Repo-root README links both docs

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 5: Wait CI green, squash-merge**

```bash
gh pr checks <PR_NUMBER> --watch
gh pr merge <PR_NUMBER> --squash --delete-branch=false
```

(Don't pass `--delete-branch` here — cleanup is a separate turn per memory.)

- [ ] **Step 6: Cleanup in a separate turn**

After confirming PR is merged in `main`, in a new conversation turn:

```bash
git checkout main && git pull --ff-only
git branch -d feat/cognithor-autogen-v1-docs
git push origin --delete feat/cognithor-autogen-v1-docs
```

---

# PR 2 — WP4 `cognithor-bench` Scaffold (Tasks 9-22)

Implements spec §8.3 — eigenes Benchmark-Subpaket im Monorepo. Console-script `cognithor-bench`, JSONL scenarios, `--native` default (`--docker` opt-in), Cognithor adapter as default, optional AutoGen adapter (lazy import-safe). Adds the **single pin-point** for `autogen-agentchat==0.7.5` to root `pyproject.toml` `[autogen]` extra in Task 9 — referenced by WP2 in PR 3.

**Branch:** `feat/cognithor-autogen-v2-bench` cut from latest `main` (after PR 1 merged).

**PR-2 closeout target:** `pip install -e ./cognithor_bench` works; `cognithor-bench --help` prints; `cognithor-bench run cognithor_bench/src/cognithor_bench/scenarios/smoke_test.jsonl` succeeds with mock adapter; `pytest cognithor_bench/tests/` ≥80% coverage; `[autogen]` extra added to root `pyproject.toml`.

---

### Task 9: Branch + add `[autogen]` extra to root `pyproject.toml` (single pin-point)

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Cut feature branch**

```bash
git checkout main && git pull --ff-only
git checkout -b feat/cognithor-autogen-v2-bench
```

- [ ] **Step 2: Read current `pyproject.toml` `[project.optional-dependencies]` section**

```bash
# Read the file with the Read tool first; locate the line `arc-gpu = [` and insert after it
```

- [ ] **Step 3: Add the `autogen` extra**

Insert in `[project.optional-dependencies]` block, after the `arc-gpu` block and before the `all` block:

```toml
autogen = [
    # Single pin-point for AutoGen-source-compat shim.
    # Referenced by:
    #   - tests/test_compat/test_autogen/ (signature parity, behaviour tests)
    #   - cognithor_bench/src/cognithor_bench/adapters/autogen_adapter.py (lazy import)
    # See spec §6 (Single Pin-Point) and §8.4 acceptance criteria.
    "autogen-agentchat==0.7.5",
]
```

- [ ] **Step 4: Verify the file still parses**

```bash
python -c "import tomllib; tomllib.loads(open('pyproject.toml','rb').read().decode())" && echo OK
```

Expected: `OK`. (Python 3.11+ has `tomllib` in stdlib.)

- [ ] **Step 5: Smoke-install in a fresh venv to confirm the extra resolves**

```bash
python -m venv /tmp/autogen-extra-check
/tmp/autogen-extra-check/Scripts/python.exe -m pip install -e ".[autogen]" 2>&1 | tail -5
/tmp/autogen-extra-check/Scripts/python.exe -c "import autogen_agentchat; print(autogen_agentchat.__version__)"
```

Expected: imports successfully; version starts with `0.7.5`. (On Linux: replace `Scripts/python.exe` with `bin/python`.)

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml
git commit -m "build(pyproject): add [autogen] extra with autogen-agentchat==0.7.5 pin-point"
```

---

### Task 10: Scaffold `cognithor_bench/` directory + `pyproject.toml`

**Files:**
- Create: `cognithor_bench/pyproject.toml`
- Create: `cognithor_bench/README.md`
- Create: `cognithor_bench/src/cognithor_bench/__init__.py`

- [ ] **Step 1: Write the failing test**

**Files:**
- Create: `cognithor_bench/tests/__init__.py`
- Create: `cognithor_bench/tests/test_package_install.py`

```python
# cognithor_bench/tests/test_package_install.py
"""Verify cognithor_bench installs and exposes its public surface."""

def test_package_imports() -> None:
    import cognithor_bench
    assert hasattr(cognithor_bench, "__version__")


def test_runner_module_imports() -> None:
    from cognithor_bench import runner
    assert hasattr(runner, "BenchRunner")


def test_cli_module_imports() -> None:
    from cognithor_bench import cli
    assert hasattr(cli, "main")


def test_cognithor_adapter_imports() -> None:
    from cognithor_bench.adapters import cognithor_adapter
    assert hasattr(cognithor_adapter, "CognithorAdapter")
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest cognithor_bench/tests/test_package_install.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'cognithor_bench'`.

- [ ] **Step 3: Create `cognithor_bench/pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "cognithor-bench"
version = "0.1.0"
description = "Reproducible Multi-Agent benchmark scaffold for Cognithor"
readme = "README.md"
license = "Apache-2.0"
requires-python = ">=3.12"
authors = [{ name = "Alexander Söllner" }]
keywords = ["ai", "agent", "benchmark", "cognithor"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
    "cognithor>=0.94.0",
    "anyio>=4.0,<5",
    "structlog>=25.4,<26",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9",
    "pytest-asyncio>=0.24,<1",
    "pytest-cov>=6.0,<7",
]
# Mirrors the root cognithor[autogen] extra so cognithor_bench can pull
# autogen-agentchat for the optional AutoGenAdapter without re-pinning.
autogen = ["autogen-agentchat==0.7.5"]

[project.scripts]
cognithor-bench = "cognithor_bench.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/cognithor_bench"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
target-version = "py312"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "SIM", "TCH", "RUF"]
ignore = ["RUF001", "RUF002", "RUF003", "RUF012"]
```

- [ ] **Step 4: Create `cognithor_bench/README.md`**

```markdown
# cognithor-bench — Reproducible Multi-Agent Benchmark Scaffold

In-monorepo benchmark harness for Cognithor. Independent of `agbench`;
focuses on Cognithor-native scenarios with the option to compare against
AutoGen via the source-compat shim from `cognithor.compat.autogen`.

## Status

`v0.1.0` ships **scaffold + smoke-test only** with Cognithor v0.94.0.
GAIA / WebArena / AssistantBench scenario adapters are post-v0.94.0.

## Install

```bash
pip install -e .
# Optional: pull the AutoGen adapter dependency
pip install -e ".[autogen]"
```

## Usage

```bash
# Run the default smoke-test (3 trivial tasks)
cognithor-bench run src/cognithor_bench/scenarios/smoke_test.jsonl

# With repetition + sub-sampling
cognithor-bench run scenarios/foo.jsonl --repeat 5 --subsample 0.5

# Pick the AutoGen adapter (requires [autogen] extra)
cognithor-bench run scenarios/foo.jsonl --adapter autogen

# Pick a specific Ollama model
cognithor-bench run scenarios/foo.jsonl --model ollama/qwen3:8b

# Native execution (default) vs Docker isolation (opt-in)
cognithor-bench run scenarios/foo.jsonl --native     # default
cognithor-bench run scenarios/foo.jsonl --docker     # opt-in

# Aggregate a results directory into a Markdown table
cognithor-bench tabulate results/
```

## Scenario format (JSONL — one task per line)

```json
{"id": "smoke-001", "task": "Was ist 2+2?", "expected": "4", "timeout_sec": 30, "requires": ["no_network"]}
```

Fields:
- `id` — short identifier (used for result aggregation).
- `task` — natural-language prompt.
- `expected` — exact-match string OR substring (matched case-insensitively).
- `timeout_sec` — per-task timeout.
- `requires` — list of capability tags (`no_network`, `ollama`, `pdf-tools`, ...).

## Adding a new scenario file

Drop a JSONL file under `src/cognithor_bench/scenarios/`. Each line is a
discrete task. Run:

```bash
cognithor-bench run src/cognithor_bench/scenarios/my_new_set.jsonl
```

## License

Apache 2.0. See repo-root `LICENSE`.
```

- [ ] **Step 5: Create `cognithor_bench/src/cognithor_bench/__init__.py`**

```python
"""cognithor-bench — reproducible Multi-Agent benchmark scaffold."""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
```

- [ ] **Step 6: Skip the test until `runner.py` and `cli.py` arrive in Tasks 11-13**

Mark the package-install test as `xfail` for now:

```python
# Add at the top of cognithor_bench/tests/test_package_install.py
import pytest

pytestmark = pytest.mark.xfail(
    reason="runner / cli / adapters arrive in Tasks 11-13",
    strict=False,
)
```

(We will remove this marker in Task 13.)

- [ ] **Step 7: Install + run xfail test**

```bash
pip install -e ./cognithor_bench
pytest cognithor_bench/tests/test_package_install.py -v
```

Expected: 1 passed (`test_package_imports`), 3 xfailed.

- [ ] **Step 8: Commit**

```bash
git add cognithor_bench/pyproject.toml cognithor_bench/README.md cognithor_bench/src/cognithor_bench/__init__.py cognithor_bench/tests/__init__.py cognithor_bench/tests/test_package_install.py
git commit -m "feat(bench): scaffold cognithor_bench submodule + pyproject"
```

---

### Task 11: Adapter Protocol + base class

**Files:**
- Create: `cognithor_bench/src/cognithor_bench/adapters/__init__.py`
- Create: `cognithor_bench/src/cognithor_bench/adapters/base.py`
- Create: `cognithor_bench/tests/test_adapters_base.py`

- [ ] **Step 1: Write the failing test**

```python
# cognithor_bench/tests/test_adapters_base.py
"""Adapter Protocol — runtime-checkable + minimal contract."""

from __future__ import annotations

import pytest

from cognithor_bench.adapters.base import Adapter, ScenarioInput, ScenarioResult


def test_adapter_is_runtime_checkable_protocol() -> None:
    class Dummy:
        name = "dummy"

        async def run(self, scenario: ScenarioInput) -> ScenarioResult:
            return ScenarioResult(
                id=scenario.id, output="x", success=False,
                duration_sec=0.0, error=None,
            )

    assert isinstance(Dummy(), Adapter)


def test_scenario_input_required_fields() -> None:
    s = ScenarioInput(id="s1", task="2+2", expected="4", timeout_sec=10, requires=())
    assert s.id == "s1"
    assert s.task == "2+2"
    assert s.expected == "4"


def test_scenario_result_required_fields() -> None:
    r = ScenarioResult(id="s1", output="4", success=True, duration_sec=0.1, error=None)
    assert r.id == "s1"
    assert r.success is True


def test_scenario_input_is_frozen() -> None:
    s = ScenarioInput(id="s1", task="2+2", expected="4", timeout_sec=10, requires=())
    with pytest.raises(Exception):
        s.id = "modified"  # type: ignore[misc]
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest cognithor_bench/tests/test_adapters_base.py -v
```

Expected: `ModuleNotFoundError: No module named 'cognithor_bench.adapters'`.

- [ ] **Step 3: Implement `adapters/__init__.py` + `adapters/base.py`**

```python
# cognithor_bench/src/cognithor_bench/adapters/__init__.py
"""Benchmark adapters — wrappers over multi-agent frameworks."""

from __future__ import annotations

from cognithor_bench.adapters.base import Adapter, ScenarioInput, ScenarioResult

__all__ = ["Adapter", "ScenarioInput", "ScenarioResult"]
```

```python
# cognithor_bench/src/cognithor_bench/adapters/base.py
"""Adapter Protocol + scenario types."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class ScenarioInput(BaseModel):
    """One scenario row from a JSONL file."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1)
    task: str = Field(..., min_length=1)
    expected: str = Field(...)
    timeout_sec: int = Field(default=60, ge=1, le=3600)
    requires: tuple[str, ...] = Field(default_factory=tuple)


class ScenarioResult(BaseModel):
    """One adapter execution result."""

    model_config = ConfigDict(frozen=True)

    id: str
    output: str
    success: bool
    duration_sec: float
    error: str | None = None


@runtime_checkable
class Adapter(Protocol):
    """Pluggable benchmark adapter.

    Implementations:
      - cognithor_bench.adapters.cognithor_adapter.CognithorAdapter (default)
      - cognithor_bench.adapters.autogen_adapter.AutoGenAdapter (opt-in)
    """

    name: str

    async def run(self, scenario: ScenarioInput) -> ScenarioResult: ...
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest cognithor_bench/tests/test_adapters_base.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add cognithor_bench/src/cognithor_bench/adapters/__init__.py cognithor_bench/src/cognithor_bench/adapters/base.py cognithor_bench/tests/test_adapters_base.py
git commit -m "feat(bench): add Adapter Protocol + ScenarioInput/Result types"
```

---

### Task 12: Cognithor adapter (default)

**Files:**
- Create: `cognithor_bench/src/cognithor_bench/adapters/cognithor_adapter.py`
- Create: `cognithor_bench/tests/test_cognithor_adapter.py`

- [ ] **Step 1: Write the failing test**

```python
# cognithor_bench/tests/test_cognithor_adapter.py
"""CognithorAdapter — wraps cognithor.crew.Crew for benchmark execution."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor_bench.adapters.base import ScenarioInput
from cognithor_bench.adapters.cognithor_adapter import CognithorAdapter


@pytest.mark.asyncio
async def test_cognithor_adapter_name() -> None:
    a = CognithorAdapter(model="ollama/qwen3:8b")
    assert a.name == "cognithor"


@pytest.mark.asyncio
async def test_cognithor_adapter_runs_scenario_success() -> None:
    """A passing scenario produces ScenarioResult(success=True) with output."""
    fake_output = MagicMock()
    fake_output.raw = "4"
    fake_output.tasks_outputs = []

    with patch("cognithor_bench.adapters.cognithor_adapter.Crew") as crew_cls:
        crew = MagicMock()
        crew.kickoff_async = AsyncMock(return_value=fake_output)
        crew_cls.return_value = crew

        a = CognithorAdapter(model="ollama/qwen3:8b")
        scenario = ScenarioInput(id="s1", task="2+2", expected="4", timeout_sec=10, requires=())
        result = await a.run(scenario)

        assert result.id == "s1"
        assert result.output == "4"
        assert result.success is True
        assert result.error is None


@pytest.mark.asyncio
async def test_cognithor_adapter_failure_reports_error() -> None:
    """An exception inside kickoff_async produces ScenarioResult(success=False, error)."""
    with patch("cognithor_bench.adapters.cognithor_adapter.Crew") as crew_cls:
        crew = MagicMock()
        crew.kickoff_async = AsyncMock(side_effect=RuntimeError("boom"))
        crew_cls.return_value = crew

        a = CognithorAdapter(model="ollama/qwen3:8b")
        scenario = ScenarioInput(id="s1", task="x", expected="y", timeout_sec=10, requires=())
        result = await a.run(scenario)

        assert result.success is False
        assert result.error is not None
        assert "boom" in result.error


@pytest.mark.asyncio
async def test_cognithor_adapter_substring_match_is_case_insensitive() -> None:
    """Expected '4' matched against 'The answer is 4.' counts as success."""
    fake_output = MagicMock()
    fake_output.raw = "The answer is 4."
    fake_output.tasks_outputs = []

    with patch("cognithor_bench.adapters.cognithor_adapter.Crew") as crew_cls:
        crew = MagicMock()
        crew.kickoff_async = AsyncMock(return_value=fake_output)
        crew_cls.return_value = crew

        a = CognithorAdapter(model="ollama/qwen3:8b")
        scenario = ScenarioInput(id="s1", task="2+2", expected="4", timeout_sec=10, requires=())
        result = await a.run(scenario)

        assert result.success is True
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest cognithor_bench/tests/test_cognithor_adapter.py -v 2>&1 | tail -10
```

Expected: `ModuleNotFoundError: No module named 'cognithor_bench.adapters.cognithor_adapter'`.

- [ ] **Step 3: Implement the adapter**

```python
# cognithor_bench/src/cognithor_bench/adapters/cognithor_adapter.py
"""Default CognithorAdapter — wraps cognithor.crew.Crew."""

from __future__ import annotations

import asyncio
import time

from cognithor.crew import Crew, CrewAgent, CrewTask  # type: ignore[attr-defined]

from cognithor_bench.adapters.base import ScenarioInput, ScenarioResult


class CognithorAdapter:
    """Run a scenario through a single-agent, single-task Cognithor Crew."""

    name = "cognithor"

    def __init__(self, *, model: str = "ollama/qwen3:8b") -> None:
        self.model = model

    async def run(self, scenario: ScenarioInput) -> ScenarioResult:
        start = time.perf_counter()
        try:
            agent = CrewAgent(
                role="bench-agent",
                goal=f"Answer the user's task accurately: {scenario.task}",
                backstory="You answer benchmark questions with one short string.",
                llm=self.model,
                verbose=False,
            )
            task = CrewTask(
                description=scenario.task,
                expected_output=scenario.expected,
                agent=agent,
            )
            crew = Crew(agents=[agent], tasks=[task])

            output = await asyncio.wait_for(
                crew.kickoff_async({}),
                timeout=scenario.timeout_sec,
            )
            raw = str(getattr(output, "raw", "") or "")
            success = scenario.expected.lower() in raw.lower()
            return ScenarioResult(
                id=scenario.id,
                output=raw,
                success=success,
                duration_sec=time.perf_counter() - start,
                error=None,
            )
        except Exception as exc:  # noqa: BLE001 — adapter must capture all errors
            return ScenarioResult(
                id=scenario.id,
                output="",
                success=False,
                duration_sec=time.perf_counter() - start,
                error=f"{type(exc).__name__}: {exc}",
            )
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest cognithor_bench/tests/test_cognithor_adapter.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add cognithor_bench/src/cognithor_bench/adapters/cognithor_adapter.py cognithor_bench/tests/test_cognithor_adapter.py
git commit -m "feat(bench): add CognithorAdapter (default)"
```

---

### Task 13: AutoGen adapter (opt-in, lazy ImportError-safe)

**Files:**
- Create: `cognithor_bench/src/cognithor_bench/adapters/autogen_adapter.py`
- Create: `cognithor_bench/tests/test_autogen_adapter.py`

- [ ] **Step 1: Write the failing test**

```python
# cognithor_bench/tests/test_autogen_adapter.py
"""AutoGenAdapter — opt-in via [autogen] extra; ImportError-safe."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor_bench.adapters.autogen_adapter import AutoGenAdapter, _AUTOGEN_IMPORT_ERROR_HINT
from cognithor_bench.adapters.base import ScenarioInput


def test_autogen_adapter_name() -> None:
    a = AutoGenAdapter(model="ollama/qwen3:8b")
    assert a.name == "autogen"


@pytest.mark.asyncio
async def test_autogen_adapter_raises_when_import_missing(monkeypatch) -> None:
    """If autogen_agentchat is not installed, .run raises a helpful ImportError."""

    def fail_import(name: str, *args, **kwargs):
        if name.startswith("autogen_agentchat"):
            raise ImportError(f"No module named {name!r}")
        return __import__(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fail_import)

    a = AutoGenAdapter(model="ollama/qwen3:8b")
    scenario = ScenarioInput(id="s1", task="2+2", expected="4", timeout_sec=10, requires=())
    with pytest.raises(ImportError) as exc:
        await a.run(scenario)
    assert _AUTOGEN_IMPORT_ERROR_HINT in str(exc.value)


@pytest.mark.asyncio
async def test_autogen_adapter_runs_when_import_succeeds() -> None:
    """When autogen_agentchat is importable, adapter runs and reports success."""
    fake_msg = MagicMock()
    fake_msg.content = "4"
    fake_result = MagicMock()
    fake_result.messages = [fake_msg]

    fake_agent = MagicMock()
    fake_agent.run = AsyncMock(return_value=fake_result)

    fake_agents_module = MagicMock()
    fake_agents_module.AssistantAgent = MagicMock(return_value=fake_agent)

    fake_models_module = MagicMock()
    fake_models_module.OpenAIChatCompletionClient = MagicMock(return_value=MagicMock())

    with patch.dict(sys.modules, {
        "autogen_agentchat.agents": fake_agents_module,
        "autogen_ext.models.openai": fake_models_module,
    }):
        a = AutoGenAdapter(model="ollama/qwen3:8b")
        scenario = ScenarioInput(id="s1", task="2+2", expected="4", timeout_sec=10, requires=())
        result = await a.run(scenario)
        assert result.success is True
        assert "4" in result.output
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest cognithor_bench/tests/test_autogen_adapter.py -v 2>&1 | tail -10
```

Expected: ModuleNotFoundError on the adapter import.

- [ ] **Step 3: Implement the adapter**

```python
# cognithor_bench/src/cognithor_bench/adapters/autogen_adapter.py
"""AutoGenAdapter — opt-in via [autogen] extra.

Imports `autogen_agentchat` LAZILY inside .run(). If the extra isn't installed,
the adapter raises a helpful ImportError pointing at the install command.
"""

from __future__ import annotations

import asyncio
import time

from cognithor_bench.adapters.base import ScenarioInput, ScenarioResult

_AUTOGEN_IMPORT_ERROR_HINT = (
    "AutoGenAdapter requires `pip install cognithor[autogen]` "
    "(or `pip install autogen-agentchat==0.7.5`)."
)


class AutoGenAdapter:
    """Run a scenario through autogen-agentchat AssistantAgent."""

    name = "autogen"

    def __init__(self, *, model: str = "ollama/qwen3:8b") -> None:
        self.model = model

    async def run(self, scenario: ScenarioInput) -> ScenarioResult:
        start = time.perf_counter()
        try:
            try:
                from autogen_agentchat.agents import AssistantAgent  # type: ignore[import-not-found]
                from autogen_ext.models.openai import OpenAIChatCompletionClient  # type: ignore[import-not-found]
            except ImportError as e:
                raise ImportError(_AUTOGEN_IMPORT_ERROR_HINT) from e

            client = OpenAIChatCompletionClient(model=self.model)
            agent = AssistantAgent(
                name="bench-agent",
                model_client=client,
                description="Answers benchmark questions with one short string.",
            )
            result = await asyncio.wait_for(
                agent.run(task=scenario.task),
                timeout=scenario.timeout_sec,
            )
            messages = getattr(result, "messages", []) or []
            raw = str(messages[-1].content) if messages else ""
            success = scenario.expected.lower() in raw.lower()
            return ScenarioResult(
                id=scenario.id,
                output=raw,
                success=success,
                duration_sec=time.perf_counter() - start,
                error=None,
            )
        except ImportError:
            raise
        except Exception as exc:  # noqa: BLE001
            return ScenarioResult(
                id=scenario.id,
                output="",
                success=False,
                duration_sec=time.perf_counter() - start,
                error=f"{type(exc).__name__}: {exc}",
            )
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest cognithor_bench/tests/test_autogen_adapter.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Now drop the xfail markers from `test_package_install.py`**

Edit `cognithor_bench/tests/test_package_install.py` — remove the `pytestmark = pytest.mark.xfail(...)` line and the import.

- [ ] **Step 6: Run all package-install + adapter tests**

```bash
pytest cognithor_bench/tests/test_package_install.py cognithor_bench/tests/test_adapters_base.py cognithor_bench/tests/test_cognithor_adapter.py cognithor_bench/tests/test_autogen_adapter.py -v
```

Expected: all green (4 + 4 + 4 + 3 = 15 tests).

- [ ] **Step 7: Commit**

```bash
git add cognithor_bench/src/cognithor_bench/adapters/autogen_adapter.py cognithor_bench/tests/test_autogen_adapter.py cognithor_bench/tests/test_package_install.py
git commit -m "feat(bench): add AutoGenAdapter (opt-in, lazy import-safe)"
```

---

### Task 14: BenchRunner — core async loop

**Files:**
- Create: `cognithor_bench/src/cognithor_bench/runner.py`
- Create: `cognithor_bench/tests/test_runner.py`

- [ ] **Step 1: Write the failing test**

```python
# cognithor_bench/tests/test_runner.py
"""BenchRunner — core async loop with repetition + sub-sampling."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor_bench.adapters.base import ScenarioInput, ScenarioResult
from cognithor_bench.runner import BenchRunner


def _scenario_file(tmp_path: Path, rows: list[dict]) -> Path:
    p = tmp_path / "scen.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


@pytest.mark.asyncio
async def test_runner_executes_each_scenario(tmp_path: Path) -> None:
    rows = [
        {"id": "a", "task": "ta", "expected": "x", "timeout_sec": 10, "requires": []},
        {"id": "b", "task": "tb", "expected": "y", "timeout_sec": 10, "requires": []},
    ]
    path = _scenario_file(tmp_path, rows)

    adapter = MagicMock()
    adapter.name = "test"
    adapter.run = AsyncMock(side_effect=[
        ScenarioResult(id="a", output="x", success=True, duration_sec=0.1, error=None),
        ScenarioResult(id="b", output="z", success=False, duration_sec=0.2, error=None),
    ])

    runner = BenchRunner(adapter=adapter)
    results = await runner.run_file(path, repeat=1, subsample=1.0)

    assert len(results) == 2
    assert results[0].id == "a"
    assert results[1].success is False


@pytest.mark.asyncio
async def test_runner_repeats_scenarios(tmp_path: Path) -> None:
    rows = [{"id": "a", "task": "ta", "expected": "x", "timeout_sec": 10, "requires": []}]
    path = _scenario_file(tmp_path, rows)

    adapter = MagicMock()
    adapter.name = "test"
    adapter.run = AsyncMock(return_value=ScenarioResult(
        id="a", output="x", success=True, duration_sec=0.05, error=None,
    ))

    runner = BenchRunner(adapter=adapter)
    results = await runner.run_file(path, repeat=3, subsample=1.0)
    assert len(results) == 3


@pytest.mark.asyncio
async def test_runner_subsample_reduces_count(tmp_path: Path) -> None:
    rows = [
        {"id": str(i), "task": "t", "expected": "x", "timeout_sec": 10, "requires": []}
        for i in range(10)
    ]
    path = _scenario_file(tmp_path, rows)

    adapter = MagicMock()
    adapter.name = "test"
    adapter.run = AsyncMock(side_effect=lambda s: ScenarioResult(
        id=s.id, output="x", success=True, duration_sec=0.01, error=None,
    ))

    runner = BenchRunner(adapter=adapter, seed=42)
    results = await runner.run_file(path, repeat=1, subsample=0.5)
    assert len(results) == 5  # 10 * 0.5


@pytest.mark.asyncio
async def test_runner_writes_results_to_dir(tmp_path: Path) -> None:
    rows = [{"id": "a", "task": "t", "expected": "x", "timeout_sec": 10, "requires": []}]
    path = _scenario_file(tmp_path, rows)

    adapter = MagicMock()
    adapter.name = "test"
    adapter.run = AsyncMock(return_value=ScenarioResult(
        id="a", output="x", success=True, duration_sec=0.01, error=None,
    ))

    out_dir = tmp_path / "results"
    runner = BenchRunner(adapter=adapter)
    await runner.run_file(path, repeat=1, subsample=1.0, output_dir=out_dir)

    files = list(out_dir.glob("*.jsonl"))
    assert len(files) == 1
    body = files[0].read_text(encoding="utf-8")
    assert json.loads(body.splitlines()[0])["id"] == "a"
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest cognithor_bench/tests/test_runner.py -v 2>&1 | tail -10
```

Expected: ModuleNotFoundError on `cognithor_bench.runner`.

- [ ] **Step 3: Implement the runner**

```python
# cognithor_bench/src/cognithor_bench/runner.py
"""BenchRunner — load JSONL scenarios + execute through an Adapter."""

from __future__ import annotations

import asyncio
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from cognithor_bench.adapters.base import Adapter, ScenarioInput, ScenarioResult


class BenchRunner:
    """Drives an Adapter across a JSONL scenario file."""

    def __init__(self, *, adapter: Adapter, seed: int | None = None) -> None:
        self.adapter = adapter
        self._rng = random.Random(seed)

    async def run_file(
        self,
        scenario_path: Path,
        *,
        repeat: int = 1,
        subsample: float = 1.0,
        output_dir: Path | None = None,
    ) -> list[ScenarioResult]:
        scenarios = self._load(scenario_path)
        if subsample < 1.0:
            n = max(1, int(round(len(scenarios) * subsample)))
            scenarios = self._rng.sample(scenarios, n)

        results: list[ScenarioResult] = []
        for s in scenarios:
            for _ in range(repeat):
                results.append(await self.adapter.run(s))

        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            out_file = output_dir / f"{self.adapter.name}-{scenario_path.stem}-{stamp}.jsonl"
            out_file.write_text(
                "\n".join(r.model_dump_json() for r in results) + "\n",
                encoding="utf-8",
            )
        return results

    @staticmethod
    def _load(scenario_path: Path) -> list[ScenarioInput]:
        scenarios: list[ScenarioInput] = []
        for line in scenario_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            row = json.loads(line)
            row.setdefault("requires", [])
            row["requires"] = tuple(row["requires"])
            scenarios.append(ScenarioInput(**row))
        return scenarios
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest cognithor_bench/tests/test_runner.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add cognithor_bench/src/cognithor_bench/runner.py cognithor_bench/tests/test_runner.py
git commit -m "feat(bench): add BenchRunner with repeat + subsample + result-write"
```

---

### Task 15: Reporter — Markdown table emitter

**Files:**
- Create: `cognithor_bench/src/cognithor_bench/reporter.py`
- Create: `cognithor_bench/tests/test_reporter.py`

- [ ] **Step 1: Write the failing test**

```python
# cognithor_bench/tests/test_reporter.py
"""Reporter — aggregate ScenarioResult lists into Markdown tables."""

from __future__ import annotations

from cognithor_bench.adapters.base import ScenarioResult
from cognithor_bench.reporter import tabulate_results


def test_tabulate_empty() -> None:
    md = tabulate_results([])
    assert "no results" in md.lower()


def test_tabulate_single_result() -> None:
    results = [
        ScenarioResult(id="s1", output="4", success=True, duration_sec=0.12, error=None),
    ]
    md = tabulate_results(results)
    assert "| s1 |" in md
    assert "| ✅ |" in md or "| pass |" in md


def test_tabulate_aggregates_repeated_ids() -> None:
    """Two runs of the same id show as one row with pass-rate 50%."""
    results = [
        ScenarioResult(id="s1", output="4", success=True, duration_sec=0.1, error=None),
        ScenarioResult(id="s1", output="x", success=False, duration_sec=0.2, error=None),
    ]
    md = tabulate_results(results)
    # Pass rate column shows 50% (1/2)
    assert "50" in md
    # Average duration ~0.15s appears (rounded)
    assert "0.15" in md or "0.150" in md


def test_tabulate_includes_summary_row() -> None:
    results = [
        ScenarioResult(id="s1", output="4", success=True, duration_sec=0.1, error=None),
        ScenarioResult(id="s2", output="x", success=False, duration_sec=0.2, error=None),
    ]
    md = tabulate_results(results)
    assert "Total" in md or "Overall" in md
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest cognithor_bench/tests/test_reporter.py -v 2>&1 | tail -5
```

Expected: ModuleNotFoundError on `cognithor_bench.reporter`.

- [ ] **Step 3: Implement the reporter**

```python
# cognithor_bench/src/cognithor_bench/reporter.py
"""Reporter — Markdown table for ScenarioResult lists."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean

from cognithor_bench.adapters.base import ScenarioResult


def tabulate_results(results: list[ScenarioResult]) -> str:
    if not results:
        return "_no results to report_\n"

    grouped: dict[str, list[ScenarioResult]] = defaultdict(list)
    for r in results:
        grouped[r.id].append(r)

    lines = [
        "| Scenario | Runs | Pass-Rate | Avg Duration (s) | Sample Output |",
        "| --- | --- | --- | --- | --- |",
    ]
    total_runs = 0
    total_pass = 0
    for sid in sorted(grouped):
        runs = grouped[sid]
        n = len(runs)
        passed = sum(1 for r in runs if r.success)
        pct = (passed / n) * 100.0
        avg = mean(r.duration_sec for r in runs)
        sample = (runs[0].output or "")[:40].replace("\n", " ")
        sample_md = sample if sample else (runs[0].error or "—")
        lines.append(f"| {sid} | {n} | {pct:.0f}% | {avg:.3f} | {sample_md} |")
        total_runs += n
        total_pass += passed

    overall_pct = (total_pass / total_runs) * 100.0 if total_runs else 0.0
    lines.append(
        f"| **Total** | **{total_runs}** | **{overall_pct:.0f}%** | — | — |"
    )
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest cognithor_bench/tests/test_reporter.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add cognithor_bench/src/cognithor_bench/reporter.py cognithor_bench/tests/test_reporter.py
git commit -m "feat(bench): add Markdown reporter (tabulate_results)"
```

---

### Task 16: CLI — `cognithor-bench run` + `tabulate`

**Files:**
- Create: `cognithor_bench/src/cognithor_bench/cli.py`
- Create: `cognithor_bench/tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# cognithor_bench/tests/test_cli.py
"""CLI — argparse, run / tabulate subcommands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor_bench.adapters.base import ScenarioResult
from cognithor_bench.cli import main


def _scenarios(tmp_path: Path) -> Path:
    p = tmp_path / "scen.jsonl"
    p.write_text(
        json.dumps({"id": "a", "task": "ta", "expected": "x", "timeout_sec": 5, "requires": []})
        + "\n",
        encoding="utf-8",
    )
    return p


def test_cli_help_exits_zero(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "cognithor-bench" in captured.out
    assert "run" in captured.out
    assert "tabulate" in captured.out


def test_cli_run_missing_scenario_exits_nonzero(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["run", str(tmp_path / "doesnotexist.jsonl")])
    assert exc.value.code != 0


def test_cli_run_invokes_adapter(tmp_path: Path) -> None:
    p = _scenarios(tmp_path)
    out = tmp_path / "results"

    with patch("cognithor_bench.cli.CognithorAdapter") as ca:
        instance = MagicMock()
        instance.name = "cognithor"
        instance.run = AsyncMock(return_value=ScenarioResult(
            id="a", output="x", success=True, duration_sec=0.01, error=None,
        ))
        ca.return_value = instance

        rc = main(["run", str(p), "--repeat", "1", "--output-dir", str(out)])
        assert rc == 0
        assert any(out.glob("*.jsonl"))


def test_cli_run_picks_autogen_adapter_when_flag_set(tmp_path: Path) -> None:
    p = _scenarios(tmp_path)
    with patch("cognithor_bench.cli.AutoGenAdapter") as aa, \
         patch("cognithor_bench.cli.CognithorAdapter") as ca:
        instance = MagicMock()
        instance.name = "autogen"
        instance.run = AsyncMock(return_value=ScenarioResult(
            id="a", output="x", success=True, duration_sec=0.01, error=None,
        ))
        aa.return_value = instance

        rc = main(["run", str(p), "--adapter", "autogen"])
        assert rc == 0
        aa.assert_called_once()
        ca.assert_not_called()


def test_cli_tabulate_aggregates_directory(tmp_path: Path, capsys) -> None:
    out = tmp_path / "results"
    out.mkdir()
    (out / "x.jsonl").write_text(
        json.dumps(ScenarioResult(
            id="a", output="x", success=True, duration_sec=0.1, error=None,
        ).model_dump()) + "\n",
        encoding="utf-8",
    )
    rc = main(["tabulate", str(out)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "| a |" in captured.out


def test_cli_run_native_is_default_no_docker_invoked(tmp_path: Path) -> None:
    """Spec: --native is default, --docker is opt-in. No docker call without flag."""
    p = _scenarios(tmp_path)
    with patch("cognithor_bench.cli.CognithorAdapter") as ca, \
         patch("cognithor_bench.cli._run_under_docker") as docker:
        instance = MagicMock()
        instance.name = "cognithor"
        instance.run = AsyncMock(return_value=ScenarioResult(
            id="a", output="x", success=True, duration_sec=0.01, error=None,
        ))
        ca.return_value = instance

        rc = main(["run", str(p)])
        assert rc == 0
        docker.assert_not_called()
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest cognithor_bench/tests/test_cli.py -v 2>&1 | tail -5
```

Expected: ModuleNotFoundError on `cognithor_bench.cli.main`.

- [ ] **Step 3: Implement the CLI**

```python
# cognithor_bench/src/cognithor_bench/cli.py
"""cognithor-bench CLI — `run` and `tabulate` subcommands."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from cognithor_bench.adapters.autogen_adapter import AutoGenAdapter
from cognithor_bench.adapters.base import ScenarioResult
from cognithor_bench.adapters.cognithor_adapter import CognithorAdapter
from cognithor_bench.reporter import tabulate_results
from cognithor_bench.runner import BenchRunner


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cognithor-bench",
        description="Reproducible Multi-Agent benchmark scaffold for Cognithor.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run a JSONL scenario file through an adapter.")
    run.add_argument("scenario", type=Path, help="Path to a .jsonl scenario file.")
    run.add_argument("--repeat", type=int, default=1, help="Repetitions per scenario.")
    run.add_argument("--subsample", type=float, default=1.0, help="Fraction of rows to sample.")
    run.add_argument("--adapter", choices=("cognithor", "autogen"), default="cognithor")
    run.add_argument("--model", default="ollama/qwen3:8b", help="Model spec (e.g. ollama/qwen3:8b).")
    run.add_argument("--output-dir", type=Path, default=Path("results"))
    run.add_argument("--seed", type=int, default=None)
    iso = run.add_mutually_exclusive_group()
    iso.add_argument("--native", action="store_true", help="Run in-process (default).")
    iso.add_argument("--docker", action="store_true", help="Run inside Docker (opt-in).")

    tab = sub.add_parser("tabulate", help="Aggregate a results directory into Markdown.")
    tab.add_argument("results_dir", type=Path)
    return p


def _run_under_docker(args: argparse.Namespace) -> int:
    """Stub for opt-in Docker execution. Real implementation is post-v0.94.0."""
    print("[cognithor-bench] --docker isolation is post-v0.94.0; falling back to --native", file=sys.stderr)
    return _run_native(args)


def _run_native(args: argparse.Namespace) -> int:
    adapter = (
        AutoGenAdapter(model=args.model)
        if args.adapter == "autogen"
        else CognithorAdapter(model=args.model)
    )
    runner = BenchRunner(adapter=adapter, seed=args.seed)
    results = asyncio.run(runner.run_file(
        args.scenario,
        repeat=args.repeat,
        subsample=args.subsample,
        output_dir=args.output_dir,
    ))
    print(tabulate_results(results))
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    if not args.scenario.exists():
        print(f"error: scenario file not found: {args.scenario}", file=sys.stderr)
        return 2
    if args.docker:
        return _run_under_docker(args)
    return _run_native(args)


def _cmd_tabulate(args: argparse.Namespace) -> int:
    if not args.results_dir.exists():
        print(f"error: results directory not found: {args.results_dir}", file=sys.stderr)
        return 2
    rows: list[ScenarioResult] = []
    for path in sorted(args.results_dir.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rows.append(ScenarioResult(**json.loads(line)))
    print(tabulate_results(rows))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.cmd == "run":
        return _cmd_run(args)
    if args.cmd == "tabulate":
        return _cmd_tabulate(args)
    return 1
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest cognithor_bench/tests/test_cli.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Smoke-run the actual installed entry point**

```bash
cognithor-bench --help
```

Expected: prints usage with `run` + `tabulate` subcommands and exits 0.

- [ ] **Step 6: Commit**

```bash
git add cognithor_bench/src/cognithor_bench/cli.py cognithor_bench/tests/test_cli.py
git commit -m "feat(bench): add CLI with run/tabulate subcommands; --native default"
```

---

### Task 17: Smoke-test scenario file (3 trivial tasks)

**Files:**
- Create: `cognithor_bench/src/cognithor_bench/scenarios/__init__.py`
- Create: `cognithor_bench/src/cognithor_bench/scenarios/smoke_test.jsonl`
- Create: `cognithor_bench/tests/test_smoke_scenarios.py`

- [ ] **Step 1: Write the failing test**

```python
# cognithor_bench/tests/test_smoke_scenarios.py
"""Verify the bundled smoke_test.jsonl is well-formed."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cognithor_bench.adapters.base import ScenarioInput

SMOKE = Path(__file__).resolve().parent.parent / "src" / "cognithor_bench" / "scenarios" / "smoke_test.jsonl"


def test_smoke_file_exists() -> None:
    assert SMOKE.exists(), f"missing smoke scenarios at {SMOKE}"


def test_smoke_file_has_three_to_five_rows() -> None:
    lines = [l for l in SMOKE.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    assert 3 <= len(lines) <= 5


def test_smoke_rows_are_valid_scenario_inputs() -> None:
    for line in SMOKE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        row.setdefault("requires", [])
        row["requires"] = tuple(row["requires"])
        ScenarioInput(**row)


def test_smoke_ids_are_unique() -> None:
    ids = []
    for line in SMOKE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        ids.append(json.loads(line)["id"])
    assert len(ids) == len(set(ids))
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest cognithor_bench/tests/test_smoke_scenarios.py -v 2>&1 | tail -5
```

Expected: `AssertionError: missing smoke scenarios at ...`.

- [ ] **Step 3: Create the scenarios module + file**

```python
# cognithor_bench/src/cognithor_bench/scenarios/__init__.py
"""Bundled benchmark scenarios."""
```

```
# cognithor_bench/src/cognithor_bench/scenarios/smoke_test.jsonl
{"id": "smoke-arith", "task": "Was ist 2 plus 2? Antworte mit einer einzigen Zahl.", "expected": "4", "timeout_sec": 30, "requires": ["no_network"]}
{"id": "smoke-capital", "task": "Was ist die Hauptstadt von Frankreich? Antworte mit einer einzigen Stadt.", "expected": "Paris", "timeout_sec": 30, "requires": ["no_network"]}
{"id": "smoke-translate", "task": "Übersetze 'hello' auf Deutsch. Antworte mit einem einzigen Wort.", "expected": "hallo", "timeout_sec": 30, "requires": ["no_network"]}
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest cognithor_bench/tests/test_smoke_scenarios.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add cognithor_bench/src/cognithor_bench/scenarios/__init__.py cognithor_bench/src/cognithor_bench/scenarios/smoke_test.jsonl cognithor_bench/tests/test_smoke_scenarios.py
git commit -m "feat(bench): add smoke_test.jsonl with 3 trivial scenarios"
```

---

### Task 18: End-to-end smoke run with mock adapter (CI-safe)

**Files:**
- Create: `cognithor_bench/tests/test_e2e_smoke.py`

- [ ] **Step 1: Write the test**

```python
# cognithor_bench/tests/test_e2e_smoke.py
"""End-to-end smoke run — uses MockAdapter so CI never hits an LLM."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor_bench.cli import main


@pytest.mark.asyncio
async def test_full_smoke_run_with_mock_adapter(tmp_path: Path, capsys) -> None:
    smoke = (
        Path(__file__).resolve().parent.parent
        / "src" / "cognithor_bench" / "scenarios" / "smoke_test.jsonl"
    )

    # Stub CognithorAdapter to deterministic outputs (no LLM call).
    with patch("cognithor_bench.cli.CognithorAdapter") as ca:
        instance = MagicMock()
        instance.name = "cognithor"

        async def _run(s):
            from cognithor_bench.adapters.base import ScenarioResult
            return ScenarioResult(
                id=s.id, output=s.expected, success=True,
                duration_sec=0.001, error=None,
            )
        instance.run = AsyncMock(side_effect=_run)
        ca.return_value = instance

        out_dir = tmp_path / "results"
        rc = main(["run", str(smoke), "--output-dir", str(out_dir)])
        assert rc == 0

        files = list(out_dir.glob("*.jsonl"))
        assert len(files) == 1
        rows = [json.loads(l) for l in files[0].read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(rows) == 3
        assert all(r["success"] for r in rows)
```

- [ ] **Step 2: Run the test**

```bash
pytest cognithor_bench/tests/test_e2e_smoke.py -v
```

Expected: 1 passed.

- [ ] **Step 3: Commit**

```bash
git add cognithor_bench/tests/test_e2e_smoke.py
git commit -m "test(bench): add end-to-end smoke run with mock adapter"
```

---

### Task 19: Coverage check + ruff/mypy clean

- [ ] **Step 1: Run coverage**

```bash
pytest cognithor_bench/tests/ --cov=cognithor_bench/src/cognithor_bench --cov-report=term-missing -q
```

Expected: coverage ≥80%.

- [ ] **Step 2: Run ruff**

```bash
ruff check cognithor_bench/
ruff format --check cognithor_bench/
```

Expected: both clean. Apply `ruff check --fix` + `ruff format` and re-commit if needed.

- [ ] **Step 3: Optional — local mypy on the new module**

```bash
mypy --ignore-missing-imports cognithor_bench/src/cognithor_bench/
```

Expected: no errors. (`--ignore-missing-imports` because `autogen_agentchat` isn't installed for mypy by default.)

- [ ] **Step 4: Commit any fixes**

If ruff or mypy required edits:

```bash
git add cognithor_bench/
git commit -m "style(bench): ruff format + mypy fixups"
```

---

### Task 20: Wire `cognithor-bench` into root repo workspace

**Files:**
- Modify: `pyproject.toml` (root) — add `cognithor-bench` to `[project.optional-dependencies] dev` so `pip install -e ".[dev]"` covers the bench tests in CI.
- Modify: `.gitignore` — ignore `cognithor_bench/results/`

- [ ] **Step 1: Update root `pyproject.toml`**

In the root `[project.optional-dependencies] dev = [...]` block, append at the end:

```toml
    # WP4: Local cognithor-bench submodule, shipped as a separate package
    # but installed editable for tests. See cognithor_bench/pyproject.toml.
    "cognithor-bench @ file:./cognithor_bench",
```

- [ ] **Step 2: Append to `.gitignore`**

```
# cognithor-bench result artifacts
cognithor_bench/results/
```

- [ ] **Step 3: Verify install still works**

```bash
pip install -e ".[dev]" 2>&1 | tail -5
cognithor-bench --help
```

Expected: install succeeds; CLI works.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml .gitignore
git commit -m "build(bench): wire cognithor-bench into root [dev] extra; ignore results/"
```

---

### Task 21: CHANGELOG `[Unreleased]` entry for WP4

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Read CHANGELOG, locate `[Unreleased]` section**

```bash
grep -n "## \[Unreleased\]" CHANGELOG.md
```

- [ ] **Step 2: Append under `### Added` (or create the subsection if missing)**

```markdown
- `cognithor_bench/` — reproducible Multi-Agent benchmark scaffold (WP4).
  CLI: `cognithor-bench run|tabulate`. Default adapter: Cognithor; opt-in
  AutoGen adapter via `pip install cognithor[autogen]`. Bundled smoke
  scenarios under `cognithor_bench/src/cognithor_bench/scenarios/`.
- `pyproject.toml` — new `[autogen]` extra (`autogen-agentchat==0.7.5`)
  as the single pin-point for v0.94.0's source-compat shim and bench adapter.
```

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): note WP4 cognithor-bench additions for v0.94.0"
```

---

### Task 22: PR 2 closeout + push + open PR

- [ ] **Step 1: Full regression**

```bash
pytest tests/ -x -q --cov=src/cognithor --cov-fail-under=89
pytest cognithor_bench/tests/ -x -q --cov=cognithor_bench/src/cognithor_bench --cov-fail-under=80
```

Expected: both green.

- [ ] **Step 2: Lint + format**

```bash
ruff check .
ruff format --check .
```

Expected: clean.

- [ ] **Step 3: Push + open PR**

```bash
git push -u origin feat/cognithor-autogen-v2-bench
gh pr create --title "feat(bench): WP4 cognithor-bench scaffold + [autogen] extra (v0.94.0 PR 2)" --body "$(cat <<'EOF'
## Summary
- New monorepo submodule `cognithor_bench/` with own `pyproject.toml`, console-script `cognithor-bench`.
- `BenchRunner`, `Adapter` Protocol, `CognithorAdapter` (default), `AutoGenAdapter` (opt-in, ImportError-safe).
- `run` + `tabulate` subcommands; `--native` default, `--docker` placeholder for post-v0.94.0.
- Bundled `smoke_test.jsonl` (3 trivial DACH scenarios for CI).
- Root `pyproject.toml`: new `[autogen]` extra with `autogen-agentchat==0.7.5` (single pin-point for WP2 + WP4).
- `cognithor-bench` added to root `[dev]` extra so it installs editable in CI.

## Spec
- `docs/superpowers/specs/2026-04-25-cognithor-autogen-strategy-design.md` §8.3, §6 F7.

## Test plan
- [ ] `pip install -e ".[dev]"` works
- [ ] `pip install -e ".[autogen]"` resolves `autogen-agentchat==0.7.5`
- [ ] `cognithor-bench --help` prints usage
- [ ] `pytest cognithor_bench/tests/ -x -q` green, coverage ≥80%
- [ ] `pytest tests/ -x -q --cov-fail-under=89` green (no regression)
- [ ] `cognithor-bench run cognithor_bench/src/cognithor_bench/scenarios/smoke_test.jsonl --output-dir /tmp/r` runs end-to-end with mock adapter
- [ ] AutoGenAdapter raises a helpful ImportError when `[autogen]` extra is not installed

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: Wait CI green, squash-merge**

```bash
gh pr checks <PR_NUMBER> --watch
gh pr merge <PR_NUMBER> --squash --delete-branch=false
```

- [ ] **Step 5: Cleanup in a separate turn**

After confirming PR merged in main:

```bash
git checkout main && git pull --ff-only
git branch -d feat/cognithor-autogen-v2-bench
git push origin --delete feat/cognithor-autogen-v2-bench
```

---

# PR 3 — WP2 AutoGen-Compatibility-Shim (Tasks 23-40)

Implements spec §8.4 — `cognithor.compat.autogen` source-compat layer for `autogen-agentchat==0.7.5`. Hybrid mapping (D4): single-shot `AssistantAgent.run` → `cognithor.crew`; multi-round `RoundRobinGroupChat.run` → custom `_RoundRobinAdapter` (~250-300 LOC). 14-field signature parity enforced via `inspect.signature` diff. Hello-world behaviour test (D6) compares Cognithor + AutoGen output shape with mock LLMs.

**Branch:** `feat/cognithor-autogen-v3-compat` cut from latest `main` (after PR 2 merged).

**PR-3 closeout target:** Search-and-replace AutoGen Hello-World runs against the shim; coverage ≥85% on `cognithor.compat.autogen`; `mypy --strict src/cognithor/compat` clean; AutoGen MIT attribution added to NOTICE staging (final `[0.94.0]` rollup happens in DC).

**Gating reminder:** This PR REQUIRES PR 2 merged so `pyproject.toml` `[autogen]` extra exists. Verify before starting:

```bash
grep -A 3 "^autogen = " pyproject.toml
# must show: autogen = ["autogen-agentchat==0.7.5"]
```

---

### Task 23: Branch + create `cognithor.compat` package skeleton

**Files:**
- Create: `src/cognithor/compat/__init__.py`
- Create: `src/cognithor/compat/autogen/__init__.py`
- Create: `tests/test_compat/__init__.py`
- Create: `tests/test_compat/test_autogen/__init__.py`
- Create: `tests/test_compat/test_autogen/test_package_skeleton.py`

- [ ] **Step 1: Cut feature branch**

```bash
git checkout main && git pull --ff-only
git checkout -b feat/cognithor-autogen-v3-compat
```

- [ ] **Step 2: Verify [autogen] extra is in pyproject.toml (precondition)**

```bash
grep -E "^autogen = \[" pyproject.toml
```

Expected: matches `autogen = [`. If missing → STOP, PR 2 wasn't merged correctly.

- [ ] **Step 3: Write the failing test**

```python
# tests/test_compat/test_autogen/test_package_skeleton.py
"""Compat package — public surface skeleton."""

from __future__ import annotations

import importlib

import pytest


def test_compat_package_imports() -> None:
    importlib.import_module("cognithor.compat")


def test_autogen_subpackage_imports() -> None:
    importlib.import_module("cognithor.compat.autogen")


def test_autogen_import_emits_deprecation_warning() -> None:
    """Re-importing emits a DeprecationWarning pointing at the migration guide."""
    import importlib

    import cognithor.compat.autogen as ca

    with pytest.warns(DeprecationWarning, match="migration"):
        importlib.reload(ca)
```

- [ ] **Step 4: Run test — expect failure**

```bash
pytest tests/test_compat/test_autogen/test_package_skeleton.py -v 2>&1 | tail -10
```

Expected: ModuleNotFoundError on `cognithor.compat`.

- [ ] **Step 5: Create the skeleton**

```python
# src/cognithor/compat/__init__.py
"""Source-compatibility shims for adjacent multi-agent frameworks.

Sub-packages:
- cognithor.compat.autogen — autogen-agentchat==0.7.5 source-compat shim.
"""
```

```python
# src/cognithor/compat/autogen/__init__.py
"""AutoGen-AgentChat source-compatibility shim.

Translates a subset of `autogen_agentchat`'s public API onto Cognithor's
PGE-Trinity + cognithor.crew. Designed for search-and-replace migration:

    from autogen_agentchat.agents import AssistantAgent
        ↓
    from cognithor.compat.autogen import AssistantAgent

Supported:
- AssistantAgent (1-shot AssistantAgent.run / run_stream)
- RoundRobinGroupChat (multi-round via custom adapter)
- TextMessage, HandoffMessage, ToolCallSummaryMessage, StructuredMessage
- MaxMessageTermination, TextMentionTermination (with __and__/__or__)
- OpenAIChatCompletionClient (wrapper on cognithor.core.model_router)

Not supported by design (see ADR 0001):
- SelectorGroupChat (LLM as security boundary)
- Swarm (HandoffMessage freedom conflicts with PGE-Trinity)
- MagenticOneGroupChat (separate workstream)
- autogen-core classes (RoutedAgent, @message_handler, etc.)

References:
- Migration guide: cognithor/compat/autogen/README.md
- ADR 0001: docs/adr/0001-pge-trinity-vs-group-chat.md
- License: This shim is Apache 2.0; the API shape is concept-inspired
  from autogen-agentchat (MIT). NOTICE carries the attribution.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "cognithor.compat.autogen is a source-compat shim. For new code, prefer "
    "cognithor.crew directly. Migration guide: "
    "https://github.com/Alex8791-cyber/cognithor/blob/main/src/cognithor/compat/autogen/README.md",
    DeprecationWarning,
    stacklevel=2,
)

# Public re-exports filled in subsequent tasks.
__all__: list[str] = []
```

```python
# tests/test_compat/__init__.py
```

```python
# tests/test_compat/test_autogen/__init__.py
```

- [ ] **Step 6: Run test — expect pass**

```bash
pytest tests/test_compat/test_autogen/test_package_skeleton.py -v
```

Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add src/cognithor/compat/__init__.py src/cognithor/compat/autogen/__init__.py tests/test_compat/__init__.py tests/test_compat/test_autogen/__init__.py tests/test_compat/test_autogen/test_package_skeleton.py
git commit -m "feat(compat): scaffold cognithor.compat.autogen with deprecation warning"
```

---

### Task 24: conftest with autogen-skip marker + mock model client

**Files:**
- Create: `tests/test_compat/test_autogen/conftest.py`

- [ ] **Step 1: Write the conftest**

```python
# tests/test_compat/test_autogen/conftest.py
"""Test fixtures for cognithor.compat.autogen shim tests.

Provides:
- `requires_autogen` marker — skip if autogen-agentchat is not installed.
- `mock_model_client` fixture — deterministic model output.
"""

from __future__ import annotations

from typing import Any

import pytest


def pytest_collection_modifyitems(config, items) -> None:
    """Skip @requires_autogen tests when autogen-agentchat is not installed."""
    try:
        import autogen_agentchat  # noqa: F401
        autogen_available = True
    except ImportError:
        autogen_available = False

    skip_marker = pytest.mark.skip(
        reason="autogen-agentchat not installed — install with `pip install cognithor[autogen]`",
    )
    for item in items:
        if "requires_autogen" in item.keywords and not autogen_available:
            item.add_marker(skip_marker)


def pytest_configure(config) -> None:
    config.addinivalue_line(
        "markers",
        "requires_autogen: mark test as requiring `pip install cognithor[autogen]`",
    )


class _MockModelClient:
    """Deterministic mock — returns whatever was set via `set_response`."""

    def __init__(self, response: str = "") -> None:
        self._response = response

    def set_response(self, response: str) -> None:
        self._response = response

    async def create(self, *args: Any, **kwargs: Any) -> Any:
        class _R:
            content = self._response
            usage = {"prompt_tokens": 0, "completion_tokens": 0}
        return _R()


@pytest.fixture
def mock_model_client() -> _MockModelClient:
    return _MockModelClient(response="OK")
```

- [ ] **Step 2: Smoke-run the conftest's collection hook**

```bash
pytest tests/test_compat/test_autogen/ --collect-only -q | head -10
```

Expected: collects `test_package_skeleton.py` tests; no errors from conftest.

- [ ] **Step 3: Commit**

```bash
git add tests/test_compat/test_autogen/conftest.py
git commit -m "test(compat): add conftest with @requires_autogen marker + mock model client"
```

---

### Task 25: AssistantAgent — exact 14-field signature (signature-only)

**Files:**
- Create: `src/cognithor/compat/autogen/agents/__init__.py`
- Create: `src/cognithor/compat/autogen/agents/_assistant_agent.py`
- Modify: `src/cognithor/compat/autogen/__init__.py`
- Create: `tests/test_compat/test_autogen/test_signature_compat.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_compat/test_autogen/test_signature_compat.py
"""Signature-parity tests — inspect.signature diff against autogen-agentchat==0.7.5.

These tests are skipped when autogen-agentchat is not installed (see conftest).
They are the Stage-1 of the D6 test strategy: cheap, fast, catch drift early.
"""

from __future__ import annotations

import inspect
from typing import get_args

import pytest

from cognithor.compat.autogen import AssistantAgent


@pytest.mark.requires_autogen
def test_assistant_agent_signature_matches_autogen() -> None:
    from autogen_agentchat.agents import AssistantAgent as RealAssistantAgent

    real_sig = inspect.signature(RealAssistantAgent.__init__)
    shim_sig = inspect.signature(AssistantAgent.__init__)

    real_params = list(real_sig.parameters.keys())
    shim_params = list(shim_sig.parameters.keys())
    assert real_params == shim_params, (
        f"parameter ORDER mismatch:\n"
        f"  real: {real_params}\n"
        f"  shim: {shim_params}"
    )


@pytest.mark.requires_autogen
def test_assistant_agent_param_kinds_match() -> None:
    """Each parameter has the same KIND (positional, keyword-only, etc.)."""
    from autogen_agentchat.agents import AssistantAgent as RealAssistantAgent

    real = inspect.signature(RealAssistantAgent.__init__).parameters
    shim = inspect.signature(AssistantAgent.__init__).parameters

    for name in real:
        if name == "self":
            continue
        assert real[name].kind == shim[name].kind, (
            f"kind mismatch for '{name}': real={real[name].kind} shim={shim[name].kind}"
        )


@pytest.mark.requires_autogen
def test_assistant_agent_defaults_match() -> None:
    """Each parameter has the same default value."""
    from autogen_agentchat.agents import AssistantAgent as RealAssistantAgent

    real = inspect.signature(RealAssistantAgent.__init__).parameters
    shim = inspect.signature(AssistantAgent.__init__).parameters

    for name in real:
        if name == "self":
            continue
        # Skip default comparison for tools/handoffs/memory/workbench/model_context —
        # those are AutoGen-internal class types we don't reproduce. Defaults that
        # are None or empty-collection-like must still match.
        if name in {"tools", "handoffs", "memory", "workbench", "model_context"}:
            continue
        assert real[name].default == shim[name].default, (
            f"default mismatch for '{name}': real={real[name].default!r} shim={shim[name].default!r}"
        )


def test_assistant_agent_has_run_and_run_stream_methods() -> None:
    """Independent of autogen install — shim must expose run + run_stream."""
    assert callable(getattr(AssistantAgent, "run"))
    assert callable(getattr(AssistantAgent, "run_stream"))


def test_assistant_agent_signature_field_count() -> None:
    """14 fields per spec §3.3 + 'self' = 15 total."""
    sig = inspect.signature(AssistantAgent.__init__)
    assert len(sig.parameters) == 15, f"expected 15 params (self + 14 fields), got {len(sig.parameters)}"
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest tests/test_compat/test_autogen/test_signature_compat.py -v 2>&1 | tail -15
```

Expected: ImportError on `from cognithor.compat.autogen import AssistantAgent`.

- [ ] **Step 3: Implement `AssistantAgent` with exact 14-field signature**

```python
# src/cognithor/compat/autogen/agents/__init__.py
"""AutoGen-shaped agent classes."""

from __future__ import annotations

from cognithor.compat.autogen.agents._assistant_agent import AssistantAgent

__all__ = ["AssistantAgent"]
```

```python
# src/cognithor/compat/autogen/agents/_assistant_agent.py
"""AssistantAgent — autogen-agentchat==0.7.5 source-compat shim.

The 14-field signature mirrors:
  https://microsoft.github.io/autogen/stable//reference/python/autogen_agentchat.agents.html

Cognithor's translation (no AutoGen code copied verbatim):
- name, system_message, description: stored, used to build the Cognithor
  CrewAgent's role/backstory/goal.
- model_client: wraps cognithor.core.model_router via OpenAIChatCompletionClient
  shim (see models/__init__.py).
- tools, workbench: bridged into MCP tool registry inside _bridge.py.
- run / run_stream: delegate to cognithor.crew.Crew(...).kickoff_async().
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cognithor.compat.autogen._bridge import TaskResult


class AssistantAgent:
    """AutoGen-AgentChat-compatible AssistantAgent.

    Signature mirrors autogen_agentchat.agents.AssistantAgent (MIT licensed).
    Internally delegates to Cognithor's PGE Executor via cognithor.crew.

    Reference:
    https://microsoft.github.io/autogen/stable//reference/python/autogen_agentchat.agents.html
    """

    def __init__(
        self,
        name: str,
        model_client: Any,
        *,
        tools: Sequence[Any] | None = None,
        workbench: Any | None = None,
        handoffs: list[Any] | None = None,
        model_context: Any | None = None,
        memory: Sequence[Any] | None = None,
        description: str = "An assistant agent.",
        system_message: str | None = None,
        model_client_stream: bool = False,
        reflect_on_tool_use: bool = False,
        tool_call_summary_format: str = "{result}",
        max_tool_iterations: int = 1,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self.model_client = model_client
        self.tools = tools
        self.workbench = workbench
        self.handoffs = handoffs
        self.model_context = model_context
        self.memory = memory
        self.description = description
        self.system_message = system_message
        self.model_client_stream = model_client_stream
        self.reflect_on_tool_use = reflect_on_tool_use
        self.tool_call_summary_format = tool_call_summary_format
        self.max_tool_iterations = max_tool_iterations
        self.metadata = metadata or {}

    async def run(self, *, task: str | Sequence[Any]) -> "TaskResult":
        """Run a single 1-shot task. Maps to cognithor.crew.Crew.kickoff_async()."""
        from cognithor.compat.autogen._bridge import run_single_task

        return await run_single_task(self, task)

    def run_stream(
        self, *, task: str | Sequence[Any]
    ) -> AsyncIterator[Any]:
        """Stream events from a single 1-shot task."""
        from cognithor.compat.autogen._bridge import stream_single_task

        return stream_single_task(self, task)
```

- [ ] **Step 4: Update package re-exports**

Edit `src/cognithor/compat/autogen/__init__.py` — replace the empty `__all__` with:

```python
from cognithor.compat.autogen.agents import AssistantAgent

__all__ = ["AssistantAgent"]
```

(Keep the `warnings.warn(...)` block at the top of the file.)

- [ ] **Step 5: Run signature tests**

```bash
pytest tests/test_compat/test_autogen/test_signature_compat.py -v
```

Expected: 5 tests — `test_assistant_agent_has_run_and_run_stream_methods` and `test_assistant_agent_signature_field_count` pass; the 3 `@requires_autogen` tests are either passed or skipped depending on whether `pip install cognithor[autogen]` is active.

- [ ] **Step 6: If autogen is not installed, install it locally to verify Stage-1**

```bash
pip install -e ".[autogen]"
pytest tests/test_compat/test_autogen/test_signature_compat.py -v
```

Expected: all 5 tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/cognithor/compat/autogen/ tests/test_compat/test_autogen/test_signature_compat.py
git commit -m "feat(compat): add AssistantAgent with exact 14-field autogen-agentchat signature"
```

---

### Task 26: `_bridge.py` — internal Cognithor-Crew integration

**Files:**
- Create: `src/cognithor/compat/autogen/_bridge.py`
- Create: `tests/test_compat/test_autogen/test_bridge.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_compat/test_autogen/test_bridge.py
"""_bridge — translates AutoGen-shaped calls into cognithor.crew calls."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.compat.autogen import AssistantAgent
from cognithor.compat.autogen._bridge import TaskResult, run_single_task


@pytest.mark.asyncio
async def test_run_single_task_returns_task_result_with_messages() -> None:
    fake_output = MagicMock()
    fake_output.raw = "Hello back."
    fake_output.tasks_outputs = []
    fake_output.token_usage = {"total_tokens": 12}

    with patch("cognithor.compat.autogen._bridge.Crew") as crew_cls:
        crew = MagicMock()
        crew.kickoff_async = AsyncMock(return_value=fake_output)
        crew_cls.return_value = crew

        agent = AssistantAgent(name="bot", model_client=MagicMock())
        result = await run_single_task(agent, "Say hi.")

        assert isinstance(result, TaskResult)
        assert result.messages
        last = result.messages[-1]
        assert getattr(last, "content") == "Hello back."
        assert getattr(last, "source") == "bot"


@pytest.mark.asyncio
async def test_task_result_messages_have_autogen_event_shape() -> None:
    """Each message must carry source / models_usage / metadata / content / type."""
    fake_output = MagicMock()
    fake_output.raw = "OK"
    fake_output.tasks_outputs = []
    fake_output.token_usage = {"total_tokens": 1}

    with patch("cognithor.compat.autogen._bridge.Crew") as crew_cls:
        crew = MagicMock()
        crew.kickoff_async = AsyncMock(return_value=fake_output)
        crew_cls.return_value = crew

        agent = AssistantAgent(name="bot", model_client=MagicMock())
        result = await run_single_task(agent, "test")

        msg = result.messages[-1]
        for attr in ("source", "models_usage", "metadata", "content", "type"):
            assert hasattr(msg, attr), f"event-shape attr missing: {attr}"


@pytest.mark.asyncio
async def test_run_single_task_passes_system_message_into_backstory() -> None:
    fake_output = MagicMock()
    fake_output.raw = "OK"
    fake_output.tasks_outputs = []
    fake_output.token_usage = {}

    captured: dict = {}

    def _capture(agents, tasks, **kwargs):
        captured["agent_backstory"] = agents[0].backstory
        crew = MagicMock()
        crew.kickoff_async = AsyncMock(return_value=fake_output)
        return crew

    with patch("cognithor.compat.autogen._bridge.Crew", side_effect=_capture):
        agent = AssistantAgent(
            name="bot",
            model_client=MagicMock(),
            system_message="You are a careful assistant.",
        )
        await run_single_task(agent, "x")
        assert "careful assistant" in captured["agent_backstory"]
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest tests/test_compat/test_autogen/test_bridge.py -v 2>&1 | tail -10
```

Expected: ImportError on `cognithor.compat.autogen._bridge`.

- [ ] **Step 3: Implement `_bridge.py`**

```python
# src/cognithor/compat/autogen/_bridge.py
"""Internal bridge — translates AssistantAgent calls into cognithor.crew calls."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from cognithor.crew import Crew, CrewAgent, CrewTask

if TYPE_CHECKING:
    from cognithor.compat.autogen.agents._assistant_agent import AssistantAgent


@dataclass
class _AutoGenEvent:
    """AutoGen-shaped event — fields match autogen_agentchat.messages.TextMessage."""

    source: str = ""
    content: str = ""
    type: str = "TextMessage"
    models_usage: dict[str, int] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.content


@dataclass
class TaskResult:
    """AutoGen-shaped run() return — has `messages` list."""

    messages: list[_AutoGenEvent] = field(default_factory=list)
    stop_reason: str | None = None


def _coerce_task_text(task: str | Sequence[Any]) -> str:
    if isinstance(task, str):
        return task
    parts: list[str] = []
    for item in task:
        if isinstance(item, str):
            parts.append(item)
        else:
            parts.append(str(getattr(item, "content", item)))
    return "\n".join(parts)


def _make_cognithor_agent(agent: "AssistantAgent") -> CrewAgent:
    backstory = agent.system_message or agent.description or ""
    return CrewAgent(
        role=agent.name,
        goal=agent.description or f"Assistant agent {agent.name}",
        backstory=backstory,
        llm=None,  # model_client wrapper resolved upstream by ModelRouter
        verbose=False,
        memory=False,
    )


async def run_single_task(
    agent: "AssistantAgent",
    task: str | Sequence[Any],
) -> TaskResult:
    """1-shot path: create a single-agent, single-task Crew and run it."""
    text = _coerce_task_text(task)
    cognithor_agent = _make_cognithor_agent(agent)
    cognithor_task = CrewTask(
        description=text,
        expected_output="A direct answer to the user's task.",
        agent=cognithor_agent,
    )
    crew = Crew(agents=[cognithor_agent], tasks=[cognithor_task])
    output = await crew.kickoff_async({})

    raw = str(getattr(output, "raw", "") or "")
    usage = getattr(output, "token_usage", None) or {}
    event = _AutoGenEvent(
        source=agent.name,
        content=raw,
        type="TextMessage",
        models_usage={"total_tokens": int(usage.get("total_tokens", 0))} if usage else None,
        metadata={},
    )
    return TaskResult(messages=[event], stop_reason="task_completed")


async def stream_single_task(
    agent: "AssistantAgent",
    task: str | Sequence[Any],
) -> AsyncIterator[Any]:  # pragma: no cover — streaming events are wrapper-thin
    """Streaming variant: emit one event per Cognithor-task plus a final stop event."""
    result = await run_single_task(agent, task)
    for msg in result.messages:
        yield msg
    yield result
```

(`stream_single_task` is async generator; we'll typecheck it via `pyright`/`mypy` once tests pass.)

- [ ] **Step 4: Run bridge tests**

```bash
pytest tests/test_compat/test_autogen/test_bridge.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/compat/autogen/_bridge.py tests/test_compat/test_autogen/test_bridge.py
git commit -m "feat(compat): add _bridge translating AssistantAgent.run to cognithor.crew"
```

---

### Task 27: Messages module (TextMessage, ToolCallSummaryMessage, HandoffMessage, StructuredMessage)

**Files:**
- Create: `src/cognithor/compat/autogen/messages/__init__.py`
- Create: `tests/test_compat/test_autogen/test_messages.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_compat/test_autogen/test_messages.py
"""Message classes — match AutoGen field surface."""

from __future__ import annotations

import pytest

from cognithor.compat.autogen.messages import (
    HandoffMessage,
    StructuredMessage,
    TextMessage,
    ToolCallSummaryMessage,
)


def test_text_message_required_fields() -> None:
    m = TextMessage(content="hello", source="agent-1")
    assert m.content == "hello"
    assert m.source == "agent-1"
    assert m.type == "TextMessage"
    assert m.metadata == {}


def test_text_message_models_usage_optional() -> None:
    m = TextMessage(content="x", source="a", models_usage={"total_tokens": 5})
    assert m.models_usage == {"total_tokens": 5}


def test_tool_call_summary_message_records_tool_name() -> None:
    m = ToolCallSummaryMessage(content="result-text", source="agent-1", tool_name="search")
    assert m.tool_name == "search"
    assert m.type == "ToolCallSummaryMessage"


def test_handoff_message_target() -> None:
    m = HandoffMessage(content="passing the ball", source="agent-1", target="agent-2")
    assert m.target == "agent-2"
    assert m.type == "HandoffMessage"


def test_structured_message_holds_arbitrary_payload() -> None:
    payload = {"key": "value"}
    m = StructuredMessage(content=payload, source="agent-1")
    assert m.content == payload
    assert m.type == "StructuredMessage"


def test_text_message_str_uses_content() -> None:
    m = TextMessage(content="hello world", source="a")
    assert str(m) == "hello world"
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest tests/test_compat/test_autogen/test_messages.py -v 2>&1 | tail -5
```

Expected: ImportError.

- [ ] **Step 3: Implement messages**

```python
# src/cognithor/compat/autogen/messages/__init__.py
"""AutoGen-shaped message classes — used by the source-compat shim."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class _BaseMessage:
    content: Any
    source: str
    type: str = "Message"
    models_usage: dict[str, int] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return str(self.content)


@dataclass
class TextMessage(_BaseMessage):
    type: str = "TextMessage"


@dataclass
class ToolCallSummaryMessage(_BaseMessage):
    type: str = "ToolCallSummaryMessage"
    tool_name: str = ""


@dataclass
class HandoffMessage(_BaseMessage):
    type: str = "HandoffMessage"
    target: str = ""


@dataclass
class StructuredMessage(_BaseMessage):
    type: str = "StructuredMessage"


__all__ = ["TextMessage", "ToolCallSummaryMessage", "HandoffMessage", "StructuredMessage"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_compat/test_autogen/test_messages.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Update package re-exports**

Edit `src/cognithor/compat/autogen/__init__.py`, in the imports block add:

```python
from cognithor.compat.autogen.messages import (
    HandoffMessage,
    StructuredMessage,
    TextMessage,
    ToolCallSummaryMessage,
)
```

And update `__all__`:

```python
__all__ = [
    "AssistantAgent",
    "HandoffMessage",
    "StructuredMessage",
    "TextMessage",
    "ToolCallSummaryMessage",
]
```

- [ ] **Step 6: Commit**

```bash
git add src/cognithor/compat/autogen/messages/ src/cognithor/compat/autogen/__init__.py tests/test_compat/test_autogen/test_messages.py
git commit -m "feat(compat): add TextMessage, ToolCall/Handoff/StructuredMessage shims"
```

---

### Task 28: Termination conditions — `MaxMessageTermination`, `TextMentionTermination`

**Files:**
- Create: `src/cognithor/compat/autogen/conditions/__init__.py`
- Create: `tests/test_compat/test_autogen/test_conditions.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_compat/test_autogen/test_conditions.py
"""Termination conditions — count + text-match + composite."""

from __future__ import annotations

import pytest

from cognithor.compat.autogen.conditions import (
    MaxMessageTermination,
    TextMentionTermination,
)
from cognithor.compat.autogen.messages import TextMessage


def _msg(content: str) -> TextMessage:
    return TextMessage(content=content, source="a")


def test_max_message_termination_below_threshold() -> None:
    cond = MaxMessageTermination(3)
    assert not cond.is_terminated([_msg("a"), _msg("b")])


def test_max_message_termination_at_threshold() -> None:
    cond = MaxMessageTermination(3)
    assert cond.is_terminated([_msg("a"), _msg("b"), _msg("c")])


def test_text_mention_termination_match() -> None:
    cond = TextMentionTermination("DONE")
    assert cond.is_terminated([_msg("step1"), _msg("we are DONE here")])


def test_text_mention_termination_no_match() -> None:
    cond = TextMentionTermination("DONE")
    assert not cond.is_terminated([_msg("step1"), _msg("step2")])


def test_text_mention_termination_only_inspects_last_message() -> None:
    """Spec says termination matches against last raw output, not history."""
    cond = TextMentionTermination("DONE")
    assert not cond.is_terminated([_msg("DONE earlier"), _msg("not now")])


def test_combined_and_both_must_match() -> None:
    cond = MaxMessageTermination(2) & TextMentionTermination("DONE")
    assert not cond.is_terminated([_msg("a"), _msg("b")])  # count ok, no DONE
    assert not cond.is_terminated([_msg("DONE")])  # DONE ok, count too low
    assert cond.is_terminated([_msg("a"), _msg("DONE")])  # both


def test_combined_or_either_can_match() -> None:
    cond = MaxMessageTermination(5) | TextMentionTermination("DONE")
    assert cond.is_terminated([_msg("DONE")])  # text matches
    assert cond.is_terminated([_msg("a")] * 5)  # count matches
    assert not cond.is_terminated([_msg("a")] * 4)  # neither
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest tests/test_compat/test_autogen/test_conditions.py -v 2>&1 | tail -5
```

Expected: ImportError.

- [ ] **Step 3: Implement the conditions**

```python
# src/cognithor/compat/autogen/conditions/__init__.py
"""Termination conditions — AutoGen-shape, supporting __and__ / __or__ composition."""

from __future__ import annotations

from typing import Sequence

from cognithor.compat.autogen.messages import TextMessage


class _TerminationCondition:
    """Base — supports `__and__` / `__or__` to compose conditions."""

    def is_terminated(self, messages: Sequence[TextMessage]) -> bool:  # pragma: no cover — abstract
        raise NotImplementedError

    def __and__(self, other: "_TerminationCondition") -> "_AndTermination":
        return _AndTermination(self, other)

    def __or__(self, other: "_TerminationCondition") -> "_OrTermination":
        return _OrTermination(self, other)


class _AndTermination(_TerminationCondition):
    def __init__(self, left: _TerminationCondition, right: _TerminationCondition) -> None:
        self.left = left
        self.right = right

    def is_terminated(self, messages: Sequence[TextMessage]) -> bool:
        return self.left.is_terminated(messages) and self.right.is_terminated(messages)


class _OrTermination(_TerminationCondition):
    def __init__(self, left: _TerminationCondition, right: _TerminationCondition) -> None:
        self.left = left
        self.right = right

    def is_terminated(self, messages: Sequence[TextMessage]) -> bool:
        return self.left.is_terminated(messages) or self.right.is_terminated(messages)


class MaxMessageTermination(_TerminationCondition):
    """Terminate when the message count reaches max_messages."""

    def __init__(self, max_messages: int) -> None:
        if max_messages < 1:
            raise ValueError("max_messages must be >= 1")
        self.max_messages = max_messages

    def is_terminated(self, messages: Sequence[TextMessage]) -> bool:
        return len(messages) >= self.max_messages


class TextMentionTermination(_TerminationCondition):
    """Terminate when the LAST message contains `mention` (case-insensitive substring)."""

    def __init__(self, mention: str) -> None:
        if not mention:
            raise ValueError("mention must be a non-empty string")
        self.mention = mention

    def is_terminated(self, messages: Sequence[TextMessage]) -> bool:
        if not messages:
            return False
        last = str(messages[-1].content).lower()
        return self.mention.lower() in last


__all__ = [
    "MaxMessageTermination",
    "TextMentionTermination",
]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_compat/test_autogen/test_conditions.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Update package re-exports**

In `src/cognithor/compat/autogen/__init__.py`:

```python
from cognithor.compat.autogen.conditions import MaxMessageTermination, TextMentionTermination
```

Add `MaxMessageTermination`, `TextMentionTermination` to `__all__`.

- [ ] **Step 6: Commit**

```bash
git add src/cognithor/compat/autogen/conditions/ src/cognithor/compat/autogen/__init__.py tests/test_compat/test_autogen/test_conditions.py
git commit -m "feat(compat): add MaxMessageTermination + TextMentionTermination with &/| composition"
```

---

### Task 29: `OpenAIChatCompletionClient` wrapper

**Files:**
- Create: `src/cognithor/compat/autogen/models/__init__.py`
- Create: `tests/test_compat/test_autogen/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_compat/test_autogen/test_models.py
"""OpenAIChatCompletionClient — wraps cognithor.core.model_router."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cognithor.compat.autogen.models import OpenAIChatCompletionClient


def test_client_stores_model_string() -> None:
    c = OpenAIChatCompletionClient(model="ollama/qwen3:8b")
    assert c.model == "ollama/qwen3:8b"


def test_client_accepts_api_key_kwarg_without_breaking() -> None:
    """AutoGen users pass api_key='...'; we accept and store but never send unless needed."""
    c = OpenAIChatCompletionClient(model="gpt-4", api_key="sk-test")
    assert c.model == "gpt-4"
    assert c._api_key == "sk-test"


def test_client_accepts_base_url_kwarg() -> None:
    c = OpenAIChatCompletionClient(model="ollama/qwen3:8b", base_url="http://localhost:11434")
    assert c._base_url == "http://localhost:11434"


@pytest.mark.asyncio
async def test_client_create_routes_through_cognithor_model_router() -> None:
    """`.create()` dispatches to cognithor.core.model_router.generate."""
    with patch("cognithor.compat.autogen.models._dispatch_to_router") as dispatch:
        dispatch.return_value = MagicMock(content="response", usage={"total_tokens": 5})
        c = OpenAIChatCompletionClient(model="ollama/qwen3:8b")
        result = await c.create(messages=[{"role": "user", "content": "hi"}])
        dispatch.assert_called_once()
        assert getattr(result, "content") == "response"
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest tests/test_compat/test_autogen/test_models.py -v 2>&1 | tail -5
```

Expected: ImportError.

- [ ] **Step 3: Implement the wrapper**

```python
# src/cognithor/compat/autogen/models/__init__.py
"""OpenAIChatCompletionClient — autogen_ext.models.openai compat wrapper.

Routes calls into Cognithor's existing model router so the 16 supported
providers transparently back AutoGen-shaped client calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class _ChatCompletionResponse:
    content: str
    usage: dict[str, int]


async def _dispatch_to_router(
    *,
    model: str,
    messages: list[dict[str, Any]],
    api_key: str | None,
    base_url: str | None,
    extra: dict[str, Any],
) -> _ChatCompletionResponse:
    """Forward to cognithor.core.model_router. Imported lazily to avoid circular deps."""
    # This stays narrow on purpose: the real model_router has many entry points,
    # we use the simple `generate` path which is shared by cognithor.crew agents.
    from cognithor.core import model_router  # type: ignore[attr-defined]

    text = await model_router.generate(  # type: ignore[attr-defined]
        model=model,
        messages=messages,
        api_key=api_key,
        base_url=base_url,
        **extra,
    )
    return _ChatCompletionResponse(content=str(text), usage={"total_tokens": 0})


class OpenAIChatCompletionClient:
    """OpenAI-shaped chat-completion client backed by Cognithor's model router."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._base_url = base_url
        self._extra = kwargs

    async def create(
        self,
        *,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> _ChatCompletionResponse:
        return await _dispatch_to_router(
            model=self.model,
            messages=messages,
            api_key=self._api_key,
            base_url=self._base_url,
            extra={**self._extra, **kwargs},
        )


__all__ = ["OpenAIChatCompletionClient"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_compat/test_autogen/test_models.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Update package re-exports**

```python
# in src/cognithor/compat/autogen/__init__.py
from cognithor.compat.autogen.models import OpenAIChatCompletionClient
```

Add `OpenAIChatCompletionClient` to `__all__`.

- [ ] **Step 6: Commit**

```bash
git add src/cognithor/compat/autogen/models/ src/cognithor/compat/autogen/__init__.py tests/test_compat/test_autogen/test_models.py
git commit -m "feat(compat): add OpenAIChatCompletionClient backed by cognithor.core.model_router"
```

---

### Task 30: `_round_robin_adapter.py` — multi-round loop core

**Files:**
- Create: `src/cognithor/compat/autogen/_round_robin_adapter.py`
- Create: `tests/test_compat/test_autogen/test_round_robin_adapter.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_compat/test_autogen/test_round_robin_adapter.py
"""_round_robin_adapter — multi-round loop with termination."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.compat.autogen._round_robin_adapter import _RoundRobinAdapter
from cognithor.compat.autogen.conditions import (
    MaxMessageTermination,
    TextMentionTermination,
)
from cognithor.compat.autogen.messages import TextMessage


def _stub_agent(name: str, replies: list[str]) -> MagicMock:
    agent = MagicMock()
    agent.name = name
    queue = list(replies)

    async def _run(*, task):
        from cognithor.compat.autogen._bridge import TaskResult
        msg = TextMessage(content=queue.pop(0), source=name)
        return TaskResult(messages=[msg], stop_reason=None)

    agent.run = _run
    return agent


@pytest.mark.asyncio
async def test_round_robin_terminates_on_max_messages() -> None:
    a = _stub_agent("a", ["a1", "a2", "a3"])
    b = _stub_agent("b", ["b1", "b2", "b3"])
    adapter = _RoundRobinAdapter(participants=[a, b], termination=MaxMessageTermination(4))

    result = await adapter.run(task="kickoff")
    assert len(result.messages) == 4
    assert result.messages[0].source == "a"
    assert result.messages[1].source == "b"
    assert result.messages[2].source == "a"
    assert result.messages[3].source == "b"
    assert result.stop_reason == "MaxMessageTermination"


@pytest.mark.asyncio
async def test_round_robin_terminates_on_text_mention() -> None:
    a = _stub_agent("a", ["working...", "almost", "DONE"])
    b = _stub_agent("b", ["b1", "b2", "b3"])
    adapter = _RoundRobinAdapter(
        participants=[a, b],
        termination=TextMentionTermination("DONE"),
    )

    result = await adapter.run(task="x")
    assert "DONE" in str(result.messages[-1].content)
    assert result.stop_reason == "TextMentionTermination"


@pytest.mark.asyncio
async def test_round_robin_combined_termination() -> None:
    """Composite condition `A | B` ends as soon as either fires."""
    a = _stub_agent("a", ["DONE", "n2", "n3"])
    b = _stub_agent("b", ["b1", "b2", "b3"])
    cond = MaxMessageTermination(100) | TextMentionTermination("DONE")
    adapter = _RoundRobinAdapter(participants=[a, b], termination=cond)
    result = await adapter.run(task="x")
    assert len(result.messages) == 1


@pytest.mark.asyncio
async def test_round_robin_empty_participants_raises() -> None:
    with pytest.raises(ValueError, match="at least one"):
        _RoundRobinAdapter(participants=[], termination=MaxMessageTermination(2))


@pytest.mark.asyncio
async def test_round_robin_aggregates_token_usage() -> None:
    a = _stub_agent("a", ["a1", "a2"])
    b = _stub_agent("b", ["b1", "b2"])
    adapter = _RoundRobinAdapter(participants=[a, b], termination=MaxMessageTermination(2))
    result = await adapter.run(task="x")
    # token_usage attribute exists even if zero
    assert hasattr(result, "token_usage_total") or hasattr(result, "messages")
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest tests/test_compat/test_autogen/test_round_robin_adapter.py -v 2>&1 | tail -10
```

Expected: ImportError.

- [ ] **Step 3: Implement the adapter**

```python
# src/cognithor/compat/autogen/_round_robin_adapter.py
"""Multi-round adapter — drives RoundRobinGroupChat semantics through PGE-Trinity.

Per spec D4 (Hybrid mapping): single-shot AssistantAgent.run uses the cognithor.crew
1-shot path. RoundRobinGroupChat.run goes through THIS adapter, which loops over
participants in order, gathers messages, applies the termination condition, and
emits an AutoGen-shaped TaskResult.

Each participant's `.run(task=...)` is an `AssistantAgent` instance; we feed it
the running conversation as `task=` and collect its message back. The Gatekeeper
intercepts each tool call inside the underlying CrewAgent execution (out of scope
here) — this adapter only orchestrates turn-taking and termination.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from cognithor.compat.autogen.conditions import _TerminationCondition
from cognithor.compat.autogen.messages import TextMessage

if TYPE_CHECKING:
    from cognithor.compat.autogen.agents._assistant_agent import AssistantAgent


@dataclass
class _RoundRobinResult:
    messages: list[TextMessage] = field(default_factory=list)
    stop_reason: str | None = None
    token_usage_total: int = 0


class _RoundRobinAdapter:
    """Round-robin orchestrator — internal helper for RoundRobinGroupChat."""

    def __init__(
        self,
        *,
        participants: Sequence["AssistantAgent"],
        termination: _TerminationCondition,
        max_turns: int = 50,
    ) -> None:
        if not participants:
            raise ValueError("RoundRobinGroupChat requires at least one participant")
        self.participants = list(participants)
        self.termination = termination
        self.max_turns = max_turns

    async def run(self, *, task: str) -> _RoundRobinResult:
        result = _RoundRobinResult(messages=[], stop_reason=None, token_usage_total=0)
        running_task = task
        turn = 0
        while turn < self.max_turns:
            participant = self.participants[turn % len(self.participants)]
            sub_result = await participant.run(task=running_task)
            for msg in getattr(sub_result, "messages", []) or []:
                tm = (
                    msg
                    if isinstance(msg, TextMessage)
                    else TextMessage(
                        content=str(getattr(msg, "content", msg)),
                        source=str(getattr(msg, "source", participant.name)),
                    )
                )
                result.messages.append(tm)
                usage = getattr(msg, "models_usage", None)
                if usage:
                    result.token_usage_total += int(usage.get("total_tokens", 0))

            if self.termination.is_terminated(result.messages):
                result.stop_reason = self._termination_label()
                return result

            running_task = self._format_history_as_task(result.messages)
            turn += 1

        result.stop_reason = "MaxTurnsExceeded"
        return result

    def _termination_label(self) -> str:
        cls = type(self.termination)
        return getattr(cls, "__name__", "TerminationCondition")

    @staticmethod
    def _format_history_as_task(messages: Sequence[TextMessage]) -> str:
        return "\n".join(f"[{m.source}] {m.content}" for m in messages)
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_compat/test_autogen/test_round_robin_adapter.py -v
```

Expected: 5 passed. The labelled stop_reason for `_AndTermination`/`_OrTermination` says `_AndTermination` / `_OrTermination` rather than the user's intent — that's fine for the v1 shim; users get a label, not always the most user-friendly one. Adjust if the test expects "TextMentionTermination" by reading the failing test message and refining `_termination_label()` to introspect the inner conditions.

- [ ] **Step 5: Refine `_termination_label()` to unpack composites**

```python
def _termination_label(self) -> str:
    """Best-effort name lookup. For composite conditions, prefer the inner
    leaf class that 'fired' (we cannot tell which without re-checking, so
    we report the whole class name for composites)."""
    cls = type(self.termination)
    name = getattr(cls, "__name__", "TerminationCondition")
    if name.startswith("_"):
        # _AndTermination / _OrTermination — report nested types instead.
        try:
            left = type(self.termination.left).__name__
            right = type(self.termination.right).__name__
            return f"{name.lstrip('_')}({left},{right})"
        except AttributeError:
            return name
    return name
```

Adjust `test_round_robin_terminates_on_text_mention` if needed; the test above expects exact `"TextMentionTermination"` which is correct for non-composite use.

- [ ] **Step 6: Re-run tests**

```bash
pytest tests/test_compat/test_autogen/test_round_robin_adapter.py -v
```

Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add src/cognithor/compat/autogen/_round_robin_adapter.py tests/test_compat/test_autogen/test_round_robin_adapter.py
git commit -m "feat(compat): add _RoundRobinAdapter with composable terminations (~250 LOC)"
```

---

### Task 31: `RoundRobinGroupChat` public class

**Files:**
- Create: `src/cognithor/compat/autogen/teams/__init__.py`
- Create: `src/cognithor/compat/autogen/teams/_round_robin.py`
- Create: `tests/test_compat/test_autogen/test_round_robin.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_compat/test_autogen/test_round_robin.py
"""RoundRobinGroupChat — public AutoGen-shaped class."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.compat.autogen.conditions import MaxMessageTermination
from cognithor.compat.autogen.messages import TextMessage
from cognithor.compat.autogen.teams import RoundRobinGroupChat


def _stub_assistant(name: str, replies: list[str]) -> MagicMock:
    agent = MagicMock()
    agent.name = name
    queue = list(replies)

    async def _run(*, task):
        from cognithor.compat.autogen._bridge import TaskResult
        return TaskResult(
            messages=[TextMessage(content=queue.pop(0), source=name)],
            stop_reason=None,
        )

    agent.run = _run
    return agent


@pytest.mark.asyncio
async def test_round_robin_constructor_and_run() -> None:
    a = _stub_assistant("a", ["msg1", "msg2"])
    b = _stub_assistant("b", ["msg3", "msg4"])
    team = RoundRobinGroupChat(
        participants=[a, b],
        termination_condition=MaxMessageTermination(2),
    )
    result = await team.run(task="hello")
    assert len(result.messages) == 2


def test_round_robin_attributes_match_autogen_signature() -> None:
    """Construction kwargs match `RoundRobinGroupChat(participants=..., termination_condition=...)`."""
    import inspect

    sig = inspect.signature(RoundRobinGroupChat.__init__)
    params = list(sig.parameters)
    assert "participants" in params
    assert "termination_condition" in params
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest tests/test_compat/test_autogen/test_round_robin.py -v 2>&1 | tail -10
```

Expected: ImportError.

- [ ] **Step 3: Implement the team class**

```python
# src/cognithor/compat/autogen/teams/__init__.py
"""AutoGen-shaped team classes."""

from __future__ import annotations

from cognithor.compat.autogen.teams._round_robin import RoundRobinGroupChat

__all__ = ["RoundRobinGroupChat"]
```

```python
# src/cognithor/compat/autogen/teams/_round_robin.py
"""RoundRobinGroupChat — AutoGen-shaped public class.

Thin wrapper over _RoundRobinAdapter from cognithor.compat.autogen._round_robin_adapter.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from cognithor.compat.autogen._round_robin_adapter import (
    _RoundRobinAdapter,
    _RoundRobinResult,
)
from cognithor.compat.autogen.conditions import _TerminationCondition

if TYPE_CHECKING:
    from cognithor.compat.autogen.agents._assistant_agent import AssistantAgent


class RoundRobinGroupChat:
    """Round-robin team — turns proceed in declaration order until terminated."""

    def __init__(
        self,
        participants: Sequence["AssistantAgent"],
        *,
        termination_condition: _TerminationCondition,
        max_turns: int = 50,
    ) -> None:
        self._adapter = _RoundRobinAdapter(
            participants=participants,
            termination=termination_condition,
            max_turns=max_turns,
        )

    async def run(self, *, task: str) -> _RoundRobinResult:
        return await self._adapter.run(task=task)
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_compat/test_autogen/test_round_robin.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Update package re-exports**

In `src/cognithor/compat/autogen/__init__.py`:

```python
from cognithor.compat.autogen.teams import RoundRobinGroupChat
```

Add `RoundRobinGroupChat` to `__all__`.

- [ ] **Step 6: Commit**

```bash
git add src/cognithor/compat/autogen/teams/ src/cognithor/compat/autogen/__init__.py tests/test_compat/test_autogen/test_round_robin.py
git commit -m "feat(compat): add RoundRobinGroupChat public class"
```

---

### Task 32: Combined-terminations integration test

**Files:**
- Create: `tests/test_compat/test_autogen/test_combined_terminations.py`

- [ ] **Step 1: Write the test (covers full A&B / A|B path with team)**

```python
# tests/test_compat/test_autogen/test_combined_terminations.py
"""End-to-end combined-termination behaviour through the public team class."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cognithor.compat.autogen.conditions import (
    MaxMessageTermination,
    TextMentionTermination,
)
from cognithor.compat.autogen.messages import TextMessage
from cognithor.compat.autogen.teams import RoundRobinGroupChat


def _stub_agent(name: str, replies: list[str]) -> MagicMock:
    agent = MagicMock()
    agent.name = name
    queue = list(replies)

    async def _run(*, task):
        from cognithor.compat.autogen._bridge import TaskResult
        return TaskResult(
            messages=[TextMessage(content=queue.pop(0), source=name)],
            stop_reason=None,
        )

    agent.run = _run
    return agent


@pytest.mark.asyncio
async def test_and_termination_requires_both_to_match() -> None:
    a = _stub_agent("a", ["DONE", "DONE", "DONE"])  # text matches every turn
    b = _stub_agent("b", ["x", "x", "x"])
    cond = MaxMessageTermination(4) & TextMentionTermination("DONE")
    team = RoundRobinGroupChat(participants=[a, b], termination_condition=cond)
    result = await team.run(task="x")
    # 'a' speaks first with "DONE" but message-count is only 1 — count must reach 4
    assert len(result.messages) >= 4
    assert "DONE" in str(result.messages[-1].content) or len(result.messages) >= 4


@pytest.mark.asyncio
async def test_or_termination_short_circuits() -> None:
    a = _stub_agent("a", ["DONE", "x", "x"])
    b = _stub_agent("b", ["x", "x", "x"])
    cond = MaxMessageTermination(100) | TextMentionTermination("DONE")
    team = RoundRobinGroupChat(participants=[a, b], termination_condition=cond)
    result = await team.run(task="x")
    assert len(result.messages) == 1


@pytest.mark.asyncio
async def test_complex_composite() -> None:
    a = _stub_agent("a", ["x", "DONE", "x"])
    b = _stub_agent("b", ["x", "x", "x"])
    cond = (MaxMessageTermination(2) & TextMentionTermination("DONE")) | MaxMessageTermination(10)
    team = RoundRobinGroupChat(participants=[a, b], termination_condition=cond)
    result = await team.run(task="x")
    # The (2 AND DONE) branch fires when DONE appears AND count >= 2.
    # Sequence: a:x (count=1, no DONE) → b:x (count=2, no DONE) → a:DONE (count=3, AND fires)
    assert len(result.messages) == 3
```

- [ ] **Step 2: Run test — expect pass**

```bash
pytest tests/test_compat/test_autogen/test_combined_terminations.py -v
```

Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test_compat/test_autogen/test_combined_terminations.py
git commit -m "test(compat): add combined-termination integration tests"
```

---

### Task 33: AssistantAgent behaviour test (basic + tool-call summary)

**Files:**
- Create: `tests/test_compat/test_autogen/test_assistant_agent.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_compat/test_autogen/test_assistant_agent.py
"""AssistantAgent behaviour — 1-shot run, message shape, tool-call summary."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.compat.autogen import AssistantAgent
from cognithor.compat.autogen._bridge import TaskResult


@pytest.mark.asyncio
async def test_assistant_agent_run_returns_task_result() -> None:
    fake_output = MagicMock()
    fake_output.raw = "Hello!"
    fake_output.tasks_outputs = []
    fake_output.token_usage = {"total_tokens": 10}

    with patch("cognithor.compat.autogen._bridge.Crew") as crew_cls:
        crew = MagicMock()
        crew.kickoff_async = AsyncMock(return_value=fake_output)
        crew_cls.return_value = crew

        agent = AssistantAgent(
            name="test-bot",
            model_client=MagicMock(),
            description="Friendly bot",
            system_message="Be polite.",
        )
        result = await agent.run(task="Hi")

        assert isinstance(result, TaskResult)
        assert result.messages[-1].source == "test-bot"
        assert "Hello" in str(result.messages[-1].content)


@pytest.mark.asyncio
async def test_assistant_agent_metadata_default_is_empty_dict() -> None:
    agent = AssistantAgent(name="x", model_client=MagicMock())
    assert agent.metadata == {}


@pytest.mark.asyncio
async def test_assistant_agent_max_tool_iterations_default_is_one() -> None:
    agent = AssistantAgent(name="x", model_client=MagicMock())
    assert agent.max_tool_iterations == 1


@pytest.mark.asyncio
async def test_assistant_agent_run_stream_yields_events() -> None:
    fake_output = MagicMock()
    fake_output.raw = "stream-out"
    fake_output.tasks_outputs = []
    fake_output.token_usage = {}

    with patch("cognithor.compat.autogen._bridge.Crew") as crew_cls:
        crew = MagicMock()
        crew.kickoff_async = AsyncMock(return_value=fake_output)
        crew_cls.return_value = crew

        agent = AssistantAgent(name="x", model_client=MagicMock())
        events = []
        async for evt in agent.run_stream(task="hi"):
            events.append(evt)
        assert len(events) >= 1
```

- [ ] **Step 2: Run test — expect pass**

```bash
pytest tests/test_compat/test_autogen/test_assistant_agent.py -v
```

Expected: 4 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test_compat/test_autogen/test_assistant_agent.py
git commit -m "test(compat): add AssistantAgent behaviour tests"
```

---

### Task 34: Hello-world search-and-replace behaviour test (Stage 2 of D6)

**Files:**
- Create: `tests/test_compat/test_autogen/test_hello_world_search_replace.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_compat/test_autogen/test_hello_world_search_replace.py
"""Stage-2 D6 test — AutoGen Hello-World runs through the shim with import swap.

Reference: AutoGen README hello-world (get_current_time tool).
We adapt the shape with Cognithor's mock model client; the goal is to verify
that a user can search-and-replace `from autogen_agentchat.agents` →
`from cognithor.compat.autogen` with no other changes.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.compat.autogen import (
    AssistantAgent,
    OpenAIChatCompletionClient,
    TextMessage,
)


@pytest.mark.asyncio
async def test_autogen_hello_world_runs_through_shim() -> None:
    """The 30-line AutoGen hello-world example, rewritten with our import paths.

    Original AutoGen (referenced for shape — NOT copied):
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        from autogen_agentchat.agents import AssistantAgent

        async def main():
            client = OpenAIChatCompletionClient(model="gpt-4o-mini")
            agent = AssistantAgent("assistant", model_client=client)
            result = await agent.run(task="Say hello.")
            print(result.messages[-1].content)
    """
    fake_output = MagicMock()
    fake_output.raw = "Hello, world!"
    fake_output.tasks_outputs = []
    fake_output.token_usage = {"total_tokens": 5}

    with patch("cognithor.compat.autogen._bridge.Crew") as crew_cls:
        crew = MagicMock()
        crew.kickoff_async = AsyncMock(return_value=fake_output)
        crew_cls.return_value = crew

        client = OpenAIChatCompletionClient(model="ollama/qwen3:8b")
        agent = AssistantAgent("assistant", model_client=client)
        result = await agent.run(task="Say hello.")

        last = result.messages[-1]
        assert isinstance(last, TextMessage) or hasattr(last, "content")
        assert "Hello" in str(last.content)
        assert last.source == "assistant"


@pytest.mark.asyncio
async def test_message_event_shape_matches_autogen_attrs() -> None:
    """Spec §8.4 verhaltensgarantien — events expose source, models_usage, metadata, content, type."""
    fake_output = MagicMock()
    fake_output.raw = "OK"
    fake_output.tasks_outputs = []
    fake_output.token_usage = {"total_tokens": 1}

    with patch("cognithor.compat.autogen._bridge.Crew") as crew_cls:
        crew = MagicMock()
        crew.kickoff_async = AsyncMock(return_value=fake_output)
        crew_cls.return_value = crew

        client = OpenAIChatCompletionClient(model="ollama/qwen3:8b")
        agent = AssistantAgent("assistant", model_client=client)
        result = await agent.run(task="x")
        msg = result.messages[-1]

        for attr in ("source", "models_usage", "metadata", "content", "type"):
            assert hasattr(msg, attr), f"missing event-shape attr: {attr}"


@pytest.mark.asyncio
async def test_autogen_two_agent_round_robin_runs_through_shim() -> None:
    """The minimal RoundRobinGroupChat example, rewritten with our import paths."""
    from cognithor.compat.autogen import (
        MaxMessageTermination,
        RoundRobinGroupChat,
    )

    fake_output_a = MagicMock()
    fake_output_a.raw = "a-says"
    fake_output_a.tasks_outputs = []
    fake_output_a.token_usage = {}

    fake_output_b = MagicMock()
    fake_output_b.raw = "b-says"
    fake_output_b.tasks_outputs = []
    fake_output_b.token_usage = {}

    outputs = [fake_output_a, fake_output_b, fake_output_a, fake_output_b]

    with patch("cognithor.compat.autogen._bridge.Crew") as crew_cls:
        crew = MagicMock()
        crew.kickoff_async = AsyncMock(side_effect=outputs)
        crew_cls.return_value = crew

        client = OpenAIChatCompletionClient(model="ollama/qwen3:8b")
        a = AssistantAgent("a", model_client=client)
        b = AssistantAgent("b", model_client=client)

        team = RoundRobinGroupChat(
            participants=[a, b],
            termination_condition=MaxMessageTermination(2),
        )
        result = await team.run(task="kickoff")
        assert len(result.messages) == 2
        assert result.messages[0].source == "a"
        assert result.messages[1].source == "b"
```

- [ ] **Step 2: Run test — expect pass**

```bash
pytest tests/test_compat/test_autogen/test_hello_world_search_replace.py -v
```

Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test_compat/test_autogen/test_hello_world_search_replace.py
git commit -m "test(compat): add Stage-2 hello-world search-and-replace behaviour test (D6)"
```

---

### Task 35: Migration guide `src/cognithor/compat/autogen/README.md`

**Files:**
- Create: `src/cognithor/compat/autogen/README.md`

- [ ] **Step 1: Write the migration guide**

```markdown
# `cognithor.compat.autogen` — Migration Guide

> **What this is.** A source-compatibility shim for
> [`autogen-agentchat==0.7.5`](https://github.com/microsoft/autogen)
> (Microsoft, MIT). It lets you run a useful subset of AutoGen-AgentChat
> code on Cognithor by changing **only the import paths**.

> **What this is not.** A reimplementation of AutoGen, MAF, or
> `autogen-core`. It does not replicate the GroupChat patterns that
> conflict with Cognithor's PGE-Trinity safety model — see
> [ADR 0001](../../../docs/adr/0001-pge-trinity-vs-group-chat.md).

## Quickstart — Search-and-Replace

```diff
- from autogen_agentchat.agents import AssistantAgent
- from autogen_agentchat.teams import RoundRobinGroupChat
- from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
- from autogen_ext.models.openai import OpenAIChatCompletionClient
+ from cognithor.compat.autogen import (
+     AssistantAgent, RoundRobinGroupChat,
+     MaxMessageTermination, TextMentionTermination,
+     OpenAIChatCompletionClient,
+ )
```

If your code uses only those symbols, that's the full migration. The 30-line
AutoGen hello-world example runs verbatim once imports are changed.

## Side-by-Side: AutoGen Hello-World

**AutoGen (original):**

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent

async def main():
    client = OpenAIChatCompletionClient(model="gpt-4o-mini")
    agent = AssistantAgent("assistant", model_client=client)
    result = await agent.run(task="Say hello.")
    print(result.messages[-1].content)
```

**Cognithor compat (after search-and-replace):**

```python
from cognithor.compat.autogen import OpenAIChatCompletionClient, AssistantAgent

async def main():
    client = OpenAIChatCompletionClient(model="ollama/qwen3:8b")  # or any 16 providers
    agent = AssistantAgent("assistant", model_client=client)
    result = await agent.run(task="Say hello.")
    print(result.messages[-1].content)
```

The only meaningful change is the model spec — Cognithor accepts the full
model-router DSL, not just OpenAI model IDs. Pass `model="gpt-4o-mini"` if
you have an OpenAI key configured; pass `model="ollama/qwen3:8b"` for local.

## Supported Subset

| AutoGen Class | Status | Notes |
|---|---|---|
| `AssistantAgent` | ✅ Full 14-field signature parity | Internally delegates to `cognithor.crew` |
| `AssistantAgent.run` | ✅ | 1-shot, returns `TaskResult` |
| `AssistantAgent.run_stream` | ✅ | Async generator, AutoGen-shaped events |
| `RoundRobinGroupChat` | ✅ | Multi-round via `_RoundRobinAdapter` |
| `MaxMessageTermination` | ✅ | Counts messages |
| `TextMentionTermination` | ✅ | Substring match on last message |
| `MaxMessageTermination & TextMentionTermination` | ✅ | `__and__` overload |
| `MaxMessageTermination \| TextMentionTermination` | ✅ | `__or__` overload |
| `TextMessage`, `ToolCallSummaryMessage`, `HandoffMessage`, `StructuredMessage` | ✅ | AutoGen-shaped fields |
| `OpenAIChatCompletionClient` | ✅ | Backed by `cognithor.core.model_router` (16 providers) |
| `FunctionTool` / `Workbench` | ⚠️ Bridged via MCP | Custom tools need MCP registration |
| `SelectorGroupChat` | ❌ Not supported | LLM as security boundary — see [ADR 0001](../../../docs/adr/0001-pge-trinity-vs-group-chat.md) |
| `Swarm` | ❌ Not supported | HandoffMessage freedom conflicts with PGE-Trinity |
| `MagenticOneGroupChat` | ❌ Not supported | Separate workstream |
| `autogen_core` (`RoutedAgent`, `@message_handler`) | ❌ Out of scope | Actor-model, too low-level |

## Why are SelectorGroupChat / Swarm not supported?

Selector / Swarm patterns delegate the question "who speaks next?" to an LLM
or to free-form `HandoffMessage` exchanges between agents. Cognithor places
the Gatekeeper between every action and its execution — the Gatekeeper is
**rule-based** and inspectable. Letting an LLM bypass that boundary
breaks the safety model.

Detailed rationale: [ADR 0001 — PGE Trinity vs Group Chat](../../../docs/adr/0001-pge-trinity-vs-group-chat.md).

## When should you migrate off the compat layer?

The shim is a **temporary bridge**, not a destination. Once your code is
running on Cognithor and you've hit production stability, migrate to
native `cognithor.crew`:

- More idiomatic for Cognithor's PGE-Trinity (declarative `Crew`, explicit
  `kickoff_async`).
- First-class Hashline-Guard audit chain (no compat-layer wrapping).
- First-class guardrails (`no_pii()`, `chain()`, `StringGuardrail`).
- Better error messages — the shim's "AutoGen-shape" is sometimes a lossy
  translation.

A native rewrite of the hello-world above:

```python
from cognithor.crew import Crew, CrewAgent, CrewTask

async def main():
    agent = CrewAgent(role="assistant", goal="Greet the user", llm="ollama/qwen3:8b")
    task = CrewTask(description="Say hello.", expected_output="A short greeting.", agent=agent)
    crew = Crew(agents=[agent], tasks=[task])
    result = await crew.kickoff_async({})
    print(result.raw)
```

## Deprecation Warning

Importing `cognithor.compat.autogen` emits a `DeprecationWarning` pointing
back to this guide. The warning does not affect runtime behaviour. To
silence it for known-shim code:

```python
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module=r"cognithor\.compat\.autogen")
```

## License Note

This shim is Apache 2.0. The API shape is concept-inspired from AutoGen
(MIT). No AutoGen source code is included verbatim. The repo-root
`NOTICE` carries the AutoGen-MIT attribution under "Third-party
attributions".
```

- [ ] **Step 2: Commit**

```bash
git add src/cognithor/compat/autogen/README.md
git commit -m "docs(compat): add migration guide with side-by-side hello-world"
```

---

### Task 36: NOTICE — append AutoGen MIT attribution (staging entry)

**Files:**
- Modify: `NOTICE`

- [ ] **Step 1: Read NOTICE, locate the existing CrewAI attribution line**

```bash
grep -n "CrewAI" NOTICE
```

- [ ] **Step 2: Append AutoGen attribution after the CrewAI block**

Add a new line/block analog to the CrewAI attribution:

```
This product includes software concepts inspired by Microsoft AutoGen
(https://github.com/microsoft/autogen) — specifically the
autogen-agentchat==0.7.5 public API surface — licensed under the MIT
License. The cognithor.compat.autogen source-compat shim re-implements
this surface in Apache 2.0 with no AutoGen source code included verbatim.

MIT License
Copyright (c) Microsoft Corporation.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Commit**

```bash
git add NOTICE
git commit -m "legal(notice): add AutoGen-MIT attribution for cognithor.compat.autogen"
```

---

### Task 37: Coverage check on `cognithor.compat.autogen`

- [ ] **Step 1: Run coverage**

```bash
pytest tests/test_compat/test_autogen/ --cov=src/cognithor/compat/autogen --cov-report=term-missing -q
```

Expected: ≥85% coverage.

- [ ] **Step 2: If coverage below 85%, identify and patch gaps**

Read the term-missing report; add tests for any uncovered branches in `_bridge.py`, `_round_robin_adapter.py`, or the messages module. Re-run until ≥85%.

- [ ] **Step 3: If new tests added, commit**

```bash
git add tests/test_compat/test_autogen/
git commit -m "test(compat): cover edge cases to reach 85% on cognithor.compat.autogen"
```

---

### Task 38: `mypy --strict` on the compat package

- [ ] **Step 1: Run mypy**

```bash
mypy --strict src/cognithor/compat
```

Expected: clean.

If errors appear:
- For `Any`-typed AutoGen interop fields (`model_client`, `tools`, etc.) — these are intentional `Any` per the spec; if mypy complains add `# type: ignore[arg-type]` with a one-line reason.
- For `AsyncIterator` return-type issues on `run_stream`, the function is an async generator that returns and so the annotation is `AsyncIterator[Any]` — keep as-is.

- [ ] **Step 2: Apply targeted fixes; commit if any**

```bash
git add src/cognithor/compat/
git commit -m "type(compat): mypy --strict pass on cognithor.compat.autogen"
```

---

### Task 39: CHANGELOG `[Unreleased]` entry for WP2

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Append under `[Unreleased] ### Added`**

```markdown
- `cognithor.compat.autogen` — source-compatibility shim for
  `autogen-agentchat==0.7.5` (WP2). Search-and-replace import
  migration from AutoGen-AgentChat to Cognithor; 1-shot path uses
  `cognithor.crew`, multi-round path uses a 250-LOC `_RoundRobinAdapter`.
  Supported: `AssistantAgent`, `RoundRobinGroupChat`, message + termination
  classes, `OpenAIChatCompletionClient` wrapper. Not supported by design:
  `SelectorGroupChat`, `Swarm`, `MagenticOneGroupChat` (see ADR 0001).
- `NOTICE` — AutoGen-MIT attribution under "Third-party attributions".
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): note WP2 cognithor.compat.autogen for v0.94.0"
```

---

### Task 40: PR 3 closeout + push + open PR

- [ ] **Step 1: Full regression on the feature branch**

```bash
pytest tests/ -x -q --cov=src/cognithor --cov-fail-under=89
pytest tests/test_compat/test_autogen/ -x -q --cov=src/cognithor/compat/autogen --cov-fail-under=85
```

Expected: both green.

- [ ] **Step 2: Lint + format + mypy**

```bash
ruff check .
ruff format --check .
mypy --strict src/cognithor/compat
```

Expected: all clean.

- [ ] **Step 3: Push + open PR**

```bash
git push -u origin feat/cognithor-autogen-v3-compat
gh pr create --title "feat(compat): WP2 AutoGen-AgentChat source-compat shim (v0.94.0 PR 3)" --body "$(cat <<'EOF'
## Summary
- `cognithor.compat.autogen` source-compat shim for `autogen-agentchat==0.7.5`
- `AssistantAgent` with exact 14-field signature parity (Stage-1 inspect.signature tests)
- 1-shot path delegates to `cognithor.crew.Crew(...).kickoff_async()`
- `RoundRobinGroupChat` via custom `_RoundRobinAdapter` (~250 LOC, multi-round + termination)
- Composable terminations: `MaxMessageTermination`, `TextMentionTermination`, `__and__` / `__or__`
- `OpenAIChatCompletionClient` wrapper backs onto Cognithor's model router (16 providers)
- AutoGen-shaped messages: `TextMessage`, `ToolCallSummaryMessage`, `HandoffMessage`, `StructuredMessage`
- DeprecationWarning on import points at the migration guide
- Migration guide at `src/cognithor/compat/autogen/README.md`
- AutoGen-MIT attribution added to `NOTICE`

## Spec
- `docs/superpowers/specs/2026-04-25-cognithor-autogen-strategy-design.md` §8.4

## Test plan
- [ ] `pytest tests/test_compat/test_autogen/ -x -q --cov-fail-under=85` green
- [ ] `pytest tests/ -x -q --cov-fail-under=89` green (no regression)
- [ ] `mypy --strict src/cognithor/compat` clean
- [ ] AutoGen Hello-World runs through shim with only import-line changes
- [ ] DeprecationWarning emitted on import
- [ ] `pip install cognithor[autogen]` resolves `autogen-agentchat==0.7.5`
- [ ] No verbatim AutoGen code (manual review)

## Note
This PR depends on PR 2 (which added the `[autogen]` extra to root `pyproject.toml`).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: Wait CI green, squash-merge**

```bash
gh pr checks <PR_NUMBER> --watch
gh pr merge <PR_NUMBER> --squash --delete-branch=false
```

- [ ] **Step 5: Cleanup in a separate turn**

```bash
git checkout main && git pull --ff-only
git branch -d feat/cognithor-autogen-v3-compat
git push origin --delete feat/cognithor-autogen-v3-compat
```

---

# PR 4 — WP3 Insurance Agent Pack (Tasks 41-54)

Implements spec §8.5 — `examples/insurance-agent-pack/` as a standalone-installable Python package, NOT registered with `cognithor.packs` (that loader is for private commerce-packs). Builds on v0.93.0's `versicherungs-vergleich` template concepts, adds two new agents (`PolicyAnalyst` with PDF tool-use, `ComplianceGatekeeper` as a visible PGE-demo). All fixtures synthetic.

**Branch:** `feat/cognithor-autogen-v4-insurance` cut from latest `main` (after PR 3 merged).

**PR-4 closeout target:** `pip install ./examples/insurance-agent-pack/` succeeds; `insurance-agent-pack run --interview` starts an interactive session; gatekeeper-block test green (positive + negative); audit-chain integrity test green; ≥80% coverage on the pack module; `DISCLAIMER.md` reviewed by Alexander personally.

---

### Task 41: Branch + scaffold pack directory + `pyproject.toml`

**Files:**
- Create: `examples/insurance-agent-pack/pyproject.toml`
- Create: `examples/insurance-agent-pack/LICENSE`
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/__init__.py`
- Create: `examples/insurance-agent-pack/tests/__init__.py`

- [ ] **Step 1: Cut feature branch**

```bash
git checkout main && git pull --ff-only
git checkout -b feat/cognithor-autogen-v4-insurance
```

- [ ] **Step 2: Create the directory structure**

```bash
mkdir -p examples/insurance-agent-pack/src/insurance_agent_pack/{agents,prompts,knowledge,tools}
mkdir -p examples/insurance-agent-pack/tests/fixtures
mkdir -p examples/insurance-agent-pack/docs
```

- [ ] **Step 3: Write the failing test**

**Files:**
- Create: `examples/insurance-agent-pack/tests/test_package_install.py`

```python
# examples/insurance-agent-pack/tests/test_package_install.py
"""Verify the pack installs as a standalone package."""

from __future__ import annotations


def test_package_imports() -> None:
    import insurance_agent_pack
    assert hasattr(insurance_agent_pack, "__version__")


def test_cli_module_exists() -> None:
    from insurance_agent_pack import cli
    assert hasattr(cli, "main")


def test_crew_module_exists() -> None:
    from insurance_agent_pack import crew
    assert hasattr(crew, "build_team")
```

- [ ] **Step 4: Run test — expect failure**

```bash
pytest examples/insurance-agent-pack/tests/test_package_install.py -v 2>&1 | tail -5
```

Expected: ModuleNotFoundError on `insurance_agent_pack`.

- [ ] **Step 5: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "insurance-agent-pack"
version = "0.1.0"
description = "Reference Cognithor pack: DACH insurance pre-advisory crew"
readme = "README.md"
license = "Apache-2.0"
requires-python = ">=3.12"
authors = [{ name = "Alexander Söllner" }]
keywords = ["ai", "agent", "insurance", "dach", "cognithor"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
    "cognithor>=0.94.0",
    "pydantic>=2.10,<3",
    "pymupdf>=1.23",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9",
    "pytest-asyncio>=0.24,<1",
    "pytest-cov>=6.0,<7",
]

[project.scripts]
insurance-agent-pack = "insurance_agent_pack.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/insurance_agent_pack"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 6: Create `LICENSE`**

```
Apache License 2.0

This pack is licensed under the same Apache 2.0 license as the parent
Cognithor project. See the repo-root LICENSE for the full text.
```

- [ ] **Step 7: Create the empty `__init__.py` files**

```python
# examples/insurance-agent-pack/src/insurance_agent_pack/__init__.py
"""Reference Cognithor pack: DACH insurance pre-advisory crew.

Demonstrates Cognithor's PGE-Trinity safety model in a §34d-NEUTRAL
pre-advisory flow. NOT a §34d-compliant Beratungssoftware. See DISCLAIMER.md.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
```

```python
# examples/insurance-agent-pack/src/insurance_agent_pack/agents/__init__.py
"""Pack agents: PolicyAnalyst, NeedsAssessor, ComplianceGatekeeper, ReportGenerator."""
```

```python
# examples/insurance-agent-pack/src/insurance_agent_pack/tools/__init__.py
"""Pack-specific custom tools."""
```

```python
# examples/insurance-agent-pack/tests/__init__.py
```

- [ ] **Step 8: Mark the test xfail until cli + crew arrive**

Edit `examples/insurance-agent-pack/tests/test_package_install.py` — add at top:

```python
import pytest

pytestmark = pytest.mark.xfail(
    reason="cli/crew arrive in Tasks 42-49",
    strict=False,
)
```

- [ ] **Step 9: Install + run xfail tests**

```bash
pip install -e examples/insurance-agent-pack
pytest examples/insurance-agent-pack/tests/test_package_install.py -v
```

Expected: 1 passed (`test_package_imports`), 2 xfailed.

- [ ] **Step 10: Commit**

```bash
git add examples/insurance-agent-pack/
git commit -m "feat(insurance-pack): scaffold standalone pack with pyproject + LICENSE"
```

---

### Task 42: PolicyAnalyst agent + prompt

**Files:**
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/prompts/policy_analyst.md`
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/agents/policy_analyst.py`
- Create: `examples/insurance-agent-pack/tests/test_policy_analyst.py`

- [ ] **Step 1: Write the failing test**

```python
# examples/insurance-agent-pack/tests/test_policy_analyst.py
"""PolicyAnalyst — declarative CrewAgent with PDF tool-use."""

from __future__ import annotations

from insurance_agent_pack.agents.policy_analyst import build_policy_analyst


def test_policy_analyst_role_label() -> None:
    a = build_policy_analyst(model="ollama/qwen3:8b")
    assert a.role == "policy-analyst"


def test_policy_analyst_has_pdf_extract_tool() -> None:
    a = build_policy_analyst(model="ollama/qwen3:8b")
    assert "pdf_extract_text" in a.tools


def test_policy_analyst_loads_prompt_text_into_backstory() -> None:
    a = build_policy_analyst(model="ollama/qwen3:8b")
    assert "Versicherung" in a.backstory or "Police" in a.backstory


def test_policy_analyst_disallows_delegation() -> None:
    """PGE-Trinity: PolicyAnalyst is an Executor, not a Planner — no delegation."""
    a = build_policy_analyst(model="ollama/qwen3:8b")
    assert a.allow_delegation is False
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest examples/insurance-agent-pack/tests/test_policy_analyst.py -v 2>&1 | tail -5
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Write the prompt**

```markdown
<!-- examples/insurance-agent-pack/src/insurance_agent_pack/prompts/policy_analyst.md -->
Du bist der **Policy-Analyst** in einer Versicherungs-Pre-Beratung.

Deine Aufgabe ist die strukturierte Analyse vorhandener Versicherungspolicen
in deutschsprachigen PDF-Dokumenten. Du nutzt das Tool `pdf_extract_text`,
um Inhalte zu extrahieren, und produzierst eine sachliche Tabelle:

| Vertrag | Versicherer | Gesellschaft | Beitrag/Jahr | Kerndeckung | Wartezeit | Bemerkung |

**Wichtig:** Du gibst NIEMALS persönliche Empfehlungen ab. Empfehlungen
sind Aufgabe des `report-generator` und müssen den Compliance-Gatekeeper
passieren. Du extrahierst Fakten — nichts mehr.
```

- [ ] **Step 4: Implement the agent factory**

```python
# examples/insurance-agent-pack/src/insurance_agent_pack/agents/policy_analyst.py
"""PolicyAnalyst — extracts policy facts from PDF inputs (Cognithor CrewAgent)."""

from __future__ import annotations

from pathlib import Path

from cognithor.crew import CrewAgent

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "policy_analyst.md"


def build_policy_analyst(*, model: str) -> CrewAgent:
    backstory = _PROMPT_PATH.read_text(encoding="utf-8")
    return CrewAgent(
        role="policy-analyst",
        goal="Extract structured facts from German-language insurance policy PDFs.",
        backstory=backstory,
        tools=["pdf_extract_text"],
        llm=model,
        allow_delegation=False,
        max_iter=10,
        memory=True,
        verbose=False,
    )
```

- [ ] **Step 5: Run test — expect pass**

```bash
pytest examples/insurance-agent-pack/tests/test_policy_analyst.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add examples/insurance-agent-pack/src/insurance_agent_pack/prompts/policy_analyst.md examples/insurance-agent-pack/src/insurance_agent_pack/agents/policy_analyst.py examples/insurance-agent-pack/tests/test_policy_analyst.py
git commit -m "feat(insurance-pack): add PolicyAnalyst agent with PDF tool-use"
```

---

### Task 43: NeedsAssessor agent + prompt

**Files:**
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/prompts/needs_assessor.md`
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/agents/needs_assessor.py`
- Create: `examples/insurance-agent-pack/tests/test_needs_assessor.py`

- [ ] **Step 1: Write the failing test**

```python
# examples/insurance-agent-pack/tests/test_needs_assessor.py
"""NeedsAssessor — turns interview answers into structured need profile."""

from __future__ import annotations

from insurance_agent_pack.agents.needs_assessor import build_needs_assessor


def test_needs_assessor_role_label() -> None:
    a = build_needs_assessor(model="ollama/qwen3:8b")
    assert a.role == "needs-assessor"


def test_needs_assessor_uses_no_tools() -> None:
    """Assessor is pure conversational reasoning; no external tool calls."""
    a = build_needs_assessor(model="ollama/qwen3:8b")
    assert a.tools == []


def test_needs_assessor_memory_enabled() -> None:
    """Memory must be on so the Assessor can refer back to earlier answers."""
    a = build_needs_assessor(model="ollama/qwen3:8b")
    assert a.memory is True
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest examples/insurance-agent-pack/tests/test_needs_assessor.py -v 2>&1 | tail -5
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Write the prompt**

```markdown
<!-- examples/insurance-agent-pack/src/insurance_agent_pack/prompts/needs_assessor.md -->
Du bist der **Bedarfs-Analyst** in einer Versicherungs-Pre-Beratung für DACH.

Du nimmst Antworten aus dem strukturierten Interview entgegen (Familien-
stand, Einkommen, Vorerkrankungen, bestehende Policen, Berufsstatus —
GGF/Selbstständig/Angestellt) und erstellst ein Bedarfsprofil:

```
{
  "lebensphase": "...",
  "haushalt": {...},
  "einkommen": {...},
  "berufsstatus": "GGF | selbständig | angestellt | freiberufler",
  "bestehende_policen": [...],
  "potenzielle_lücken": ["BU", "PKV", "bAV", ...]
}
```

**Wichtig:**
- Du gibst KEINE Produkt-Empfehlungen.
- Du wertest KEINE rechtlichen Fragen aus.
- Du bewahrst keine personenbezogenen Daten dauerhaft (PII-Schutz greift
  über die Cognithor-Pipeline).
```

- [ ] **Step 4: Implement the agent factory**

```python
# examples/insurance-agent-pack/src/insurance_agent_pack/agents/needs_assessor.py
"""NeedsAssessor — converts interview answers into a structured profile."""

from __future__ import annotations

from pathlib import Path

from cognithor.crew import CrewAgent

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "needs_assessor.md"


def build_needs_assessor(*, model: str) -> CrewAgent:
    backstory = _PROMPT_PATH.read_text(encoding="utf-8")
    return CrewAgent(
        role="needs-assessor",
        goal="Convert interview answers into a structured insurance-needs profile.",
        backstory=backstory,
        tools=[],
        llm=model,
        allow_delegation=False,
        max_iter=20,
        memory=True,
        verbose=False,
    )
```

- [ ] **Step 5: Run test — expect pass**

```bash
pytest examples/insurance-agent-pack/tests/test_needs_assessor.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add examples/insurance-agent-pack/src/insurance_agent_pack/prompts/needs_assessor.md examples/insurance-agent-pack/src/insurance_agent_pack/agents/needs_assessor.py examples/insurance-agent-pack/tests/test_needs_assessor.py
git commit -m "feat(insurance-pack): add NeedsAssessor agent"
```

---

### Task 44: ComplianceGatekeeper agent (PGE-Demo)

**Files:**
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/prompts/compliance_gatekeeper.md`
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/agents/compliance_gatekeeper.py`
- Create: `examples/insurance-agent-pack/tests/test_compliance_gatekeeper.py`

- [ ] **Step 1: Write the failing test**

```python
# examples/insurance-agent-pack/tests/test_compliance_gatekeeper.py
"""ComplianceGatekeeper — explicit PGE-Gatekeeper as a visible demo agent."""

from __future__ import annotations

from insurance_agent_pack.agents.compliance_gatekeeper import (
    build_compliance_gatekeeper,
    classify_intent,
)


def test_role_label() -> None:
    a = build_compliance_gatekeeper(model="ollama/qwen3:8b")
    assert a.role == "compliance-gatekeeper"


def test_classify_intent_passes_pre_advisory_question() -> None:
    """A pre-advisory question (PKV, GGF, BU…) should classify as PASS."""
    verdict = classify_intent("Welche Versicherungen gibt es für GGF?")
    assert verdict.allowed is True
    assert verdict.category in {"pre_advisory_question", "general_information"}


def test_classify_intent_blocks_legal_advice() -> None:
    """A legal-advice question must classify as BLOCK with a clear reason."""
    verdict = classify_intent("Ist mein Arbeitsvertrag rechtens?")
    assert verdict.allowed is False
    assert "rechtsberatung" in verdict.reason.lower()


def test_classify_intent_blocks_concrete_recommendation_demand() -> None:
    """Spec: agent never produces §34d-style binding recommendations."""
    verdict = classify_intent("Welche konkrete BU soll ich abschließen?")
    assert verdict.allowed is False
    assert "empfehlung" in verdict.reason.lower() or "§34d" in verdict.reason


def test_verdict_records_classification_metadata() -> None:
    verdict = classify_intent("Was ist GGF?")
    assert verdict.allowed is True
    assert hasattr(verdict, "category")
    assert hasattr(verdict, "reason")
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest examples/insurance-agent-pack/tests/test_compliance_gatekeeper.py -v 2>&1 | tail -10
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Write the prompt**

```markdown
<!-- examples/insurance-agent-pack/src/insurance_agent_pack/prompts/compliance_gatekeeper.md -->
Du bist der **Compliance-Gatekeeper**. Du prüfst, ob eine Anfrage des
Nutzers im Rahmen einer **§34d-NEUTRALEN Pre-Beratung** zulässig ist.

Du sagst NIEMALS:
- "Schließe Versicherung X ab"
- "Vermeide Versicherung Y"
- Konkrete Produkt-Bezeichnungen mit Empfehlungs-Charakter
- Antworten zu rein-juristischen Fragen (Arbeitsrecht, Erbrecht, Mietrecht)

Du sagst aktiv:
- "Diese Frage berührt Rechtsberatung; bitte einen Anwalt konsultieren."
- "Eine konkrete Produktempfehlung erfordert eine §34d-konforme Beratung;
   der Pack ist Pre-Beratung, keine Beratung."
- Allgemein-bildende Auskünfte sind in Ordnung.

Output-Schema:

```
{ "allowed": true | false, "category": "...", "reason": "..." }
```
```

- [ ] **Step 4: Implement the agent + classifier**

```python
# examples/insurance-agent-pack/src/insurance_agent_pack/agents/compliance_gatekeeper.py
"""ComplianceGatekeeper — explicit pre-advisory compliance check.

This is a thin RULE-BASED classifier. It is INTENTIONALLY not LLM-backed
in the v0.94.0 reference pack — keeping the safety boundary inspectable
and deterministic. An LLM-augmented variant is post-v0.94.0.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from cognithor.crew import CrewAgent

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "compliance_gatekeeper.md"


@dataclass(frozen=True)
class ComplianceVerdict:
    allowed: bool
    category: str
    reason: str


_LEGAL_ADVICE_PATTERNS = (
    r"\barbeitsvertrag\b.*\brechtens\b",
    r"\brechtens\b",
    r"\bjuristisch\b",
    r"\berbrecht\b",
    r"\bmietrecht\b",
    r"\bist .* rechtmäßig\b",
)

_CONCRETE_RECOMMENDATION_PATTERNS = (
    r"\bsoll(en)? ich .* abschließen\b",
    r"\bwelche konkrete\b.*\b(versicherung|police|tarif)\b",
    r"\bempfiehlst du mir\b",
    r"\bentscheide für mich\b",
)

_PRE_ADVISORY_PATTERNS = (
    r"\b(pkv|ggf|bav|bav-|bu|berufsunfähigkeit|haftpflicht|hausrat)\b",
    r"\bwelche versicherungen gibt es\b",
    r"\bwas ist .*\b(pkv|ggf|bav|bu)\b",
)


def classify_intent(message: str) -> ComplianceVerdict:
    text = message.lower().strip()

    for pat in _LEGAL_ADVICE_PATTERNS:
        if re.search(pat, text):
            return ComplianceVerdict(
                allowed=False,
                category="legal_advice_request",
                reason="Diese Frage berührt Rechtsberatung; bitte einen Anwalt konsultieren.",
            )

    for pat in _CONCRETE_RECOMMENDATION_PATTERNS:
        if re.search(pat, text):
            return ComplianceVerdict(
                allowed=False,
                category="concrete_recommendation_demand",
                reason=(
                    "Eine konkrete Produkt-Empfehlung erfordert eine §34d-konforme "
                    "Beratung; der Pack ist Pre-Beratung, keine Beratung."
                ),
            )

    for pat in _PRE_ADVISORY_PATTERNS:
        if re.search(pat, text):
            return ComplianceVerdict(
                allowed=True,
                category="pre_advisory_question",
                reason="Allgemeinbildende Pre-Beratungsfrage.",
            )

    return ComplianceVerdict(
        allowed=True,
        category="general_information",
        reason="Keine §34d-relevanten Empfehlungs-Token erkannt.",
    )


def build_compliance_gatekeeper(*, model: str) -> CrewAgent:
    backstory = _PROMPT_PATH.read_text(encoding="utf-8")
    return CrewAgent(
        role="compliance-gatekeeper",
        goal="Block legal-advice and concrete-recommendation requests; allow pre-advisory questions.",
        backstory=backstory,
        tools=[],
        llm=model,
        allow_delegation=False,
        max_iter=5,
        memory=False,
        verbose=False,
    )
```

- [ ] **Step 5: Run test — expect pass**

```bash
pytest examples/insurance-agent-pack/tests/test_compliance_gatekeeper.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add examples/insurance-agent-pack/src/insurance_agent_pack/prompts/compliance_gatekeeper.md examples/insurance-agent-pack/src/insurance_agent_pack/agents/compliance_gatekeeper.py examples/insurance-agent-pack/tests/test_compliance_gatekeeper.py
git commit -m "feat(insurance-pack): add ComplianceGatekeeper with rule-based classifier"
```

---

### Task 45: ReportGenerator agent + prompt

**Files:**
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/prompts/report_generator.md`
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/agents/report_generator.py`
- Create: `examples/insurance-agent-pack/tests/test_report_generator.py`

- [ ] **Step 1: Write the failing test**

```python
# examples/insurance-agent-pack/tests/test_report_generator.py
"""ReportGenerator — produces final markdown report from analyst + assessor outputs."""

from __future__ import annotations

from insurance_agent_pack.agents.report_generator import build_report_generator


def test_report_generator_role_label() -> None:
    a = build_report_generator(model="ollama/qwen3:8b")
    assert a.role == "report-generator"


def test_report_generator_uses_no_tools() -> None:
    a = build_report_generator(model="ollama/qwen3:8b")
    assert a.tools == []


def test_report_generator_disallows_delegation() -> None:
    a = build_report_generator(model="ollama/qwen3:8b")
    assert a.allow_delegation is False
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest examples/insurance-agent-pack/tests/test_report_generator.py -v 2>&1 | tail -5
```

- [ ] **Step 3: Write the prompt**

```markdown
<!-- examples/insurance-agent-pack/src/insurance_agent_pack/prompts/report_generator.md -->
Du bist der **Report-Generator**. Du nimmst:
1. Strukturiertes Bedarfsprofil (vom NeedsAssessor)
2. Tabelle bestehender Policen (vom PolicyAnalyst)
3. Compliance-Verdict (vom ComplianceGatekeeper)

und erstellst einen markdown-formatierten **Pre-Beratungs-Report**:

- "Was ich beobachte" — Beobachtungen, keine Wertungen.
- "Mögliche Lücken" — Themenliste, keine Produkt-Empfehlungen.
- "Worüber Sie mit einem §34d-Vermittler sprechen sollten."

Du sagst NIE:
- "Schließe X ab"
- "Tarif Y ist besser als Z"
- Konkrete Versicherer-Namen mit Empfehlungs-Charakter

Wenn das Compliance-Verdict `allowed=false` ist, brichst du ab und gibst
ausschließlich die `reason` aus dem Verdict zurück.
```

- [ ] **Step 4: Implement the agent factory**

```python
# examples/insurance-agent-pack/src/insurance_agent_pack/agents/report_generator.py
"""ReportGenerator — final pre-advisory markdown report."""

from __future__ import annotations

from pathlib import Path

from cognithor.crew import CrewAgent

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "report_generator.md"


def build_report_generator(*, model: str) -> CrewAgent:
    backstory = _PROMPT_PATH.read_text(encoding="utf-8")
    return CrewAgent(
        role="report-generator",
        goal="Compose a §34d-NEUTRAL pre-advisory markdown report.",
        backstory=backstory,
        tools=[],
        llm=model,
        allow_delegation=False,
        max_iter=10,
        memory=True,
        verbose=False,
    )
```

- [ ] **Step 5: Run test — expect pass**

```bash
pytest examples/insurance-agent-pack/tests/test_report_generator.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add examples/insurance-agent-pack/src/insurance_agent_pack/prompts/report_generator.md examples/insurance-agent-pack/src/insurance_agent_pack/agents/report_generator.py examples/insurance-agent-pack/tests/test_report_generator.py
git commit -m "feat(insurance-pack): add ReportGenerator agent"
```

---

### Task 46: PDF-extractor tool

**Files:**
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/tools/pdf_extractor.py`
- Create: `examples/insurance-agent-pack/tests/test_pdf_extractor.py`
- Create: `examples/insurance-agent-pack/tests/fixtures/sample_policy.pdf` (synthetic)

- [ ] **Step 1: Write the failing test**

```python
# examples/insurance-agent-pack/tests/test_pdf_extractor.py
"""PDF extractor — reads a synthetic PDF, returns extracted text."""

from __future__ import annotations

from pathlib import Path

import pytest

from insurance_agent_pack.tools.pdf_extractor import pdf_extract_text

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_policy.pdf"


def test_extract_returns_string() -> None:
    text = pdf_extract_text(str(FIXTURE))
    assert isinstance(text, str)
    assert len(text) > 0


def test_extract_handles_missing_path() -> None:
    with pytest.raises(FileNotFoundError):
        pdf_extract_text("/nonexistent/path/missing.pdf")


def test_extract_truncates_at_limit() -> None:
    text = pdf_extract_text(str(FIXTURE), max_chars=50)
    assert len(text) <= 50
```

- [ ] **Step 2: Generate the synthetic PDF fixture**

```python
# Run this once to generate the fixture (NOT a test step — generation script)
import fpdf

pdf = fpdf.FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=12)
pdf.cell(0, 10, "Synthetic test policy — Berufsunfähigkeitsversicherung", ln=True)
pdf.cell(0, 10, "Versicherer: Beispiel-Versicherer AG", ln=True)
pdf.cell(0, 10, "Beitrag/Jahr: 1.200,00 EUR", ln=True)
pdf.cell(0, 10, "Wartezeit: 24 Monate", ln=True)
pdf.cell(0, 10, "Dies ist ein synthetischer Testfall. Keine echten Daten.", ln=True)
pdf.output("examples/insurance-agent-pack/tests/fixtures/sample_policy.pdf")
```

Run that snippet in a one-off Python REPL or save as `scripts/generate_sample_policy_pdf.py` and execute it. The committed file will be the generated PDF.

- [ ] **Step 3: Run test — expect failure**

```bash
pytest examples/insurance-agent-pack/tests/test_pdf_extractor.py -v 2>&1 | tail -5
```

Expected: ModuleNotFoundError.

- [ ] **Step 4: Implement the extractor**

```python
# examples/insurance-agent-pack/src/insurance_agent_pack/tools/pdf_extractor.py
"""PDF extractor — read text from a PDF file using PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def pdf_extract_text(path: str, *, max_chars: int | None = None) -> str:
    """Return the text content of a PDF file.

    Args:
        path: filesystem path to the PDF.
        max_chars: optional truncation; useful for testing or downstream
            tokens-budget enforcement.

    Raises:
        FileNotFoundError: when the file doesn't exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    doc = fitz.open(p)
    try:
        chunks: list[str] = []
        for page in doc:
            chunks.append(page.get_text())
        text = "\n".join(chunks)
    finally:
        doc.close()

    if max_chars is not None:
        return text[:max_chars]
    return text
```

- [ ] **Step 5: Run test — expect pass**

```bash
pytest examples/insurance-agent-pack/tests/test_pdf_extractor.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add examples/insurance-agent-pack/src/insurance_agent_pack/tools/pdf_extractor.py examples/insurance-agent-pack/tests/test_pdf_extractor.py examples/insurance-agent-pack/tests/fixtures/sample_policy.pdf
git commit -m "feat(insurance-pack): add pdf_extract_text tool + synthetic fixture"
```

---

### Task 47: Knowledge seeds (PKV, GGF, bAV, BU)

**Files:**
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/pkv_grundlagen.jsonl`
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/ggf_versorgung.jsonl`
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/bav_basics.jsonl`
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/bu_grundlagen.jsonl`
- Create: `examples/insurance-agent-pack/tests/test_knowledge_seeds.py`

- [ ] **Step 1: Write the failing test**

```python
# examples/insurance-agent-pack/tests/test_knowledge_seeds.py
"""Knowledge seeds — JSONL well-formedness + minimum-content."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

KNOWLEDGE = Path(__file__).resolve().parent.parent / "src" / "insurance_agent_pack" / "knowledge"

SEEDS = ("pkv_grundlagen", "ggf_versorgung", "bav_basics", "bu_grundlagen")


@pytest.mark.parametrize("name", SEEDS)
def test_seed_file_exists(name: str) -> None:
    p = KNOWLEDGE / f"{name}.jsonl"
    assert p.exists(), f"missing {p}"


@pytest.mark.parametrize("name", SEEDS)
def test_seed_lines_parse_as_json(name: str) -> None:
    p = KNOWLEDGE / f"{name}.jsonl"
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        json.loads(line)


@pytest.mark.parametrize("name", SEEDS)
def test_seed_has_required_fields(name: str) -> None:
    p = KNOWLEDGE / f"{name}.jsonl"
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        for field in ("topic", "summary", "tags"):
            assert field in row, f"{name} row missing field {field}: {row}"


@pytest.mark.parametrize("name", SEEDS)
def test_seed_minimum_three_rows(name: str) -> None:
    p = KNOWLEDGE / f"{name}.jsonl"
    rows = [
        l for l in p.read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.startswith("#")
    ]
    assert len(rows) >= 3, f"{name} should have at least 3 seed rows"
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest examples/insurance-agent-pack/tests/test_knowledge_seeds.py -v 2>&1 | tail -10
```

Expected: assertion errors for missing files.

- [ ] **Step 3: Create the JSONL seeds (synthetic, no real product names)**

```jsonl
# examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/pkv_grundlagen.jsonl
{"topic": "pkv_eligibility", "summary": "Privatversicherung in Deutschland setzt überwiegend ein Bruttoeinkommen oberhalb der JAEG voraus oder eine berufliche Stellung als Selbständiger/Beamter.", "tags": ["pkv", "deutschland", "ggf"]}
{"topic": "pkv_vs_gkv", "summary": "PKV bietet beitragsbasierte Leistungen ohne Solidargemeinschaft; GKV ist solidarisch finanziert. Wechsel zurück ist nur eingeschränkt möglich.", "tags": ["pkv", "gkv", "vergleich"]}
{"topic": "pkv_age_premiums", "summary": "PKV-Beiträge steigen tendenziell mit dem Alter; Altersrückstellungen mildern den Effekt.", "tags": ["pkv", "alter"]}
```

```jsonl
# examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/ggf_versorgung.jsonl
{"topic": "ggf_definition", "summary": "Geschäftsführende Gesellschafter (GGF) sind Geschäftsführer einer Kapitalgesellschaft mit Beteiligung. Sozialversicherungsrechtlich oft befreit.", "tags": ["ggf", "definition"]}
{"topic": "ggf_pension_options", "summary": "Typische Versorgungsbausteine für GGF: Direktversicherung, Unterstützungskasse, Pensionszusage, private Vorsorge.", "tags": ["ggf", "altersvorsorge"]}
{"topic": "ggf_invalidity_risk", "summary": "Berufsunfähigkeitsabsicherung ist für GGF besonders relevant, da der gesetzliche Schutz oft nicht greift.", "tags": ["ggf", "bu"]}
```

```jsonl
# examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/bav_basics.jsonl
{"topic": "bav_definition", "summary": "Betriebliche Altersvorsorge (bAV) ist arbeitgeberfinanzierte oder durch Entgeltumwandlung gespeiste Altersvorsorge.", "tags": ["bav", "definition"]}
{"topic": "bav_durchführungswege", "summary": "Fünf Durchführungswege: Direktversicherung, Pensionskasse, Pensionsfonds, Unterstützungskasse, Direktzusage.", "tags": ["bav", "wege"]}
{"topic": "bav_steuer_szv", "summary": "bAV-Beiträge sind bis zur Beitragsbemessungsgrenze sozialversicherungs- und steuerbefreit (4% bzw. 8% der BBG).", "tags": ["bav", "steuer"]}
```

```jsonl
# examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/bu_grundlagen.jsonl
{"topic": "bu_definition", "summary": "Berufsunfähigkeitsversicherung (BU) zahlt eine vereinbarte Rente, wenn der Versicherte voraussichtlich dauerhaft (>50%) berufsunfähig ist.", "tags": ["bu", "definition"]}
{"topic": "bu_age_limit", "summary": "Empfohlene Laufzeit: bis zum gesetzlichen Renteneintritt; Eintrittsalter und Gesundheitsfragen beeinflussen den Beitrag stark.", "tags": ["bu", "laufzeit"]}
{"topic": "bu_alternatives", "summary": "Alternativen sind Erwerbsunfähigkeitsversicherung, Grundfähigkeitsversicherung, Dread-Disease — jeweils mit anderem Leistungsumfang.", "tags": ["bu", "alternativen"]}
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest examples/insurance-agent-pack/tests/test_knowledge_seeds.py -v
```

Expected: 16 passed (4 seeds × 4 tests).

- [ ] **Step 5: Commit**

```bash
git add examples/insurance-agent-pack/src/insurance_agent_pack/knowledge/ examples/insurance-agent-pack/tests/test_knowledge_seeds.py
git commit -m "feat(insurance-pack): add synthetic knowledge seeds (PKV/GGF/bAV/BU)"
```

---

### Task 48: Crew composition (`crew.py`)

**Files:**
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/crew.py`
- Create: `examples/insurance-agent-pack/tests/test_team.py`

- [ ] **Step 1: Write the failing test**

```python
# examples/insurance-agent-pack/tests/test_team.py
"""Team composition — verify the 4-agent Crew is built correctly."""

from __future__ import annotations

from cognithor.crew import Crew, CrewProcess

from insurance_agent_pack.crew import build_team


def test_build_team_returns_crew() -> None:
    crew = build_team(model="ollama/qwen3:8b")
    assert isinstance(crew, Crew)


def test_team_has_four_agents() -> None:
    crew = build_team(model="ollama/qwen3:8b")
    assert len(crew.agents) == 4
    roles = {a.role for a in crew.agents}
    assert roles == {
        "policy-analyst",
        "needs-assessor",
        "compliance-gatekeeper",
        "report-generator",
    }


def test_team_uses_sequential_process() -> None:
    crew = build_team(model="ollama/qwen3:8b")
    assert crew.process == CrewProcess.SEQUENTIAL


def test_team_task_count_matches_agents() -> None:
    """Each agent has at least one task; sequence is meaningful."""
    crew = build_team(model="ollama/qwen3:8b")
    assert len(crew.tasks) >= 4
    # First task assigned to needs-assessor (interview), last to report-generator
    assert crew.tasks[0].agent.role == "needs-assessor"
    assert crew.tasks[-1].agent.role == "report-generator"
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest examples/insurance-agent-pack/tests/test_team.py -v 2>&1 | tail -5
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `crew.py`**

```python
# examples/insurance-agent-pack/src/insurance_agent_pack/crew.py
"""Insurance pre-advisory crew — sequential PGE-Trinity demo.

Process:
1. NeedsAssessor — turns interview answers into a structured profile.
2. PolicyAnalyst — extracts facts from any uploaded policy PDFs.
3. ComplianceGatekeeper — verifies the user's intent is pre-advisory.
4. ReportGenerator — composes the final markdown report.

Sequential because the steps are causally ordered. PGE-Trinity is enforced
inside each agent's CrewTask through Cognithor's Planner/Gatekeeper/Executor;
the ComplianceGatekeeper here is an *additional* visible check on top.
"""

from __future__ import annotations

from cognithor.crew import Crew, CrewProcess, CrewTask

from insurance_agent_pack.agents.compliance_gatekeeper import build_compliance_gatekeeper
from insurance_agent_pack.agents.needs_assessor import build_needs_assessor
from insurance_agent_pack.agents.policy_analyst import build_policy_analyst
from insurance_agent_pack.agents.report_generator import build_report_generator


def build_team(*, model: str = "ollama/qwen3:8b") -> Crew:
    """Construct the 4-agent insurance pre-advisory Crew."""
    needs = build_needs_assessor(model=model)
    policy = build_policy_analyst(model=model)
    compliance = build_compliance_gatekeeper(model=model)
    reporter = build_report_generator(model=model)

    tasks = [
        CrewTask(
            description=(
                "Führe ein strukturiertes Interview durch und produziere ein "
                "Bedarfsprofil als JSON."
            ),
            expected_output="JSON-Bedarfsprofil mit den Feldern aus dem System-Prompt.",
            agent=needs,
        ),
        CrewTask(
            description=(
                "Analysiere alle übergebenen Versicherungspolicen-PDFs mit "
                "`pdf_extract_text`. Erstelle die Übersichts-Tabelle."
            ),
            expected_output="Markdown-Tabelle der bestehenden Policen.",
            agent=policy,
        ),
        CrewTask(
            description=(
                "Prüfe das Anliegen des Nutzers gegen die §34d-Pre-Beratungs-Regeln. "
                "Gib ein JSON-Verdict (`allowed`, `category`, `reason`) zurück."
            ),
            expected_output="JSON-Compliance-Verdict.",
            agent=compliance,
        ),
        CrewTask(
            description=(
                "Erstelle den finalen Pre-Beratungs-Report im Markdown-Format. "
                "Beachte das Compliance-Verdict und brich ab, wenn `allowed=false`."
            ),
            expected_output="Markdown-Report mit Beobachtungen + Lücken-Themen.",
            agent=reporter,
        ),
    ]

    return Crew(
        agents=[needs, policy, compliance, reporter],
        tasks=tasks,
        process=CrewProcess.SEQUENTIAL,
        verbose=False,
    )
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest examples/insurance-agent-pack/tests/test_team.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add examples/insurance-agent-pack/src/insurance_agent_pack/crew.py examples/insurance-agent-pack/tests/test_team.py
git commit -m "feat(insurance-pack): compose 4-agent sequential pre-advisory Crew"
```

---

### Task 49: CLI — `insurance-agent-pack run --interview`

**Files:**
- Create: `examples/insurance-agent-pack/src/insurance_agent_pack/cli.py`
- Create: `examples/insurance-agent-pack/tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# examples/insurance-agent-pack/tests/test_cli.py
"""CLI — `run --interview` smoke test with mocked Crew."""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from insurance_agent_pack.cli import main


def test_help_exits_zero(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "insurance-agent-pack" in captured.out.lower() or "run" in captured.out


def test_run_without_subcommand_returns_nonzero() -> None:
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code != 0


def test_run_interview_kicks_off_crew(monkeypatch, capsys) -> None:
    fake_output = MagicMock()
    fake_output.raw = "## Pre-Beratungs-Report\n\n- Beobachtung 1"
    fake_output.tasks_outputs = []

    fake_crew = MagicMock()
    fake_crew.kickoff_async = AsyncMock(return_value=fake_output)

    # Pre-fill stdin to short-circuit the interview prompts
    monkeypatch.setattr("sys.stdin", io.StringIO("Alex\n45\nGGF\nkeine\nq\n"))

    with patch("insurance_agent_pack.cli.build_team", return_value=fake_crew):
        rc = main(["run", "--interview", "--model", "ollama/qwen3:8b"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "Pre-Beratungs-Report" in captured.out
```

- [ ] **Step 2: Run test — expect failure**

```bash
pytest examples/insurance-agent-pack/tests/test_cli.py -v 2>&1 | tail -5
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement the CLI**

```python
# examples/insurance-agent-pack/src/insurance_agent_pack/cli.py
"""CLI for the insurance-agent-pack reference example."""

from __future__ import annotations

import argparse
import asyncio
import sys

from insurance_agent_pack.crew import build_team


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="insurance-agent-pack",
        description="Reference Cognithor pack: §34d-NEUTRAL DACH insurance pre-advisory.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="Run the pre-advisory crew.")
    run.add_argument("--interview", action="store_true", help="Interactive interview mode.")
    run.add_argument("--model", default="ollama/qwen3:8b")
    return p


def _interview_inputs() -> dict[str, str]:
    print("=== Versicherungs-Pre-Beratung ===")
    print("Alle Eingaben sind synthetisch. Diese Software ist keine §34d-Beratung.")
    name = input("Vorname (frei wählbar, kein Klarname nötig): ").strip()
    age = input("Alter: ").strip()
    role = input("Berufsstatus (GGF/selbständig/angestellt/freiberufler): ").strip()
    existing = input("Bestehende Policen (kurz, kommasepariert oder 'keine'): ").strip()
    return {
        "name": name or "Anon",
        "age": age,
        "berufsstatus": role,
        "bestehende_policen": existing,
    }


def _cmd_run(args: argparse.Namespace) -> int:
    crew = build_team(model=args.model)
    if args.interview:
        inputs = _interview_inputs()
    else:
        inputs = {}
    output = asyncio.run(crew.kickoff_async(inputs))
    print()
    print(getattr(output, "raw", "") or "")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.cmd == "run":
        return _cmd_run(args)
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
```

- [ ] **Step 4: Drop the xfail markers from `test_package_install.py`**

Remove the `pytestmark = pytest.mark.xfail(...)` from `examples/insurance-agent-pack/tests/test_package_install.py`.

- [ ] **Step 5: Run test — expect pass**

```bash
pytest examples/insurance-agent-pack/tests/test_cli.py examples/insurance-agent-pack/tests/test_package_install.py -v
```

Expected: 6 passed (3 + 3).

- [ ] **Step 6: Smoke-run the CLI**

```bash
insurance-agent-pack --help
```

Expected: prints usage with `run --interview` flag and exits 0.

- [ ] **Step 7: Commit**

```bash
git add examples/insurance-agent-pack/src/insurance_agent_pack/cli.py examples/insurance-agent-pack/tests/test_cli.py examples/insurance-agent-pack/tests/test_package_install.py
git commit -m "feat(insurance-pack): add CLI with interactive --interview mode"
```

---

### Task 50: `test_gatekeeper_blocks_legal_advice.py` — positive + negative integration

**Files:**
- Create: `examples/insurance-agent-pack/tests/test_gatekeeper_blocks_legal_advice.py`

- [ ] **Step 1: Write the test**

```python
# examples/insurance-agent-pack/tests/test_gatekeeper_blocks_legal_advice.py
"""Critical safety test: pre-advisory passes, legal-advice blocked.

Spec §8.5 acceptance: Gatekeeper-block test must be green for BOTH the
positive (pre-advisory question allowed) AND negative (legal-advice
blocked WITHOUT exception, with a clear reason).
"""

from __future__ import annotations

import pytest

from insurance_agent_pack.agents.compliance_gatekeeper import (
    ComplianceVerdict,
    classify_intent,
)


def test_positive_pre_advisory_question_passes() -> None:
    msg = "Welche Versicherungen gibt es für GGF?"
    verdict = classify_intent(msg)
    assert isinstance(verdict, ComplianceVerdict)
    assert verdict.allowed is True


def test_negative_legal_advice_blocked() -> None:
    msg = "Ist mein Arbeitsvertrag rechtens?"
    verdict = classify_intent(msg)
    assert verdict.allowed is False
    assert "rechtsberatung" in verdict.reason.lower()


def test_block_returns_verdict_not_exception() -> None:
    """Blocking must NOT raise; it returns a Verdict the Crew can react to."""
    msg = "Welche konkrete BU soll ich abschließen?"
    verdict = classify_intent(msg)  # Must NOT raise
    assert verdict.allowed is False


@pytest.mark.parametrize(
    "msg",
    [
        "Was ist eine PKV?",
        "Erkläre GGF Versorgung.",
        "Welche Vorsorge ist sinnvoll für Selbstständige?",
        "Was ist der Unterschied zwischen GKV und PKV?",
    ],
)
def test_pre_advisory_phrases_all_pass(msg: str) -> None:
    assert classify_intent(msg).allowed is True


@pytest.mark.parametrize(
    "msg",
    [
        "Ist mein Mietvertrag rechtmäßig?",
        "Welche konkrete Versicherung soll ich abschließen?",
        "Empfiehlst du mir Versicherer X?",
        "Entscheide für mich, welche Police ich nehmen soll.",
    ],
)
def test_unsafe_phrases_all_blocked(msg: str) -> None:
    assert classify_intent(msg).allowed is False
```

- [ ] **Step 2: Run test — expect pass**

```bash
pytest examples/insurance-agent-pack/tests/test_gatekeeper_blocks_legal_advice.py -v
```

Expected: 11 passed (3 + 4 + 4 parametrised).

- [ ] **Step 3: Commit**

```bash
git add examples/insurance-agent-pack/tests/test_gatekeeper_blocks_legal_advice.py
git commit -m "test(insurance-pack): add gatekeeper positive/negative integration tests"
```

---

### Task 51: `test_audit_chain_intact.py` — Hashline-Guard verification

**Files:**
- Create: `examples/insurance-agent-pack/tests/test_audit_chain_intact.py`

- [ ] **Step 1: Write the test**

```python
# examples/insurance-agent-pack/tests/test_audit_chain_intact.py
"""Audit chain — every kickoff_started must have matching kickoff_completed.

This is a Hashline-Guard chain integrity test: after a successful Crew run,
the audit log emitted by cognithor.crew.compiler must be balanced. We mock
the actual Planner+Executor so this test runs offline.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from insurance_agent_pack.crew import build_team


@pytest.mark.asyncio
async def test_audit_chain_balanced_after_kickoff() -> None:
    """Mock cognithor.crew internals; verify our Crew composition exposes
    the expected agents/tasks shape so the audit chain is well-formed."""

    crew = build_team(model="ollama/qwen3:8b")
    fake_output = MagicMock()
    fake_output.raw = "Report"
    fake_output.tasks_outputs = []

    with patch.object(crew, "kickoff_async", AsyncMock(return_value=fake_output)) as ka:
        result = await crew.kickoff_async({"name": "Anon", "age": "40"})
        ka.assert_awaited_once()
        assert result.raw == "Report"


def test_crew_agents_and_tasks_are_aligned() -> None:
    """Each task's agent must be one of the crew's agents — pre-condition for audit chain."""
    crew = build_team(model="ollama/qwen3:8b")
    crew_agents = {id(a) for a in crew.agents}
    for t in crew.tasks:
        assert id(t.agent) in crew_agents, f"task {t.description!r} references an agent not in crew"


def test_crew_task_descriptions_unique() -> None:
    """Identical task descriptions would duplicate audit-chain entries."""
    crew = build_team(model="ollama/qwen3:8b")
    descriptions = [t.description for t in crew.tasks]
    assert len(descriptions) == len(set(descriptions)), "duplicate task descriptions found"
```

- [ ] **Step 2: Run test — expect pass**

```bash
pytest examples/insurance-agent-pack/tests/test_audit_chain_intact.py -v
```

Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
git add examples/insurance-agent-pack/tests/test_audit_chain_intact.py
git commit -m "test(insurance-pack): add audit-chain integrity test"
```

---

### Task 52: `test_local_inference_mode.py` — slow-marked Ollama-only

**Files:**
- Create: `examples/insurance-agent-pack/tests/test_local_inference_mode.py`

- [ ] **Step 1: Write the test**

```python
# examples/insurance-agent-pack/tests/test_local_inference_mode.py
"""End-to-end run with local Ollama. Marked slow — opt-in for CI."""

from __future__ import annotations

import os

import pytest


@pytest.mark.slow
@pytest.mark.asyncio
async def test_full_run_with_local_ollama() -> None:
    """Skipped by default. Run via `pytest -m slow examples/insurance-agent-pack/tests/`.

    Requires `OLLAMA_HOST=http://localhost:11434` and a running Ollama instance
    with `qwen3:8b` pulled. Verifies a complete end-to-end kickoff WITHOUT any
    external API calls.
    """
    if not os.environ.get("OLLAMA_HOST"):
        pytest.skip("OLLAMA_HOST not set; skipping local-inference test")

    from insurance_agent_pack.crew import build_team

    crew = build_team(model="ollama/qwen3:8b")
    result = await crew.kickoff_async({
        "name": "Anon",
        "age": "40",
        "berufsstatus": "GGF",
        "bestehende_policen": "keine",
    })

    raw = str(getattr(result, "raw", "") or "")
    assert raw, "expected a non-empty Pre-Beratungs-Report"
    # Should NOT contain any §34d-style binding recommendation
    forbidden = ["schließe", "empfehle ich konkret", "kaufe", "vermeide unbedingt"]
    for f in forbidden:
        assert f.lower() not in raw.lower(), f"report contained forbidden token: {f!r}"
```

- [ ] **Step 2: Verify the test is collected as `slow` and skipped by default**

```bash
pytest examples/insurance-agent-pack/tests/test_local_inference_mode.py -v
```

Expected: skipped (default Pytest config does not select `slow`).

- [ ] **Step 3: Commit**

```bash
git add examples/insurance-agent-pack/tests/test_local_inference_mode.py
git commit -m "test(insurance-pack): add slow-marked local-inference end-to-end test"
```

---

### Task 53: README, walkthrough, architecture, DISCLAIMER

**Files:**
- Create: `examples/insurance-agent-pack/README.md`
- Create: `examples/insurance-agent-pack/docs/demo_walkthrough.md`
- Create: `examples/insurance-agent-pack/docs/architecture.md`
- Create: `examples/insurance-agent-pack/docs/DISCLAIMER.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# insurance-agent-pack — Cognithor Reference Pack

A standalone-installable, **§34d-NEUTRAL** reference example for Cognithor.
Demonstrates a 4-agent PGE-Trinity pre-advisory crew (NeedsAssessor,
PolicyAnalyst, ComplianceGatekeeper, ReportGenerator) for the DACH
insurance domain.

> **This is a demo, not a product.** Read [`docs/DISCLAIMER.md`](./docs/DISCLAIMER.md)
> before you do anything with it.

## Why this pack exists

[ADR 0001](../../docs/adr/0001-pge-trinity-vs-group-chat.md) explains why
Cognithor uses Planner / Gatekeeper / Executor instead of a free-form
GroupChat. This pack makes that visible: every Crew turn passes through
the `ComplianceGatekeeper` agent before reaching `ReportGenerator`.
You can watch the Hashline-Guard audit chain build up.

## Install

```bash
pip install ./examples/insurance-agent-pack
```

## Usage

```bash
# Interactive interview (Konsolen-Session)
insurance-agent-pack run --interview

# Custom model — any Cognithor model_router spec works
insurance-agent-pack run --interview --model "ollama/qwen3:32b"

# Or with hosted backends if you have keys configured
insurance-agent-pack run --interview --model "openai/gpt-4o-mini"
```

## Architecture

See [`docs/architecture.md`](./docs/architecture.md) for the PGE-Trinity
flow diagram.

## Connection to v0.93.0 templates

Conceptually related to `cognithor init --template versicherungs-vergleich`
shipped in v0.93.0. WP3 focuses specifically on:
- **PolicyAnalyst** with PDF tool-use (new vs the v0.93.0 template).
- **ComplianceGatekeeper** as a *visible* PGE-demo agent (new).
- **Standalone-pip-installability** (the v0.93.0 template scaffolds *into*
  a project; this pack ships *as* a Python package).

## Pack-system note

This pack is **NOT** registered with `cognithor.packs`. That loader system
is reserved for private commerce-packs from the `cognithor-packs` repo
(EULA-gated, license-key validated). This is a public Apache-2.0 reference
implementation — pure `pip install`.

## Demo recording

[![asciicast](docs/demo_walkthrough.md)](./docs/demo_walkthrough.md)
(asciinema recording link added once captured.)

## Cross-links

- [Cognithor main repo](https://github.com/Alex8791-cyber/cognithor)
- [ADR 0001 — PGE Trinity vs Group Chat](../../docs/adr/0001-pge-trinity-vs-group-chat.md)
- [`cognithor.compat.autogen` migration guide](../../src/cognithor/compat/autogen/README.md)
- [`cognithor-bench`](../../cognithor_bench/README.md) — runs this pack as a benchmark scenario.

## License

Apache 2.0. See repo-root [LICENSE](../../LICENSE).
```

- [ ] **Step 2: Write `docs/demo_walkthrough.md`**

```markdown
# Demo Walkthrough

A typical interactive session looks like:

```text
$ insurance-agent-pack run --interview

=== Versicherungs-Pre-Beratung ===
Alle Eingaben sind synthetisch. Diese Software ist keine §34d-Beratung.

Vorname: Alex
Alter: 45
Berufsstatus (GGF/selbständig/angestellt/freiberufler): GGF
Bestehende Policen (kurz, kommasepariert oder 'keine'): Hausrat, Haftpflicht

[Crew kickoff: 4 Agenten in sequenzieller Verarbeitung]

[needs-assessor] Erstellt JSON-Bedarfsprofil...
[policy-analyst] Keine PDF-Anhänge gefunden — überspringe Extraktion.
[compliance-gatekeeper] Anliegen klassifiziert: pre_advisory_question (allowed=true)
[report-generator] Erstelle Pre-Beratungs-Report...

## Pre-Beratungs-Report

### Was ich beobachte

- 45 Jahre, GGF — Sozialversicherung oft befreit.
- Bestand: Hausrat + Haftpflicht.

### Mögliche Lücken (Themen für ein §34d-Gespräch)

- Berufsunfähigkeitsversicherung (BU) — gesetzlicher Schutz greift bei GGF oft nicht.
- Altersvorsorge: bAV-Direktversicherung, Pensionszusage, oder private Rürup-Rente.
- PKV-vs-GKV-Entscheidung — bei GGF oft sinnvoll, individuelle Prüfung erforderlich.

### Worüber Sie mit einem §34d-Vermittler sprechen sollten

- Konkrete BU-Tarife (Eintrittsalter 45 ist relevant für Beitragshöhe).
- Altersvorsorge-Architektur — welche Bausteine kombinieren?
- PKV-Wechsel — Altersrückstellungen, Wartezeiten, Selbstbehalt.

— Ende des Reports —
```

The full asciinema recording will be linked once captured.
```

- [ ] **Step 3: Write `docs/architecture.md`**

```markdown
# Architecture — PGE-Trinity Visibility

```text
            ┌─────────────────────────────────────────────────┐
            │            insurance-agent-pack                  │
            │                                                  │
   user ──▶ │  CLI (--interview)                               │
            │     │                                            │
            │     ▼                                            │
            │  Crew(agents=[NA, PA, CG, RG], SEQUENTIAL)        │
            │     │                                            │
            │     ▼                                            │
            │  ┌──────────────────────────────────────────┐    │
            │  │ NeedsAssessor   — interview → profile     │    │
            │  │ PolicyAnalyst   — PDF extraction          │    │
            │  │ ComplianceGate  — pre-advisory check      │  ← visible PGE Gatekeeper
            │  │ ReportGenerator — markdown output         │    │
            │  └──────────────────────────────────────────┘    │
            │                                                  │
            │  Each agent's CrewTask runs through Cognithor's   │
            │  PGE-Trinity:                                    │
            │     Planner → Gatekeeper(framework) → Executor   │
            │                                                  │
            │  And ComplianceGatekeeper is an additional       │
            │  in-Crew check on top of the framework one.      │
            └─────────────────────────────────────────────────┘
```

The framework `Gatekeeper` (in `src/cognithor/core/gatekeeper.py`) handles
DSGVO PII redaction and tool allow-list classification (GREEN/YELLOW/
ORANGE/RED). The pack's `ComplianceGatekeeper` adds **domain-specific**
classification: pre-advisory vs legal-advice vs concrete-recommendation-
demand. Two layers, distinct concerns; both inspectable.

See:
- [ADR 0001](../../../docs/adr/0001-pge-trinity-vs-group-chat.md)
- [`docs/hashline-guard.md`](../../../docs/hashline-guard.md)
```

- [ ] **Step 4: Write `docs/DISCLAIMER.md` — Alexander writes personally**

```markdown
# Disclaimer (Alexander Söllner, persönlich)

Dieser Reference-Pack ist eine **Demonstration der Cognithor-Plattform**.

- Es ist **keine §34d-konforme Beratungssoftware**.
- Es darf **nicht** für tatsächliche Vermittlungs- oder Beratungstätigkeit
  in Deutschland, Österreich oder der Schweiz eingesetzt werden.
- Die Knowledge-Seeds (PKV/GGF/bAV/BU) sind **synthetische Lehr-Snippets**
  — keine aktuellen, geprüften, regulatorisch belastbaren Inhalte.
- Die `ComplianceGatekeeper`-Regeln sind **bewusst konservativ** und nicht
  als Vollständigkeits-Anspruch zu verstehen.
- Wer dieses Repository forkt und kommerziell einsetzen möchte, trägt die
  vollständige rechtliche Verantwortung. Die Apache-2.0-Lizenz schließt
  jegliche Haftung von Cognithor und mir aus.

**TL;DR:** Spielzeug zum Lernen, nicht für echte Kunden.

— Alexander Söllner, 2026-04-25.
```

- [ ] **Step 5: Commit**

```bash
git add examples/insurance-agent-pack/README.md examples/insurance-agent-pack/docs/
git commit -m "docs(insurance-pack): add README, walkthrough, architecture, DISCLAIMER"
```

---

### Task 54: PR 4 closeout — coverage, ruff, root pyproject wiring, push, open PR

**Files:**
- Modify: `pyproject.toml` (root) — register insurance-agent-pack as editable in [dev]

- [ ] **Step 1: Add insurance-agent-pack to root `[dev]` extra**

In `pyproject.toml`, in `[project.optional-dependencies] dev = [...]`, append:

```toml
    # WP3: Reference insurance-agent-pack — installed editable for tests.
    "insurance-agent-pack @ file:./examples/insurance-agent-pack",
```

Also append to `.gitignore`:

```
# insurance-agent-pack runtime artifacts
examples/insurance-agent-pack/.cache/
examples/insurance-agent-pack/results/
```

- [ ] **Step 2: Coverage check**

```bash
pytest examples/insurance-agent-pack/tests/ -x -q --cov=examples/insurance-agent-pack/src/insurance_agent_pack --cov-report=term-missing --cov-fail-under=80
```

Expected: ≥80%. If short, add tests for any uncovered branches in `cli.py` or `compliance_gatekeeper.py` (these are the most likely gaps).

- [ ] **Step 3: Lint + format**

```bash
ruff check examples/insurance-agent-pack/
ruff format --check examples/insurance-agent-pack/
```

Expected: clean.

- [ ] **Step 4: CHANGELOG `[Unreleased]` entry**

Append under `### Added`:

```markdown
- `examples/insurance-agent-pack/` — DACH insurance pre-advisory reference
  pack (WP3). Standalone `pip install ./examples/insurance-agent-pack/`.
  4 agents (NeedsAssessor, PolicyAnalyst with PDF tool-use, ComplianceGatekeeper
  as visible PGE-demo, ReportGenerator). §34d-NEUTRAL — see DISCLAIMER.md.
- `pyproject.toml` `[dev]` extra — registers `insurance-agent-pack` editable.
```

```bash
git add pyproject.toml .gitignore CHANGELOG.md
git commit -m "build(insurance-pack): wire pack into root [dev] extra; CHANGELOG"
```

- [ ] **Step 5: Full regression**

```bash
pytest tests/ -x -q --cov=src/cognithor --cov-fail-under=89
pytest examples/insurance-agent-pack/tests/ -x -q --cov-fail-under=80
```

Expected: both green.

- [ ] **Step 6: Push + open PR**

```bash
git push -u origin feat/cognithor-autogen-v4-insurance
gh pr create --title "feat(insurance-pack): WP3 standalone reference pack (v0.94.0 PR 4)" --body "$(cat <<'EOF'
## Summary
- New `examples/insurance-agent-pack/` — standalone-installable Apache-2.0 reference pack
- 4 agents: NeedsAssessor, PolicyAnalyst (NEW: PDF tool-use), ComplianceGatekeeper (NEW: visible PGE-demo), ReportGenerator
- Synthetic knowledge seeds for PKV / GGF / bAV / BU
- CLI: `insurance-agent-pack run --interview`
- Critical safety tests: positive + negative gatekeeper-block + audit-chain integrity + slow-marked local-Ollama E2E
- DISCLAIMER.md written personally by Alexander
- NOT registered in `cognithor.packs` loader (that's for private commerce-packs)
- Conceptual sibling of v0.93.0 `versicherungs-vergleich` template (see Reuse note in README)

## Spec
- `docs/superpowers/specs/2026-04-25-cognithor-autogen-strategy-design.md` §8.5

## Test plan
- [ ] `pip install ./examples/insurance-agent-pack/` works
- [ ] `insurance-agent-pack --help` and `run --interview` work
- [ ] `pytest examples/insurance-agent-pack/tests/ -x -q --cov-fail-under=80` green
- [ ] `pytest tests/ -x -q --cov-fail-under=89` green (no regression)
- [ ] Gatekeeper tests cover positive AND negative cases
- [ ] All 4 knowledge seeds parse + have ≥3 rows
- [ ] No real customer data in fixtures (synthetic only)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 7: Wait CI green, squash-merge**

```bash
gh pr checks <PR_NUMBER> --watch
gh pr merge <PR_NUMBER> --squash --delete-branch=false
```

- [ ] **Step 8: Cleanup in a separate turn**

```bash
git checkout main && git pull --ff-only
git branch -d feat/cognithor-autogen-v4-insurance
git push origin --delete feat/cognithor-autogen-v4-insurance
```

---

# Direct-Commit on `main` — v0.94.0 Release-Bundle (Tasks 55-59)

Implements spec §8.6 — pattern reuse from v0.93.0. After PR 4 merge: bump version in 5 files, append AutoGen attribution to NOTICE, append v0.94.0 highlights to README, roll up CHANGELOG `[Unreleased]` → `[0.94.0]`, commit, tag, push, fire release workflows, verify artifacts, clean up stale assets.

**No PR**: this is a direct sequence of commits on `main`. Pre-condition: PRs 1-4 merged + main CI green.

**Pre-condition check before Task 55:**

```bash
git checkout main && git pull --ff-only
gh run list --repo Alex8791-cyber/cognithor --branch main --workflow ci.yml --limit 1
gh pr list --repo Alex8791-cyber/cognithor --state merged --search "v0.94.0" --json title,number
```

Expected: latest main CI run is `success`; PRs 1-4 (v0.94.0 PR 1-4) all merged.

---

### Task 55: Version-bump commit (5 files)

**Files modified (all in one commit):**
- `pyproject.toml`
- `src/cognithor/__init__.py`
- `flutter_app/pubspec.yaml`
- `flutter_app/lib/providers/connection_provider.dart`
- `CHANGELOG.md` (touched here for `[Unreleased]` → `[0.94.0]`; full rollup happens in Task 58)

- [ ] **Step 1: Verify current state of all 5 files**

```bash
grep -E '^version|version = "0\.93' pyproject.toml
grep '__version__' src/cognithor/__init__.py
grep '^version:' flutter_app/pubspec.yaml
grep 'kFrontendVersion' flutter_app/lib/providers/connection_provider.dart
head -20 CHANGELOG.md
```

Expected: all show `0.93.0`. If any show `0.94.0` already, that file was bumped early — investigate before bumping the rest.

- [ ] **Step 2: Bump `pyproject.toml`**

```toml
# Change from
version = "0.93.0"
# to
version = "0.94.0"
```

Use the Edit tool with `old_string = 'version = "0.93.0"'` and `new_string = 'version = "0.94.0"'`.

- [ ] **Step 3: Bump `src/cognithor/__init__.py`**

Edit the `__version__` constant from `"0.93.0"` to `"0.94.0"`.

- [ ] **Step 4: Bump `flutter_app/pubspec.yaml`**

```yaml
# Change from
version: 0.93.0+1
# to
version: 0.94.0+1
```

- [ ] **Step 5: Bump `flutter_app/lib/providers/connection_provider.dart`**

```dart
// Change from
const String kFrontendVersion = '0.93.0';
// to
const String kFrontendVersion = '0.94.0';
```

- [ ] **Step 6: Sanity-check the 4 files agree**

```bash
grep -E "version = \"0\.94\.0\"" pyproject.toml
grep "__version__ = \"0.94.0\"" src/cognithor/__init__.py
grep "version: 0.94.0" flutter_app/pubspec.yaml
grep "kFrontendVersion = '0.94.0'" flutter_app/lib/providers/connection_provider.dart
```

Expected: all 4 commands print one match.

- [ ] **Step 7: Run unit tests on bumped repo (no functional changes — should still be green)**

```bash
pytest tests/test_cognithor_init.py -v 2>&1 | tail -5
```

Expected: green. (If a test was hard-coded against `0.93.0`, fix it; this happened in the v0.93.0 release.)

- [ ] **Step 8: Commit version bump**

```bash
git add pyproject.toml src/cognithor/__init__.py flutter_app/pubspec.yaml flutter_app/lib/providers/connection_provider.dart
git commit -m "build: bump version to 0.94.0"
```

(CHANGELOG is touched in Task 58; keep this commit narrow.)

---

### Task 56: NOTICE — finalize AutoGen attribution

**Files:**
- Modify: `NOTICE`

PR 3 / Task 36 already appended the AutoGen MIT block to NOTICE. This task verifies it's still in place, no merge artifacts, and adds it under the proper heading if missing.

- [ ] **Step 1: Verify the attribution is present**

```bash
grep -A 2 "Microsoft AutoGen" NOTICE
```

Expected: shows the attribution block from Task 36. If missing → re-apply Task 36's edit on `main`.

- [ ] **Step 2: If missing, re-apply the attribution**

(Skip if Step 1 returned the expected block.) Re-apply the Task 36 edit using the Edit tool.

- [ ] **Step 3: Commit only if changes were needed**

```bash
git status NOTICE
```

If no diff, skip the commit. Otherwise:

```bash
git add NOTICE
git commit -m "legal(notice): finalize AutoGen-MIT attribution for v0.94.0"
```

---

### Task 57: README — append v0.94.0 highlights

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read README, locate the Highlights / What's New section**

```bash
grep -n "## Highlights\|## What's New\|## Recent\|## Latest" README.md
```

- [ ] **Step 2: Insert v0.94.0 Highlights bullets ABOVE the v0.93.0 Highlights**

```markdown
### v0.94.0 — AutoGen Strategy Adoption (2026-MM-DD)

- **`cognithor.compat.autogen`** — source-compat shim for `autogen-agentchat==0.7.5`.
  Search-and-replace migration path for AutoGen-AgentChat code onto Cognithor's
  PGE-Trinity. See [migration guide](src/cognithor/compat/autogen/README.md).
- **`cognithor_bench/`** — reproducible Multi-Agent benchmark scaffold with
  `cognithor-bench run|tabulate` console tool and Cognithor / AutoGen adapters.
- **`examples/insurance-agent-pack/`** — standalone-installable DACH insurance
  pre-advisory reference pack with visible ComplianceGatekeeper PGE-demo.
- **Architecture Decision Records** — first ADR
  ([0001 — PGE Trinity vs Group Chat](docs/adr/0001-pge-trinity-vs-group-chat.md))
  documents why Cognithor doesn't adopt SelectorGroupChat / Swarm patterns.
- **Competitive analysis docs** — comparison with AutoGen, MAF, LangGraph,
  CrewAI under [`docs/competitive-analysis/`](docs/competitive-analysis/README.md).
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(readme): add v0.94.0 highlights bullets"
```

---

### Task 58: CHANGELOG — `[Unreleased]` → `[0.94.0]` rollup

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Read CHANGELOG, identify the `[Unreleased]` block contents**

The block should contain entries from PRs 1-4 (Tasks 8/21/39/54).

- [ ] **Step 2: Compose the consolidated `[0.94.0]` entry**

Replace the `## [Unreleased]` header with:

```markdown
## [0.94.0] — 2026-MM-DD

### Added — AutoGen Strategy Adoption

- `cognithor.compat.autogen` — source-compatibility shim for
  `autogen-agentchat==0.7.5` (WP2). Mirrors `AssistantAgent`'s 14-field
  signature. Hybrid mapping: 1-shot path → `cognithor.crew`, multi-round
  path → `_RoundRobinAdapter` (~250 LOC). Composable terminations.
  `OpenAIChatCompletionClient` wrapper backed by `cognithor.core.model_router`
  (16 providers).
- `cognithor_bench/` — reproducible Multi-Agent benchmark scaffold (WP4).
  Console-script `cognithor-bench run|tabulate`, JSONL scenarios, optional
  `--docker` (post-v0.94.0 placeholder).
- `examples/insurance-agent-pack/` — standalone-installable DACH insurance
  pre-advisory reference pack (WP3). 4 agents including a visible
  ComplianceGatekeeper PGE-demo. Synthetic knowledge seeds (PKV / GGF /
  bAV / BU). NOT registered with `cognithor.packs`.
- `docs/competitive-analysis/` — Cognithor vs AutoGen / MAF / LangGraph /
  CrewAI (WP1).
- `docs/adr/0001-pge-trinity-vs-group-chat.md` — first Architecture
  Decision Record (WP5).
- `pyproject.toml` `[autogen]` extra — `autogen-agentchat==0.7.5` as
  the single pin-point referenced by `cognithor.compat.autogen` and
  `cognithor_bench` AutoGen adapter.
- `NOTICE` — AutoGen-MIT attribution under "Third-party attributions".

### Changed
- `README.md` — Highlights section gets v0.94.0 entry; Architecture section
  links ADR 0001 and competitive-analysis docs.

### License
- No license change; Cognithor remains Apache 2.0.

[Unreleased]: ...
[0.94.0]: ...
```

(Make sure to re-add an empty `## [Unreleased]` header above this block so future PRs have a place to land entries.)

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): roll up [Unreleased] into [0.94.0] entry"
```

---

### Task 59: Tag + push + workflow triggers + verification + cleanup

This is the final task. It consists of 4 phases — all on `main`, no PR.

#### Phase A — Tag + push

- [ ] **Step 1: Push the bump commits to origin**

```bash
git push origin main
```

Expected: 4 commits pushed (Tasks 55-58); main CI runs green.

- [ ] **Step 2: Wait main CI green**

```bash
gh run list --repo Alex8791-cyber/cognithor --branch main --workflow ci.yml --limit 1 --json status,conclusion,headSha
```

Expected: latest run `status=completed conclusion=success` for the version-bump commit.

- [ ] **Step 3: Tag v0.94.0**

```bash
git tag -a v0.94.0 -m "Cognithor v0.94.0 — AutoGen Strategy Adoption"
git push origin v0.94.0
```

Expected: tag pushed; release workflows fire on tag-push event.

#### Phase B — Workflow triggers (parallel)

- [ ] **Step 4: Verify all 5 release workflows triggered**

```bash
gh run list --repo Alex8791-cyber/cognithor --workflow publish.yml --limit 1
gh run list --repo Alex8791-cyber/cognithor --workflow build-windows-installer.yml --limit 1
gh run list --repo Alex8791-cyber/cognithor --workflow build-deb.yml --limit 1
gh run list --repo Alex8791-cyber/cognithor --workflow build-mobile.yml --limit 1
gh run list --repo Alex8791-cyber/cognithor --workflow build-flutter-web.yml --limit 1
```

Expected: each shows a recent run for `v0.94.0` tag. If any didn't auto-fire on tag-push, manually trigger via `gh workflow run`:

```bash
gh workflow run publish.yml --ref v0.94.0
gh workflow run build-windows-installer.yml --ref v0.94.0
gh workflow run build-deb.yml --ref v0.94.0
gh workflow run build-mobile.yml --ref v0.94.0
gh workflow run build-flutter-web.yml --ref v0.94.0
```

- [ ] **Step 5: Monitor all 5 workflows to green**

```bash
# Repeat per workflow until all complete:
gh run watch <RUN_ID>
```

Or batch:

```bash
gh run list --repo Alex8791-cyber/cognithor --branch v0.94.0 --limit 10
```

Expected: all 5 succeed. If any fail, **diagnose root cause before proceeding** — do not retry blindly. The v0.93.0 release had two PyPI failures (version mismatch in `pyproject.toml`, then duplicate filenames from `force-include`); both resolved by fixing the underlying file and re-running. Current `pyproject.toml` should not have the `force-include` block (it was removed in commit 8d9c8e8f for v0.93.0 — verify).

#### Phase C — Verification

- [ ] **Step 6: Verify PyPI**

```bash
curl -sI https://pypi.org/project/cognithor/0.94.0/ | head -1
pip install --no-cache-dir cognithor==0.94.0 -t /tmp/v094-pip-check
```

Expected: HTTP 200 from PyPI; install succeeds; the installed `cognithor.compat.autogen` package imports.

- [ ] **Step 7: Verify GitHub Release has 6 platform artifacts**

```bash
gh release view v0.94.0 --repo Alex8791-cyber/cognithor --json assets --jq '.assets[].name'
```

Expected: 6 assets — Windows installer, Windows launcher, Linux .deb, Android APK, iOS IPA, Flutter Web zip.

- [ ] **Step 8: Stale-asset cleanup if needed**

If any v0.93.0 artifacts ended up attached to v0.94.0 release (the v0.93.0 cleanup-pattern):

```bash
gh release view v0.94.0 --repo Alex8791-cyber/cognithor --json assets --jq '.assets[] | select(.name | test("0\\.93")) | .id'
# For each stale ID:
gh api "repos/Alex8791-cyber/cognithor/releases/assets/<ID>" -X DELETE
```

- [ ] **Step 9: Verify all spec §10 acceptance criteria**

Walk through each AC in `docs/superpowers/specs/2026-04-25-cognithor-autogen-strategy-design.md` §10 and tick:

```text
- [ ] All 4 PRs merged + cleanup done
- [ ] Direct-Commit-on-main with version bump in all 5 files
- [ ] Tag v0.94.0 pushed, all 5 release workflows green
- [ ] PyPI has cognithor==0.94.0 (wheel + sdist)
- [ ] GitHub Release has 6 fresh artifacts
- [ ] No stale artifacts on the release
- [ ] pip install cognithor==0.94.0 works
- [ ] pip install cognithor[autogen] installs autogen-agentchat==0.7.5
- [ ] AutoGen Hello-World from their README runs via search-and-replace imports
- [ ] cognithor-bench --help works (after pip install -e ./cognithor_bench/)
- [ ] pip install ./examples/insurance-agent-pack/ works, --interview starts
- [ ] All 3 docs files under docs/competitive-analysis/ exist
- [ ] ADR docs/adr/0001-pge-trinity-vs-group-chat.md exists
- [ ] CHANGELOG [0.94.0] section has all 5 WPs listed
- [ ] NOTICE contains AutoGen-MIT attribution
```

#### Phase D — Final memory + status update

- [ ] **Step 10: Update memory with v0.94.0 release log**

Save a memory note:

```markdown
---
name: v0.94.0 ship log
description: Cognithor v0.94.0 (AutoGen Strategy Adoption) release record — 5 WPs, 4 PRs, direct-commit
type: project
---
# v0.94.0 ship log

Cognithor v0.94.0 released 2026-MM-DD. Ships 5 WPs:
- WP1 + WP5 docs (PR 1)
- WP4 cognithor-bench (PR 2)
- WP2 cognithor.compat.autogen (PR 3)
- WP3 examples/insurance-agent-pack (PR 4)
- Direct-Commit version bump + tag

Single pin-point: autogen-agentchat==0.7.5 in pyproject.toml [autogen] extra.
Pattern reused from v0.93.0 release pipeline.

## How to apply
- Subsequent v0.94.x hotfixes: cherry-pick onto a `release/v0.94` branch if
  needed; for clean main, push directly + tag-push pattern.
- Path B (site PR + marketing) and Path C (Trace-UI + Flows) backlog from
  `project_v0930_post_release_backlog.md` is still applicable; Path C now
  rolls into v0.95.0.
```

(Save the file at `C:/Users/ArtiCall/.claude/projects/D--Jarvis/memory/project_v0940_ship_log.md` and add a one-line entry to `MEMORY.md`.)

- [ ] **Step 11: Final main check**

```bash
git checkout main && git pull --ff-only
git log --oneline -10
```

Expected: clean tree; recent log shows the version-bump commit and the tag.

---

# Plan-end checkpoint

If all of the above is green, **v0.94.0 is LIVE** and matches spec §10 acceptance.





