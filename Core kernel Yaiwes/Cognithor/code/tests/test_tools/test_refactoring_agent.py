"""Tests fuer tools/refactoring_agent.py -- RefactoringAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from cognithor.models import ArchitectureFinding, CodeSmell, RefactoringReport
from cognithor.tools.refactoring_agent import RefactoringAgent

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_code_detector() -> MagicMock:
    detector = MagicMock()
    detector.analyze_directory.return_value = [
        CodeSmell(
            file_path="test.py",
            line=10,
            smell_type="long_function",
            severity="warning",
            message="Function foo is 60 lines",
            suggestion="Split into smaller functions",
        ),
        CodeSmell(
            file_path="test.py",
            line=50,
            smell_type="deep_nesting",
            severity="warning",
            message="Function bar has nesting 5",
        ),
    ]
    return detector


@pytest.fixture
def mock_arch_analyzer() -> MagicMock:
    analyzer = MagicMock()
    analyzer.build_import_graph.return_value = 10
    analyzer.detect_circular_imports.return_value = [
        ArchitectureFinding(
            finding_type="circular_import",
            severity="error",
            modules=["a", "b"],
            message="Circular: a -> b -> a",
        ),
    ]
    analyzer.detect_layer_violations.return_value = []
    return analyzer


@pytest.fixture
def agent(mock_code_detector: MagicMock, mock_arch_analyzer: MagicMock) -> RefactoringAgent:
    return RefactoringAgent(
        code_detector=mock_code_detector,
        arch_analyzer=mock_arch_analyzer,
    )


@pytest.fixture
def src_dir(tmp_path: Path) -> Path:
    d = tmp_path / "src"
    d.mkdir()
    (d / "main.py").write_text("x = 1\n", encoding="utf-8")
    (d / "utils.py").write_text("y = 2\n", encoding="utf-8")
    return d


# ============================================================================
# RefactoringAgent.run_analysis
# ============================================================================


class TestRunAnalysis:
    def test_returns_report(self, agent: RefactoringAgent, src_dir: Path) -> None:
        report = agent.run_analysis(src_dir)
        assert isinstance(report, RefactoringReport)

    def test_report_contains_code_smells(self, agent: RefactoringAgent, src_dir: Path) -> None:
        report = agent.run_analysis(src_dir)
        assert len(report.code_smells) == 2
        assert report.code_smells[0].smell_type == "long_function"

    def test_report_contains_arch_findings(self, agent: RefactoringAgent, src_dir: Path) -> None:
        report = agent.run_analysis(src_dir)
        assert len(report.architecture_findings) == 1
        assert report.architecture_findings[0].finding_type == "circular_import"

    def test_report_summary(self, agent: RefactoringAgent, src_dir: Path) -> None:
        report = agent.run_analysis(src_dir)
        assert "Code-Smells: 2" in report.summary
        assert "Architektur-Findings: 1" in report.summary

    def test_report_counts_py_files(self, agent: RefactoringAgent, src_dir: Path) -> None:
        report = agent.run_analysis(src_dir)
        assert report.total_files_analyzed == 2

    def test_excludes_pycache(self, agent: RefactoringAgent, src_dir: Path) -> None:
        pycache = src_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "cached.py").write_text("x = 1\n", encoding="utf-8")
        report = agent.run_analysis(src_dir)
        assert report.total_files_analyzed == 2  # pycache excluded

    def test_accepts_string_path(self, agent: RefactoringAgent, src_dir: Path) -> None:
        report = agent.run_analysis(str(src_dir))
        assert isinstance(report, RefactoringReport)


class TestRunAnalysisNoSmells:
    def test_no_code_smells_message(self, mock_arch_analyzer: MagicMock, src_dir: Path) -> None:
        detector = MagicMock()
        detector.analyze_directory.return_value = []
        agent = RefactoringAgent(code_detector=detector, arch_analyzer=mock_arch_analyzer)
        mock_arch_analyzer.detect_circular_imports.return_value = []
        report = agent.run_analysis(src_dir)
        assert "Keine gefunden" in report.summary

    def test_no_arch_findings_message(self, mock_code_detector: MagicMock, src_dir: Path) -> None:
        analyzer = MagicMock()
        analyzer.build_import_graph.return_value = 5
        analyzer.detect_circular_imports.return_value = []
        analyzer.detect_layer_violations.return_value = []
        agent = RefactoringAgent(code_detector=mock_code_detector, arch_analyzer=analyzer)
        report = agent.run_analysis(src_dir)
        assert "Keine Probleme" in report.summary


# ============================================================================
# RefactoringAgent.get_priority_issues
# ============================================================================


class TestGetPriorityIssues:
    def test_returns_sorted_issues(self, agent: RefactoringAgent, src_dir: Path) -> None:
        report = agent.run_analysis(src_dir)
        issues = agent.get_priority_issues(report)
        # arch finding (error) should come before code smells (warning)
        assert issues[0]["type"] == "architecture"
        assert issues[0]["severity"] == "error"

    def test_respects_n_limit(self, agent: RefactoringAgent, src_dir: Path) -> None:
        report = agent.run_analysis(src_dir)
        issues = agent.get_priority_issues(report, n=1)
        assert len(issues) == 1

    def test_issue_contains_required_fields(self, agent: RefactoringAgent, src_dir: Path) -> None:
        report = agent.run_analysis(src_dir)
        issues = agent.get_priority_issues(report)
        for issue in issues:
            assert "type" in issue
            assert "subtype" in issue
            assert "severity" in issue
            assert "message" in issue
            assert "sort_key" in issue

    def test_code_smell_has_file_and_line(self, agent: RefactoringAgent, src_dir: Path) -> None:
        report = agent.run_analysis(src_dir)
        issues = agent.get_priority_issues(report)
        code_issues = [i for i in issues if i["type"] == "code_smell"]
        assert len(code_issues) >= 1
        assert code_issues[0]["file"] == "test.py"
        assert code_issues[0]["line"] == 10

    def test_empty_report(self) -> None:
        agent = RefactoringAgent(
            code_detector=MagicMock(analyze_directory=MagicMock(return_value=[])),
            arch_analyzer=MagicMock(
                build_import_graph=MagicMock(return_value=0),
                detect_circular_imports=MagicMock(return_value=[]),
                detect_layer_violations=MagicMock(return_value=[]),
            ),
        )
        report = RefactoringReport(
            code_smells=[],
            architecture_findings=[],
            summary="Empty",
            total_files_analyzed=0,
        )
        issues = agent.get_priority_issues(report)
        assert issues == []

    def test_unknown_severity_gets_high_sort_key(
        self, agent: RefactoringAgent, src_dir: Path
    ) -> None:
        report = agent.run_analysis(src_dir)
        # Add a smell with unknown severity
        report.code_smells.append(
            CodeSmell(
                file_path="x.py",
                line=1,
                smell_type="unknown",
                severity="unknown",
                message="test",
            )
        )
        issues = agent.get_priority_issues(report)
        unknown = [i for i in issues if i["severity"] == "unknown"]
        assert len(unknown) == 1
        assert unknown[0]["sort_key"] == 9


# ============================================================================
# Default Constructor
# ============================================================================


class TestDefaultConstructor:
    def test_default_creates_detector_and_analyzer(self) -> None:
        agent = RefactoringAgent()
        assert agent._code_detector is not None
        assert agent._arch_analyzer is not None
