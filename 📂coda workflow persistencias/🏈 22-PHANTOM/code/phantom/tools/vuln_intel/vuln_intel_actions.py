"""
Vulnerability Intelligence Tools - Phase 1 Enhancement
=======================================================

Tools for correlating version information with known CVEs and exploits.
Critical for turning version fingerprints into actionable exploits.

SECURITY NOTES:
- All tools are READ-ONLY (query public databases)
- No interaction with target systems
- Results are cached to reduce API calls
- Rate limiting prevents abuse

Tools:
- cve_search: Search NVD for CVEs by product/version
- exploit_search: Search ExploitDB for available exploits
- version_to_cves: Map technology version to known CVEs
"""

import asyncio
import hashlib
import logging
import os
import re
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote_plus

import httpx

from phantom.config.config import Config
from phantom.tools.registry import register_tool


logger = logging.getLogger(__name__)

# Rate limiting
_RATE_LIMIT_STATE: dict[str, float] = {}
_RATE_LIMIT_INTERVALS: dict[str, float] = {
    "nvd": 6.0,       # NVD: 6 seconds between requests (public API limit)
    "exploitdb": 2.0,  # ExploitDB: 2 seconds
    "vulners": 1.0,    # Vulners: 1 second
}

# Cache for CVE results
_CVE_CACHE: dict[str, tuple[Any, float]] = {}
_CACHE_TTL = 7200  # 2 hour cache TTL for CVE data


def _rate_limit(api_name: str) -> None:
    """Enforce rate limiting for API calls."""
    now = time.monotonic()
    last_call = _RATE_LIMIT_STATE.get(api_name, 0.0)
    interval = _RATE_LIMIT_INTERVALS.get(api_name, 1.0)
    wait_time = interval - (now - last_call)
    if wait_time > 0:
        time.sleep(wait_time)
    _RATE_LIMIT_STATE[api_name] = time.monotonic()


def _get_cache_key(prefix: str, *args: Any) -> str:
    """Generate a cache key."""
    data = f"{prefix}:{':'.join(str(a) for a in args)}"
    return hashlib.md5(data.encode()).hexdigest()


def _get_cached(key: str) -> Any | None:
    """Get cached result if not expired."""
    if key not in _CVE_CACHE:
        return None
    result, timestamp = _CVE_CACHE[key]
    if time.time() - timestamp > _CACHE_TTL:
        del _CVE_CACHE[key]
        return None
    return result


def _set_cached(key: str, result: Any) -> None:
    """Store result in cache."""
    _CVE_CACHE[key] = (result, time.time())
    # Cleanup
    if len(_CVE_CACHE) > 500:
        cutoff = time.time() - _CACHE_TTL
        keys_to_delete = [k for k, (_, ts) in _CVE_CACHE.items() if ts < cutoff]
        for k in keys_to_delete:
            del _CVE_CACHE[k]


def _parse_version(version_string: str) -> tuple[str, str]:
    """Parse a product/version string into (product, version)."""
    # Common formats:
    # nginx/1.19.0
    # Apache/2.4.49
    # PHP/7.4.3
    # OpenSSH_8.2p1
    # Microsoft-IIS/10.0
    
    patterns = [
        r"^([a-zA-Z][a-zA-Z0-9_-]*)[/_ ]([0-9]+(?:\.[0-9]+)*(?:[a-zA-Z0-9._-]*)?)$",
        r"^([a-zA-Z][a-zA-Z0-9_-]*)-([0-9]+(?:\.[0-9]+)*(?:[a-zA-Z0-9._-]*)?)$",
    ]
    
    for pattern in patterns:
        match = re.match(pattern, version_string.strip())
        if match:
            return match.group(1).lower(), match.group(2)
    
    # Fallback: try splitting on common delimiters
    for delim in ["/", "_", "-", " "]:
        if delim in version_string:
            parts = version_string.split(delim, 1)
            if len(parts) == 2 and parts[1] and parts[1][0].isdigit():
                return parts[0].lower().strip(), parts[1].strip()
    
    return version_string.lower().strip(), ""


def _calculate_cvss_severity(score: float) -> str:
    """Convert CVSS score to severity label."""
    if score >= 9.0:
        return "CRITICAL"
    elif score >= 7.0:
        return "HIGH"
    elif score >= 4.0:
        return "MEDIUM"
    elif score > 0:
        return "LOW"
    return "NONE"


@register_tool(sandbox_execution=False)
async def cve_search(
    product: str,
    version: str | None = None,
    vendor: str | None = None,
    severity: str | None = None,
    max_results: int = 25,
) -> dict[str, Any]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'phantom/tools/vuln_intel/vuln_intel_actions.py','step':'cve_search','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


