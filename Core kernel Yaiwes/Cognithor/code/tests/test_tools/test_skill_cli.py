"""Tests fuer tools/skill_cli.py -- SkillCLI Developer Tools Coverage-Erweiterung."""

from __future__ import annotations

from pathlib import Path

import pytest

from cognithor.tools.skill_cli import (
    BUILT_IN_TEMPLATES,
    ContributorReward,
    LintIssue,
    LintSeverity,
    PublishRequest,
    PublishStatus,
    RewardSystem,
    ScaffoldResult,
    SkillCLI,
    SkillLinter,
    SkillPublisher,
    SkillScaffolder,
    SkillTemplate,
    SkillTester,
    SkillTestResult,
    TemplateType,
)

# ============================================================================
# SkillScaffolder — additional coverage
# ============================================================================


class TestSkillScaffolderExtended:
    def test_scaffold_api_template(self, tmp_path: Path) -> None:
        scaffolder = SkillScaffolder()
        result = scaffolder.scaffold(
            "API Tool",
            TemplateType.API_INTEGRATION,
            base_dir=str(tmp_path / "skills"),
        )
        assert result.template_used == "TPL-API"
        assert any("skill.py" in f for f in result.files_created)

    def test_scaffold_automation_template(self, tmp_path: Path) -> None:
        scaffolder = SkillScaffolder()
        result = scaffolder.scaffold(
            "Auto Task",
            TemplateType.AUTOMATION,
            base_dir=str(tmp_path / "skills"),
        )
        assert result.template_used == "TPL-AUTO"

    def test_scaffold_unknown_template_raises(self, tmp_path: Path) -> None:
        scaffolder = SkillScaffolder()
        # Remove all templates
        scaffolder._templates.clear()
        with pytest.raises(ValueError, match="Unknown template"):
            scaffolder.scaffold("X", TemplateType.BASIC, base_dir=str(tmp_path))

    def test_add_custom_template(self, tmp_path: Path) -> None:
        scaffolder = SkillScaffolder()
        custom = SkillTemplate(
            "TPL-CUSTOM",
            "Custom",
            TemplateType.TOOL_WRAPPER,
            "Custom template",
            {"custom.py": "print('hello')"},
        )
        scaffolder.add_template(custom)
        assert scaffolder.template_count >= 4  # 3 built-in + 1 custom

    def test_available_templates(self) -> None:
        scaffolder = SkillScaffolder()
        templates = scaffolder.available_templates()
        assert len(templates) >= 3
        assert all("template_id" in t for t in templates)

    def test_stats(self, tmp_path: Path) -> None:
        scaffolder = SkillScaffolder()
        scaffolder.scaffold("Test", base_dir=str(tmp_path / "skills"))
        stats = scaffolder.stats()
        assert stats["skills_created"] == 1
        assert stats["templates"] >= 3

    def test_scaffold_result_to_dict(self, tmp_path: Path) -> None:
        scaffolder = SkillScaffolder()
        result = scaffolder.scaffold("Dict Test", base_dir=str(tmp_path / "skills"))
        d = result.to_dict()
        assert d["skill"] == "Dict Test"
        assert "slug" in d

    def test_scaffold_with_description(self, tmp_path: Path) -> None:
        scaffolder = SkillScaffolder()
        result = scaffolder.scaffold(
            "Desc Test",
            description="My description",
            base_dir=str(tmp_path / "skills"),
        )
        # Check files contain the description
        for fpath in result.files_created:
            content = Path(fpath).read_text(encoding="utf-8")
            if "My description" in content:
                break
        else:
            pytest.fail("Description not found in any created file")


# ============================================================================
# SkillLinter — additional coverage
# ============================================================================


