"""Loader for the shipped seed playbooks (data lives in seed_playbooks.py). A fresh install isn't
fully cold on a popular site's first task: seed_for returns the site's starting strategy bullets,
which browser_playbook uses as a FALLBACK until a real verified run distills a learned playbook
that supersedes them. Match is canonical-host, with and without a leading 'www.'."""

from backend.apps.agents.browser.seed_playbooks import SEED_PLAYBOOKS


def seed_for(host: str) -> list[str]:
    """Seed bullets for a host, or []. Matches with and without a leading 'www.'."""
    h = (host or "").lower().strip()
    if not h:
        return []
    bare = h[4:] if h.startswith("www.") else h
    return SEED_PLAYBOOKS.get(h) or SEED_PLAYBOOKS.get(bare) or SEED_PLAYBOOKS.get("www." + bare) or []
