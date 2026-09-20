from workflow_core.providers_fake import FakeGitHubProvider, FakePyPIProvider
from workflow_core.research import ResearchRequest
from workflow_core.research_engine import ResearchEngine


def test_fake_github_provider() -> None:
    provider = FakeGitHubProvider()
    request = ResearchRequest(
        research_id="r1",
        objective="test objective",
        component="core",
        minimum_sources=3,
    )
    findings = provider.search(request, limit=3)
    assert len(findings) == 3
    assert all(f.source == "github" for f in findings)


def test_fake_providers_with_engine() -> None:
    gh = FakeGitHubProvider()
    pypi = FakePyPIProvider()
    request = ResearchRequest(
        research_id="r2",
        objective="combine",
        component="core",
        minimum_sources=4,
    )
    findings = list(gh.search(request, limit=3)) + list(pypi.search(request, limit=2))
    result = ResearchEngine().run(request, findings)
    assert result.complete is True
    assert len(result.findings) == 5
