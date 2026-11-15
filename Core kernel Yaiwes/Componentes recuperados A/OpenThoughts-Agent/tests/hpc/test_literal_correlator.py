"""Unit tests for the opencode literal-token correlator.

Covers ``scripts/harbor/literal_correlator.py``:
  * parsing RecordProxy JSONL into usable records (filters junk),
  * per-trial chain reconstruction by exact message-prefix extension,
  * duplicate-task ambiguity detection (skip, never mis-join),
  * count-sequence binding (verify-or-skip) + window tie-break,
  * per-step verify-or-skip injection,
  * end-to-end trajectory enrichment against on-disk trial dirs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.harbor.literal_correlator import (  # noqa: E402
    Chain,
    LiteralRecord,
    _strip_literal_metrics,
    bind_chain,
    enrich_trajectories_with_literals,
    inject_literals,
    parse_literal_records,
    reconstruct_chains,
    trajectory_count_sequence,
)

SYS = {"role": "system", "content": "SYS"}


def _msg(role: str, content: str) -> dict:
    return {"role": role, "content": content}


def _record_line(messages, pids, cids, logprobs=None, ts=0.0, status=200) -> str:
    return json.dumps(
        {
            "timestamp": ts,
            "status_code": status,
            "request": {"messages": messages},
            "literal": {
                "prompt_token_ids": pids,
                "completion_token_ids": cids,
                "logprobs": logprobs,
                "response_id": "chatcmpl-x",
                "model": "m",
            },
        }
    )


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
def test_parse_filters_non200_and_missing_literal():
    lines = [
        _record_line([SYS, _msg("user", "A")], [1, 2, 3], [9, 9]),  # keep
        _record_line([SYS, _msg("user", "B")], [1], [9], status=500),  # drop: non-200
        json.dumps(
            {"status_code": 200, "request": {"messages": []}}
        ),  # drop: no literal
        json.dumps(
            {"status_code": 200, "literal": {"completion_token_ids": [1]}}
        ),  # drop: no messages
        "not json",  # drop
    ]
    recs = parse_literal_records(lines)
    assert len(recs) == 1
    assert recs[0].counts == (3, 2)


# --------------------------------------------------------------------------- #
# Chain reconstruction
# --------------------------------------------------------------------------- #
def _trial_records(task: str, steps: list[tuple[list[int], list[int]]], base_ts: float):
    """Build a growing-history chain of records for one trial."""
    recs = []
    messages = [SYS, _msg("user", task)]
    for i, (pids, cids) in enumerate(steps):
        recs.append(
            LiteralRecord(
                timestamp=base_ts + i,
                messages=[dict(m) for m in messages],
                prompt_token_ids=pids,
                completion_token_ids=cids,
                logprobs=[-0.1] * len(cids),
            )
        )
        # opencode replays full history: append this turn's assistant + observation
        messages = messages + [
            _msg("assistant", f"{task}-a{i}"),
            _msg("user", f"{task}-o{i}"),
        ]
    return recs


def test_reconstruct_distinct_trials_into_clean_ordered_chains():
    a = _trial_records(
        "TASK_A", [([1, 2, 3, 4, 5], [7, 7]), (list(range(9)), [7, 7, 7])], base_ts=100
    )
    b = _trial_records("TASK_B", [([1, 2, 3, 4, 5, 6], [8, 8, 8, 8])], base_ts=200)
    # Interleave arrival order; reconstruction must not depend on it.
    chains = reconstruct_chains([a[1], b[0], a[0]])
    by_len = {len(c.records): c for c in chains}
    assert set(by_len) == {1, 2}
    assert not any(c.ambiguous for c in chains)
    assert by_len[2].count_sequence == [(5, 2), (9, 3)]
    assert by_len[1].count_sequence == [(6, 4)]
    # order within the 2-step chain is oldest-first
    assert by_len[2].records[0].timestamp < by_len[2].records[1].timestamp


def test_reconstruct_duplicate_task_marks_continuations_ambiguous():
    # Two trials with the IDENTICAL instruction seed -> the shared [SYS, TASK]
    # prefix makes continuations un-attributable; they must be flagged, not guessed.
    steps = [([1, 2, 3, 4, 5], [7, 7]), (list(range(9)), [7, 7, 7])]
    a = _trial_records("TASK_DUP", steps, base_ts=100)
    c = _trial_records("TASK_DUP", steps, base_ts=200)
    chains = reconstruct_chains([a[0], c[0], a[1], c[1]])
    # No clean 2-step chain survives -> binding a 2-step trajectory returns None.
    assert bind_chain(chains, [(5, 2), (9, 3)]) is None


# --------------------------------------------------------------------------- #
# Binding (verify-or-skip)
# --------------------------------------------------------------------------- #
def test_bind_exact_match_unique():
    a = _trial_records(
        "TASK_A", [([1, 2, 3, 4, 5], [7, 7]), (list(range(9)), [7, 7, 7])], base_ts=100
    )
    b = _trial_records("TASK_B", [([1, 2, 3, 4, 5, 6], [8, 8, 8, 8])], base_ts=200)
    chains = reconstruct_chains(a + b)
    bound = bind_chain(chains, [(5, 2), (9, 3)])
    assert bound is not None
    assert bound.count_sequence == [(5, 2), (9, 3)]


def test_bind_no_match_returns_none():
    a = _trial_records("TASK_A", [([1, 2, 3, 4, 5], [7, 7])], base_ts=100)
    chains = reconstruct_chains(a)
    # completion count differs -> no bind (verify-or-skip)
    assert bind_chain(chains, [(5, 99)]) is None
    # a -1 (missing count) never binds
    assert bind_chain(chains, [(5, -1)]) is None


def test_bind_tie_broken_by_window():
    # Two DISTINCT trials that happen to share the same count sequence: ambiguous by
    # counts alone, disambiguated by the agent_execution window.
    a = _trial_records("TASK_A", [([1, 2, 3], [7, 7])], base_ts=100)
    b = _trial_records("TASK_B", [([1, 2, 3], [7, 7])], base_ts=5000)
    chains = reconstruct_chains(a + b)
    assert bind_chain(chains, [(3, 2)]) is None  # ambiguous, no window
    bound = bind_chain(chains, [(3, 2)], window=(90.0, 110.0))
    assert bound is not None and bound.records[0].timestamp == 100


# --------------------------------------------------------------------------- #
# Injection (per-step verify-or-skip)
# --------------------------------------------------------------------------- #
def test_inject_populates_matching_steps():
    trajectory = {
        "steps": [
            {
                "source": "agent",
                "metrics": {"prompt_tokens": 5, "completion_tokens": 2},
            },
            {
                "source": "agent",
                "metrics": {"prompt_tokens": 9, "completion_tokens": 3},
            },
        ]
    }
    chain = Chain(
        records=[
            LiteralRecord(0.0, [], [1, 2, 3, 4, 5], [7, 7], [-0.1, -0.2]),
            LiteralRecord(1.0, [], list(range(9)), [7, 7, 7], [-0.1, -0.2, -0.3]),
        ]
    )
    n = inject_literals(trajectory, chain)
    assert n == 2
    m0 = trajectory["steps"][0]["metrics"]
    assert m0["prompt_token_ids"] == [1, 2, 3, 4, 5]
    assert m0["completion_token_ids"] == [7, 7]
    assert m0["logprobs"] == [-0.1, -0.2]


def test_inject_skips_step_on_count_mismatch():
    # Defensive: a step whose completion count disagrees with the record is left
    # untouched (never poison training tokens), even if the chain was bound.
    trajectory = {
        "steps": [
            {
                "source": "agent",
                "metrics": {"prompt_tokens": 5, "completion_tokens": 999},
            }
        ]
    }
    chain = Chain(records=[LiteralRecord(0.0, [], [1, 2, 3, 4, 5], [7, 7], None)])
    assert inject_literals(trajectory, chain) == 0
    assert "completion_token_ids" not in trajectory["steps"][0]["metrics"]


def test_trajectory_count_sequence_skips_copied_and_nonagent():
    trajectory = {
        "steps": [
            {"source": "system", "message": "task"},
            {
                "source": "agent",
                "is_copied_context": True,
                "metrics": {"prompt_tokens": 1, "completion_tokens": 1},
            },
            {
                "source": "agent",
                "metrics": {"prompt_tokens": 5, "completion_tokens": 2},
            },
        ]
    }
    assert trajectory_count_sequence(trajectory) == [(5, 2)]


# --------------------------------------------------------------------------- #
# End-to-end enrichment against on-disk trial dirs
# --------------------------------------------------------------------------- #
def _write_trial(root: Path, name: str, count_seq, window=None) -> Path:
    trial = root / name
    (trial / "agent").mkdir(parents=True)
    steps = [
        {
            "source": "agent",
            "message": f"turn-{i}",
            "metrics": {"prompt_tokens": p, "completion_tokens": c},
        }
        for i, (p, c) in enumerate(count_seq)
    ]
    (trial / "agent" / "trajectory.json").write_text(json.dumps({"steps": steps}))
    result = {"trial_name": name}
    if window:
        result["agent_execution"] = {"started_at": window[0], "finished_at": window[1]}
    (trial / "result.json").write_text(json.dumps(result))
    return trial


def test_enrich_end_to_end_joins_correct_trial(tmp_path):
    job = tmp_path / "job"
    job.mkdir()
    trial_a = _write_trial(job, "trial-A", [(5, 2), (9, 3)])
    _write_trial(job, "trial-B", [(6, 4)])

    a = _trial_records(
        "TASK_A",
        [([1, 2, 3, 4, 5], [70, 71]), (list(range(9)), [72, 73, 74])],
        base_ts=100,
    )
    b = _trial_records("TASK_B", [([1, 2, 3, 4, 5, 6], [80, 81, 82, 83])], base_ts=200)
    log = tmp_path / "literal.jsonl"
    log.write_text(
        "\n".join(
            _record_line(
                r.messages,
                r.prompt_token_ids,
                r.completion_token_ids,
                r.logprobs,
                r.timestamp,
            )
            for r in [a[1], b[0], a[0]]
        )
    )

    def _iter(root):
        return [p for p in Path(root).iterdir() if (p / "agent").exists()]

    stats = enrich_trajectories_with_literals(str(job), str(log), iter_trial_dirs=_iter)
    assert stats.trials == 2
    assert stats.trials_enriched == 2
    assert stats.steps_enriched == 3

    traj_a = json.loads((trial_a / "agent" / "trajectory.json").read_text())
    assert traj_a["steps"][0]["metrics"]["completion_token_ids"] == [70, 71]
    assert traj_a["steps"][1]["metrics"]["prompt_token_ids"] == list(range(9))
    assert traj_a["steps"][1]["metrics"]["logprobs"] == [-0.1, -0.1, -0.1]


def test_enrich_skips_ambiguous_duplicate_tasks(tmp_path):
    # Two trials, identical instruction + identical counts -> unbindable -> omitted
    # (columns absent), never cross-contaminated.
    job = tmp_path / "job"
    job.mkdir()
    trial_a = _write_trial(job, "trial-A", [(5, 2), (9, 3)])
    trial_c = _write_trial(job, "trial-C", [(5, 2), (9, 3)])

    steps = [([1, 2, 3, 4, 5], [70, 71]), (list(range(9)), [72, 73, 74])]
    a = _trial_records("TASK_DUP", steps, base_ts=100)
    c = _trial_records("TASK_DUP", steps, base_ts=200)
    log = tmp_path / "literal.jsonl"
    log.write_text(
        "\n".join(
            _record_line(
                r.messages,
                r.prompt_token_ids,
                r.completion_token_ids,
                r.logprobs,
                r.timestamp,
            )
            for r in [a[0], c[0], a[1], c[1]]
        )
    )

    def _iter(root):
        return [p for p in Path(root).iterdir() if (p / "agent").exists()]

    stats = enrich_trajectories_with_literals(str(job), str(log), iter_trial_dirs=_iter)
    assert stats.trials_enriched == 0
    for trial in (trial_a, trial_c):
        traj = json.loads((trial / "agent" / "trajectory.json").read_text())
        assert "completion_token_ids" not in traj["steps"][0]["metrics"]


# --------------------------------------------------------------------------- #
# Stage 1 — strip stale trajectory token_ids (correlator is the sole authority)
# --------------------------------------------------------------------------- #
def _write_trial_with_bogus_ids(root: Path, name: str, count_seq) -> Path:
    """A trial whose steps carry BOGUS prompt/completion token_ids in metrics."""
    trial = root / name
    (trial / "agent").mkdir(parents=True)
    steps = [
        {
            "source": "agent",
            "message": f"turn-{i}",
            "metrics": {
                "prompt_tokens": p,
                "completion_tokens": c,
                "prompt_token_ids": [999] * p,  # BOGUS
                "completion_token_ids": [999] * c,  # BOGUS
                "logprobs": [-9.9] * c,  # BOGUS
            },
        }
        for i, (p, c) in enumerate(count_seq)
    ]
    (trial / "agent" / "trajectory.json").write_text(json.dumps({"steps": steps}))
    (trial / "result.json").write_text(json.dumps({"trial_name": name}))
    return trial


def _iter(root):
    return [p for p in Path(root).iterdir() if (p / "agent").exists()]


def test_strip_literal_metrics_removes_ids_keeps_counts():
    traj = {
        "steps": [
            {
                "source": "agent",
                "metrics": {
                    "prompt_tokens": 5,
                    "completion_tokens": 2,
                    "prompt_token_ids": [9, 9, 9, 9, 9],
                    "completion_token_ids": [9, 9],
                    "logprobs": [-1.0, -1.0],
                },
            },
            {
                "source": "agent",
                "metrics": {"prompt_tokens": 9, "completion_tokens": 3},
            },  # counts only
        ]
    }
    n = _strip_literal_metrics(traj)
    assert n == 1  # only the first step had token_ids
    m0 = traj["steps"][0]["metrics"]
    assert (
        "prompt_token_ids" not in m0
        and "completion_token_ids" not in m0
        and "logprobs" not in m0
    )
    # counts preserved (binding relies on them)
    assert m0["prompt_tokens"] == 5 and m0["completion_tokens"] == 2


def test_enrich_overwrites_bogus_ids_on_bound_trial(tmp_path):
    job = tmp_path / "job"
    job.mkdir()
    trial = _write_trial_with_bogus_ids(job, "trial-A", [(5, 2), (9, 3)])
    a = _trial_records(
        "TASK_A",
        [([1, 2, 3, 4, 5], [70, 71]), (list(range(9)), [72, 73, 74])],
        base_ts=100,
    )
    log = tmp_path / "literal.jsonl"
    log.write_text(
        "\n".join(
            _record_line(
                r.messages,
                r.prompt_token_ids,
                r.completion_token_ids,
                r.logprobs,
                r.timestamp,
            )
            for r in a
        )
    )
    stats = enrich_trajectories_with_literals(str(job), str(log), iter_trial_dirs=_iter)
    assert stats.trials_enriched == 1
    traj = json.loads((trial / "agent" / "trajectory.json").read_text())
    # bogus [999...] replaced by the REAL literal.jsonl values, never left as-is
    assert traj["steps"][0]["metrics"]["completion_token_ids"] == [70, 71]
    assert traj["steps"][1]["metrics"]["prompt_token_ids"] == list(range(9))
    assert 999 not in traj["steps"][0]["metrics"]["prompt_token_ids"]


def test_enrich_strips_bogus_ids_on_unbound_trial(tmp_path):
    # A trajectory with bogus token_ids that DOES NOT bind (no matching literal chain)
    # must have its bogus ids STRIPPED, never leaked into the export.
    job = tmp_path / "job"
    job.mkdir()
    trial = _write_trial_with_bogus_ids(job, "trial-Z", [(5, 2)])
    # literal.jsonl for a DIFFERENT trial with different counts -> no bind for trial-Z
    other = _trial_records("TASK_OTHER", [([1, 2, 3], [7, 7, 7, 7])], base_ts=100)
    log = tmp_path / "literal.jsonl"
    log.write_text(
        "\n".join(
            _record_line(
                r.messages,
                r.prompt_token_ids,
                r.completion_token_ids,
                r.logprobs,
                r.timestamp,
            )
            for r in other
        )
    )
    stats = enrich_trajectories_with_literals(str(job), str(log), iter_trial_dirs=_iter)
    assert stats.trials_enriched == 0
    assert stats.trials_stripped == 1
    m = json.loads((trial / "agent" / "trajectory.json").read_text())["steps"][0][
        "metrics"
    ]
    assert (
        "prompt_token_ids" not in m
        and "completion_token_ids" not in m
        and "logprobs" not in m
    )


def test_enrich_zero_bind_condition_for_fail_loud(tmp_path):
    # The main() fail-loud guard triggers on (trials > 0 and trials_enriched == 0);
    # assert enrich produces exactly that when nothing binds.
    job = tmp_path / "job"
    job.mkdir()
    _write_trial(job, "trial-Z", [(5, 2)])
    other = _trial_records("OTHER", [([1, 2, 3], [7, 7, 7, 7])], base_ts=100)
    log = tmp_path / "literal.jsonl"
    log.write_text(
        "\n".join(
            _record_line(
                r.messages,
                r.prompt_token_ids,
                r.completion_token_ids,
                r.logprobs,
                r.timestamp,
            )
            for r in other
        )
    )
    stats = enrich_trajectories_with_literals(str(job), str(log), iter_trial_dirs=_iter)
    assert stats.trials > 0 and stats.trials_enriched == 0


def test_enrich_binds_across_two_serve_files(tmp_path):
    # Resume-safety: a preempted job has TWO per-serve literal files; a trial's
    # records live entirely in whichever serve ran it. enrich over the UNION must
    # bind BOTH attempts' trials, with no cross-attempt mis-merge (0 ambiguous).
    job = tmp_path / "job"
    job.mkdir()
    trial_a = _write_trial(job, "trial-A", [(5, 2), (9, 3)])  # served by attempt 0
    trial_b = _write_trial(job, "trial-B", [(6, 4)])  # served by attempt 1
    a = _trial_records(
        "TASK_A",
        [([1, 2, 3, 4, 5], [70, 71]), (list(range(9)), [72, 73, 74])],
        base_ts=100,
    )
    b = _trial_records("TASK_B", [([1, 2, 3, 4, 5, 6], [80, 81, 82, 83])], base_ts=9000)
    f0 = tmp_path / "s0_literal.jsonl"
    f1 = tmp_path / "s1_literal.jsonl"
    f0.write_text(
        "\n".join(
            _record_line(
                r.messages,
                r.prompt_token_ids,
                r.completion_token_ids,
                r.logprobs,
                r.timestamp,
            )
            for r in a
        )
    )
    f1.write_text(
        "\n".join(
            _record_line(
                r.messages,
                r.prompt_token_ids,
                r.completion_token_ids,
                r.logprobs,
                r.timestamp,
            )
            for r in b
        )
    )

    stats = enrich_trajectories_with_literals(
        str(job), [str(f0), str(f1)], iter_trial_dirs=_iter
    )
    assert stats.trials == 2
    assert stats.trials_enriched == 2  # BOTH attempts' trials bound
    assert stats.ambiguous_chains == 0  # no cross-attempt mis-merge
    ta = json.loads((trial_a / "agent" / "trajectory.json").read_text())
    tb = json.loads((trial_b / "agent" / "trajectory.json").read_text())
    assert ta["steps"][0]["metrics"]["completion_token_ids"] == [70, 71]
    assert tb["steps"][0]["metrics"]["completion_token_ids"] == [80, 81, 82, 83]
