    def test_main_loop_checkpoint(self):
        state = run_main_12(_raw(), loop_path=LOOP)
        cp = state.get("checkpoint")
        self.assertIsInstance(cp, dict)
        self.assertIn("expires_at", cp)
        self.assertEqual(cp.get("status"), "COMPLETED")


class TestFichaW7(unittest.TestCase):
    def test_ficha_abi(self):
        self.assertTrue(FICHA.is_file())
        data = json.loads(FICHA.read_text(encoding="utf-8"))
        self.assertEqual(data["abi_version"], "2.0")
        self.assertEqual(data["llm_control"], "DENY")
        self.assertEqual(data["mount_mode"], "sidecar")
        self.assertEqual(data["artifact_id"], "wordflow.yaiwes.v1")
        self.assertEqual(data["extension_type"], "wordflow_runtime")
        self.assertEqual(data["entry_point"], "extensions.wordflow.engine.entrypoint_v1:run_v1")


if __name__ == "__main__":
    unittest.main()
