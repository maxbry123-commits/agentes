"""Abstract base class for lead sources.

A ``LeadSource`` represents one origin for leads (Reddit, Hacker News,
Discord, RSS, etc.). Source implementations live in agent packs and
register with the ``SourceRegistry`` via ``PackContext.leads.register_source``
during ``AgentPack.register()``.

Required metadata (ClassVars on concrete subclasses):

- ``source_id`` — stable short identifier, used as a key in the registry and
  persisted on every ``Lead`` record. Must be unique across all registered
  sources.
- ``display_name`` — human-friendly name for UI.
- ``icon`` — Material icon name (e.g. ``"forum"``, ``"rss_feed"``) OR data URL.
- ``color`` — hex color string for UI accents (e.g. ``"#FF4500"`` for Reddit).
- ``capabilities`` — frozen set of capability strings. Known values:
  ``"scan"`` (always required), ``"draft_reply"``, ``"refine_reply"``,
  ``"auto_post"``, ``"discover_targets"``.

Required methods:

- ``scan(config, product, product_description, min_score)`` — fetch posts from
  the source, score them via LLM, return ``list[Lead]``.

Optional methods (default to ``NotImplementedError``; callers check
``capabilities`` before invoking):

- ``draft_reply(lead, tone)`` — generate a reply draft for a lead.
- ``refine_reply(lead, draft)`` — refine an existing reply draft.
- ``post_reply(lead, text)`` — actually post the reply (e.g. via browser
  automation).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from cognithor.leads.models import Lead


class LeadSource(ABC):
    """Abstract lead source — one per origin (Reddit, HN, Discord, RSS, ...)."""

    source_id: ClassVar[str]
    display_name: ClassVar[str]
    icon: ClassVar[str]
    color: ClassVar[str]
    capabilities: ClassVar[frozenset[str]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # ABCMeta computes ``__abstractmethods__`` after ``__init_subclass__``
        # runs, so we inspect it at the start of ``__init__`` below. Here we
        # only short-circuit when the subclass is itself still abstract — i.e.
        # it does not provide its own ``scan`` anywhere in its MRO above
        # ``LeadSource`` — in which case the ClassVar checks don't apply yet.
        for base in cls.__mro__:
            if base is LeadSource:
                break
            if "scan" in base.__dict__:
                break
        else:
            # No concrete ``scan`` between cls and LeadSource: cls is abstract.
            return
        required = ("source_id", "display_name", "icon", "color", "capabilities")
        for attr in required:
            if not hasattr(cls, attr) or getattr(cls, attr) is None:
                raise TypeError(f"LeadSource subclass {cls.__name__} must set class attr {attr!r}")

    @abstractmethod
    async def scan(
        self,
        *,
        config: dict[str, Any],
        product: str,
        product_description: str,
        min_score: int,
    ) -> list[Lead]:
        """Fetch, score, and return leads from this source.

        ``config`` is the source-specific config dict (e.g. for Reddit it
        contains ``subreddits``, ``reply_tone``, etc.). ``product`` and
        ``product_description`` drive LLM scoring. ``min_score`` filters
        out low-intent posts.
        """

    async def draft_reply(self, lead: Lead, *, tone: str) -> str:
        """Generate a reply draft. Default: raises ``NotImplementedError``."""
        raise NotImplementedError(
            f"{self.source_id}: draft_reply not implemented (capability not declared)"
        )

    async def refine_reply(self, lead: Lead, draft: str) -> str:
        """Refine an existing draft. Default: raises ``NotImplementedError``."""
        raise NotImplementedError(f"{self.source_id}: refine_reply not implemented")

    async def post_reply(self, lead: Lead, text: str) -> None:
        """Post a reply to the external platform. Default: raises ``NotImplementedError``."""
        raise NotImplementedError(f"{self.source_id}: post_reply not implemented")
