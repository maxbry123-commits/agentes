from workflow_core.research import ResearchFinding, ResearchRequest
from workflow_core.research_engine import ResearchEngine
from workflow_core.skills import SkillRequirement


def test_research_engine_incomplete() -> None:
    engine = ResearchEngine()
    request = ResearchRequest(
        research_id="r1",
        objective="test",
        component="core",
        minimum_sources=20,
    )
    findings = [
        ResearchFinding(
            finding_id="f1",
            source="github",
            url="https://example.com",
            repository="owner/repo",
            version="1.0",
            commit="abc123",
            finding="example",
        )
    ]
    result = engine.run(request, findings)
    assert result.complete is False
    assert len(result.findings) == 1


def test_research_engine_complete() -> None:
    engine = ResearchEngine()
    request = ResearchRequest(
        research_id="r2",
        objective="test",
        component="core",
        minimum_sources=2,
    )
    findings = [
        ResearchFinding(
            finding_id=f"f{i}",
            source="github",
            url=f"https://example.com/{i}",
            repository="owner/repo",
            version="1.0",
            commit="abc",
            finding="x",
        )
        for i in range(3)
    ]
    result = engine.run(request, findings, skills=[SkillRequirement("python")])
    assert result.complete is True
    assert len(result.resolved) == 3
    assert result.context.objective == "test"
