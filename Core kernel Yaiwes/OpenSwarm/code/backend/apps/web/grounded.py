"""Provider-grounded search/fetch backends for the /api/web cascade.

These are the PAID tiers: the user's own Gemini / OpenAI key, or the same
providers reached through a 9Router subscription. They are slow (tens of
seconds) but render and reason over pages, so they sit behind the free
keyless tiers and only run when those come up empty."""

import time
from typing import Dict, List, Optional, Set, Tuple

import httpx
from typeguard import typechecked

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_GROUNDING_MODEL = "gemini-2.5-flash"  # cheapest + fastest for grounded calls

OPENAI_API_BASE = "https://api.openai.com/v1"
OPENAI_SEARCH_MODEL = "gpt-5-mini"  # cheapest model that supports web_search_preview

NINE_ROUTER_MESSAGES_URL = "http://localhost:20128/v1/messages"


@typechecked
async def gemini_grounded_call(api_key: str, prompt: str, *, use_url_context: bool) -> Dict:
    """Call Gemini with googleSearch (+ optionally urlContext) grounding.

    Returns {"text": grounded_answer, "chunks": [(title, uri), ...],
             "queries": [...]} or raises httpx.HTTPError on failure.
    """
    tools: List[Dict] = [{"googleSearch": {}}]
    if use_url_context:
        tools.append({"urlContext": {}})
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "tools": tools,
        "generationConfig": {"thinkingConfig": {"thinkingBudget": 0}},
    }
    url = f"{GEMINI_API_BASE}/models/{GEMINI_GROUNDING_MODEL}:generateContent"
    async with httpx.AsyncClient(timeout=45.0) as client:
        r = await client.post(
            url,
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json=body,
        )
        r.raise_for_status()
        data = r.json()

    cand = (data.get("candidates") or [{}])[0]
    text = "".join(
        p.get("text", "") for p in (cand.get("content", {}).get("parts") or [])
        if isinstance(p, dict)
    )
    gm = cand.get("groundingMetadata") or {}
    chunks: List[Tuple[str, str]] = []
    for gc in (gm.get("groundingChunks") or []):
        web = (gc or {}).get("web") or {}
        uri = web.get("uri") or web.get("url") or ""
        title = web.get("title") or uri
        if uri:
            chunks.append((title, uri))
    queries = gm.get("webSearchQueries") or []
    return {"text": text, "chunks": chunks, "queries": queries}


@typechecked
def format_grounded_as_search_results(grounded: Dict, query: str) -> str:
    """Format Gemini grounding output to match WebSearchTool's text shape."""
    lines: List[str] = []
    chunks = grounded.get("chunks") or []
    for i, (title, uri) in enumerate(chunks[:10], start=1):
        lines.append(f"[{i}] {title}\n    {uri}")
    text = grounded.get("text") or ""
    if text:
        lines.append("\n" + text)
    if not lines:
        return f"No search results found for: {query}"
    return "\n\n".join(lines)


@typechecked
def format_grounded_as_fetch(grounded: Dict, url: str) -> str:
    """Format Gemini urlContext output to match WebFetchTool's text shape."""
    parts = [f"Contents of {url}:", ""]
    text = grounded.get("text") or ""
    if text:
        parts.append(text)
    chunks = grounded.get("chunks") or []
    if chunks:
        parts.append("\nCited sources:")
        for i, (title, uri) in enumerate(chunks[:5], start=1):
            parts.append(f"  [{i}] {title}; {uri}")
    return "\n".join(parts)


@typechecked
def resolve_gemini_api_key() -> Optional[str]:
    """Pull the AI Studio API key from settings, or None."""
    try:
        from backend.apps.settings.settings import load_settings
        s = load_settings()
        return getattr(s, "google_api_key", None) or None
    except Exception:
        return None


@typechecked
def resolve_openai_api_key() -> Optional[str]:
    try:
        from backend.apps.settings.settings import load_settings
        s = load_settings()
        return getattr(s, "openai_api_key", None) or None
    except Exception:
        return None


# Cache of which 9Router subscriptions are connected. Refreshed rather than hit on every search call; 9Router's /api/providers is fast but not free and we already query it from many places.
p_nine_router_connected: Set[str] = set()
p_nine_router_cache_at: float = 0.0


