"""Jarvis Skills package.

This package contains utility functions for managing additional
procedures ("Skills"). Skills are Markdown files with
frontmatter that define trigger keywords, prerequisites, and step-by-step
instructions. They are stored in the ``skills`` directory
within the Cognithor home and automatically loaded at startup.

The CLI module ``jarvis.skills.cli`` can be used to list,
create, or install skills.
"""

from .base import BaseSkill, SkillError
from .circles import CircleManager, TrustedCircle
from .ecosystem_control import (
    EcosystemController,
    FraudDetector,
    SecurityTrainer,
    SkillCurator,
    TrustBoundaryManager,
)
from .governance import (
    AbuseReporter,
    GovernancePolicy,
    ReputationEngine,
    SkillRecallManager,
)
from .hermes_compat import HermesCompatLayer, HermesSkill
from .manager import create_skill, list_skills
from .marketplace import SkillMarketplace
from .persistence import MarketplaceStore
from .registry import SkillRegistry
from .seed_data import seed_marketplace
from .updater import SkillUpdater
