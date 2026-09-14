"""Extended tests for skills/generator.py -- missing lines coverage.

Targets:
  - SkillGenerator with LLM fn (generate, test, register with LLM)
  - _extract_code_block with various formats
  - register with package_builder
  - register with audit_logger
  - approve() workflow
  - rollback() workflow
  - process_gap with retries
  - process_all_gaps
  - SkillGap priority calculation
  - GeneratedSkill properties
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.skills.generator import (
    GapDetector,
    GeneratedSkill,
    GenerationStatus,
    SkillGap,
    SkillGapType,
    SkillGenerator,
)

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================================
# SkillGap
# ============================================================================


class TestSkillGapExtended:
    def test_priority_user_request(self) -> None:
        gap = SkillGap(id="g1", gap_type=SkillGapType.USER_REQUEST, description="test")
        gap.frequency = 1
        assert gap.priority == 2.0  # 1 * 2.0

    def test_priority_repeated_failure(self) -> None:
        gap = SkillGap(id="g1", gap_type=SkillGapType.REPEATED_FAILURE, description="test")
        gap.frequency = 3
        assert gap.priority == 4.5  # 3 * 1.5

    def test_priority_low_success(self) -> None:
        gap = SkillGap(id="g1", gap_type=SkillGapType.LOW_SUCCESS_RATE, description="test")
        gap.frequency = 2
        assert gap.priority == 1.2  # 2 * 0.6


# ============================================================================
# GeneratedSkill
# ============================================================================


class TestGeneratedSkillExtended:
    def test_module_name(self) -> None:
        s = GeneratedSkill(name="my_tool")
        assert s.module_name == "auto_my_tool"

    def test_version_tag(self) -> None:
        s = GeneratedSkill(name="tool", version=3)
        assert s.version_tag == "v3"


# ============================================================================
# SkillGenerator -- extract code block
# ============================================================================


class TestExtractCodeBlock:
    def test_python_fenced_block(self) -> None:
        text = "Some explanation\n```python\nprint('hello')\n```\nMore text"
        result = SkillGenerator._extract_code_block(text)
        assert result == "print('hello')"

    def test_generic_fenced_block(self) -> None:
        text = "Here:\n```\ndef foo(): pass\n```\n"
        result = SkillGenerator._extract_code_block(text)
        assert result == "def foo(): pass"

    def test_no_fences(self) -> None:
        text = "def foo(): pass"
        result = SkillGenerator._extract_code_block(text)
        assert result == "def foo(): pass"


# ============================================================================
# SkillGenerator -- LLM path
# ============================================================================


class TestSkillGeneratorLLM:
    @pytest.mark.asyncio
    async def test_generate_with_llm(self, tmp_path: Path) -> None:
        llm_fn = AsyncMock(
            side_effect=[
                "```python\ndef handler(): pass\n```",  # code
                "```python\ndef test_handler(): assert True\n```",  # test
            ]
        )
        gen = SkillGenerator(skills_dir=tmp_path / "skills", llm_fn=llm_fn)
        gap = SkillGap(
            id="g1",
            gap_type=SkillGapType.USER_REQUEST,
            description="Create a calculator",
            context="math operations",
        )
        skill = await gen.generate(gap)
        assert skill.code == "def handler(): pass"
        assert skill.test_code == "def test_handler(): assert True"
        assert llm_fn.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_llm_error(self, tmp_path: Path) -> None:
        llm_fn = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        gen = SkillGenerator(skills_dir=tmp_path / "skills", llm_fn=llm_fn)
        gap = SkillGap(
            id="g1",
            gap_type=SkillGapType.USER_REQUEST,
            description="Broken gen",
        )
        skill = await gen.generate(gap)
        assert skill.status == GenerationStatus.FAILED
        assert len(skill.test_errors) > 0


# ============================================================================
# SkillGenerator -- test and register
# ============================================================================


class TestSkillGeneratorTestAndRegister:
    @pytest.mark.asyncio
    async def test_test_without_sandbox(self, tmp_path: Path) -> None:
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        skill = GeneratedSkill(name="test_skill", code="x = 1")
        passed = await gen.test(skill)
        assert passed is True
        assert skill.status == GenerationStatus.TEST_PASSED

    @pytest.mark.asyncio
    async def test_test_syntax_error(self, tmp_path: Path) -> None:
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        skill = GeneratedSkill(name="bad_skill", code="def (:")
        passed = await gen.test(skill)
        assert passed is False
        assert skill.status == GenerationStatus.TEST_FAILED

    def test_register_untested_rejected(self, tmp_path: Path) -> None:
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        skill = GeneratedSkill(name="untested", test_passed=False)
        assert gen.register(skill) is False

    def test_register_requires_approval(self, tmp_path: Path) -> None:
        gen = SkillGenerator(
            skills_dir=tmp_path / "skills",
            require_approval=True,
        )
        skill = GeneratedSkill(name="needs_approval", test_passed=True)
        skill.requires_approval = True
        assert gen.register(skill) is False
        assert skill.status == GenerationStatus.AWAITING_APPROVAL

    def test_register_success(self, tmp_path: Path) -> None:
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        skill = GeneratedSkill(
            name="good_skill",
            test_passed=True,
            code="x = 1",
            test_code="assert True",
            skill_markdown="# Test",
        )
        gen._generated["good_skill"] = skill
        assert gen.register(skill) is True
        assert skill.status == GenerationStatus.REGISTERED
        # Files should be written
        assert (tmp_path / "skills" / "auto_good_skill.py").exists()
        assert (tmp_path / "skills" / "auto_good_skill.md").exists()

    def test_register_with_audit_logger(self, tmp_path: Path) -> None:
        audit = MagicMock()
        gen = SkillGenerator(
            skills_dir=tmp_path / "skills",
            audit_logger=audit,
        )
        skill = GeneratedSkill(
            name="audited",
            test_passed=True,
            code="x = 1",
            test_code="assert True",
        )
        gen.register(skill)
        audit.log_skill_install.assert_called_once()

    def test_register_with_package_builder(self, tmp_path: Path) -> None:
        builder = MagicMock()
        package = MagicMock()
        package.package_id = "PKG-001"
        package.to_bytes.return_value = b"package-data"
        builder.build.return_value = package

        gen = SkillGenerator(
            skills_dir=tmp_path / "skills",
            package_builder=builder,
        )
        gap = SkillGap(id="g1", gap_type=SkillGapType.USER_REQUEST, description="test")
        skill = GeneratedSkill(
            name="packaged",
            test_passed=True,
            code="x = 1",
            test_code="assert True",
            gap=gap,
        )
        gen.register(skill)
        builder.build.assert_called_once()

    def test_register_with_skill_registry(self, tmp_path: Path) -> None:
        registry = MagicMock()
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        skill = GeneratedSkill(
            name="reg_skill",
            test_passed=True,
            code="x = 1",
            test_code="assert True",
        )
        gen.register(skill, skill_registry=registry)
        registry.load_from_directories.assert_called_once()


# ============================================================================
# SkillGenerator -- approve and rollback
# ============================================================================


class TestApproveAndRollback:
    def test_approve_success(self, tmp_path: Path) -> None:
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        skill = GeneratedSkill(name="awaiting", status=GenerationStatus.AWAITING_APPROVAL)
        gen._generated["awaiting"] = skill
        assert gen.approve("awaiting", "admin") is True
        assert skill.approved_by == "admin"

    def test_approve_not_found(self, tmp_path: Path) -> None:
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        assert gen.approve("nonexistent") is False

    def test_approve_wrong_status(self, tmp_path: Path) -> None:
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        skill = GeneratedSkill(name="running", status=GenerationStatus.GENERATING)
        gen._generated["running"] = skill
        assert gen.approve("running") is False

    def test_rollback_no_previous_version(self, tmp_path: Path) -> None:
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        skill = GeneratedSkill(name="v1_only", version=1)
        gen._generated["v1_only"] = skill
        assert gen.rollback("v1_only") is False

    def test_rollback_history_not_found(self, tmp_path: Path) -> None:
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        skill = GeneratedSkill(name="missing_hist", version=2)
        gen._generated["missing_hist"] = skill
        assert gen.rollback("missing_hist") is False

    def test_rollback_success(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        gen = SkillGenerator(skills_dir=skills_dir)

        # Create "previous version" in history
        history_dir = skills_dir / "history"
        history_file = history_dir / "auto_my_tool_v1.py"
        history_file.write_text("# v1 code", encoding="utf-8")

        # Create current version
        current_file = skills_dir / "auto_my_tool.py"
        current_file.write_text("# v2 code", encoding="utf-8")

        skill = GeneratedSkill(name="my_tool", version=2)
        gen._generated["my_tool"] = skill
        assert gen.rollback("my_tool") is True
        assert skill.version == 1
        assert skill.status == GenerationStatus.ROLLED_BACK

    def test_rollback_not_found(self, tmp_path: Path) -> None:
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        assert gen.rollback("nonexistent") is False


# ============================================================================
# SkillGenerator -- process_gap E2E
# ============================================================================


class TestProcessGap:
    @pytest.mark.asyncio
    async def test_process_gap_success(self, tmp_path: Path) -> None:
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        gap = SkillGap(
            id="g1",
            gap_type=SkillGapType.USER_REQUEST,
            description="calc tool",
            tool_name="calculator",
        )
        skill = await gen.process_gap(gap)
        assert skill.status == GenerationStatus.REGISTERED

    @pytest.mark.asyncio
    async def test_process_gap_failed_generation(self, tmp_path: Path) -> None:
        llm_fn = AsyncMock(side_effect=RuntimeError("LLM down"))
        gen = SkillGenerator(skills_dir=tmp_path / "skills", llm_fn=llm_fn)
        gap = SkillGap(
            id="g1",
            gap_type=SkillGapType.USER_REQUEST,
            description="fail tool",
        )
        skill = await gen.process_gap(gap)
        assert skill.status == GenerationStatus.FAILED

    @pytest.mark.asyncio
    async def test_process_all_gaps(self, tmp_path: Path) -> None:
        gen = SkillGenerator(skills_dir=tmp_path / "skills")
        # Add gaps that are actionable
        gen.gap_detector.report_user_request("New calc tool")
        results = await gen.process_all_gaps()
        assert len(results) >= 1


# ============================================================================
# GapDetector
# ============================================================================


class TestGapDetectorExtended:
    def test_eviction_on_overflow(self) -> None:
        detector = GapDetector()
        detector.MAX_GAPS = 3
        detector.report_unknown_tool("t1")
        detector.report_unknown_tool("t2")
        detector.report_unknown_tool("t3")
        # This should evict the lowest priority
        detector.report_unknown_tool("t4")
        assert detector.gap_count == 3

    def test_context_length_limit(self) -> None:
        detector = GapDetector()
        long_ctx = "x" * 10000
        gap = detector.report_unknown_tool("t1", context=long_ctx)
        assert len(gap.context) <= GapDetector.MAX_CONTEXT_LENGTH

    def test_upsert_updates_frequency(self) -> None:
        detector = GapDetector()
        detector.report_unknown_tool("t1")
        gap = detector.report_unknown_tool("t1")
        assert gap.frequency == 2

    def test_upsert_updates_context(self) -> None:
        detector = GapDetector()
        detector.report_unknown_tool("t1", context="ctx1")
        gap = detector.report_unknown_tool("t1", context="ctx2")
        assert gap.context == "ctx2"
