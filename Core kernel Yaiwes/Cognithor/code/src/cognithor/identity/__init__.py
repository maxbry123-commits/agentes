"""Jarvis Identity Layer — Cognitive personality powered by Immortal Mind Protocol.

The IdentityLayer is the sole interface between Cognithor and Immortal Mind's
CognitioEngine. It wraps the 12-layer cognitive architecture and provides
hooks for the PGE cycle (Plan-Gate-Execute).

Usage::

    from cognithor.identity import IdentityLayer

    identity = IdentityLayer(
        identity_id="jarvis",
        data_dir="~/.cognithor/identity/jarvis",
        llm_fn=my_llm_function,
    )

    # Pre-Planner: enrich context
    ctx = identity.enrich_context(user_message, session_history)

    # Post-Execution: process interaction
    identity.process_interaction("assistant", response_text, emotional_tone=0.6)

    # Post-Reflection: reflect
    identity.reflect(session_summary, success_score=0.8)

    # Persist
    identity.save()
"""

from __future__ import annotations

from cognithor.identity.adapter import IdentityLayer

__all__ = ["IdentityLayer"]