class TestSkillLinterExtended:
    def test_lint_missing_all_files(self) -> None:
        linter = SkillLinter()
        issues = linter.lint({})
        errors = [i for i in issues if i.severity == LintSeverity.ERROR]
        assert len(errors) == 3  # SKILL.md, skill.py, manifest.json

    def test_lint_short_skill_md(self) -> None:
        linter = SkillLinter()
        issues = linter.lint(
            {
                "SKILL.md": "short",
                "skill.py": "class Foo(BaseSkill): pass",
                "manifest.json": '{"name": "x", "version": "1", "permissions": []}',
            }
        )
        warnings = [i for i in issues if i.rule == "short-docs"]
        assert len(warnings) == 1

    def test_lint_missing_description_heading(self) -> None:
        linter = SkillLinter()
        issues = linter.lint(
            {
                "SKILL.md": "# My Skill\n\nSome content that is long"
                " enough to pass the length check " * 3,
                "skill.py": "class Foo(BaseSkill): pass",
                "manifest.json": '{"name": "x", "version": "1", "permissions": []}',
            }
        )
        desc_issues = [i for i in issues if i.rule == "missing-description"]
        assert len(desc_issues) == 1

    def test_lint_missing_manifest_fields(self) -> None:
        linter = SkillLinter()
        issues = linter.lint(
            {
                "SKILL.md": "## Beschreibung\n" + "x" * 100,
                "skill.py": "class Foo(BaseSkill): pass",
                "manifest.json": "{}",
            }
        )
        manifest_issues = [i for i in issues if i.rule == "missing-manifest-field"]
        assert len(manifest_issues) == 3

    def test_lint_no_tests(self) -> None:
        linter = SkillLinter()
        issues = linter.lint(
            {
                "SKILL.md": "## Beschreibung\n" + "x" * 100,
                "skill.py": "class Foo(BaseSkill): pass",
                "manifest.json": '{"name": "x", "version": "1", "permissions": []}',
            }
        )
        test_issues = [i for i in issues if i.rule == "no-tests"]
        assert len(test_issues) == 1

    def test_lint_no_base_class(self) -> None:
        linter = SkillLinter()
        issues = linter.lint(
            {
                "SKILL.md": "## Beschreibung\n" + "x" * 100,
                "skill.py": "class Foo: pass",
                "manifest.json": '{"name": "x", "version": "1", "permissions": []}',
                "test_skill.py": "def test_x(): pass",
            }
        )
        base_issues = [i for i in issues if i.rule == "no-base-class"]
        assert len(base_issues) == 1

    def test_is_valid_true(self) -> None:
        linter = SkillLinter()
        valid = linter.is_valid(
            {
                "SKILL.md": "## Beschreibung\n" + "x" * 100,
                "skill.py": "class Foo(BaseSkill): pass",
                "manifest.json": '{"name": "x", "version": "1", "permissions": []}',
                "test_skill.py": "def test_x(): pass",
            }
        )
        assert valid is True

    def test_is_valid_false(self) -> None:
        linter = SkillLinter()
        assert linter.is_valid({}) is False

    def test_lint_issue_to_dict(self) -> None:
        issue = LintIssue("rule1", LintSeverity.WARNING, "msg", "file.py")
        d = issue.to_dict()
        assert d["rule"] == "rule1"
        assert d["severity"] == "warning"


# ============================================================================
# SkillPublisher — additional coverage
# ============================================================================


