import json
from pathlib import Path

from scripts.harbor.analyze_sft_export_gaps import analyze_dataset


def write_result(trial_dir: Path, trial_name: str, reward: float | None) -> None:
    trial_dir.mkdir(parents=True)
    payload = {
        "task_name": f"task-{trial_name}",
        "trial_name": trial_name,
        "config": {
            "agent": {"name": "terminus-2", "model_name": "test-model"},
            "job_name": "test-run",
        },
        "agent_info": {
            "name": "terminus-2",
            "model_info": {"name": "test-model", "provider": "vllm"},
        },
        "verifier_result": (
            {"rewards": {"reward": reward}} if reward is not None else None
        ),
    }
    (trial_dir / "result.json").write_text(json.dumps(payload))


def write_trajectory(trial_dir: Path, steps: list[dict]) -> None:
    agent_dir = trial_dir / "agent"
    agent_dir.mkdir()
    (agent_dir / "trajectory.json").write_text(json.dumps({"steps": steps}))


def test_analysis_accounts_for_both_export_boundaries(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "result.json").write_text(
        json.dumps(
            {
                "stats": {
                    "evals": {
                        "terminus-2/test-model": {
                            "reward_stats": {
                                "reward": {
                                    "0.0": [
                                        "numeric-no-trajectory",
                                        "invalid-trajectory",
                                        "valid-trace",
                                        "aggregate-only",
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        )
    )

    write_result(run_dir / "numeric-no-trajectory", "numeric-no-trajectory", 0.0)

    invalid = run_dir / "invalid-trajectory"
    write_result(invalid, "invalid-trajectory", 0.0)
    (invalid / "agent").mkdir()
    (invalid / "agent" / "trajectory.json").write_text("not json")

    no_agent_steps = run_dir / "no-agent-steps"
    write_result(no_agent_steps, "no-agent-steps", None)
    write_trajectory(no_agent_steps, [{"source": "user", "message": "hello"}])

    valid = run_dir / "valid-trace"
    write_result(valid, "valid-trace", 1.0)
    write_trajectory(
        valid,
        [
            {"source": "user", "message": "solve it"},
            {"source": "agent", "message": "done"},
        ],
    )

    report = analyze_dataset([run_dir])
    summary = report["summary"]

    assert summary["numeric_result_identities"] == 4
    assert summary["aggregate_numeric_result_identities"] == 4
    assert summary["direct_numeric_result_identities"] == 3
    assert summary["numeric_identities_with_trajectory"] == 2
    assert summary["trajectory_files"] == 3
    assert summary["trajectory_files_with_sft_rows"] == 1
    assert summary["collected_conversation_rows"] == 1
    assert summary["sft_ready_rows"] == 1
    assert summary["trajectory_file_to_sft_row_delta"] == 2
    assert summary["numeric_to_trajectory_gap"] == 2
    assert summary["trajectory_to_sft_gap"] == 2
    assert summary["numeric_to_trajectory_reasons"] == {
        "agent_directory_missing": 1,
        "no_trial_directory": 1,
    }
    assert summary["trajectory_to_sft_reasons"] == {
        "invalid_trajectory_json": 1,
        "no_agent_steps": 1,
    }

    by_name = {record["trial_name"]: record for record in report["trials"]}
    assert by_name["aggregate-only"]["numeric_sources"] == ["aggregate"]
    assert by_name["valid-trace"]["numeric_sources"] == ["aggregate", "trial"]
    assert by_name["valid-trace"]["sft_ready_rows"] == 1


def test_analysis_reports_duplicate_aggregate_references_without_inflating_trials(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "result.json").write_text(
        json.dumps(
            {
                "stats": {
                    "evals": {
                        "first": {"reward_stats": {"reward": {"1": ["same-trial"]}}},
                        "second": {"reward_stats": {"other": {"0": ["same-trial"]}}},
                    }
                }
            }
        )
    )

    report = analyze_dataset([run_dir])

    assert report["summary"]["numeric_result_identities"] == 1
    assert report["summary"]["aggregate_numeric_references"] == 2
    assert report["summary"]["duplicate_aggregate_numeric_references"] == 1
