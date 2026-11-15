from __future__ import annotations
from unittest import TestCase, main
from schemas.auto_debug_record import AutoDebugRecord


class AutoDebugRecordSchemaTest(TestCase):
    def test_defaults(self):
        record = AutoDebugRecord()
        self.assertTrue(record.record_id.startswith("debug_"))
        self.assertEqual(record.experiment_id, "")
        self.assertEqual(record.result_id, "")
        self.assertEqual(record.patch_id, "")
        self.assertEqual(record.attempt_number, 0)
        self.assertEqual(record.error_summary, "")
        self.assertEqual(record.fix_description, "")
        self.assertEqual(record.fix_file_contents, {})
        self.assertFalse(record.fix_successful)
        self.assertEqual(record.llm_call_id, "")
        self.assertEqual(record.log_artifact_id, "")


if __name__ == "__main__":
    main()
