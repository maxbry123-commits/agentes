from __future__ import annotations

from types import SimpleNamespace

import pytest

from hpc.iris.outputs import IrisOutputPaths
from scripts.iris import mirror_models
from scripts.iris.launch_mirror import GcsToS3Launcher, HfMirrorIrisLauncher


def test_mirror_router_dispatches_hf_to_gcs_without_changing_route_arguments(
    monkeypatch,
):
    calls = []
    monkeypatch.setattr(
        mirror_models.mirror_hf_to_gcs,
        "mirror",
        lambda repo, prefixes, **kwargs: calls.append((repo, prefixes, kwargs)),
    )
    assert (
        mirror_models.main(
            [
                "hf-to-gcs",
                "--repo",
                "org/model",
                "--gcs-prefix",
                "gs://models",
                "--quiet",
            ]
        )
        == 0
    )
    assert calls == [
        ("org/model", ["gs://models"], {"verbose": False, "iris_job_id": None})
    ]


def test_mirror_router_rejects_wrong_source_scheme_before_any_transfer(monkeypatch):
    monkeypatch.setattr(mirror_models.mirror_gcs_to_s3, "mirror_repo", pytest.fail)
    with pytest.raises(SystemExit, match="must start with gs://"):
        mirror_models.main(
            [
                "gcs-to-s3",
                "--repo",
                "org/model",
                "--gcs-prefix",
                "bad",
                "--s3-bucket",
                "bucket",
                "--s3-prefix",
                "models",
            ]
        )


def test_mirror_launchers_issue_the_canonical_mirror_command():
    output_paths = IrisOutputPaths("unused", "unused", "unused")
    hf_args = SimpleNamespace(gcs_prefix=["gs://one", "gs://two"], repo=["org/model"])
    gcs_args = SimpleNamespace(
        gcs_prefix="gs://models",
        s3_bucket="bucket",
        s3_prefix="models",
        s3_endpoint=None,
        repo=["org/model"],
    )
    assert HfMirrorIrisLauncher(".").build_task_command(hf_args, output_paths) == [
        "python",
        "-m",
        "scripts.iris.mirror_models",
        "hf-to-gcs",
        "--gcs-prefix",
        "gs://one",
        "--gcs-prefix",
        "gs://two",
        "--repo",
        "org/model",
    ]
    assert GcsToS3Launcher(".").build_task_command(gcs_args, output_paths) == [
        "python",
        "-m",
        "scripts.iris.mirror_models",
        "gcs-to-s3",
        "--gcs-prefix",
        "gs://models",
        "--s3-bucket",
        "bucket",
        "--s3-prefix",
        "models",
        "--repo",
        "org/model",
    ]
