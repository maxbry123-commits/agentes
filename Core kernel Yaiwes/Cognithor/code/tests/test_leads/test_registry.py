"""Tests for cognithor.leads.registry — SourceRegistry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from cognithor.leads.registry import SourceRegistry
from cognithor.leads.source import LeadSource

if TYPE_CHECKING:
    from cognithor.leads.models import Lead


def _make_source(source_id_value: str) -> LeadSource:
    """Build a concrete LeadSource with the given id for registry tests.

    Defines a proper subclass with ``scan`` in the class body (not a
    post-body assignment) so ABC's ``__abstractmethods__`` is empty at
    class creation time and the instance can be constructed normally.
    """

    class _Concrete(LeadSource):
        source_id = source_id_value
        display_name = source_id_value.upper()
        icon = "forum"
        color = "#123456"
        capabilities = frozenset({"scan"})

        async def scan(
            self,
            *,
            config: dict[str, Any],
            product: str,
            product_description: str,
            min_score: int,
        ) -> list[Lead]:
            return []

    return _Concrete()


class TestSourceRegistry:
    def test_register_and_list(self) -> None:
        reg = SourceRegistry()
        reg.register(_make_source("reddit"))
        reg.register(_make_source("hn"))
        ids = {s.source_id for s in reg.list()}
        assert ids == {"reddit", "hn"}

    def test_get_by_id(self) -> None:
        reg = SourceRegistry()
        src = _make_source("rss")
        reg.register(src)
        assert reg.get("rss") is src
        assert reg.get("nonexistent") is None

    def test_register_duplicate_raises(self) -> None:
        reg = SourceRegistry()
        reg.register(_make_source("reddit"))
        with pytest.raises(ValueError, match="already registered"):
            reg.register(_make_source("reddit"))

    def test_unregister(self) -> None:
        reg = SourceRegistry()
        reg.register(_make_source("reddit"))
        reg.unregister("reddit")
        assert reg.get("reddit") is None
        assert reg.list() == []

    def test_unregister_nonexistent_is_noop(self) -> None:
        reg = SourceRegistry()
        reg.unregister("nothing")  # must not raise

    def test_contains(self) -> None:
        reg = SourceRegistry()
        reg.register(_make_source("hn"))
        assert "hn" in reg
        assert "reddit" not in reg

    def test_len(self) -> None:
        reg = SourceRegistry()
        assert len(reg) == 0
        reg.register(_make_source("a"))
        reg.register(_make_source("b"))
        assert len(reg) == 2
        reg.unregister("a")
        assert len(reg) == 1
