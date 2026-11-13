"""Tell a bot wall apart from a page, so the cascade keeps going instead of
handing the model a challenge screen and calling it content.

An HTTP error is easy: the fetch tier already falls through on any 4xx/5xx. The
gap was the wall that answers 200. Measured live, Reddit serves "Reddit -
Please wait for verification" with a 200, and Cloudflare's interstitial is a
normal 200 whose whole body is "Enable JavaScript and cookies to continue".
Those are exactly the pages our own offscreen Chromium CAN read, because it
runs a real browser on the user's own residential IP, so treating them as a
successful fetch spends the one tier that would have worked.

Both conditions must hold: a challenge phrase AND a page too small to be an
article. A news story about Cloudflare outages contains the phrase and must not
be thrown away for it.
"""

import re
from typing import Tuple

from typeguard import typechecked

# A wall is a stub page. Real articles that merely mention these run long.
MAX_WALL_CHARS = 2000

P_WALL_MARKERS: Tuple[str, ...] = (
    "just a moment...",
    "enable javascript and cookies to continue",
    "checking your browser before accessing",
    "verifying you are human",
    "please wait for verification",
    "attention required! | cloudflare",
    "you need to enable javascript to run this app",
    "please enable js and disable any ad blocker",
    "sorry, you have been blocked",
    "why have i been blocked",
    "performed triggered the security solution",
    "confirm you are a human",
    "press & hold",
)

P_SPACE_RE = re.compile(r"\s+")


@typechecked
def looks_like_bot_wall(text: str) -> bool:
    """True when this 200 is a challenge screen rather than the page."""
    if len(text) > MAX_WALL_CHARS:
        return False
    # Rendered walls arrive line-wrapped ("confirm you are\na human"), so match on flattened text.
    return any(marker in P_SPACE_RE.sub(" ", text.lower()) for marker in P_WALL_MARKERS)
