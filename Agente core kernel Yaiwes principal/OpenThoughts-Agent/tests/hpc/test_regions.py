"""Unit tests for region -> output/weight bucket resolution.

Covers ``hpc/iris/regions.py``'s two DISTINCT region maps:

- :func:`output_bucket_for_region` — the exact per-region SINGLE-region output
  bucket for transient outputs (datagen/eval/xla_cache), and the runtime resolver
  :func:`region_local_output_prefix` built on it.
- :func:`gcs_bucket_for_region` / :func:`assert_yaml_regions_match_pin` — the
  MULTI-region weight-mirror bucket + guard, which must stay unchanged (weights
  are durable and live on ``gs://marin-models-{us,eu}``).

The metadata lookup for the runtime resolver is stubbed — these tests exercise
the region -> bucket mapping and the fail-fast branches, not the network call.

Run:
    .venv/bin/python -m pytest tests/hpc/test_regions.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hpc.iris import regions


# ---------------------------------------------------------------------------
# output_bucket_for_region — single-region transient-output map (exact lookup)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("region", "expected"),
    [
        ("us-central1", "gs://marin-us-central1"),
        ("us-central2", "gs://marin-us-central2"),
        ("us-east1", "gs://marin-us-east1"),
        ("us-east5", "gs://marin-us-east5"),
        ("us-west4", "gs://marin-us-west4"),
        ("europe-west4", "gs://marin-eu-west4"),
    ],
)
def test_output_bucket_for_region_known(region: str, expected: str) -> None:
    assert regions.output_bucket_for_region(region) == expected


@pytest.mark.parametrize(
    "region",
    [
        "asia-northeast1",  # unmapped continent
        "europe-west1",  # EU region other than europe-west4 (not mapped)
        "us-west1",  # US region we have no single-region bucket for
        "",
    ],
)
def test_output_bucket_for_region_unmapped_is_none(region: str) -> None:
    # Exact map: no continent-prefix fallback. Unmapped -> None so callers
    # fail-fast / drop the region rather than emit a wrong-continent bucket.
    assert regions.output_bucket_for_region(region) is None


# ---------------------------------------------------------------------------
# region_local_output_prefix — runtime resolver on the single-region map
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("region", "expected"),
    [
        ("us-east5", "gs://marin-us-east5/ot-agent"),
        ("us-central1", "gs://marin-us-central1/ot-agent"),
        ("europe-west4", "gs://marin-eu-west4/ot-agent"),
    ],
)
def test_region_local_output_prefix_maps_known_region(
    monkeypatch: pytest.MonkeyPatch, region: str, expected: str
) -> None:
    monkeypatch.setattr(regions, "region_from_metadata", lambda: region)
    assert regions.region_local_output_prefix() == expected


def test_region_local_output_prefix_honors_subpath(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(regions, "region_from_metadata", lambda: "us-east5")
    assert (
        regions.region_local_output_prefix("ot-agent/xla_cache")
        == "gs://marin-us-east5/ot-agent/xla_cache"
    )


def test_region_local_output_prefix_unmapped_region_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # asia-* has no configured single-region bucket: refuse rather than silently
    # writing to a cross-continent default.
    monkeypatch.setattr(regions, "region_from_metadata", lambda: "asia-northeast1")
    with pytest.raises(ValueError, match="asia-northeast1"):
        regions.region_local_output_prefix()


def test_region_local_output_prefix_off_gcp_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # No metadata server (laptop/CI): can't resolve a region-local bucket.
    monkeypatch.setattr(regions, "region_from_metadata", lambda: None)
    with pytest.raises(RuntimeError, match="metadata"):
        regions.region_local_output_prefix()


# ---------------------------------------------------------------------------
# Weight guard stays MULTI-region — the output migration must not touch it.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("region", "expected"),
    [
        ("us-east5", "gs://marin-models-us"),
        ("us-central1", "gs://marin-models-us"),
        ("europe-west4", "gs://marin-models-eu"),
    ],
)
def test_gcs_bucket_for_region_stays_multi_region(region: str, expected: str) -> None:
    # Weights are durable + multi-region; this is the guard's map and must NOT
    # move to single-region (that would reject correct weight YAMLs).
    assert regions.gcs_bucket_for_region(region) == expected


def test_weight_guard_rejects_wrong_continent_multi_region(tmp_path: Path) -> None:
    # A us-east5-pinned job whose weights point at the EU multi-region mirror is
    # rejected: the guard still keys on gs://marin-models-{us,eu} and expects the
    # US mirror for a us-* pin. (Confirms the guard was NOT switched to the
    # single-region output map.)
    yaml_path = tmp_path / "cfg.yaml"
    yaml_path.write_text(
        "vllm_server:\n  model_path: gs://marin-models-eu/ot-agent/models/foo\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="marin-models-us"):
        regions.assert_yaml_regions_match_pin([yaml_path], "us-east5")


def test_weight_guard_accepts_matching_multi_region(tmp_path: Path) -> None:
    yaml_path = tmp_path / "cfg.yaml"
    yaml_path.write_text(
        "vllm_server:\n  model_path: gs://marin-models-us/ot-agent/models/foo\n",
        encoding="utf-8",
    )
    # No exception: weights on the correct continent's multi-region mirror.
    regions.assert_yaml_regions_match_pin([yaml_path], "us-east5")