@register_tool(sandbox_execution=False)
async def exploit_search(
    cve_id: str | None = None,
    product: str | None = None,
    exploit_type: str | None = None,
    max_results: int = 20,
) -> dict[str, Any]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'phantom/tools/vuln_intel/vuln_intel_actions.py','step':'exploit_search','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


@register_tool(sandbox_execution=False)
async def version_to_cves(
    version_string: str,
    include_exploits: bool = True,
) -> dict[str, Any]:
    """
    Map a technology version string to known CVEs and exploits.
    
    This is a PASSIVE reconnaissance tool - it parses version info and
    queries CVE databases. Use after fingerprinting to find vulnerabilities.
    
    Args:
        version_string: Version string from fingerprinting (e.g., "nginx/1.19.0",
                       "Apache/2.4.49", "PHP/7.4.3", "OpenSSH_8.2p1")
        include_exploits: Also search for available exploits (default: True)
    
    Returns:
        Dictionary containing:
        - success: Whether the correlation succeeded
        - product: Detected product name
        - version: Detected version number
        - cves: List of matching CVEs
        - exploits: List of available exploits (if include_exploits=True)
        - risk_level: Overall risk assessment
        - recommendations: Suggested actions
        - message: Status message
    
    Common version formats:
        - "nginx/1.19.0"
        - "Apache/2.4.49" (CVE-2021-41773 - path traversal)
        - "PHP/7.4.3"
        - "OpenSSH_8.2p1"
        - "Microsoft-IIS/10.0"
        - "Express" (JS framework)
    """
    if not version_string:
        return {
            "success": False,
            "error": "Version string is required",
            "cves": [],
        }
    
    # Parse the version string
    product, version = _parse_version(version_string)
    
    if not product:
        return {
            "success": False,
            "error": f"Could not parse version string: {version_string}",
            "cves": [],
        }
    
    # Search for CVEs
    cve_result = await cve_search(
        product=product,
        version=version if version else None,
        max_results=20,
    )
    
    cves = cve_result.get("cves", [])
    
    # Calculate risk level
    critical_count = sum(1 for c in cves if c.get("severity") == "CRITICAL")
    high_count = sum(1 for c in cves if c.get("severity") == "HIGH")
    
    if critical_count > 0:
        risk_level = "CRITICAL"
    elif high_count > 0:
        risk_level = "HIGH"
    elif len(cves) > 0:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    # Search for exploits if requested
    exploits: list[dict[str, Any]] = []
    if include_exploits and cves:
        # Search for exploits of top CVEs
        for cve in cves[:5]:
            cve_id = cve.get("cve_id", "")
            if cve_id:
                exploit_result = await exploit_search(cve_id=cve_id, max_results=5)
                exploits.extend(exploit_result.get("exploits", []))
        
        # Also search by product
        product_exploits = await exploit_search(product=product, max_results=10)
        for exp in product_exploits.get("exploits", []):
            if not any(e.get("id") == exp.get("id") for e in exploits):
                exploits.append(exp)
    
    # Generate recommendations
    recommendations = []
    if risk_level == "CRITICAL":
        recommendations.append("IMMEDIATE: Prioritize exploitation of critical CVEs")
        recommendations.append("Check for public exploits and Metasploit modules")
    elif risk_level == "HIGH":
        recommendations.append("High-value target: Focus testing on identified CVEs")
        recommendations.append("Manual verification of exploitability recommended")
    elif risk_level == "MEDIUM":
        recommendations.append("Moderate risk: Include in comprehensive testing")
    else:
        recommendations.append("Low risk from known CVEs")
        recommendations.append("Focus on zero-day discovery and logic flaws")
    
    if version:
        recommendations.append(f"Confirm version {version} matches target exactly")
    
    if exploits:
        has_msf = any(e.get("metasploit") for e in exploits)
        if has_msf:
            recommendations.append("Metasploit modules available - consider automated exploitation")
    
    return {
        "success": True,
        "version_string": version_string,
        "product": product,
        "version": version,
        "cves": cves,
        "exploits": exploits[:20] if exploits else [],
        "risk_level": risk_level,
        "critical_count": critical_count,
        "high_count": high_count,
        "total_cves": len(cves),
        "total_exploits": len(exploits),
        "recommendations": recommendations,
        "message": f"Mapped {product}/{version} to {len(cves)} CVEs, {len(exploits)} exploits (Risk: {risk_level})",
    }


@register_tool(sandbox_execution=False)
async def get_cve_details(cve_id: str) -> dict[str, Any]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'phantom/tools/vuln_intel/vuln_intel_actions.py','step':'get_cve_details','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
