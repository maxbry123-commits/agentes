import pytest

from runtime.src.core.reuse_selector import (
    CatalogValidationError,
    ReuseCandidate,
    ReuseDecision,
    select_reuse,
    validate_catalog,
)


def _candidate(**overrides):
    base = {
        "candidate_id": "C01",
        "name": "local",
        "source_url": "https://example.com/local",
        "license": "PROJECT_INTERNAL",
        "maintenance": "CURRENT_LOCAL",
        "compatibility": "NATIVE",
        "risk": "LOW",
        "footprint": "SMALL",
        "capabilities": ["dag"],
        "local": True,
        "patchable": True,
    }
    base.update(overrides)
    return ReuseCandidate.from_mapping(base)


def test_local_native_wins_reuse():
    local = _candidate()
    external = _candidate(
        candidate_id="C02",
        name="external",
        source_url="https://example.com/external",
        license="MIT",
        maintenance="ACTIVE",
        compatibility="HIGH",
        local=False,
        patchable=False,
    )
    result = select_reuse("dag", [external, local])
    assert result.decision is ReuseDecision.REUSE
    assert result.candidate_id == "C01"


def test_external_match_requires_adapt():
    external = _candidate(
        candidate_id="C02",
        name="external",
        source_url="https://example.com/external",
        license="MIT",
        maintenance="ACTIVE",
        compatibility="HIGH",
        local=False,
        patchable=False,
    )
    result = select_reuse("dag", [external])
    assert result.decision is ReuseDecision.ADAPT


def test_no_match_allows_generate_only_after_research():
    result = select_reuse("missing", [_candidate()])
    assert result.decision is ReuseDecision.GENERATE
    assert result.reason == "NO_MATCHING_CANDIDATE_AFTER_RESEARCH"


def test_high_risk_forces_more_research():
    risky = _candidate(risk="HIGH")
    result = select_reuse("dag", [risky])
    assert result.decision is ReuseDecision.RESEARCH_MORE


def test_catalog_max_10_and_unique_ids():
    items = []
    for index in range(10):
        items.append({
            "candidate_id": f"C{index}",
            "name": f"candidate-{index}",
            "source_url": f"https://example.com/{index}",
            "license": "MIT",
            "maintenance": "ACTIVE",
            "compatibility": "MEDIUM",
            "risk": "LOW",
            "footprint": "SMALL",
            "capabilities": ["x"],
        })
    assert len(validate_catalog(items)) == 10
    with pytest.raises(CatalogValidationError):
        validate_catalog(items + [dict(items[0], candidate_id="C10")])
    with pytest.raises(CatalogValidationError):
        validate_catalog([items[0], dict(items[0])])


def test_invalid_source_or_missing_license_fails_closed():
    with pytest.raises(CatalogValidationError):
        _candidate(source_url="relative/path")
    with pytest.raises(CatalogValidationError):
        _candidate(license="")