@typechecked
async def refresh_9r_connected() -> Set[str]:
    """The currently-active 9Router subscription providers, cached 20s."""
    global p_nine_router_connected, p_nine_router_cache_at
    now = time.time()
    if now - p_nine_router_cache_at < 20.0:
        return p_nine_router_connected
    try:
        from backend.apps.nine_router import is_running as p_9r_running, get_providers as p_9r_providers
        if not p_9r_running():
            p_nine_router_connected = set()
        else:
            conns = await p_9r_providers()
            p_nine_router_connected = {
                c.get("provider")
                for c in conns
                if isinstance(c, dict) and c.get("isActive") and c.get("provider")
            }
        p_nine_router_cache_at = now
    except Exception:
        # Cache stays; best-effort.
        pass
    return p_nine_router_connected


@typechecked
async def p_nine_router_text(body: Dict) -> str:
    """POST an Anthropic-shape body to 9Router and concatenate its text blocks."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(
            NINE_ROUTER_MESSAGES_URL,
            json=body,
            headers={"x-api-key": "9router", "anthropic-version": "2023-06-01"},
        )
        if r.status_code != 200:
            return ""
        data = r.json()
    return "".join(
        block.get("text", "")
        for block in (data.get("content") or [])
        if isinstance(block, dict) and block.get("type") == "text"
    )


@typechecked
async def gemini_grounded_via_9router(prompt: str, use_url_context: bool) -> Dict:
    """Grounded Gemini through the user's OAuth subscription instead of an AI Studio key.

    Shapes its return like `gemini_grounded_call` so the formatters work
    unchanged. 9Router doesn't surface citations as a structured field
    uniformly across providers, so we hand back text-only."""
    connected = await refresh_9r_connected()
    if "gemini-cli" in connected:
        model = "gc/gemini-2.5-flash"
    elif "antigravity" in connected:
        model = "ag/gemini-3-flash"
    else:
        return {}
    sys_prompt = (
        "You fetch URLs and return concise summaries with citations."
        if use_url_context
        else "You search the web and return concise grounded answers with "
             "source citations. Always cite the URLs you used."
    )
    text = await p_nine_router_text({
        "model": model,
        "max_tokens": 1024,
        "system": sys_prompt,
        "messages": [{"role": "user", "content": prompt}],
    })
    return {"text": text, "chunks": []}


@typechecked
async def openai_websearch_via_9router(query: str) -> Dict:
    """Same idea for OpenAI, through the user's Codex 9Router connection."""
    connected = await refresh_9r_connected()
    if "codex" not in connected:
        return {}
    text = await p_nine_router_text({
        "model": "cx/gpt-5.4-mini",
        "max_tokens": 1024,
        "system": (
            "You search the web and return concise grounded answers "
            "with source citations. Always cite the URLs you used."
        ),
        "messages": [{"role": "user", "content": f"Search the web for: {query}"}],
    })
    return {"text": text, "chunks": []}


@typechecked
def p_parse_openai_response(data: Dict) -> Dict:
    """Pull output_text + url_citation annotations out of a Responses API body."""
    text_parts: List[str] = []
    chunks: List[Tuple[str, str]] = []
    for item in (data.get("output") or []):
        if not isinstance(item, dict):
            continue
        for content in (item.get("content") or []):
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text":
                text_parts.append(content.get("text", ""))
            for ann in (content.get("annotations") or []):
                if isinstance(ann, dict) and ann.get("type") == "url_citation":
                    uri = ann.get("url", "")
                    if uri:
                        chunks.append((ann.get("title", uri), uri))
    return {"text": "".join(text_parts), "chunks": chunks}


@typechecked
async def p_openai_responses(api_key: str, prompt: str) -> Dict:
    async with httpx.AsyncClient(timeout=45.0) as client:
        r = await client.post(
            f"{OPENAI_API_BASE}/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": OPENAI_SEARCH_MODEL,
                "input": prompt,
                "tools": [{"type": "web_search_preview"}],
            },
        )
        r.raise_for_status()
        return p_parse_openai_response(r.json())


@typechecked
async def openai_websearch(api_key: str, query: str) -> Dict:
    """Call OpenAI Responses API with the web_search_preview tool."""
    grounded = await p_openai_responses(
        api_key, f"Search the web for: {query}\n\nReturn a concise summary. Cite sources.",
    )
    grounded["queries"] = [query]
    return grounded


@typechecked
async def openai_urlfetch(api_key: str, url: str, prompt: Optional[str]) -> Dict:
    """Use OpenAI's web_search_preview to fetch/summarize a specific URL."""
    prompt_text = f"Fetch and summarize the content at: {url}"
    if prompt:
        prompt_text += f"\n\nFocus on: {prompt}"
    return await p_openai_responses(api_key, prompt_text)
