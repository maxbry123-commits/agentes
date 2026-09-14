"""Tests for HIM collectors."""

from __future__ import annotations

import pytest

from cognithor.osint.collectors.crunchbase import CrunchbaseCollector
from cognithor.osint.collectors.linkedin import LinkedInCollector
from cognithor.osint.collectors.scholar import ScholarCollector
from cognithor.osint.collectors.social import SocialCollector


def test_stub_scholar_not_available():
    c = ScholarCollector()
    assert c.is_available() is False


def test_stub_linkedin_not_available():
    c = LinkedInCollector()
    assert c.is_available() is False


def test_stub_crunchbase_not_available():
    c = CrunchbaseCollector()
    assert c.is_available() is False


def test_stub_social_not_available():
    c = SocialCollector()
    assert c.is_available() is False


@pytest.mark.asyncio
async def test_stub_scholar_returns_empty():
    c = ScholarCollector()
    result = await c.collect("test", [])
    assert result == []


@pytest.mark.asyncio
async def test_stub_social_returns_empty():
    c = SocialCollector()
    result = await c.collect("test", [])
    assert result == []
