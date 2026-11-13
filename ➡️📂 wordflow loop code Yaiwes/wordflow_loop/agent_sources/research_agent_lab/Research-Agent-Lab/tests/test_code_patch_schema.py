from __future__ import annotations
from unittest import TestCase, main
from schemas.code_patch import CodePatch


class CodePatchSchemaTest(TestCase):
    def test_defaults(self):
        patch = CodePatch()
        self.assertTrue(patch.patch_id.startswith("patch_"))
        self.assertEqual(patch.experiment_id, "")
        self.assertEqual(patch.task_id, "")
        self.assertEqual(patch.attempt, 0)
        self.assertEqual(patch.mode, "copy")
        self.assertEqual(patch.work_dir, "")
        self.assertEqual(patch.changed_files, [])
        self.assertEqual(patch.backup_paths, {})
        self.assertEqual(patch.diff_summary, "")
        self.assertEqual(patch.status, "pending")
        self.assertEqual(patch.reason, "")

    def test_changed_files_structure(self):
        patch = CodePatch(
            experiment_id="exp_1",
            changed_files=[
                {
                    "relative_path": "model/decoder.py",
                    "action": "modify",
                    "diff": "- old line\n+ new line",
                    "base_file_hash": "abc123",
                    "new_file_hash": "def456",
                }
            ],
        )
        self.assertEqual(len(patch.changed_files), 1)
        self.assertEqual(patch.changed_files[0]["relative_path"], "model/decoder.py")
        self.assertEqual(patch.changed_files[0]["action"], "modify")
        self.assertEqual(patch.changed_files[0]["diff"], "- old line\n+ new line")
        self.assertEqual(patch.changed_files[0]["base_file_hash"], "abc123")
        self.assertEqual(patch.changed_files[0]["new_file_hash"], "def456")


if __name__ == "__main__":
    main()
