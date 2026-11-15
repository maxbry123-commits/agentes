"""Tests for the rescue/cleanup FAVOR-literals default (Stage 0/1).

Covers ``scripts/harbor/make_and_upload_trace_dataset.resolve_literal_inclusion``
(auto-detect + favor-when-present + opt-out + force-require) and the Stage-1
correlator guards (strip stale trajectory token_ids; the fail-loud 0-bind
condition).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.harbor.make_and_upload_trace_dataset import resolve_literal_inclusion  # noqa: E402


def _job_with_literal(tmp_path: Path, name: str = "job") -> Path:
    """A job dir with a trial + a sibling logs/<slug>_literal.jsonl (durable layout)."""
    job = tmp_path / name
    (job / "trial-A" / "agent").mkdir(parents=True)
    (job / "trial-A" / "agent" / "trajectory.json").write_text(
        json.dumps({"steps": []})
    )
    (job / "logs").mkdir()
    lit = job / "logs" / f"{name}_literal.jsonl"
    lit.write_text(
        '{"status_code":200,"request":{"messages":[]},"literal":{"completion_token_ids":[1]}}\n'
    )
    return job


def _job_without_literal(tmp_path: Path) -> Path:
    job = tmp_path / "plain"
    (job / "trial-A" / "agent").mkdir(parents=True)
    (job / "trial-A" / "agent" / "trajectory.json").write_text(
        json.dumps({"steps": []})
    )
    return job


# --------------------------------------------------------------------------- #
# Stage 0 — resolve_literal_inclusion
# --------------------------------------------------------------------------- #
def test_parity_no_literal_no_flags_is_text_only(tmp_path):
    # GLOBAL INVARIANT: a job with no literal.jsonl and no flags -> text-only.
    job = _job_without_literal(tmp_path)
    assert resolve_literal_inclusion(
        str(job),
        literal_log=None,
        include_literal_tokens=False,
        no_literal_tokens=False,
    ) == (False, [])


def test_favor_literal_present_default_on(tmp_path):
    # FAVOR: a discoverable sibling logs/*literal.jsonl -> literals ON, no flag needed.
    job = _job_with_literal(tmp_path)
    include, uris = resolve_literal_inclusion(
        str(job),
        literal_log=None,
        include_literal_tokens=False,
        no_literal_tokens=False,
    )
    assert include is True
    assert len(uris) == 1 and uris[0].endswith("job_literal.jsonl")


def test_opt_out_forces_text_only_even_with_literal(tmp_path):
    job = _job_with_literal(tmp_path)
    assert resolve_literal_inclusion(
        str(job), literal_log=None, include_literal_tokens=False, no_literal_tokens=True
    ) == (False, [])


def test_explicit_literal_log_wins(tmp_path):
    job = _job_without_literal(tmp_path)
    explicit = "gs://bucket/x/logs/y_literal.jsonl"
    assert resolve_literal_inclusion(
        str(job),
        literal_log=explicit,
        include_literal_tokens=False,
        no_literal_tokens=False,
    ) == (True, [explicit])


def test_require_missing_fails_loud(tmp_path):
    # --include_literal_tokens (REQUIRE) with no literal.jsonl -> refuse (SystemExit),
    # never silently downgrade to text-only.
    job = _job_without_literal(tmp_path)
    with pytest.raises(SystemExit):
        resolve_literal_inclusion(
            str(job),
            literal_log=None,
            include_literal_tokens=True,
            no_literal_tokens=False,
        )


def test_no_literal_wins_over_require(tmp_path):
    # --no_literal_tokens is an explicit text-only override; it short-circuits before
    # the require check so it never raises.
    job = _job_without_literal(tmp_path)
    assert resolve_literal_inclusion(
        str(job), literal_log=None, include_literal_tokens=True, no_literal_tokens=True
    ) == (False, [])


# --------------------------------------------------------------------------- #
# Stage 2 — post-upload literal-column verify helper
# --------------------------------------------------------------------------- #
def test_count_populated_literal_rows():
    import pyarrow as pa
    from scripts.harbor.make_and_upload_trace_dataset import (
        count_populated_literal_rows,
    )

    # 3 rows: two with non-empty prompt_token_ids, one empty.
    t = pa.table(
        {"prompt_token_ids": [[[1, 2, 3]], [], [[4]]], "conversations": [[], [], []]}
    )
    assert count_populated_literal_rows(t) == 2
    # column absent -> 0 (a text-only dataset), never raises.
    t2 = pa.table({"conversations": [[], []]})
    assert count_populated_literal_rows(t2) == 0


# --------------------------------------------------------------------------- #
# Schema-pin: null-leading chunks must not drop the literal token columns
# --------------------------------------------------------------------------- #
def test_pin_literal_token_columns_recovers_dropped_tokens():
    """The pin rebuilds token columns from source rows even when the Dataset dropped them.

    Reproduces the data-loss failure mode: type inference on a null-leading chunk drops the
    token columns from the built Dataset, but the enriched rows still hold the tokens in the
    source `rows`. The pin must re-materialize them with the correct nested type.
    """
    from datasets import Dataset, Sequence, Value

    from scripts.harbor.make_and_upload_trace_dataset import (
        count_populated_literal_rows,
        _pin_literal_token_columns,
    )

    # source rows: row 0 has no literals (leading null), row 1 does
    rows = [
        {
            "conversations": [{"role": "user", "content": "a"}],
            "prompt_token_ids": [],
            "completion_token_ids": [],
            "logprobs": [],
        },
        {
            "conversations": [{"role": "user", "content": "b"}],
            "prompt_token_ids": [[1, 2]],
            "completion_token_ids": [[10, 11, 12]],
            "logprobs": [[-0.1, -0.2, -0.3]],
        },
    ]
    # Dataset as the lossy pipeline would leave it: token columns absent entirely.
    ds = Dataset.from_list([{"conversations": r["conversations"]} for r in rows])
    assert "completion_token_ids" not in ds.column_names

    pinned = _pin_literal_token_columns(ds, rows)

    # columns restored, with the explicit nested types
    for name in ("prompt_token_ids", "completion_token_ids"):
        assert pinned.features[name] == Sequence(Sequence(Value("int64")))
    assert pinned.features["logprobs"] == Sequence(Sequence(Value("float64")))
    # values preserved from source, aligned by row index
    assert pinned["completion_token_ids"] == [[], [[10, 11, 12]]]
    assert pinned["prompt_token_ids"] == [[], [[1, 2]]]
    # exactly the one enriched row survives as populated (not zero — the bug)
    assert count_populated_literal_rows(pinned.data.table) == 1
    # other columns untouched, order/count preserved
    assert pinned["conversations"] == [r["conversations"] for r in rows]


def test_pin_literal_token_columns_all_empty_chunk_is_present_but_empty():
    """A chunk with zero enriched rows still gets the columns (present-but-empty, stable schema)."""
    from datasets import Dataset

    from scripts.harbor.make_and_upload_trace_dataset import (
        count_populated_literal_rows,
        _pin_literal_token_columns,
    )

    rows = [{"conversations": [{"role": "user", "content": "x"}]} for _ in range(3)]
    ds = Dataset.from_list(rows)
    pinned = _pin_literal_token_columns(ds, rows)
    assert "completion_token_ids" in pinned.column_names
    assert count_populated_literal_rows(pinned.data.table) == 0
    assert pinned["completion_token_ids"] == [[], [], []]


# --------------------------------------------------------------------------- #
# Resume-safety: multiple per-serve literal.jsonl files (preempted job)
# --------------------------------------------------------------------------- #
def _job_with_two_literal_files(tmp_path):
    """A job dir with a logs/ holding TWO per-serve literal files (attempt 0 + 1)."""
    job = tmp_path / "job"
    (job / "logs").mkdir(parents=True)
    (job / "trial-A" / "agent").mkdir(parents=True)
    (job / "trial-A" / "agent" / "trajectory.json").write_text(
        json.dumps({"steps": []})
    )
    (job / "logs" / "tracegen__x__20260704_111941_literal.jsonl").write_text(
        '{"status_code":200,"request":{"messages":[]},"literal":{"completion_token_ids":[1]}}\n'
    )
    (job / "logs" / "tracegen__x__20260704_161605_literal.jsonl").write_text(
        '{"status_code":200,"request":{"messages":[]},"literal":{"completion_token_ids":[2]}}\n'
    )
    return job


def test_discover_literal_logs_returns_all_attempts(tmp_path):
    from scripts.harbor.literal_correlator import (
        discover_literal_logs,
        discover_literal_log,
    )

    job = _job_with_two_literal_files(tmp_path)
    logs = discover_literal_logs(str(job))
    assert len(logs) == 2
    assert any("111941" in u for u in logs) and any("161605" in u for u in logs)
    # back-compat singular still returns the first (sorted)
    assert discover_literal_log(str(job)).endswith("111941_literal.jsonl")


def test_resolve_returns_all_literal_files(tmp_path):
    job = _job_with_two_literal_files(tmp_path)
    include, uris = resolve_literal_inclusion(
        str(job),
        literal_log=None,
        include_literal_tokens=False,
        no_literal_tokens=False,
    )
    assert include is True and len(uris) == 2


def test_load_literal_records_unions_multiple_files(tmp_path):
    from scripts.harbor.literal_correlator import load_literal_records

    a = tmp_path / "a_literal.jsonl"
    b = tmp_path / "b_literal.jsonl"
    a.write_text(
        '{"status_code":200,"request":{"messages":[{"role":"user","content":"A"}]},'
        '"literal":{"prompt_token_ids":[1],"completion_token_ids":[9]}}\n'
    )
    b.write_text(
        '{"status_code":200,"request":{"messages":[{"role":"user","content":"B"}]},'
        '"literal":{"prompt_token_ids":[2],"completion_token_ids":[8]}}\n'
    )
    # one file
    assert len(load_literal_records(str(a))) == 1
    # union of both
    recs = load_literal_records([str(a), str(b)])
    assert len(recs) == 2
    assert {r.completion_token_ids[0] for r in recs} == {9, 8}


# --------------------------------------------------------------------------- #
# Tokenizer provenance stamp (self-service decodability of literal columns)
# --------------------------------------------------------------------------- #
def test_read_served_model_name_from_literals_first_record(tmp_path):
    from scripts.harbor.make_and_upload_trace_dataset import (
        read_served_model_name_from_literals,
    )

    lit = tmp_path / "j_literal.jsonl"
    lit.write_text(
        '{"status_code":200,"request":{"messages":[]},"literal":{"model":"served-slug-abc","completion_token_ids":[1]}}\n'
        '{"status_code":200,"request":{"messages":[]},"literal":{"model":"other","completion_token_ids":[2]}}\n'
    )
    assert read_served_model_name_from_literals([str(lit)]) == "served-slug-abc"


def test_read_served_model_name_absent_returns_none(tmp_path):
    from scripts.harbor.make_and_upload_trace_dataset import (
        read_served_model_name_from_literals,
    )

    lit = tmp_path / "j_literal.jsonl"
    lit.write_text(
        '{"status_code":200,"request":{"messages":[]},"literal":{"completion_token_ids":[1]}}\n'
    )
    assert read_served_model_name_from_literals([str(lit)]) is None
    # unreadable file -> None, never raises
    assert (
        read_served_model_name_from_literals([str(tmp_path / "missing.jsonl")]) is None
    )


def test_build_tokenizer_provenance_carries_served_model():
    from scripts.harbor.make_and_upload_trace_dataset import build_tokenizer_provenance

    prov = build_tokenizer_provenance(
        served_model="Qwen/Qwen3.5-122B-A10B-FP8",
        served_model_name_observed="served-slug",
    )
    assert prov["served_model"] == "Qwen/Qwen3.5-122B-A10B-FP8"
    assert prov["served_model_name_observed"] == "served-slug"
    assert prov["literal_columns"] == [
        "prompt_token_ids",
        "completion_token_ids",
        "logprobs",
    ]
    assert prov["schema"] == "tokenizer_provenance/v1"


def test_write_tokenizer_provenance_stamps_json_and_readme():
    from scripts.harbor.make_and_upload_trace_dataset import (
        PROVENANCE_FILENAME,
        build_tokenizer_provenance,
        write_tokenizer_provenance,
    )

    class _FakeApi:
        def __init__(self):
            self.uploads = {}

        def upload_file(
            self, *, path_or_fileobj, path_in_repo, repo_id, repo_type, commit_message
        ):
            self.uploads[path_in_repo] = bytes(path_or_fileobj)

    api = _FakeApi()
    prov = build_tokenizer_provenance(
        served_model="Qwen/Qwen3.5-122B-A10B-FP8",
        served_model_name_observed="served-slug",
    )
    write_tokenizer_provenance(api, "penfever/example-traces", prov)

    assert set(api.uploads) == {PROVENANCE_FILENAME, "README.md"}
    parsed = json.loads(api.uploads[PROVENANCE_FILENAME].decode("utf-8"))
    assert parsed["served_model"] == "Qwen/Qwen3.5-122B-A10B-FP8"
    readme = api.uploads["README.md"].decode("utf-8")
    # the decode recipe + exact model ref + per-turn note must be in the card
    assert "Qwen/Qwen3.5-122B-A10B-FP8" in readme
    assert "AutoTokenizer.from_pretrained" in readme
    assert PROVENANCE_FILENAME in readme
