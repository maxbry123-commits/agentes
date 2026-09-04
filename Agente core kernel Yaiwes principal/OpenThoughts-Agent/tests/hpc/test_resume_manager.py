"""Unit tests for ``hpc/resume_manager.py``.

Each test seeds a temp job_dir with synthetic state (config.json,
per-trial config.json, result.json blobs), then asserts the manager's
classification and side effects. No Harbor, Daytona, or network.

Run from the OT-Agent repo root with:
    .venv/bin/python -m pytest tests/hpc/test_resume_manager.py -v
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from hpc import resume_manager as rm
from hpc.resume_manager import (
    ResumeAction,
    ResumeBail,
    ResumeState,
    apply_mutation,
    inspect_resume,
    plan_mutation,
    render_bail_message,
    resolve_resume_policy,
    resolve_resume_policy_for_launch,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


def _planned_config(
    *,
    model_name: str = "Qwen/Qwen3-32B",
    n_concurrent: int = 32,
    api_base: str = "http://node-0:8000/v1",
    timeout_multiplier: float = 1.0,
    agent_name: str = "terminus-2",
) -> Dict[str, Any]:
    """Build a synthetic planned top-level config dict."""
    return {
        "job_name": "test-job",
        "n_attempts": 1,
        "timeout_multiplier": timeout_multiplier,
        "n_concurrent_trials": n_concurrent,
        "orchestrator": {"n_concurrent_trials": n_concurrent},
        "agents": [
            {
                "name": agent_name,
                "model_name": model_name,
                "kwargs": {
                    "api_base": api_base,
                    "metrics_endpoint": "http://node-0:9090/metrics",
                },
            }
        ],
        "environment": {"type": "daytona"},
        "verifier": {},
    }


def _trial_config(
    *,
    agent_name: str = "terminus-2",
    model_name: str = "Qwen/Qwen3-32B",
    api_base: str = "http://node-0:8000/v1",
    metrics_endpoint: str = "http://node-0:9090/metrics",
    timeout_multiplier: float = 1.0,
) -> Dict[str, Any]:
    return {
        "timeout_multiplier": timeout_multiplier,
        "agent": {
            "name": agent_name,
            "model_name": model_name,
            "kwargs": {
                "api_base": api_base,
                "metrics_endpoint": metrics_endpoint,
            },
        },
    }


def _trial_result(
    *,
    exception_type: Optional[str] = None,
    reward: Optional[float] = 1.0,
    finished_at: str = "2026-05-15T12:34:56+00:00",
) -> Dict[str, Any]:
    blob: Dict[str, Any] = {
        "started_at": "2026-05-15T12:00:00+00:00",
        "finished_at": finished_at,
        "verifier_result": (
            {"rewards": {"reward": reward}} if reward is not None else None
        ),
    }
    if exception_type:
        blob["exception_info"] = {
            "exception_type": exception_type,
            "exception_message": "...",
        }
    return blob


def _seed_prior(
    job_dir: Path,
    *,
    top_level: Dict[str, Any],
    trials: Optional[List[Dict[str, Any]]] = None,
    trial_results: Optional[List[Optional[Dict[str, Any]]]] = None,
    job_result: Optional[Dict[str, Any]] = None,
) -> None:
    """Create a job_dir on disk matching the supplied state."""
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "config.json").write_text(json.dumps(top_level, indent=2))
    if job_result is not None:
        (job_dir / "result.json").write_text(json.dumps(job_result, indent=2))
    for idx, trial in enumerate(trials or []):
        trial_dir = job_dir / f"task-{idx}"
        trial_dir.mkdir(parents=True, exist_ok=True)
        (trial_dir / "config.json").write_text(json.dumps(trial, indent=2))
        res = (trial_results or [None] * len(trials or []))[idx]
        if res is not None:
            (trial_dir / "result.json").write_text(json.dumps(res, indent=2))


# -----------------------------------------------------------------------------
# Inspection
# -----------------------------------------------------------------------------


def test_no_prior_dir(tmp_path):
    report = inspect_resume(tmp_path / "nonexistent", _planned_config())
    assert report.state == ResumeState.NO_PRIOR
    assert report.coverage is None
    assert not report.job_config_drift
    assert not report.has_fatal_drift


def test_clean_resume_no_drift(tmp_path):
    job_dir = tmp_path / "job"
    planned = _planned_config()
    _seed_prior(
        job_dir,
        top_level=planned,
        trials=[_trial_config(), _trial_config()],
        trial_results=[_trial_result(reward=1.0), None],
    )
    report = inspect_resume(job_dir, planned)
    assert report.state == ResumeState.CLEAN_RESUME
    assert report.coverage.n_existing == 2
    assert report.coverage.n_with_result == 1
    assert report.coverage.n_without_result == 1
    assert not report.has_fatal_drift


def test_already_complete(tmp_path):
    job_dir = tmp_path / "job"
    planned = _planned_config()
    _seed_prior(
        job_dir,
        top_level=planned,
        trials=[_trial_config()],
        trial_results=[_trial_result(reward=1.0)],
        job_result={
            "id": "abc",
            "started_at": "2026-05-15T12:00:00+00:00",
            "finished_at": "2026-05-15T13:00:00+00:00",
            "n_total_trials": 1,
        },
    )
    report = inspect_resume(job_dir, planned)
    assert report.state == ResumeState.ALREADY_COMPLETE


def test_mutable_drift_n_concurrent(tmp_path):
    job_dir = tmp_path / "job"
    prior = _planned_config(n_concurrent=32)
    _seed_prior(job_dir, top_level=prior, trials=[_trial_config()])

    new_plan = _planned_config(n_concurrent=64)
    report = inspect_resume(job_dir, new_plan)
    assert report.state == ResumeState.MUTABLE_DRIFT
    assert not report.has_fatal_drift
    paths = [tuple(d.path) for d in report.job_config_drift]
    # Both flat n_concurrent_trials and nested orchestrator.n_concurrent_trials
    # show up; both are mutable.
    assert ("n_concurrent_trials",) in paths
    assert ("orchestrator", "n_concurrent_trials") in paths


def test_mutable_drift_api_base_across_trials(tmp_path):
    job_dir = tmp_path / "job"
    prior_top = _planned_config(api_base="http://OLD:8000/v1")
    prior_trials = [
        _trial_config(api_base="http://OLD:8000/v1"),
        _trial_config(api_base="http://OLD:8000/v1"),
        _trial_config(api_base="http://OLD:8000/v1"),
    ]
    _seed_prior(job_dir, top_level=prior_top, trials=prior_trials)

    new_plan = _planned_config(api_base="http://NEW:8000/v1")
    report = inspect_resume(job_dir, new_plan)
    assert report.state == ResumeState.MUTABLE_DRIFT
    assert all(not td.fatal for td in report.trial_drifts)
    # Every trial sees the api_base drift.
    api_base_drift_count = sum(
        1
        for td in report.trial_drifts
        for d in td.drifts
        if tuple(d.path) == ("agent", "kwargs", "api_base")
    )
    assert api_base_drift_count == 3


def test_fatal_drift_model_name_swap(tmp_path):
    job_dir = tmp_path / "job"
    prior_top = _planned_config(model_name="Qwen/Qwen3-32B")
    _seed_prior(
        job_dir,
        top_level=prior_top,
        trials=[_trial_config(model_name="Qwen/Qwen3-32B")],
    )

    new_plan = _planned_config(model_name="Qwen/Qwen3-32B-Instruct")
    report = inspect_resume(job_dir, new_plan)
    assert report.state == ResumeState.FATAL_DRIFT
    assert report.has_fatal_drift


def test_synthetic_vllm_id_rotation_is_mutable(tmp_path):
    job_dir = tmp_path / "job"
    prior_top = _planned_config(model_name="hosted_vllm/1715800123456789")
    prior_trials = [_trial_config(model_name="hosted_vllm/1715800123456789")]
    _seed_prior(job_dir, top_level=prior_top, trials=prior_trials)

    # New launch generated a fresh synthetic ID
    new_plan = _planned_config(model_name="hosted_vllm/1715802991234567")
    report = inspect_resume(job_dir, new_plan)
    assert report.state == ResumeState.MUTABLE_DRIFT
    assert not report.has_fatal_drift
    # Annotation present
    notes = [d.note for d in report.job_config_drift if "rotation" in d.note]
    assert any("rotation" in n for n in notes)


def test_synthetic_vllm_old_to_canonical_new_is_mutable(tmp_path):
    """OLD=hosted_vllm/<id> + NEW=canonical-repo-name is MUTABLE.

    The OLD-side ``hosted_vllm/<digits>`` is a runtime alias generated by
    vLLM-local-serve — it tells us nothing about which model was actually
    served. Whatever we patch the trial config to gets overwritten on
    resume when Harbor re-discovers the served name from the live vLLM
    endpoint. So this drift is structurally a no-op for Harbor, and
    treating it as fatal blocks legitimate resumes of vLLM-local-serve
    runs whose planned configs reference the canonical HF repo.
    """
    job_dir = tmp_path / "job"
    prior_top = _planned_config(model_name="hosted_vllm/1715800123456789")
    _seed_prior(
        job_dir,
        top_level=prior_top,
        trials=[_trial_config(model_name="hosted_vllm/1715800123456789")],
    )

    new_plan = _planned_config(model_name="Qwen/Qwen3-32B-Instruct")
    report = inspect_resume(job_dir, new_plan)
    assert report.state == ResumeState.MUTABLE_DRIFT


def test_canonical_old_to_synthetic_new_is_mutable(tmp_path):
    """OLD=canonical-repo-name + NEW=hosted_vllm/<id> is MUTABLE (symmetric).

    Production failure mode that the directionality fix targets: a prior
    ``resume_manager`` mutation rewrote on-disk ``config.json`` with the
    resolved canonical HF name (the planned config at that time carried
    the real name because ``_materialize_planned_config`` hadn't yet
    started applying the synthetic alias). The next launch's YAML
    contains a freshly-generated ``hosted_vllm/<id>`` — Harbor's strict
    equality check then fails with ``FileExistsError``. The predicate
    must accept either-side-synthetic so the resume_manager classifies
    the drift as mutable and rewrites the on-disk JSON to match the
    new YAML.
    """
    job_dir = tmp_path / "job"
    prior_top = _planned_config(model_name="cyankiwi/MiniMax-M2.7-AWQ-4bit")
    _seed_prior(
        job_dir,
        top_level=prior_top,
        trials=[_trial_config(model_name="cyankiwi/MiniMax-M2.7-AWQ-4bit")],
    )

    new_plan = _planned_config(model_name="hosted_vllm/2855472115409990")
    report = inspect_resume(job_dir, new_plan)
    assert report.state == ResumeState.MUTABLE_DRIFT


def test_real_to_real_model_swap_stays_fatal(tmp_path):
    """OLD=real-repo + NEW=different-real-repo is still FATAL.

    The synthetic-vLLM-ID predicate only fires when the OLD side
    matches ``hosted_vllm/<digits>``. Two distinct real HF repo names
    on either side is a genuine model swap — those trials were
    generated by a different model and mixing them with new trials
    produces a corrupted dataset.
    """
    job_dir = tmp_path / "job"
    prior_top = _planned_config(model_name="meta-llama/Llama-3-8B")
    _seed_prior(
        job_dir,
        top_level=prior_top,
        trials=[_trial_config(model_name="meta-llama/Llama-3-8B")],
    )

    new_plan = _planned_config(model_name="Qwen/Qwen3-32B-Instruct")
    report = inspect_resume(job_dir, new_plan)
    assert report.state == ResumeState.FATAL_DRIFT


def test_orphan_trial_with_unrecognized_agent(tmp_path):
    job_dir = tmp_path / "job"
    prior = _planned_config(agent_name="terminus-2")
    # Seed with a trial whose agent.name is "old-agent" — not in the plan.
    orphan_trial = _trial_config(agent_name="old-agent")
    _seed_prior(job_dir, top_level=prior, trials=[orphan_trial, _trial_config()])

    new_plan = _planned_config(agent_name="terminus-2")
    report = inspect_resume(job_dir, new_plan)
    orphans = [td for td in report.trial_drifts if td.orphan]
    assert len(orphans) == 1
    assert report.state == ResumeState.FATAL_DRIFT
    assert report.coverage.n_orphans == 1


def test_corrupt_top_level_config(tmp_path):
    job_dir = tmp_path / "job"
    job_dir.mkdir(parents=True)
    (job_dir / "config.json").write_text("{not valid JSON")
    report = inspect_resume(job_dir, _planned_config())
    assert report.state == ResumeState.CORRUPT


def test_corrupt_trial_result_quarantine_via_plan(tmp_path):
    job_dir = tmp_path / "job"
    planned = _planned_config()
    # Same config; only a trial result is corrupt.
    _seed_prior(job_dir, top_level=planned, trials=[_trial_config()])
    corrupt_path = job_dir / "task-0" / "result.json"
    corrupt_path.write_text("{not valid")

    report = inspect_resume(job_dir, planned)
    assert corrupt_path in report.corrupt_trial_dirs

    plan = plan_mutation(report, planned)
    # No top-level drift here so plan exists trivially.
    assert plan is not None
    assert corrupt_path in plan.trial_results_to_quarantine

    apply_mutation(plan, job_dir=job_dir)
    assert not corrupt_path.exists()
    assert (job_dir / "task-0" / "result.json.corrupt").exists()


# -----------------------------------------------------------------------------
# Planning + applying
# -----------------------------------------------------------------------------


def test_plan_mutation_returns_none_on_fatal(tmp_path):
    job_dir = tmp_path / "job"
    _seed_prior(
        job_dir,
        top_level=_planned_config(model_name="A"),
        trials=[_trial_config(model_name="A")],
    )
    new_plan = _planned_config(model_name="B")
    report = inspect_resume(job_dir, new_plan)
    assert plan_mutation(report, new_plan) is None


def test_apply_mutation_rewrites_trial_configs(tmp_path):
    job_dir = tmp_path / "job"
    prior_top = _planned_config(api_base="http://OLD:8000/v1")
    _seed_prior(
        job_dir,
        top_level=prior_top,
        trials=[
            _trial_config(api_base="http://OLD:8000/v1"),
            _trial_config(api_base="http://OLD:8000/v1"),
        ],
    )

    new_plan = _planned_config(api_base="http://NEW:8000/v1")
    report = inspect_resume(job_dir, new_plan)
    plan = plan_mutation(report, new_plan)
    assert plan is not None
    apply_mutation(plan, job_dir=job_dir)

    # All trial configs now point at NEW.
    for trial_dir in [job_dir / "task-0", job_dir / "task-1"]:
        cfg = json.loads((trial_dir / "config.json").read_text())
        assert cfg["agent"]["kwargs"]["api_base"] == "http://NEW:8000/v1"

    # Top-level config is also rewritten to the plan.
    new_top = json.loads((job_dir / "config.json").read_text())
    assert new_top["agents"][0]["kwargs"]["api_base"] == "http://NEW:8000/v1"


def test_apply_mutation_is_idempotent(tmp_path):
    job_dir = tmp_path / "job"
    prior_top = _planned_config(api_base="http://OLD:8000/v1")
    _seed_prior(
        job_dir,
        top_level=prior_top,
        trials=[_trial_config(api_base="http://OLD:8000/v1")],
    )

    new_plan = _planned_config(api_base="http://NEW:8000/v1")
    report = inspect_resume(job_dir, new_plan)
    plan = plan_mutation(report, new_plan)
    apply_mutation(plan, job_dir=job_dir)

    # Second inspect should classify as clean resume.
    report2 = inspect_resume(job_dir, new_plan)
    assert report2.state == ResumeState.CLEAN_RESUME

    # Re-apply is a no-op (same content written).
    plan2 = plan_mutation(report2, new_plan)
    # No drift → plan is still constructible but has no rewrites.
    if plan2 is not None:
        assert plan2.trial_config_rewrites == []


def test_apply_mutation_wipes_orphans(tmp_path):
    job_dir = tmp_path / "job"
    prior = _planned_config()
    # Orphan trial (agent name not in plan) + valid trial with drift.
    _seed_prior(
        job_dir,
        top_level=prior,
        trials=[
            _trial_config(agent_name="OLD-AGENT"),
            _trial_config(api_base="http://OLD:8000/v1"),
        ],
    )

    # Plan changes api_base but keeps agent terminus-2; the OLD-AGENT trial
    # is fatal-orphan → no mutation possible.
    new_plan = _planned_config(api_base="http://NEW:8000/v1")
    report = inspect_resume(job_dir, new_plan)
    assert report.has_fatal_drift  # orphan
    assert plan_mutation(report, new_plan) is None


# -----------------------------------------------------------------------------
# resolve_resume_policy matrix
# -----------------------------------------------------------------------------


def test_matrix_no_prior_returns_no_engagement(tmp_path):
    result = resolve_resume_policy(
        tmp_path / "missing",
        _planned_config(),
        force_mutate=False,
        allow_overwrite=False,
    )
    assert result.action == ResumeAction.NO_ENGAGEMENT


def test_matrix_clean_resume(tmp_path):
    job_dir = tmp_path / "job"
    planned = _planned_config()
    _seed_prior(job_dir, top_level=planned, trials=[_trial_config()])
    result = resolve_resume_policy(
        job_dir,
        planned,
        force_mutate=False,
        allow_overwrite=False,
    )
    assert result.action == ResumeAction.CLEAN_RESUME


def test_matrix_default_bails_on_mutable(tmp_path):
    job_dir = tmp_path / "job"
    _seed_prior(
        job_dir, top_level=_planned_config(n_concurrent=32), trials=[_trial_config()]
    )
    with pytest.raises(ResumeBail) as excinfo:
        resolve_resume_policy(
            job_dir,
            _planned_config(n_concurrent=64),
            force_mutate=False,
            allow_overwrite=False,
        )
    assert "--force_mutate" in excinfo.value.message
    assert "--allow_overwrite" in excinfo.value.message


def test_matrix_force_mutate_alone_patches(tmp_path):
    job_dir = tmp_path / "job"
    _seed_prior(
        job_dir,
        top_level=_planned_config(api_base="http://OLD:8000/v1"),
        trials=[_trial_config(api_base="http://OLD:8000/v1")],
    )
    result = resolve_resume_policy(
        job_dir,
        _planned_config(api_base="http://NEW:8000/v1"),
        force_mutate=True,
        allow_overwrite=False,
    )
    assert result.action == ResumeAction.MUTATE_AND_RESUME
    cfg = json.loads((job_dir / "task-0" / "config.json").read_text())
    assert cfg["agent"]["kwargs"]["api_base"] == "http://NEW:8000/v1"


def test_matrix_force_mutate_alone_bails_on_fatal(tmp_path):
    job_dir = tmp_path / "job"
    _seed_prior(
        job_dir,
        top_level=_planned_config(model_name="A"),
        trials=[_trial_config(model_name="A")],
    )
    with pytest.raises(ResumeBail):
        resolve_resume_policy(
            job_dir,
            _planned_config(model_name="B"),
            force_mutate=True,
            allow_overwrite=False,
        )


def test_matrix_allow_overwrite_alone_wipes(tmp_path):
    job_dir = tmp_path / "job"
    _seed_prior(
        job_dir,
        top_level=_planned_config(api_base="http://OLD:8000/v1"),
        trials=[_trial_config(api_base="http://OLD:8000/v1")],
    )
    result = resolve_resume_policy(
        job_dir,
        _planned_config(api_base="http://NEW:8000/v1"),
        force_mutate=False,
        allow_overwrite=True,
    )
    assert result.action == ResumeAction.WIPE_AND_FRESH
    # Trial dirs are gone.
    assert not (job_dir / "task-0").exists()
    # Top-level dir kept (it's where the next launch lands).
    assert job_dir.exists()


def test_matrix_force_mutate_plus_overwrite_falls_back_to_wipe(tmp_path):
    """Fatal drift + both flags → wipe."""
    job_dir = tmp_path / "job"
    _seed_prior(
        job_dir,
        top_level=_planned_config(model_name="A"),
        trials=[_trial_config(model_name="A")],
    )
    result = resolve_resume_policy(
        job_dir,
        _planned_config(model_name="B"),
        force_mutate=True,
        allow_overwrite=True,
    )
    assert result.action == ResumeAction.WIPE_AND_FRESH


def test_matrix_already_complete_default_bails(tmp_path):
    job_dir = tmp_path / "job"
    planned = _planned_config()
    _seed_prior(
        job_dir,
        top_level=planned,
        trials=[_trial_config()],
        trial_results=[_trial_result(reward=1.0)],
        job_result={"started_at": "x", "finished_at": "y", "n_total_trials": 1},
    )
    with pytest.raises(ResumeBail) as excinfo:
        resolve_resume_policy(
            job_dir, planned, force_mutate=False, allow_overwrite=False
        )
    assert "ALREADY COMPLETE" in excinfo.value.message


def test_matrix_already_complete_with_overwrite_wipes(tmp_path):
    job_dir = tmp_path / "job"
    planned = _planned_config()
    _seed_prior(
        job_dir,
        top_level=planned,
        trials=[_trial_config()],
        trial_results=[_trial_result(reward=1.0)],
        job_result={"started_at": "x", "finished_at": "y", "n_total_trials": 1},
    )
    result = resolve_resume_policy(
        job_dir, planned, force_mutate=False, allow_overwrite=True
    )
    assert result.action == ResumeAction.WIPE_AND_FRESH


# -----------------------------------------------------------------------------
# Bail-message format
# -----------------------------------------------------------------------------


def test_bail_message_includes_diff_and_flags(tmp_path):
    job_dir = tmp_path / "job"
    _seed_prior(
        job_dir,
        top_level=_planned_config(n_concurrent=32, api_base="http://OLD:8000/v1"),
        trials=[_trial_config(api_base="http://OLD:8000/v1")],
    )
    new_plan = _planned_config(n_concurrent=64, api_base="http://NEW:8000/v1")
    report = inspect_resume(job_dir, new_plan)
    msg = render_bail_message(report, force_mutate=False, allow_overwrite=False)
    assert "n_concurrent_trials" in msg
    assert "api_base" in msg
    assert "--force_mutate" in msg
    assert "--allow_overwrite" in msg
    assert "--experiments_dir" in msg


def test_bail_message_marks_fatal_when_present(tmp_path):
    job_dir = tmp_path / "job"
    _seed_prior(
        job_dir,
        top_level=_planned_config(model_name="A"),
        trials=[_trial_config(model_name="A")],
    )
    report = inspect_resume(job_dir, _planned_config(model_name="B"))
    msg = render_bail_message(report, force_mutate=False, allow_overwrite=False)
    assert "fatal" in msg.lower()
    assert "NOT applicable" in msg  # mutate flag is annotated as not applicable


# -----------------------------------------------------------------------------
# Top-level seam (resolve_resume_policy_for_launch) + job-type gate
# -----------------------------------------------------------------------------


def test_job_type_gate_skips_sft(tmp_path):
    """SFT job_type should not engage the resume manager even when prior dir exists."""
    job_dir = tmp_path / "experiments" / "test-job" / "trace_jobs" / "test-job_traces"
    _seed_prior(job_dir, top_level=_planned_config(), trials=[_trial_config()])
    exp_args = {
        "job_type": "sft",
        "experiments_dir": str(tmp_path / "experiments" / "test-job"),
        "trace_harbor_config": "/nonexistent/path.yaml",  # would normally fail but gate skips
    }
    result = resolve_resume_policy_for_launch(exp_args, job_name="test-job")
    assert result is None


def test_job_type_gate_skips_rl(tmp_path):
    result = resolve_resume_policy_for_launch({"job_type": "rl"}, job_name="x")
    assert result is None


def test_job_type_gate_skips_consolidate(tmp_path):
    result = resolve_resume_policy_for_launch({"job_type": "consolidate"}, job_name="x")
    assert result is None


def test_for_launch_declines_when_no_prior_dir(tmp_path):
    exp_args = {
        "job_type": "eval",
        "experiments_dir": str(tmp_path / "nonexistent"),
        "trace_harbor_config": str(tmp_path / "fake.yaml"),
    }
    result = resolve_resume_policy_for_launch(exp_args, job_name="test-job")
    assert result is None


def test_for_launch_declines_when_planned_config_unavailable(tmp_path):
    """No harbor_config → can't materialize plan → manager declines."""
    job_dir = tmp_path / "experiments" / "test-job" / "trace_jobs" / "test-job_traces"
    _seed_prior(job_dir, top_level=_planned_config(), trials=[_trial_config()])
    exp_args = {
        "job_type": "eval",
        "experiments_dir": str(tmp_path / "experiments" / "test-job"),
        # no trace_harbor_config
    }
    result = resolve_resume_policy_for_launch(exp_args, job_name="test-job")
    assert result is None


def test_resolve_prior_job_dir_defaults_when_experiments_dir_missing():
    """Without --experiments_dir, prior dir defaults to experiments/<job>/trace_jobs/<job>_traces."""
    from hpc.launch_utils import PROJECT_ROOT

    prior = rm._resolve_prior_job_dir({"job_type": "datagen"}, "demo")
    assert prior is not None
    assert prior.name == "demo_traces"
    assert prior.parent.name == "trace_jobs"
    assert prior.parent.parent.name == "demo"
    assert prior.parent.parent.parent == (PROJECT_ROOT / "experiments").resolve()


def test_resolve_prior_job_dir_honors_explicit_experiments_dir(tmp_path):
    """Explicit --experiments_dir is used verbatim under a trace_jobs/<job>_traces leaf."""
    explicit = tmp_path / "custom_exp"
    prior = rm._resolve_prior_job_dir({"experiments_dir": str(explicit)}, "myjob")
    assert prior == explicit / "trace_jobs" / "myjob_traces"