class TestSkillPublisherExtended:
    def test_submit_without_checks_fails(self) -> None:
        pub = SkillPublisher()
        req = pub.create_request("s", "1.0", "dev")
        assert pub.submit(req.request_id) is False

    def test_publish_without_security_fails(self) -> None:
        pub = SkillPublisher()
        req = pub.create_request("s", "1.0", "dev")
        pub.run_checks(req.request_id, lint=True, tests=True)
        assert pub.submit(req.request_id) is True
        assert pub.publish(req.request_id) is False

    def test_full_publish_flow(self) -> None:
        pub = SkillPublisher()
        req = pub.create_request("s", "1.0", "dev")
        pub.run_checks(req.request_id, lint=True, tests=True, security=True)
        assert pub.submit(req.request_id) is True
        assert pub.publish(req.request_id) is True
        assert req.status == PublishStatus.PUBLISHED

    def test_reject(self) -> None:
        pub = SkillPublisher()
        req = pub.create_request("s", "1.0", "dev")
        assert pub.reject(req.request_id, "bad") is True
        assert req.status == PublishStatus.REJECTED

    def test_reject_nonexistent(self) -> None:
        pub = SkillPublisher()
        assert pub.reject("ghost", "reason") is False

    def test_run_checks_nonexistent(self) -> None:
        pub = SkillPublisher()
        assert pub.run_checks("ghost", lint=True) is False

    def test_pending(self) -> None:
        pub = SkillPublisher()
        req = pub.create_request("s", "1.0", "dev")
        pub.run_checks(req.request_id, lint=True, tests=True)
        pub.submit(req.request_id)
        assert len(pub.pending()) == 1

    def test_stats(self) -> None:
        pub = SkillPublisher()
        pub.create_request("a", "1.0", "dev")
        stats = pub.stats()
        assert stats["total_requests"] == 1

    def test_publish_request_can_submit(self) -> None:
        req = PublishRequest("PUB-0001", "test", "1.0", "dev")
        assert req.can_submit is False
        req.lint_passed = True
        req.tests_passed = True
        assert req.can_submit is True

    def test_publish_request_can_publish(self) -> None:
        req = PublishRequest("PUB-0001", "test", "1.0", "dev")
        req.lint_passed = True
        req.tests_passed = True
        req.security_scan_passed = True
        assert req.can_publish is True

    def test_publish_request_to_dict(self) -> None:
        req = PublishRequest("PUB-0001", "test", "1.0", "dev")
        d = req.to_dict()
        assert d["id"] == "PUB-0001"
        assert d["skill"] == "test"


# ============================================================================
# RewardSystem — additional coverage
# ============================================================================


class TestRewardSystemExtended:
    def test_award_skill_published(self) -> None:
        rs = RewardSystem()
        pts = rs.award_points("dev1", "skill_published")
        assert pts == 100
        cr = rs.get_or_create("dev1")
        # First skill bonus: 200 extra
        assert cr.points == 300

    def test_five_skills_badge(self) -> None:
        rs = RewardSystem()
        for _ in range(5):
            rs.award_points("dev1", "skill_published")
        cr = rs.get_or_create("dev1")
        assert any("5 Skills" in b for b in cr.badges)

    def test_ten_skills_badge(self) -> None:
        rs = RewardSystem()
        for _ in range(10):
            rs.award_points("dev1", "skill_published")
        cr = rs.get_or_create("dev1")
        assert any("10 Skills" in b for b in cr.badges)

    def test_reviewer_badge(self) -> None:
        rs = RewardSystem()
        for _ in range(5):
            rs.award_points("dev1", "review_given")
        cr = rs.get_or_create("dev1")
        assert any("Reviewer" in b for b in cr.badges)

    def test_expert_badge(self) -> None:
        rs = RewardSystem()
        for _ in range(10):
            rs.award_points("dev1", "skill_published")
        cr = rs.get_or_create("dev1")
        assert any("Experte" in b for b in cr.badges)

    def test_unknown_action(self) -> None:
        rs = RewardSystem()
        pts = rs.award_points("dev1", "unknown_action")
        assert pts == 0

    def test_leaderboard(self) -> None:
        rs = RewardSystem()
        rs.award_points("dev1", "skill_published")
        rs.award_points("dev2", "review_given")
        lb = rs.leaderboard(top_n=10)
        assert len(lb) == 2
        assert lb[0].points >= lb[1].points

    def test_contributor_levels(self) -> None:
        cr = ContributorReward(contributor="test")
        assert cr.level == "beginner"
        cr.points = 100
        assert cr.level == "intermediate"
        cr.points = 500
        assert cr.level == "advanced"
        cr.points = 1000
        assert cr.level == "expert"

    def test_contributor_to_dict(self) -> None:
        cr = ContributorReward(contributor="test", points=150, skills_published=2)
        d = cr.to_dict()
        assert d["contributor"] == "test"
        assert d["level"] == "intermediate"

    def test_stats(self) -> None:
        rs = RewardSystem()
        rs.award_points("dev1", "skill_published")
        stats = rs.stats()
        assert stats["contributors"] == 1
        assert stats["total_skills"] == 1
        assert stats["top_contributor"] == "dev1"

    def test_stats_empty(self) -> None:
        rs = RewardSystem()
        stats = rs.stats()
        assert stats["top_contributor"] is None


