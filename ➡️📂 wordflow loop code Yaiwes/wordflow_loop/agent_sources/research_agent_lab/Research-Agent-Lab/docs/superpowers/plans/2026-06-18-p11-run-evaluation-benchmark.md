# P11: Run Evaluation Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic run-quality evaluation layer so each research workflow run can be scored, compared, and safely promoted to larger LLM or experiment budgets.

**Architecture:** Add a schema-backed `RunEvaluationAgent` after `ReviewerAgent`. It reads `ResearchState`, review results, experiment tree state, LLM budgets, experiment enablement flags, and artifact presence, then writes a structured `run_evaluations/*.json` artifact and summary values into state. Keep the evaluator itself rule-based in P11 so tests are stable and cheap, but include real DeepSeek API workflow verification after implementation.

**Tech Stack:** Python stdlib dataclasses, existing `Agent` / `AgentContext` / `ResearchState`, `ArtifactStore`, `unittest`, existing `video_llava` interpreter.

---

## Confirmed Execution Parameters

- Real LLM API verification is allowed for P11.
- Use the existing DeepSeek configuration loaded from `.env`; do not add or print any key.
- Verification should trigger multiple LLM-backed agents with a controlled budget to expose integration issues.
- Unit tests must remain offline and must not call the API.
- Internal experiment execution remains gated by `--enable-experiments`; P11 verification can run LLM API without changing `Intent-LED-mul-agent`.
- No experiment results are only acceptable when `enable_experiments` is false. If experiments are enabled but no result is produced, `RunEvaluationAgent` must block the run.

---

## File Structure

- Create: `schemas/run_evaluation.py`
  - Defines `RunEvaluationCheck` and `RunEvaluationReport`.
- Create: `agents/run_evaluator.py`
  - Implements deterministic run-quality checks.
- Modify: `agents/__init__.py`
  - Exports `RunEvaluationAgent`.
- Modify: `workflows/factory.py`
  - Inserts `RunEvaluationAgent` after `ReviewerAgent` and before `LiteratureMemoryPersistenceAgent`.
- Create: `tests/test_run_evaluator.py`
  - Unit tests for scoring, blocking issues, warnings, and tree integrity checks.
- Modify: `tests/test_full_research_loop.py`
  - Verifies offline workflow produces a run evaluation artifact and state values.
- Modify: `docs/project_handoff.md`
  - Updates P10/P11 test count, agent list, commands, and next steps.
- Create: `docs/run_evaluation.md`
  - Human-facing explanation of score semantics and how to inspect reports.

---

## Task 1: Schema For Run Evaluation

**Files:**
- Create: `schemas/run_evaluation.py`
- Test: `tests/test_run_evaluator.py`

- [ ] **Step 1: Write failing schema test**

Add the first test file with schema assertions:

```python
# tests/test_run_evaluator.py
from __future__ import annotations

from unittest import TestCase, main

from schemas.run_evaluation import RunEvaluationCheck, RunEvaluationReport


class RunEvaluationSchemaTest(TestCase):
    def test_report_defaults(self):
        check = RunEvaluationCheck(
            name="llm_budget",
            status="pass",
            severity="info",
            message="budget ok",
        )
        report = RunEvaluationReport(
            status="pass",
            score=100,
            checks=[check],
            recommended_next_action="expand_budget_carefully",
        )

        self.assertTrue(report.evaluation_id.startswith("runeval_"))
        self.assertEqual(report.status, "pass")
        self.assertEqual(report.score, 100)
        self.assertEqual(report.checks[0].name, "llm_budget")
        self.assertEqual(report.blocking_issues, [])
        self.assertEqual(report.warnings, [])


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_evaluator.RunEvaluationSchemaTest
```

Expected: `ModuleNotFoundError: No module named 'schemas.run_evaluation'`.

- [ ] **Step 3: Implement schema**

Create:

```python
# schemas/run_evaluation.py
from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id, utc_now


@dataclass(slots=True)
class RunEvaluationCheck:
    name: str
    status: str
    severity: str
    message: str
    evidence: dict = field(default_factory=dict)


@dataclass(slots=True)
class RunEvaluationReport:
    status: str
    score: int
    recommended_next_action: str
    evaluation_id: str = field(default_factory=lambda: new_id("runeval"))
    created_at: str = field(default_factory=utc_now)
    checks: list[RunEvaluationCheck] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)
```

- [ ] **Step 4: Run schema test to verify it passes**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_evaluator.RunEvaluationSchemaTest
```

Expected: `OK`.

---

## Task 2: Deterministic RunEvaluationAgent

**Files:**
- Create: `agents/run_evaluator.py`
- Test: `tests/test_run_evaluator.py`

- [ ] **Step 1: Add failing tests for scoring and blocking issues**

Append to `tests/test_run_evaluator.py`:

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from agents.run_evaluator import RunEvaluationAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


def _topic() -> TopicPack:
    return TopicPack(
        topic_name="eval_test",
        experiment_metrics=["ADE", "FDE"],
    )


def _context(tmp: str, settings: dict | None = None) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp)),
        memory_store=None,  # type: ignore
        tool_registry=None,  # type: ignore
        settings=settings or {},
    )


class RunEvaluationAgentTest(TestCase):
    def test_passes_clean_offline_run(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 2,
                "method_card_count": 2,
                "unsupported_evidence_count": 0,
                "review_status": "pass",
                "llm_calls_used": 0,
                "llm_tokens_used": 0,
            })

            result = RunEvaluationAgent().run(state, _context(tmp))

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "pass")
            self.assertGreaterEqual(report["score"], 85)
            self.assertEqual(state.values["run_evaluation_status"], "pass")
            self.assertIn("run_evaluations", result.artifacts)

    def test_blocks_budget_overrun(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "llm_calls_used": 5,
                "llm_tokens_used": 100,
            })
            ctx = _context(tmp, {"llm_call_budget": 3, "llm_token_budget": 20000})

            RunEvaluationAgent().run(state, ctx)

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("LLM call budget" in item for item in report["blocking_issues"]))

    def test_blocks_selected_tree_node_without_result(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_tree": {
                    "root_id": "root",
                    "max_depth": 2,
                    "max_active_nodes": 3,
                    "nodes": [
                        {"node_id": "root", "status": "active", "depth": 0, "children_ids": ["n1"], "result": {}},
                        {"node_id": "n1", "status": "selected", "depth": 1, "children_ids": [], "result": {}},
                    ],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_tree_search": True}))

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("selected" in item.lower() for item in report["blocking_issues"]))

    def test_experiment_results_absent_is_pass_when_experiments_disabled(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_results": [],
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_experiments": False}))

            checks = state.values["run_evaluation"]["checks"]
            exp_check = next(c for c in checks if c["name"] == "experiment_results")
            self.assertEqual(exp_check["status"], "pass")
            self.assertEqual(exp_check["severity"], "info")

    def test_experiment_results_absent_blocks_when_experiments_enabled(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_results": [],
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_experiments": True}))

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("no experiment results" in item for item in report["blocking_issues"]))
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_evaluator
```

Expected: import failure for `agents.run_evaluator`.

- [ ] **Step 3: Implement RunEvaluationAgent**

Create:

```python
# agents/run_evaluator.py
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.run_evaluation import RunEvaluationCheck, RunEvaluationReport


class RunEvaluationAgent(Agent):
    name = "run_evaluator"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        checks: list[RunEvaluationCheck] = []

        checks.extend(_literature_checks(state))
        checks.extend(_budget_checks(state, context.settings))
        checks.extend(_experiment_checks(state, context.settings))
        checks.extend(_tree_checks(state))
        checks.extend(_review_checks(state))

        blocking = [c.message for c in checks if c.status == "fail" and c.severity == "blocker"]
        warnings = [c.message for c in checks if c.status in {"warn", "fail"} and c.severity != "blocker"]
        score = _score(checks)
        status = "block" if blocking else ("needs_review" if warnings or score < 85 else "pass")
        action = _recommended_action(status, checks)

        report = RunEvaluationReport(
            status=status,
            score=score,
            checks=checks,
            blocking_issues=blocking,
            warnings=warnings,
            recommended_next_action=action,
            summary=[
                f"status={status}",
                f"score={score}",
                f"checks={len(checks)}",
                f"blocking={len(blocking)}",
                f"warnings={len(warnings)}",
            ],
        )
        payload = asdict(report)
        context.artifact_store.save_json(
            state.run_id, "run_evaluations", report.evaluation_id, payload
        )
        state.values["run_evaluation"] = payload
        state.values["run_evaluation_status"] = status
        state.values["run_quality_score"] = score
        return AgentResult(
            notes=[f"run evaluation status={status} score={score}"],
            artifacts={"run_evaluations": [report.evaluation_id]},
            values={
                "run_evaluation": payload,
                "run_evaluation_status": status,
                "run_quality_score": score,
            },
        )


def _literature_checks(state: ResearchState) -> list[RunEvaluationCheck]:
    selected = int(state.values.get("selected_paper_count", 0) or 0)
    method_cards = int(state.values.get("method_card_count", 0) or len(state.values.get("method_cards", []) or []))
    unsupported = int(state.values.get("unsupported_evidence_count", 0) or 0)
    checks = [
        RunEvaluationCheck(
            name="literature_selected_papers",
            status="pass" if selected > 0 else "warn",
            severity="warning",
            message="selected papers are available" if selected > 0 else "no selected papers found",
            evidence={"selected_paper_count": selected},
        ),
        RunEvaluationCheck(
            name="method_cards",
            status="pass" if method_cards >= min(selected, 1) else "warn",
            severity="warning",
            message="method cards are available" if method_cards else "no method cards found",
            evidence={"method_card_count": method_cards, "selected_paper_count": selected},
        ),
        RunEvaluationCheck(
            name="evidence_support",
            status="pass" if unsupported == 0 else "fail",
            severity="warning",
            message="no unsupported evidence" if unsupported == 0 else f"{unsupported} unsupported evidence record(s)",
            evidence={"unsupported_evidence_count": unsupported},
        ),
    ]
    return checks


def _budget_checks(state: ResearchState, settings: dict[str, Any]) -> list[RunEvaluationCheck]:
    calls = int(state.values.get("llm_calls_used", 0) or 0)
    tokens = int(state.values.get("llm_tokens_used", 0) or 0)
    call_budget = settings.get("llm_call_budget")
    token_budget = settings.get("llm_token_budget")
    checks: list[RunEvaluationCheck] = []
    if isinstance(call_budget, int) and call_budget >= 0:
        checks.append(RunEvaluationCheck(
            name="llm_call_budget",
            status="pass" if calls <= call_budget else "fail",
            severity="blocker",
            message="LLM call budget ok" if calls <= call_budget else f"LLM call budget exceeded: {calls}>{call_budget}",
            evidence={"llm_calls_used": calls, "llm_call_budget": call_budget},
        ))
    if isinstance(token_budget, int) and token_budget >= 0:
        checks.append(RunEvaluationCheck(
            name="llm_token_budget",
            status="pass" if tokens <= token_budget else "fail",
            severity="blocker",
            message="LLM token budget ok" if tokens <= token_budget else f"LLM token budget exceeded: {tokens}>{token_budget}",
            evidence={"llm_tokens_used": tokens, "llm_token_budget": token_budget},
        ))
    return checks


def _experiment_checks(state: ResearchState, settings: dict[str, Any]) -> list[RunEvaluationCheck]:
    results = state.values.get("experiment_results") or []
    if not results:
        experiments_enabled = bool(settings.get("enable_experiments"))
        return [RunEvaluationCheck(
            name="experiment_results",
            status="fail" if experiments_enabled else "pass",
            severity="blocker" if experiments_enabled else "info",
            message=(
                "experiments were enabled but no experiment results were produced"
                if experiments_enabled
                else "experiments disabled; no experiment results expected"
            ),
            evidence={"enable_experiments": experiments_enabled},
        )]
    errors = [r for r in results if isinstance(r, dict) and r.get("status") == "error"]
    unparsed = [r for r in results if isinstance(r, dict) and r.get("status") == "unparsed"]
    return [
        RunEvaluationCheck(
            name="experiment_errors",
            status="pass" if not errors else "fail",
            severity="blocker",
            message="no experiment execution errors" if not errors else f"{len(errors)} experiment error(s)",
            evidence={"error_count": len(errors)},
        ),
        RunEvaluationCheck(
            name="experiment_unparsed",
            status="pass" if not unparsed else "warn",
            severity="warning",
            message="all experiment results parsed" if not unparsed else f"{len(unparsed)} unparsed experiment result(s)",
            evidence={"unparsed_count": len(unparsed)},
        ),
    ]


def _tree_checks(state: ResearchState) -> list[RunEvaluationCheck]:
    tree = state.values.get("experiment_tree")
    if not isinstance(tree, dict) or not tree.get("nodes"):
        return [RunEvaluationCheck(
            name="experiment_tree",
            status="pass",
            severity="info",
            message="no experiment tree to evaluate",
            evidence={},
        )]
    nodes = tree.get("nodes") or []
    root_id = tree.get("root_id", "")
    node_ids = {n.get("node_id") for n in nodes}
    selected_without_result = [
        n.get("node_id") for n in nodes
        if n.get("status") == "selected" and not n.get("result")
    ]
    pending = [
        n for n in nodes
        if n.get("status") == "pending" and n.get("depth", 0) < tree.get("max_depth", 2)
    ]
    max_active = int(tree.get("max_active_nodes", 3) or 3)
    checks = [
        RunEvaluationCheck(
            name="tree_root_exists",
            status="pass" if root_id in node_ids else "fail",
            severity="blocker",
            message="experiment tree root exists" if root_id in node_ids else f"experiment tree root missing: {root_id}",
            evidence={"root_id": root_id, "node_count": len(nodes)},
        ),
        RunEvaluationCheck(
            name="tree_selected_nodes",
            status="pass" if not selected_without_result else "fail",
            severity="blocker",
            message="no selected nodes without result" if not selected_without_result else f"selected nodes without result: {selected_without_result}",
            evidence={"selected_without_result": selected_without_result},
        ),
        RunEvaluationCheck(
            name="tree_active_width",
            status="pass" if len(pending) <= max_active else "fail",
            severity="warning",
            message="pending branch count within max active" if len(pending) <= max_active else f"pending branches exceed max active: {len(pending)}>{max_active}",
            evidence={"pending_count": len(pending), "max_active_nodes": max_active},
        ),
    ]
    checks.extend(_tree_bidirectional_checks(nodes))
    return checks


def _tree_bidirectional_checks(nodes: list[dict]) -> list[RunEvaluationCheck]:
    node_map = {n.get("node_id"): n for n in nodes}
    problems: list[str] = []
    for node in nodes:
        nid = node.get("node_id")
        for cid in node.get("children_ids", []) or []:
            child = node_map.get(cid)
            if not child:
                problems.append(f"{nid} references missing child {cid}")
            elif child.get("parent_id") != nid:
                problems.append(f"{nid}->{cid} but child parent_id={child.get('parent_id')}")
    return [RunEvaluationCheck(
        name="tree_bidirectional_links",
        status="pass" if not problems else "fail",
        severity="warning",
        message="tree parent/child links are consistent" if not problems else "; ".join(problems[:5]),
        evidence={"problem_count": len(problems), "problems": problems[:10]},
    )]


def _review_checks(state: ResearchState) -> list[RunEvaluationCheck]:
    review_status = str(state.values.get("review_status", "unknown"))
    return [RunEvaluationCheck(
        name="review_status",
        status="pass" if review_status == "pass" else "warn",
        severity="warning",
        message=f"review_status={review_status}",
        evidence={"review_status": review_status},
    )]


def _score(checks: list[RunEvaluationCheck]) -> int:
    score = 100
    for check in checks:
        if check.status == "fail" and check.severity == "blocker":
            score -= 30
        elif check.status == "fail":
            score -= 15
        elif check.status == "warn":
            score -= 5
    return max(0, min(100, score))


def _recommended_action(status: str, checks: list[RunEvaluationCheck]) -> str:
    if status == "block":
        return "fix_blocking_issues_before_next_run"
    if any(c.status == "warn" for c in checks):
        return "review_warnings_before_expanding_budget"
    return "expand_budget_carefully"
```

