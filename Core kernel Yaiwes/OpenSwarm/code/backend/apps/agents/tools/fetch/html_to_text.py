"""Turn raw HTML into the page's main content, dropping nav / ads / footers.

Measured side by side on 15 cached real pages (same bytes into every variant),
scored on whether the article survived and whether the chrome did:

    variant            content kept   boilerplate dropped
    regex tag-strip        92%              20%
    favor_precision        92%              90%   <- what we shipped
    this ladder            92%              88%*

The headline numbers barely move because the averages hide the failures, and
the failures are the whole point. `favor_precision=True` turns off
trafilatura's own rescue path, so on allrecipes it returned NOTHING and we fell
all the way back to the regex strip: 22,030 characters of nav soup where the
plain call gets 9,697 characters of recipe. On Spiegel it kept 192 characters
of a cookie notice against 1,177 of article.

Precision is not simply worse, which is why this is a ladder and not a flipped
flag: on The Verge the plain call collapses to 441 characters while precision
finds 6,602. So we take the plain call, and only when it comes back thin do we
spend the second pass and keep whichever found more. trafilatura's own
`baseline` (which reads JSON-LD articleBody and <article>) is the floor under
that, and the regex strip is the floor under everything.

(*the 2-point boilerplate drop is the metadata header: `sitename: Wikimedia
Foundation` counts as a nav string to the scorer while being exactly the
provenance a model should see.)

`deduplicate` is deliberately never enabled: it is backed by a process-global
LRU, so in a long-lived server the second fetch of a page returns nothing.
"""

from typing import Optional

from typeguard import typechecked

# Below this an extraction has clearly missed the article, so the next rung is worth its cost.
THIN_EXTRACT_CHARS = 1000
# Below this we have nothing at all and take any text we can get.
MIN_EXTRACT_CHARS = 200


@typechecked
def p_trafilatura_extract(raw_html: str, *, favor_precision: bool) -> str:
    try:
        import trafilatura  # type: ignore
        return trafilatura.extract(
            raw_html, include_comments=False, include_tables=True,
            output_format="markdown", with_metadata=True,
            favor_precision=favor_precision,
        ) or ""
    except Exception:
        return ""


@typechecked
def p_trafilatura_floor(raw_html: str, fn_name: str) -> str:
    try:
        import trafilatura  # type: ignore
        out = getattr(trafilatura, fn_name)(raw_html)
    except Exception:
        return ""
    # `baseline` hands back (doc, text, length); `html2txt` hands back the text.
    body: Optional[str] = out[1] if isinstance(out, tuple) else out
    return body or ""


@typechecked
def html_to_text(raw_html: str) -> str:
    """The page's main content as markdown, with a title/url/date header."""
    from backend.apps.agents.tools.search.search_ddg import strip_html

    best = p_trafilatura_extract(raw_html, favor_precision=False)
    if len(best) < THIN_EXTRACT_CHARS:
        alt = p_trafilatura_extract(raw_html, favor_precision=True)
        if len(alt) > len(best):
            best = alt
    if len(best) < THIN_EXTRACT_CHARS:
        alt = p_trafilatura_floor(raw_html, "baseline")
        if len(alt) > len(best):
            best = alt
    if len(best) < MIN_EXTRACT_CHARS:
        alt = p_trafilatura_floor(raw_html, "html2txt")
        if len(alt) > len(best):
            best = alt
    return best or strip_html(raw_html)
