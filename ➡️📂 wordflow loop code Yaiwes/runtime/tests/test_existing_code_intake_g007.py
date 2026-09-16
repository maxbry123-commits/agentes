import tempfile
import unittest
from pathlib import Path

from runtime.src.core.existing_code_intake import (
    ExistingCodeIntakeError,
    ExistingCodeRequest,
    execute_existing_code_transfer,
    validate_existing_code,
)


def _request(**overrides):
    values = {
        "intake_id": "E1",
        "source_ref": "https://github.com/example/repo@abc/file.py",
        "source_content": b"def add(a,b): return a+b\n",
        "source_license": "MIT",
        "language": "python",
        "requested_decision": "ADAPT",
        "destination": "➡️📂 Wordflow LOOP Yaiwes/runtime/src/tools/add.py",
        "provenance_refs": ("source:abc", "license:MIT"),
        "safety_verdict": "ALLOW_STATIC_REVIEW",
        "motor_operation": "COPY",
    }
    values.update(overrides)
    return ExistingCodeRequest(**values)


class ExistingCodeIntakeTests(unittest.TestCase):
    def test_packet_is_hash_bound_and_not_executable(self):
        packet = validate_existing_code(_request())
        self.assertEqual(len(packet.source_sha256), 64)
        self.assertEqual(packet.decision, "ADAPT")
        self.assertFalse(packet.execution_authorized)
        self.assertFalse(packet.deployment_authorized)

    def test_static_gates_fail_closed(self):
        with self.assertRaisesRegex(ExistingCodeIntakeError, "DESTINATION_OUTSIDE_AUTHORIZED_ROOT"):
            validate_existing_code(_request(destination="Core kernel Yaiwes/file.py"))
        with self.assertRaisesRegex(ExistingCodeIntakeError, "UNSAFE_CODE_CANNOT_ADVANCE"):
            validate_existing_code(_request(safety_verdict="BLOCK_AND_REVIEW"))
        with self.assertRaisesRegex(ExistingCodeIntakeError, "CANONICAL_MOTOR_OPERATION_REQUIRED"):
            validate_existing_code(_request(motor_operation="RSYNC"))

    def _tree(self, operation="COPY"):
        temp = tempfile.TemporaryDirectory()
        base = Path(temp.name)
        repo = base / "repo"
        auth = repo / "➡️📂 Wordflow LOOP Yaiwes"
        source_dir = base / "source"
        source_dir.mkdir(parents=True)
        auth.mkdir(parents=True)
        source = source_dir / "add.py"
        content = b"def add(a,b): return a+b\n"
        source.write_bytes(content)
        actual_repo = Path(__file__).resolve().parents[3]
        motor_root = actual_repo / "➡️📂 Wordflow LOOP Yaiwes" / "➡️📂motores de descarga extracción copiado movimiento archivos agentes"
        target_motor_root = auth / "➡️📂motores de descarga extracción copiado movimiento archivos agentes"
        import shutil
        shutil.copytree(motor_root, target_motor_root)
        request = _request(
            source_content=content,
            motor_operation=operation,
            destination="➡️📂 Wordflow LOOP Yaiwes/runtime/src/tools/add.py",
        )
        return temp, repo, auth, source, request

    def test_copy_runs_canonical_motor_and_reads_back(self):
        temp, repo, auth, source, request = self._tree("COPY")
        self.addCleanup(temp.cleanup)
        result = execute_existing_code_transfer(
            request,
            repo_root=repo,
            authorized_root=auth,
            source_file=source,
            state_file=auth / "state/copy.json",
            mutation_authorized=True,
        )
        self.assertTrue(result.readback_verified)
        self.assertTrue(result.source_retained)
        self.assertEqual(result.destination_sha256, result.packet.source_sha256)

    def test_move_requires_separate_removal_authority(self):
        temp, repo, auth, source, request = self._tree("MOVE")
        self.addCleanup(temp.cleanup)
        with self.assertRaisesRegex(ExistingCodeIntakeError, "REMOVE_SOURCE_NOT_AUTHORIZED"):
            execute_existing_code_transfer(
                request, repo_root=repo, authorized_root=auth, source_file=source,
                state_file=auth / "state/move.json", mutation_authorized=True,
            )
        self.assertTrue(source.exists())
        result = execute_existing_code_transfer(
            request, repo_root=repo, authorized_root=auth, source_file=source,
            state_file=auth / "state/move.json", mutation_authorized=True,
            remove_source_authorized=True,
        )
        self.assertFalse(result.source_retained)

    def test_scope_and_content_fail_without_transfer(self):
        temp, repo, auth, source, request = self._tree("COPY")
        self.addCleanup(temp.cleanup)
        (source.parent / "unreviewed.py").write_text("pass\n", encoding="utf-8")
        with self.assertRaisesRegex(ExistingCodeIntakeError, "SOURCE_SCOPE_MUST_CONTAIN_ONE_FILE"):
            execute_existing_code_transfer(
                request, repo_root=repo, authorized_root=auth, source_file=source,
                state_file=auth / "state/copy.json", mutation_authorized=True,
            )
        self.assertFalse((auth / "runtime/src/tools/add.py").exists())


if __name__ == "__main__":
    unittest.main()
