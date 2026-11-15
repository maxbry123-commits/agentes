"""Integration tests for IdentityLayer hooks in Gateway."""

from __future__ import annotations


class TestIdentityConfig:
    """Tests for IdentityConfig in CognithorConfig."""

    def test_identity_config_exists(self) -> None:
        import tempfile

        from cognithor.config import CognithorConfig, IdentityConfig

        cfg = CognithorConfig(cognithor_home=tempfile.mkdtemp())
        assert hasattr(cfg, "identity")
        assert isinstance(cfg.identity, IdentityConfig)

    def test_identity_enabled_default(self) -> None:
        from cognithor.config import IdentityConfig

        ic = IdentityConfig()
        assert ic.enabled is True
        assert ic.identity_id == "jarvis"
        assert ic.checkpoint_every_n == 5
        assert ic.blockchain_enabled is False

    def test_identity_disabled(self) -> None:
        from cognithor.config import IdentityConfig

        ic = IdentityConfig(enabled=False)
        assert ic.enabled is False


class TestGatekeeperGenesisAnchors:
    """Tests for Genesis Anchor policy in Gatekeeper."""

    def test_genesis_anchors_count(self) -> None:
        from cognithor.identity.cognitio.engine import GENESIS_ANCHOR_CONTENTS

        assert len(GENESIS_ANCHOR_CONTENTS) == 7

    def test_genesis_anchors_immutable_content(self) -> None:
        from cognithor.identity.cognitio.engine import GENESIS_ANCHOR_CONTENTS

        # Anchor 0: No harm
        assert "harm" in GENESIS_ANCHOR_CONTENTS[0].lower()
        # Anchor 1: No deception
        assert (
            "truth" in GENESIS_ANCHOR_CONTENTS[1].lower()
            or "distort" in GENESIS_ANCHOR_CONTENTS[1].lower()
        )
        # Anchor 3: No illegal content
        assert (
            "illegal" in GENESIS_ANCHOR_CONTENTS[3].lower()
            or "harmful" in GENESIS_ANCHOR_CONTENTS[3].lower()
        )

    def test_gatekeeper_identity_tools_green(self) -> None:
        """Identity tools should be classified as GREEN."""
        import tempfile

        from cognithor.config import CognithorConfig
        from cognithor.core.gatekeeper import Gatekeeper
        from cognithor.models import PlannedAction, RiskLevel

        cfg = CognithorConfig(cognithor_home=tempfile.mkdtemp())
        gk = Gatekeeper(cfg)

        for tool in ["identity_recall", "identity_state", "identity_reflect", "identity_dream"]:
            action = PlannedAction(tool=tool, params={})
            assert gk._classify_risk(action) == RiskLevel.GREEN, f"{tool} should be GREEN"


class TestIdentityPhaseInit:
    """Tests for Phase 9 identity initialization."""

    def test_pge_attrs_include_identity(self) -> None:
        """declare_pge_attrs should include identity_layer."""
        import tempfile

        from cognithor.config import CognithorConfig
        from cognithor.gateway.phases.pge import declare_pge_attrs

        cfg = CognithorConfig(cognithor_home=tempfile.mkdtemp())
        attrs = declare_pge_attrs(cfg)
        assert "identity_layer" in attrs


class TestIdentityLayerLifecycle:
    """Tests for IdentityLayer lifecycle methods."""

    def test_freeze_unfreeze(self) -> None:
        from cognithor.identity import IdentityLayer

        il = IdentityLayer.__new__(IdentityLayer)
        il._engine = None
        il._frozen = False
        il._identity_id = "test"

        il.freeze()
        assert il._frozen is True
        assert not il.available

        il.unfreeze()
        assert il._frozen is False

    def test_empty_enrichment_when_unavailable(self) -> None:
        from cognithor.identity import IdentityLayer

        il = IdentityLayer.__new__(IdentityLayer)
        il._engine = None
        il._frozen = False
        il._identity_id = "test"

        result = il.enrich_context("hello")
        assert result["cognitive_context"] == ""
        assert result["temperature_modifier"] == 0.0

    def test_process_interaction_when_unavailable(self) -> None:
        from cognithor.identity import IdentityLayer

        il = IdentityLayer.__new__(IdentityLayer)
        il._engine = None
        il._frozen = False
        il._identity_id = "test"

        result = il.process_interaction("user", "hello")
        assert result == {}

    def test_recall_when_unavailable(self) -> None:
        from cognithor.identity import IdentityLayer

        il = IdentityLayer.__new__(IdentityLayer)
        il._engine = None
        il._frozen = False
        il._identity_id = "test"

        result = il.recall_for_cognithor("test query")
        assert result == []

    def test_state_summary_when_unavailable(self) -> None:
        from cognithor.identity import IdentityLayer

        il = IdentityLayer.__new__(IdentityLayer)
        il._engine = None
        il._frozen = False
        il._identity_id = "test"

        state = il.get_state_summary()
        assert state["available"] is False
