import pytest

from runtime.src.core.code_generation_policy import GenerationRequest, authorize_generation
from runtime.src.core.crazy_wall_concurrency import ConcurrencyError, Mutation, apply_mutation
from runtime.src.core.goals12 import GOALS12, evaluate_goals12
from runtime.src.core.llm_boundary import enforce_boundary
from runtime.src.core.no_value_gap import ValueAssessment, decide_value
from runtime.src.core.parallel_scheduler import SchedulerError, TaskEnvelope, plan_tasks
from runtime.src.core.security_rewriter import assess_python, neutralize_python
from runtime.src.core.truth_reconciler import reconcile_sources


def test_g006_generation_last_resort_and_no_execution_authority():
    request = GenerationRequest(
        task_id="T-1",
        capability="new-capability",
        reuse_decision="GENERATE",
        placement="D_WORDFLOW",
        target_path="runtime/src/core/new_capability.py",
        contract_id="yaiwes.capability/v1",
        fables_binding="UNIVERSAL_PLUGIN_BUS",
        provenance_ref="audit:T-1",
        requested_by_llm=True,
    )
    decision = authorize_generation(request)
    assert decision.allowed is True
    assert decision.candidate_generation_allowed is True
    assert decision.execution_authorized is False
    assert decision.deployment_authorized is False
    assert authorize_generation(
        GenerationRequest(
            "T-2", "x", "REUSE", "D_WORDFLOW", "x.py", "c",
            "UNIVERSAL_PLUGIN_BUS", "p"
        )
    ).allowed is False


def test_g008_unsafe_call_is_blocked_and_neutralized():
    source = "import os\nresult = os.system('echo blocked')\n"
    assessment = assess_python(source)
    assert assessment.verdict == "BLOCK_AND_REVIEW"
    rewritten, reasons = neutralize_python(source)
    assert "SHELL_EXEC" in reasons
    assert "_yaiwes_blocked_operation" in rewritten
    assert assess_python("def add(a, b): return a + b").verdict == "ALLOW_STATIC_REVIEW"


def test_g009_no_unique_value_is_gap_and_review_is_required_for_value():
    duplicate = ValueAssessment("dup", 0, 4, 1, 1, 1, "APPROVE")
    assert decide_value(duplicate).verdict == "NO_VALUE_GAP"
    useful = ValueAssessment("useful", 2, 1, 1, 1, 2, "APPROVE")
    assert decide_value(useful).verdict == "VALUE_CONFIRMED"
    pending = ValueAssessment("pending", 2, 0, 1, 1, 1, "PENDING")
    assert decide_value(pending).verdict == "REVIEW_REQUIRED"


def test_g013_truth_drift_and_precedence():
    result = reconcile_sources(
        {"STATE": {"node": "A"}, "CHECKPOINT": {"node": "B"}},
        ("STATE", "CHECKPOINT"),
        ("STATE", "CHECKPOINT"),
        ("node",),
    )
    assert result.status == "DRIFT_DETECTED"
    assert result.canonical["node"] == "A"


def test_g015_goals12_requires_12_council_3_simulations_3_refutations():
    evidence = {goal: True for goal in GOALS12}
    assert evaluate_goals12(
        evidence,
        council_checks=12,
        simulations=3,
        refutations=3,
        cross_check=True,
    ).passed is True
    assert evaluate_goals12(
        evidence,
        council_checks=11,
        simulations=3,
        refutations=3,
        cross_check=True,
    ).passed is False


def test_g021_priority_parallel_fan_in_and_cycle_fail_closed():
    tasks = [
        TaskEnvelope("A", 1, "a"),
        TaskEnvelope("B", 5, "b"),
        TaskEnvelope("C", 2, "c", ("A", "B")),
    ]
    plan = plan_tasks(tasks, max_concurrency=2)
    assert plan.batches == (("B", "A"), ("C",))
    with pytest.raises(SchedulerError, match="CYCLE_DETECTED"):
        plan_tasks([
            TaskEnvelope("X", 1, "x", ("Y",)),
            TaskEnvelope("Y", 1, "y", ("X",)),
        ])


def test_g024_llm_is_advisory_only_for_deterministic_actions():
    assert enforce_boundary("draft_code", "LLM").allowed is True
    assert enforce_boundary("promote_deployment", "LLM").allowed is False
    assert enforce_boundary("schedule_dag", "DETERMINISTIC").allowed is True


def test_g030_optimistic_concurrency_owner_and_idempotency():
    document = {"version": 1, "applied_idempotency_keys": []}
    first = apply_mutation(document, Mutation("agent-a", 1, "k1", {"node": "X"}))
    assert first.status == "APPLIED"
    assert first.document["version"] == 2
    replay = apply_mutation(first.document, Mutation("agent-a", 2, "k1", {"node": "Y"}))
    assert replay.status == "IDEMPOTENT_REPLAY"
    assert replay.document["node"] == "X"
    with pytest.raises(ConcurrencyError, match="OWNER_CONFLICT"):
        apply_mutation(first.document, Mutation("agent-b", 2, "k2", {"node": "Y"}))