# ============================================================================
# SkillCLI — additional coverage
# ============================================================================


class TestSkillCLIExtended:
    def test_cmd_new(self) -> None:
        cli = SkillCLI()
        cli._scaffolder = SkillScaffolder()
        result = cli.cmd_new("Test")
        assert isinstance(result, ScaffoldResult)
        assert result.skill_name == "Test"

    def test_cmd_lint(self) -> None:
        cli = SkillCLI()
        issues = cli.cmd_lint({"SKILL.md": "short"})
        assert isinstance(issues, list)

    def test_cmd_publish(self) -> None:
        cli = SkillCLI()
        req = cli.cmd_publish("s", "1.0", "dev")
        assert isinstance(req, PublishRequest)

    def test_full_pipeline_success(self, tmp_path: Path) -> None:
        cli = SkillCLI()
        files = {
            "SKILL.md": "## Beschreibung\n" + "x" * 100,
            "skill.py": "class Foo(BaseSkill): pass",
            "manifest.json": '{"name": "x", "version": "1", "permissions": []}',
            "test_skill.py": "def test_x(): assert True\n",
        }
        result = cli.full_pipeline("test-skill", "1.0", "dev", files)
        assert "lint" in result
        assert "test" in result
        assert "publish" in result

    def test_stats(self) -> None:
        cli = SkillCLI()
        stats = cli.stats()
        assert "scaffolder" in stats
        assert "tester" in stats
        assert "publisher" in stats
        assert "rewards" in stats

    def test_properties(self) -> None:
        cli = SkillCLI()
        assert cli.scaffolder is not None
        assert cli.linter is not None
        assert cli.tester is not None
        assert cli.publisher is not None
        assert cli.rewards is not None


# ============================================================================
# SkillTester — additional coverage
# ============================================================================


class TestSkillTesterExtended:
    def test_test_no_tests(self) -> None:
        tester = SkillTester()
        result = tester.test_skill("empty", "x = 1")
        assert result.total_tests == 0
        assert result.success is False

    def test_pass_rate_empty(self) -> None:
        tester = SkillTester()
        assert tester.pass_rate() == 0.0

    def test_all_results(self) -> None:
        tester = SkillTester()
        tester.test_skill("a", "")
        tester.test_skill("b", "")
        assert len(tester.all_results()) == 2

    def test_stats(self) -> None:
        tester = SkillTester()
        tester.test_skill("a", "")
        stats = tester.stats()
        assert stats["total_runs"] == 1

    def test_test_result_to_dict(self) -> None:
        r = SkillTestResult(skill_name="t", total_tests=2, passed=1, failed=1)
        d = r.to_dict()
        assert d["skill"] == "t"
        assert d["total"] == 2


# ============================================================================
# SkillTemplate
# ============================================================================


class TestSkillTemplate:
    def test_to_dict(self) -> None:
        t = BUILT_IN_TEMPLATES[TemplateType.BASIC]
        d = t.to_dict()
        assert d["template_id"] == "TPL-BASIC"
        assert "files" in d
        assert "deps" in d
