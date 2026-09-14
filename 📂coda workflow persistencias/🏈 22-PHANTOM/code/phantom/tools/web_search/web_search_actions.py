import asyncio
import os
import re
from typing import Any

import httpx

from phantom.tools.registry import register_tool

# Try to import DuckDuckGo for fallback
_DDG_AVAILABLE = False
try:
    from ddgs import DDGS
    _DDG_AVAILABLE = True
except ImportError:
    pass  # DuckDuckGo not installed, will use Perplexity only


SYSTEM_PROMPT = """You are assisting a cybersecurity agent specialized in vulnerability scanning
and security assessment running on Kali Linux. When responding to search queries:

1. Prioritize cybersecurity-relevant information including:
   - Vulnerability details (CVEs, CVSS scores, impact)
   - Security tools, techniques, and methodologies
   - Exploit information and proof-of-concepts
   - Security best practices and mitigations
   - Penetration testing approaches
   - Web application security findings

2. Provide technical depth appropriate for security professionals
3. Include specific versions, configurations, and technical details when available
4. Focus on actionable intelligence for security assessment
5. Cite reliable security sources (NIST, OWASP, CVE databases, security vendors)
6. When providing commands or installation instructions, prioritize Kali Linux compatibility
   and use apt package manager or tools pre-installed in Kali
7. Be detailed and specific - avoid general answers. Always include concrete code examples,
   command-line instructions, configuration snippets, or practical implementation steps
   when applicable

Structure your response to be comprehensive yet concise, emphasizing the most critical
security implications and details."""


def _duckduckgo_search_fallback(query: str, max_results: int = 5) -> dict[str, Any]:
    """
    Fallback search using DuckDuckGo when Perplexity API key is not available.
    This is FREE and requires no API key.
    """
    if not _DDG_AVAILABLE:
        return {
            "success": False,
            "message": "DuckDuckGo not installed. Install with: pip install duckduckgo-search",
            "results": [],
        }
    
    try:
        results_text = ""
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return {
                "success": True,
                "query": query,
                "content": "No search results found.",
                "message": "Search completed but no results found",
                "results": [],
            }
        
        # Format results for LLM
        results_text = f"[WEB SEARCH RESULTS FOR: {query}]\n"
        results_text += "=" * 50 + "\n\n"
        for i, r in enumerate(results, 1):
            results_text += f"[{i}] {r.get('title', 'N/A')}\n"
            results_text += f"    URL     : {r.get('href', 'N/A')}\n"
            results_text += f"    Snippet : {r.get('body', 'N/A')}\n\n"
        
        return {
            "success": True,
            "query": query,
            "content": results_text,
            "message": f"Found {len(results)} results via DuckDuckGo (free fallback)",
            "results": results,
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"DuckDuckGo search failed: {e}",
            "results": [],
        }


def _search_cve_fallback(cve_id: str) -> dict[str, Any]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'phantom/tools/web_search/web_search_actions.py','step':'_search_cve_fallback','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def _smart_search_router(query: str) -> dict[str, Any]:
    """
    Automatically detect query type and route to appropriate search:
    - CVE pattern (CVE-YYYY-NNNNN) → CVE lookup
    - Exploit/poc keywords → Exploit search  
    - Fix/patch/mitigate keywords → Fix search
    - Default → General web search
    """
    query_lower = query.lower()
    
    # CVE pattern detection
    cve_pattern = re.compile(r'cve-\d{4}-\d{4,7}', re.IGNORECASE)
    cve_match = cve_pattern.search(query)
    if cve_match:
        cve_id = cve_match.group().upper()
        return {
            "search_type": "cve",
            "query": cve_id,
            "result": _search_cve_fallback(cve_id),
        }
    
    # Exploit keywords
    exploit_keywords = ["exploit", "poc", "payload", "rce", "lfi", "sqli", "xss", "injection"]
    if any(word in query_lower for word in exploit_keywords):
        ddg_result = _duckduckgo_search_fallback(query + " exploit github", max_results=5)
        return {
            "search_type": "exploit",
            "query": query,
            "result": ddg_result,
        }
    
    # Fix/patch keywords
    fix_keywords = ["fix", "patch", "mitigate", "harden", "secure", "remediation"]
    if any(word in query_lower for word in fix_keywords):
        ddg_result = _duckduckgo_search_fallback(query + " security fix mitigation", max_results=5)
        return {
            "search_type": "fix",
            "query": query,
            "result": ddg_result,
        }
    
    # Default: general search
    ddg_result = _duckduckgo_search_fallback(query, max_results=5)
    return {
        "search_type": "general",
        "query": query,
        "result": ddg_result,
    }


@register_tool(sandbox_execution=False)
async def web_search(query: str, use_smart_router: bool = False) -> dict[str, Any]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'phantom/tools/web_search/web_search_actions.py','step':'web_search','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
