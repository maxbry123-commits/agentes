from __future__ import annotations

import asyncio
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

from parallel_kernel import ContractError, ParallelEvolutionKernel, _fingerprint, _validate


def registry(tmp_path: Path) -> dict[str, object]:
    return {
        "lanes": [
            {"id": "ok", "command": [sys.executable, "-c", "print('ok')"], "cwd": str(tmp_path), "timeout_seconds": 5},
            {"id": "bad", "command": [sys.executable, "-c", "raise SystemExit(7)"], "cwd": str(tmp_path), "timeout_seconds": 5},
        ]
    }


def authorization(value: dict[str, object], lanes: list[str]) -> dict[str, object]:
    return {"state": "AUTHORIZED", "proposal_fingerprint": _fingerprint(value), "approved_lane_ids": lanes}


class ParallelKernelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_missing_authorization_fails_closed(self) -> None:
        value = registry(self.root)
        with self.assertRaisesRegex(ContractError, "authorization"):
            _validate(value, {"state": "PROPOSED"})

    def test_fingerprint_mismatch_fails_closed(self) -> None:
        value = registry(self.root)
        auth = authorization(value, ["ok"])
        auth["proposal_fingerprint"] = hashlib.sha256(b"different").hexdigest()
        with self.assertRaisesRegex(ContractError, "fingerprint"):
            _validate(value, auth)

    def test_failure_does_not_cancel_independent_lane(self) -> None:
        value = registry(self.root)
        lanes = _validate(value, authorization(value, ["ok", "bad"]))
        report = asyncio.run(ParallelEvolutionKernel(max_parallel=2).run(lanes=lanes, fingerprint=_fingerprint(value)))
        self.assertEqual(report.verdict, "FAIL")
        self.assertEqual({item.lane_id: item.status for item in report.results}, {"bad": "FAIL", "ok": "PASS"})
        self.assertEqual(next(item for item in report.results if item.lane_id == "ok").stdout.strip(), "ok")

    def test_results_are_deterministically_sorted(self) -> None:
        value = registry(self.root)
        lanes = _validate(value, authorization(value, ["ok", "bad"]))
        report = asyncio.run(ParallelEvolutionKernel(max_parallel=2).run(lanes=lanes, fingerprint=_fingerprint(value)))
        self.assertEqual([item.lane_id for item in report.results], ["bad", "ok"])


if __name__ == "__main__":
    unittest.main()
