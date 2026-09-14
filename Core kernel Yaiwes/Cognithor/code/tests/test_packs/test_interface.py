"""Tests for cognithor.packs.interface — PackManifest + AgentPack base."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from cognithor.packs.interface import (
    AgentPack,
    PackContext,
    PackManifest,
    PricingTier,
    Publisher,
    RevenueShare,
)


def _minimal_manifest_dict(**overrides: Any) -> dict[str, Any]:
    """Minimal valid manifest dict for a free pack. Use overrides to specialize."""
    base = {
        "schema_version": 1,
        "namespace": "cognithor-official",
        "pack_id": "test-pack",
        "version": "1.0.0",
        "display_name": "Test Pack",
        "description": "A test pack",
        "license": "apache-2.0",
        "min_cognithor_version": ">=0.92.0",
        "eula_sha256": "a" * 64,
        "publisher": {
            "id": "cognithor-official",
            "display_name": "Cognithor",
        },
    }
    base.update(overrides)
    return base


def _minimal_paid_manifest_dict(**overrides: Any) -> dict[str, Any]:
    base = _minimal_manifest_dict(license="proprietary")
    base["pricing"] = {
        "indie": {
            "list_price": 149,
            "launch_price": 79,
            "post_launch_price": 99,
            "launch_cap": 100,
            "currency": "USD",
        }
    }
    base.update(overrides)
    return base


class TestPublisher:
    def test_minimal_publisher(self) -> None:
        p = Publisher(id="alex", display_name="Alex")
        assert p.id == "alex"
        assert p.website is None

    def test_publisher_id_required(self) -> None:
        with pytest.raises(ValidationError):
            Publisher(display_name="x")  # type: ignore[call-arg]


class TestRevenueShare:
    def test_default_is_70_30(self) -> None:
        rs = RevenueShare()
        assert rs.creator == 70
        assert rs.platform == 30

    def test_custom(self) -> None:
        rs = RevenueShare(creator=80, platform=20)
        assert rs.creator == 80

    def test_must_sum_to_100(self) -> None:
        with pytest.raises(ValidationError):
            RevenueShare(creator=60, platform=30)


class TestPricingTier:
    def test_minimal(self) -> None:
        t = PricingTier(list_price=149, launch_price=79, post_launch_price=99, launch_cap=100)
        assert t.currency == "USD"
        assert t.launch_price == 79


class TestPackManifest:
    def test_minimal_free_pack(self) -> None:
        m = PackManifest(**_minimal_manifest_dict())
        assert m.namespace == "cognithor-official"
        assert m.pack_id == "test-pack"
        assert m.revenue_share.creator == 70  # default
        assert m.entrypoint == "pack.py"
        assert m.pricing == {}

    def test_qualified_id(self) -> None:
        m = PackManifest(**_minimal_manifest_dict())
        assert m.qualified_id == "cognithor-official/test-pack"

    def test_eula_hash_must_be_hex_64(self) -> None:
        with pytest.raises(ValidationError):
            PackManifest(**_minimal_manifest_dict(eula_sha256="notahash"))

    def test_namespace_slash_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            PackManifest(**_minimal_manifest_dict(namespace="bad/ns"))

    def test_pack_id_slash_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            PackManifest(**_minimal_manifest_dict(pack_id="bad/id"))

    def test_version_semver(self) -> None:
        with pytest.raises(ValidationError):
            PackManifest(**_minimal_manifest_dict(version="not-semver"))

    def test_pricing_required_for_paid_license(self) -> None:
        # proprietary license without pricing must fail
        bad = _minimal_manifest_dict(license="proprietary")
        with pytest.raises(ValidationError):
            PackManifest(**bad)

    def test_pricing_optional_for_free_license(self) -> None:
        m = PackManifest(**_minimal_manifest_dict())
        assert m.pricing == {}

    def test_full_paid_manifest(self) -> None:
        m = PackManifest(**_minimal_paid_manifest_dict())
        assert "indie" in m.pricing
        assert m.pricing["indie"].launch_price == 79

    def test_json_round_trip(self) -> None:
        m = PackManifest(**_minimal_manifest_dict())
        s = m.model_dump_json()
        m2 = PackManifest.model_validate_json(s)
        assert m2 == m


class _ConcretePack(AgentPack):
    def __init__(self, manifest: PackManifest) -> None:
        super().__init__(manifest)
        self.registered = False

    def register(self, context: PackContext) -> None:
        self.registered = True


class TestAgentPack:
    def test_concrete_pack_can_register(self) -> None:
        manifest = PackManifest(**_minimal_manifest_dict())
        pack = _ConcretePack(manifest)
        pack.register(PackContext())
        assert pack.registered is True

    def test_unregister_default_is_noop(self) -> None:
        manifest = PackManifest(**_minimal_manifest_dict())
        pack = _ConcretePack(manifest)
        # Should not raise
        pack.unregister(PackContext())
