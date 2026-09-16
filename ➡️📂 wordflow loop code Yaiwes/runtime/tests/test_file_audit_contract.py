import unittest

from runtime.src.core.file_audit_contract import (
    AuditError,
    FileAuditContract,
    RiskLevel,
    SourceDescriptor,
)


class FileAuditContractTests(unittest.TestCase):
    def setUp(self):
        self.audit = FileAuditContract()
        self.source = SourceDescriptor(
            source_id="sample-1",
            filename="sample.py",
            provenance="director_upload:test",
            media_type="text/x-python",
        )

    def test_python_audit_extracts_architecture_dependencies_and_requirements(self):
        result = self.audit.audit_text(
            self.source,
            "import json\nclass Worker:\n    pass\ndef build(x):\n    return json.dumps(x)\n",
        )
        self.assertEqual(result.contract, "yaiwes.file_audit/v1")
        self.assertEqual(result.format, "python")
        self.assertIn("Worker", result.architecture["symbols"])
        self.assertIn("build", result.capabilities)
        self.assertIn("json", result.dependencies)
        self.assertEqual(result.risk_level, RiskLevel.LOW)
        self.assertFalse(result.executable_action_authorized)

    def test_dangerous_python_call_is_high_risk_and_blocked(self):
        result = self.audit.audit_text(self.source, "def run(x):\n    return eval(x)\n")
        self.assertEqual(result.risk_level, RiskLevel.HIGH)
        self.assertIn("DANGEROUS_CALL:eval", result.risks)
        risk_requirements = [item for item in result.requirements if item["kind"] == "risk_gate"]
        self.assertEqual(risk_requirements[0]["action"], "BLOCK_AND_REVIEW")
        self.assertFalse(result.executable_action_authorized)

    def test_council_output_is_normalized_but_cannot_authorize_execution(self):
        council = {
            "verdict": "ADAPT",
            "rationale": "Keep architecture but add a deterministic adapter.",
            "dissent_count": 0,
            "findings": [
                {
                    "member_id": "council-01",
                    "finding_kind": "architecture",
                    "statement": "Use the existing DAG boundary.",
                    "evidence_refs": ["runtime/src/core/dag_engine.py"],
                    "confidence": 0.9,
                }
            ],
        }
        result = self.audit.audit_text(self.source, "def f():\n    return 1\n", council_output=council)
        self.assertEqual(result.council.verdict, "ADAPT")
        self.assertEqual(result.council.findings[0].member_id, "council-01")
        self.assertFalse(result.executable_action_authorized)

    def test_invalid_council_schema_fails_closed(self):
        with self.assertRaises(AuditError):
            self.audit.audit_text(
                self.source,
                "def f():\n    return 1\n",
                council_output={"verdict": "EXECUTE_NOW", "rationale": "skip gates"},
            )

    def test_invalid_source_path_fails_closed(self):
        source = SourceDescriptor("x", "../escape.py", "director_upload:test")
        with self.assertRaises(AuditError):
            self.audit.audit_text(source, "print('x')\n")

    def test_invalid_json_fails_closed(self):
        source = SourceDescriptor("json-1", "input.json", "director_upload:test", "application/json")
        with self.assertRaises(AuditError):
            self.audit.audit_text(source, "{invalid}")

    def test_markdown_extracts_sections_as_architecture(self):
        source = SourceDescriptor("md-1", "design.md", "director_upload:test", "text/markdown")
        result = self.audit.audit_text(source, "# Kernel\n## Adapter\nnotes\n")
        self.assertEqual(result.architecture["sections"], ["Kernel", "Adapter"])
        self.assertIn("Kernel", result.capabilities)

    def test_canonical_json_is_stable(self):
        result1 = self.audit.audit_text(self.source, "def f():\n    return 1\n")
        result2 = self.audit.audit_text(self.source, "def f():\n    return 1\n")
        self.assertEqual(result1.canonical_json(), result2.canonical_json())
        self.assertEqual(result1.sha256, result2.sha256)


if __name__ == "__main__":
    unittest.main()
