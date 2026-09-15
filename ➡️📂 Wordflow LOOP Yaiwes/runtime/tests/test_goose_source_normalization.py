from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CORE = Path(__file__).resolve().parents[1] / "src" / "core"
sys.path.insert(0, str(CORE))

from goose_official_acquisition_runner import normalize_tracked_source  # noqa: E402


def git(repo: Path, *args: str) -> None:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stdout)


def init_repo(repo: Path) -> None:
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "yaiwes-test")
    git(repo, "config", "user.email", "yaiwes-test@example.invalid")


def commit_all(repo: Path) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "fixture")


class GooseSourceNormalizationTests(unittest.TestCase):
    def test_tracked_internal_symlink_is_materialized_and_untracked_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "repo"
            repo.mkdir()
            init_repo(repo)
            bin_dir = repo / "bin"
            bin_dir.mkdir()
            hermit = bin_dir / "hermit"
            hermit.write_text("#!/bin/sh\necho hermit\n", encoding="utf-8")
            hermit.chmod(0o755)
            os.symlink("hermit", bin_dir / ".rustup.pkg")
            os.symlink(".rustup.pkg", bin_dir / "cargo")
            (repo / "README.md").write_text("goose\n", encoding="utf-8")
            commit_all(repo)
            (repo / "UNTRACKED.txt").write_text("must not copy\n", encoding="utf-8")

            normalized = root / "normalized"
            evidence = normalize_tracked_source(repo, normalized)

            self.assertEqual(
                evidence["strategy"],
                "TRACKED_INTERNAL_SYMLINKS_MATERIALIZED_TO_REGULAR_FILES",
            )
            self.assertEqual(evidence["materialized_symlinks"], 2)
            self.assertFalse((normalized / "bin" / "cargo").is_symlink())
            self.assertEqual(
                (normalized / "bin" / "cargo").read_text(encoding="utf-8"),
                hermit.read_text(encoding="utf-8"),
            )
            self.assertTrue(os.access(normalized / "bin" / "cargo", os.X_OK))
            self.assertFalse((normalized / "UNTRACKED.txt").exists())
            mapping = {row["path"]: row for row in evidence["materialization_map"]}
            self.assertEqual(mapping["bin/cargo"]["link_target"], ".rustup.pkg")
            self.assertEqual(mapping["bin/cargo"]["resolved_tracked_path"], "bin/hermit")
            self.assertFalse(evidence["runtime_semantics_claimed"])

    def test_absolute_symlink_is_rejected_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "repo"
            repo.mkdir()
            init_repo(repo)
            os.symlink("/etc/passwd", repo / "bad-link")
            commit_all(repo)

            with self.assertRaisesRegex(
                RuntimeError, "GOOSE_SYMLINK_ABSOLUTE_TARGET_GAP"
            ):
                normalize_tracked_source(repo, root / "normalized")

    def test_relative_symlink_escaping_repo_is_rejected_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            outside = root / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            repo = root / "repo"
            repo.mkdir()
            init_repo(repo)
            os.symlink("../outside.txt", repo / "bad-link")
            commit_all(repo)

            with self.assertRaisesRegex(RuntimeError, "GOOSE_SYMLINK_RESOLUTION_GAP"):
                normalize_tracked_source(repo, root / "normalized")


if __name__ == "__main__":
    unittest.main(verbosity=2)
