from workflow_core.mirror import RepositoryMirror
from workflow_core.research import ResearchFinding, ResearchRequest
from workflow_core.research_engine import ResearchEngine
from workflow_core.research_sheriff import ResearchSheriff
from workflow_core.resolver import ResolvedRepository


def test_mirror_path() -> None:
    mirror = RepositoryMirror(base_dir="/tmp/mirrors")
    resolved = ResolvedRepository(
        repository="owner/repo",
        commit="abc",
        version="1.0",
        source_url="https://github.com/owner/repo",
    )
    record = mirror.register(resolved, category="backend")
    assert "owner__repo" in record.local_path
    assert record.commit == "abc"


def test_research_sheriff_rejects_incomplete() -> None:
    engine = ResearchEngine()
    request = ResearchRequest(
        research_id="r1", objective="x", component="c", minimum_sources=5
    )
    findings = [
        ResearchFinding(
            finding_id="f1",
            source="gh",
            url="https://x.com",
            repository="o/r",
            version=None,
            commit=None,
            finding="f",
            evidence=(),
        )
    ]
    result = engine.run(request, findings)
    decision = ResearchSheriff().inspect(result)
    assert decision.allowed is False
