"""Discord Lead Hunter -- pack entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

from cognithor.packs.interface import AgentPack, PackContext
from cognithor.utils.logging import get_logger

log = get_logger(__name__)


class Pack(AgentPack):
    def __init__(self, manifest):
        super().__init__(manifest)
        self._source = None

    def register(self, context: PackContext) -> None:
        _src = str(Path(__file__).parent / "src")
        if _src not in sys.path:
            sys.path.insert(0, _src)

        from discord_source import DiscordLeadSource

        if context.leads is None:
            log.warning("discord_pack_no_leads_service")
            return

        llm_fn = None
        gw = context.gateway
        if gw is not None and hasattr(gw, "_ollama") and gw._ollama is not None:
            _model = (
                getattr(gw._config.models.planner, "name", "qwen3:27b")
                if gw._config
                else "qwen3:27b"
            )
            _ollama = gw._ollama

            async def _llm_fn(**kw):
                return await _ollama.chat(model=_model, **kw)

            llm_fn = _llm_fn

        self._source = DiscordLeadSource(llm_fn=llm_fn)
        context.leads.register_source(self._source)
        log.info("discord_lead_hunter_registered")

    def unregister(self, context: PackContext) -> None:
        if context.leads is not None and self._source is not None:
            context.leads.unregister_source("discord")
            self._source = None
