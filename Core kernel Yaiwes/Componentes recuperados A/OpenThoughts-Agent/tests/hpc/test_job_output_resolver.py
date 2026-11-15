"""Unit tests for :mod:`hpc.iris.job_output_resolver`.

The resolver returns a job's RECORDED output URI so both legacy multi-region
jobs and new single-region jobs read/write the correct bucket with no flag day.
These tests stub the registry and the iris query (no network / no DB): the point
under test is the resolution ORDER and that each URI shape round-trips verbatim.

Run:
    .venv/bin/python -m pytest tests/hpc/test_job_output_resolver.py -v
"""

from __future__ import annotations

import pytest

from hpc.iris import job_output_resolver as resolver
from hpc.iris_job_registry import JobRecord


def _record(job_name: str, gcs_output_dir: str) -> JobRecord:
    return JobRecord(
        job_id=f"/benjaminfeuer/{job_name}",
        job_name=job_name,
        submitted_at="2026-07-13T00:00:00Z",
        gcs_output_dir=gcs_output_dir,
        local_dest=f"~/.ot-agent/runs/{job_name}",
        cluster_config="marin",
        status="running",
        last_polled_at=None,
        fetched_at=None,
        exit_code=None,
        error_msg=None,
        iris_attempt_id=None,
        bytes_fetched=None,
    )


def _stub_registry(monkeypatch: pytest.MonkeyPatch, record: JobRecord | None) -> None:
    monkeypatch.setattr(resolver, "get_latest_by_job_name", lambda name: record)
    monkeypatch.setattr(resolver, "get", lambda job_id: None)


def test_registry_multi_region_job_resolves_to_multi_region(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # #31-style: an old job recorded on the MULTI-region bucket must resolve back
    # to its multi-region URI so the live rescue path keeps working.
    job = "tracegen-iris-20260713-053947"
    uri = f"gs://marin-models-us/ot-agent/{job}"
    _stub_registry(monkeypatch, _record(job, uri))
    assert resolver.resolve_job_output_dir(job) == uri


def test_registry_single_region_job_resolves_to_single_region(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A new job recorded on a SINGLE-region bucket resolves to its single-region
    # URI — same resolver, different bucket, no flag day.
    job = "tracegen-iris-20260714-010101"
    uri = f"gs://marin-us-east5/ot-agent/{job}"
    _stub_registry(monkeypatch, _record(job, uri))
    assert resolver.resolve_job_output_dir(job) == uri


def test_registry_strips_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    job = "j1"
    _stub_registry(monkeypatch, _record(job, "gs://marin-us-east5/ot-agent/j1/"))
    assert resolver.resolve_job_output_dir(job) == "gs://marin-us-east5/ot-agent/j1"


def test_fully_qualified_job_ref_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A /<user>/<name> id resolves via the bare-name registry lookup.
    seen: dict[str, str] = {}

    def _get_latest(name: str) -> JobRecord | None:
        seen["name"] = name
        return _record(name, f"gs://marin-us-east5/ot-agent/{name}")

    monkeypatch.setattr(resolver, "get_latest_by_job_name", _get_latest)
    monkeypatch.setattr(resolver, "get", lambda job_id: None)
    out = resolver.resolve_job_output_dir("/benjaminfeuer/myjob")
    assert seen["name"] == "myjob"
    assert out == "gs://marin-us-east5/ot-agent/myjob"


def test_iris_fallback_parses_jobs_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    # Registry miss + cluster given: parse --jobs-dir out of the baked worker
    # command exactly as the live iris job_config.entrypoint_json carries it.
    _stub_registry(monkeypatch, None)
    entrypoint = (
        '{"run_command": {"argv": ["bash", "-c", "exec python run_tracegen.py '
        "--jobs-dir gs://marin-us-east5/ot-agent/xjob "
        '--experiments_dir gs://marin-us-east5/ot-agent/xjob"]}}'
    )
    monkeypatch.setattr(
        resolver, "_iris_query", lambda cfg, sql: [{"entrypoint_json": entrypoint}]
    )
    out = resolver.resolve_job_output_dir("xjob", cluster_config="marin.yaml")
    assert out == "gs://marin-us-east5/ot-agent/xjob"


def test_iris_fallback_multi_region_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_registry(monkeypatch, None)
    entrypoint = (
        '{"run_command": {"argv": ["bash", "-c", '
        '"exec python x.py --jobs-dir gs://marin-models-us/ot-agent/oldjob"]}}'
    )
    monkeypatch.setattr(
        resolver, "_iris_query", lambda cfg, sql: [{"entrypoint_json": entrypoint}]
    )
    out = resolver.resolve_job_output_dir("oldjob", cluster_config="marin.yaml")
    assert out == "gs://marin-models-us/ot-agent/oldjob"


def test_registry_miss_without_cluster_fails_fast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # No registry row and no cluster_config: fail-fast, never guess a bucket.
    _stub_registry(monkeypatch, None)
    with pytest.raises(LookupError, match="cluster_config"):
        resolver.resolve_job_output_dir("ghost")


def test_iris_fallback_job_absent_fails_fast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_registry(monkeypatch, None)
    monkeypatch.setattr(resolver, "_iris_query", lambda cfg, sql: [])
    with pytest.raises(LookupError, match="not found on the iris controller"):
        resolver.resolve_job_output_dir("ghost", cluster_config="marin.yaml")


def test_iris_fallback_no_output_arg_fails_fast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_registry(monkeypatch, None)
    entrypoint = (
        '{"run_command": {"argv": ["bash", "-c", "exec python x.py --model foo"]}}'
    )
    monkeypatch.setattr(
        resolver, "_iris_query", lambda cfg, sql: [{"entrypoint_json": entrypoint}]
    )
    with pytest.raises(LookupError, match="no --jobs-dir"):
        resolver.resolve_job_output_dir("ghost", cluster_config="marin.yaml")
