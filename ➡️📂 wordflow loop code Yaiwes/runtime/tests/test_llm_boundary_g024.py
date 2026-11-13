import unittest

from runtime.src.core.llm_boundary import (
    ACTION_POLICY,
    BoundaryViolation,
    execute_with_boundary,
    enforce_boundary,
)


class LLMBoundaryG024Tests(unittest.TestCase):
    def test_matrix_covers_literal_deterministic_controls(self):
        required = {
            "authorize_execution",
            "evaluate_gate",
            "hash_verify",
            "persist_checkpoint",
            "persist_evidence",
            "promote_deployment",
            "rollback_deployment",
            "route_task",
            "sandbox_policy",
            "schedule_dag",
            "select_target_path",
            "state_transition",
            "validate_contract",
            "validate_schema",
        }
        self.assertEqual(set(), required - ACTION_POLICY.keys())
        self.assertTrue(all(ACTION_POLICY[action] == "DETERMINISTIC" for action in required))

    def test_every_deterministic_action_rejects_every_llm_actor(self):
        deterministic = [key for key, value in ACTION_POLICY.items() if value == "DETERMINISTIC"]
        for action in deterministic:
            for actor in ("LLM", "AGENT_LLM", "llm"):
                with self.subTest(action=action, actor=actor):
                    decision = enforce_boundary(action, actor)
                    self.assertFalse(decision.allowed)
                    self.assertEqual("LLM_CANNOT_AUTHORIZE_DETERMINISTIC_ACTION", decision.reason)

    def test_unknown_or_ambiguous_actor_fails_closed(self):
        for actor in ("", "human", "agent", " deterministic-ish "):
            with self.subTest(actor=actor):
                decision = enforce_boundary("promote_deployment", actor)
                self.assertFalse(decision.allowed)
                self.assertEqual("ACTOR_NOT_ALLOWLISTED", decision.reason)

    def test_unknown_action_fails_closed(self):
        decision = enforce_boundary("deploy_without_gate", "DETERMINISTIC")
        self.assertFalse(decision.allowed)
        self.assertEqual("ACTION_NOT_ALLOWLISTED", decision.reason)

    def test_rejected_callback_is_never_invoked(self):
        calls = []

        def promote():
            calls.append("called")

        with self.assertRaisesRegex(BoundaryViolation, "LLM_CANNOT_AUTHORIZE"):
            execute_with_boundary("promote_deployment", "LLM", promote)
        self.assertEqual([], calls)

    def test_trusted_runtime_can_execute_deterministic_callback(self):
        result = execute_with_boundary(
            "hash_verify", "DETERMINISTIC_RUNTIME", lambda value: value == "sha256:ok", "sha256:ok"
        )
        self.assertTrue(result)

    def test_llm_advisory_actions_remain_allowed_without_authority(self):
        for action in ("analyze_file", "council_opinion", "generate_candidate"):
            with self.subTest(action=action):
                decision = enforce_boundary(action, "LLM")
                self.assertTrue(decision.allowed)
                self.assertEqual("LLM_ALLOWED", decision.authority)


if __name__ == "__main__":
    unittest.main()
