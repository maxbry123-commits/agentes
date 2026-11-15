"""SpaceAgentsLoader — parse agents.md style docs into SpaceContract (minimal)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .contract import ResourceContract


@dataclass
class SpaceContract:
    space_id: str
    schema_url: str | None = None
    call_url: str | None = None
    poll_url: str | None = None
    upload_url: str | None = None
    auth: str | None = None
    endpoints: tuple[str, ...] = ()
    raw_keys: tuple[str, ...] = ()


class SpaceAgentsLoader:
    URL_RE = re.compile(r"https?://[^\s)\]]+", re.I)

    def parse(self, text: str, space_id: str = "") -> SpaceContract:
        urls = self.URL_RE.findall(text)
        keys = []
        for line in text.splitlines():
            if ":" in line and not line.strip().startswith("#"):
                k = line.split(":", 1)[0].strip().lower()
                if k:
                    keys.append(k)
        call = next((u for u in urls if "call" in u or "api" in u or "gradio" in u), urls[0] if urls else None)
        poll = next((u for u in urls if "poll" in u or "status" in u), None)
        schema = next((u for u in urls if "schema" in u or "openapi" in u), None)
        return SpaceContract(
            space_id=space_id or "space",
            schema_url=schema,
            call_url=call,
            poll_url=poll,
            endpoints=tuple(urls[:20]),
            raw_keys=tuple(keys[:30]),
        )

    def to_resource_contract(self, space: SpaceContract) -> ResourceContract:
        return ResourceContract(
            resource_id=f"hf://space/{space.space_id}",
            provider="huggingface",
            kind="space",
            source_uri=space.call_url or f"https://huggingface.co/spaces/{space.space_id}",
            capabilities=("space.invoke",),
            transport="http",
            entrypoint=space.call_url,
            acquisition_mode="remote",
            requires_auth=bool(space.auth),
        )
