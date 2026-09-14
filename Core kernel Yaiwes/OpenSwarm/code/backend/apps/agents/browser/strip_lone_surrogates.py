import re

from typeguard import typechecked


@typechecked
def strip_lone_surrogates(s: str) -> str:
    # The JS/webview hands us page text as UTF-16, so an emoji can arrive as half of its surrogate
    # pair; Python carries the orphan but .encode('utf-8') later (anything serializing the text to
    # an LLM) detonates with "surrogates not allowed" and kills the turn. Swap any orphan for the
    # replacement char. It lives in its own file because the agent loop learned this the hard way
    # and prestage then learned it again, live on twitch, where half an emoji killed the whole
    # composer-reach stage.
    return re.sub(r"[\ud800-\udfff]", "�", s) if s else s
