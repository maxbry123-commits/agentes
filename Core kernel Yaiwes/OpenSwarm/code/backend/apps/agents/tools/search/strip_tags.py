"""Collapse a fragment of SERP markup to its visible one-line text."""

import html
import re

from typeguard import typechecked

# Some engines inline <style> blocks INSIDE result anchors, so tag-stripping alone would emit CSS as the title.
P_NOISE_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", flags=re.DOTALL | re.IGNORECASE)
P_TAG_RE = re.compile(r"<[^>]+>")


@typechecked
def strip_tags(raw: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(P_TAG_RE.sub(" ", P_NOISE_RE.sub("", raw)))).strip()