- [ ] **Step 4: Run agent tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_evaluator
```

Expected: `OK`.

---

## Task 3: Workflow Integration

**Files:**
- Modify: `agents/__init__.py`
- Modify: `workflows/factory.py`
- Modify: `tests/test_full_research_loop.py`

- [ ] **Step 1: Add failing workflow test**

Add these assertions to `FullResearchLoopTest.test_offline_workflow_produces_reviewable_artifacts` after `state = workflow.run(topic)`:

```python
self.assertIn("run_evaluation_status", state.values)
self.assertIn("run_quality_score", state.values)
self.assertTrue(
    (run_dir / "artifacts" / "run_evaluations").exists()
)
self.assertGreaterEqual(
    len(list((run_dir / "artifacts" / "run_evaluations").glob("*.json"))),
    1,
)
```

- [ ] **Step 2: Run workflow test to verify it fails**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_full_research_loop.FullResearchLoopTest
```

Expected: missing `run_evaluation_status`.

- [ ] **Step 3: Export RunEvaluationAgent**

Modify `agents/__init__.py`:

```python
from agents.run_evaluator import RunEvaluationAgent
```

Add `"RunEvaluationAgent"` to `__all__`.

- [ ] **Step 4: Insert agent into workflow**

Modify `workflows/factory.py` imports:

```python
    RunEvaluationAgent,
```

Insert after `ReviewerAgent()` and before `LiteratureMemoryPersistenceAgent(...)`:

```python
    agents.append(ReviewerAgent())
    agents.append(RunEvaluationAgent())
    agents.append(LiteratureMemoryPersistenceAgent(lit_memory_store=literature_memory_store))
```

- [ ] **Step 5: Run workflow test**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_full_research_loop.FullResearchLoopTest
```

Expected: `OK`.

---

## Task 4: Tree Integrity Regression Coverage

**Files:**
- Modify: `tests/test_run_evaluator.py`

- [ ] **Step 1: Add failing bidirectional-link test**

Append:

```python
    def test_warns_on_inconsistent_tree_links(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_tree": {
                    "root_id": "root",
                    "max_depth": 2,
                    "max_active_nodes": 3,
                    "nodes": [
                        {"node_id": "root", "status": "active", "depth": 0, "children_ids": ["child"], "result": {}},
                        {"node_id": "child", "status": "pending", "depth": 1, "parent_id": "other", "children_ids": [], "result": {}},
                    ],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp))

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "needs_review")
            self.assertTrue(any("parent/child" in w or "root->child" in w for w in report["warnings"]))
```

- [ ] **Step 2: Run tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_evaluator
```

Expected: `OK` after Task 2 implementation.

---

## Task 5: Human-Facing Documentation

**Files:**
- Create: `docs/run_evaluation.md`
- Modify: `docs/project_handoff.md`

- [ ] **Step 1: Create run evaluation guide**

Create:

```markdown
# Run Evaluation

`RunEvaluationAgent` is a deterministic quality gate for each workflow run.

It runs after `ReviewerAgent` and writes:

- `state.values["run_evaluation_status"]`
- `state.values["run_quality_score"]`
- `artifacts/run_evaluations/<runeval_id>.json`

## Status

- `pass`: no blocking issues and score >= 85
- `needs_review`: no blocking issues, but warnings or lower score exist
- `block`: one or more blocking issues exist

## Current Checks

- literature selected papers and method cards
- unsupported evidence count
- LLM call and token budgets
- experiment execution errors and unparsed results
- experiment tree root, selected-node, width, and parent/child consistency
- reviewer status

## Recommended Use

Before increasing `--max-papers`, `--llm-call-budget`, or `--max-parallel-branches`, inspect the latest run evaluation artifact.

Do not expand budget when status is `block`.
```

- [ ] **Step 2: Update project handoff**

Update `docs/project_handoff.md`:

- `更新时间` to `2026-06-18（P11 规划/实施中）` when implementing begins.
- Add `RunEvaluationAgent` to implemented agents.
- Add `RunEvaluationReport` / `RunEvaluationCheck` to structured artifacts.
- Update test count after implementation.
- Replace stale “Paper triage flash LLM path 待实现” with the current fact that it is implemented.
- Add P11 verification commands, including the real DeepSeek API run below.
- Add next step after P11: inspect run evaluation trends across multiple runs before expanding experiment depth or branch width.

---

## Task 6: Verification

**Files:**
- All files touched above.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_evaluator tests.test_full_research_loop
```

Expected: `OK`.

- [ ] **Step 2: Run all tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p "test*.py"
```

Expected: all tests pass. Current baseline before P11 is `Ran 165 tests ... OK`.

- [ ] **Step 3: Run offline workflow smoke**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 1
```

Expected:

```text
stage=completed
review_status=<pass or needs_human_review>
```

Then inspect:

```text
data/runs/<run_id>/artifacts/run_evaluations/*.json
```

Expected JSON includes `status`, `score`, `checks`, `blocking_issues`, and `recommended_next_action`.

- [ ] **Step 4: Run controlled DeepSeek API workflow smoke**

This command intentionally triggers multiple LLM-backed agents through the current DeepSeek routes. It does not enable experiment execution.

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 2 --enable-llm --llm-call-budget 6 --llm-token-budget 50000
```

Expected:

```text
stage=completed
review_status=<pass or needs_human_review>
```

Then inspect:

```text
data/runs/<run_id>/artifacts/llm_calls/*.json
data/runs/<run_id>/artifacts/run_evaluations/*.json
```

Expected:

- At least one `llm_calls/*.json` record has `status="ok"` or a concrete non-secret error.
- No artifact contains an API key.
- `run_evaluation` reports LLM calls/tokens within budget.
- If an LLM agent fails, `run_evaluation_status` is `needs_review` or `block` with a concrete reason.

- [ ] **Step 5: Optional controlled API + tree-search smoke**

Run only after Step 4 completes without secret leakage or uncontrolled cost. This verifies tree-search integration while still keeping experiment execution disabled.

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 2 --enable-llm --llm-call-budget 6 --llm-token-budget 50000 --enable-tree-search --max-parallel-branches 2
```

Expected:

```text
stage=completed
review_status=<pass or needs_human_review>
```

Then inspect:

```text
data/runs/<run_id>/artifacts/run_evaluations/*.json
data/runs/<run_id>/artifacts/experiment_trees/
```

Expected:

- `run_evaluation` treats missing experiment results as non-blocking because `--enable-experiments` was not set.
- Any selected tree node without a result is reverted or reported as a blocker.
- Mermaid export, if produced, contains no recursion error or malformed tree.

---

## Self-Review

- Spec coverage: This plan implements the missing quality gate requested by `code_plan.md` section 14 and makes P8-P10 safer to expand.
- Placeholder scan: No `TBD`, `TODO`, or undefined future behavior remains in required code snippets.
- Type consistency: `RunEvaluationCheck`, `RunEvaluationReport`, `RunEvaluationAgent`, and state keys are consistently named across schema, agent, tests, and docs.
