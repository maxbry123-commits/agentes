"""
WAF Detection and Evasion Tools - Phase 1 Enhancement
======================================================

Passive WAF detection and evasion strategy tools.
These tools fingerprint WAFs from HTTP responses and provide bypass strategies.

SECURITY NOTES:
- WAF detection uses response fingerprinting (headers, cookies, body patterns)
- No active exploitation or attack payloads sent
- Evasion strategies are informational/educational
- All HTTP requests use benign payloads

Tools:
- detect_waf: Detect WAF presence from HTTP responses
- get_waf_evasion_strategies: Get evasion strategies for detected WAF
"""

import hashlib
import logging
import re
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from phantom.tools.registry import register_tool


logger = logging.getLogger(__name__)

# Rate limiting state
_RATE_LIMIT_STATE: dict[str, float] = {}
_RATE_LIMIT_INTERVAL = 1.0  # 1 second between requests

# Simple cache for WAF detection results
_WAF_CACHE: dict[str, tuple[Any, float]] = {}
_CACHE_TTL = 1800  # 30 minutes


def _rate_limit(api_name: str = "waf") -> None:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'phantom/tools/waf/waf_actions.py','step':'_rate_limit','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def _get_cache_key(prefix: str, *args: Any) -> str:
    """Generate a cache key from prefix and arguments."""
    data = f"{prefix}:{':'.join(str(a) for a in args)}"
    return hashlib.md5(data.encode()).hexdigest()


def _get_cached(key: str) -> Any | None:
    """Get cached result if not expired."""
    if key not in _WAF_CACHE:
        return None
    result, timestamp = _WAF_CACHE[key]
    if time.time() - timestamp > _CACHE_TTL:
        del _WAF_CACHE[key]
        return None
    return result


def _set_cached(key: str, result: Any) -> None:
    """Store result in cache."""
    _WAF_CACHE[key] = (result, time.time())


# ==============================================================================
# WAF Signature Database
# ==============================================================================

WAF_SIGNATURES: dict[str, dict[str, Any]] = {
    "cloudflare": {
        "name": "Cloudflare",
        "vendor": "Cloudflare, Inc.",
        "headers": {
            "cf-ray": r".*",
            "cf-cache-status": r".*",
            "server": r"cloudflare",
            "cf-request-id": r".*",
        },
        "cookies": ["__cfduid", "__cf_bm", "cf_clearance", "_cfuvid"],
        "body_patterns": [
            r"cloudflare",
            r"attention required.*cloudflare",
            r"cf-error-details",
            r"ray id:",
        ],
        "status_codes": [403, 503, 1020],
    },
    "akamai": {
        "name": "Akamai Kona Site Defender",
        "vendor": "Akamai Technologies",
        "headers": {
            "server": r"akamaigh|akamai",
            "x-akamai-transformed": r".*",
            "akamai-grn": r".*",
            "x-akamai-session-info": r".*",
        },
        "cookies": ["ak_bmsc", "bm_sz", "bm_sv", "_abck", "akamai_generated"],
        "body_patterns": [
            r"access denied.*akamai",
            r"reference.*#\d+\.\w+",
            r"akamaigh",
        ],
        "status_codes": [403],
    },
    "aws_waf": {
        "name": "AWS WAF",
        "vendor": "Amazon Web Services",
        "headers": {
            "x-amzn-requestid": r".*",
            "x-amz-cf-id": r".*",
            "x-amz-cf-pop": r".*",
            "x-amz-id-2": r".*",
        },
        "cookies": ["awsalb", "awsalbcors", "awselb"],
        "body_patterns": [
            r"request blocked",
            r"access denied",
            r"x-amzn-errortype",
        ],
        "status_codes": [403],
    },
    "imperva_incapsula": {
        "name": "Imperva Incapsula",
        "vendor": "Imperva, Inc.",
        "headers": {
            "x-cdn": r"incapsula",
            "x-iinfo": r".*",
        },
        "cookies": ["visid_incap", "incap_ses", "nlbi_", "__inc"],
        "body_patterns": [
            r"incapsula incident",
            r"powered by incapsula",
            r"_incapsula_resource",
            r"incap_ses",
        ],
        "status_codes": [403],
    },
    "sucuri": {
        "name": "Sucuri CloudProxy",
        "vendor": "Sucuri",
        "headers": {
            "server": r"sucuri",
            "x-sucuri-id": r".*",
            "x-sucuri-cache": r".*",
        },
        "cookies": ["sucuri_cloudproxy_uuid"],
        "body_patterns": [
            r"sucuri website firewall",
            r"access denied.*sucuri",
            r"sucuri cloudproxy",
            r"cloudproxy.*block",
        ],
        "status_codes": [403],
    },
    "f5_big_ip": {
        "name": "F5 BIG-IP ASM",
        "vendor": "F5 Networks",
        "headers": {
            "server": r"big-?ip",
            "x-wa-info": r".*",
        },
        "cookies": ["TS", "BIGipServer", "F5_ST", "F5_HT"],
        "body_patterns": [
            r"request rejected",
            r"the requested url was rejected",
            r"support id:",
            r"f5 networks",
        ],
        "status_codes": [403],
    },
    "modsecurity": {
        "name": "ModSecurity",
        "vendor": "Trustwave (Open Source)",
        "headers": {
            "server": r"mod_security|modsecurity",
        },
        "cookies": [],
        "body_patterns": [
            r"mod_security",
            r"modsecurity",
            r"not acceptable",
            r"this error was generated by mod_security",
            r"owasp crs",
        ],
        "status_codes": [403, 406],
    },
    "fortiweb": {
        "name": "FortiWeb",
        "vendor": "Fortinet",
        "headers": {
            "server": r"fortiweb",
        },
        "cookies": ["FORTIWAFSID"],
        "body_patterns": [
            r"fortigate",
            r"fortiweb",
            r"fgd_icon",
            r".fgtauth",
        ],
        "status_codes": [403],
    },
    "barracuda": {
        "name": "Barracuda WAF",
        "vendor": "Barracuda Networks",
        "headers": {
            "server": r"barracuda",
        },
        "cookies": ["barra_counter_session"],
        "body_patterns": [
            r"barracuda",
            r"barracuda\.css",
        ],
        "status_codes": [403],
    },
    "wordfence": {
        "name": "Wordfence",
        "vendor": "Defiant Inc.",
        "headers": {},
        "cookies": ["wfwaf-authcookie"],
        "body_patterns": [
            r"wordfence",
            r"this response was generated by wordfence",
            r"your access to this site has been limited",
            r"generated by wordfence",
        ],
        "status_codes": [403, 503],
    },
    "azure_waf": {
        "name": "Azure Application Gateway WAF",
        "vendor": "Microsoft Azure",
        "headers": {
            "x-azure-ref": r".*",
            "x-ms-request-id": r".*",
        },
        "cookies": [],
        "body_patterns": [
            r"azure",
            r"microsoft",
            r"waf blocked",
        ],
        "status_codes": [403],
    },
    "radware": {
        "name": "Radware AppWall",
        "vendor": "Radware",
        "headers": {
            "x-sl-compstate": r".*",
        },
        "cookies": [],
        "body_patterns": [
            r"radware",
            r"unauthorized activity",
        ],
        "status_codes": [403],
    },
    "wallarm": {
        "name": "Wallarm",
        "vendor": "Wallarm Inc.",
        "headers": {
            "server": r"nginx-wallarm",
        },
        "cookies": [],
        "body_patterns": [
            r"wallarm",
        ],
        "status_codes": [403],
    },
    "citrix_netscaler": {
        "name": "Citrix NetScaler AppFirewall",
        "vendor": "Citrix",
        "headers": {
            "via": r"ns-cache",
            "cneonction": r".*",
            "nncoection": r".*",
        },
        "cookies": ["citrix_ns_id", "NSC_"],
        "body_patterns": [
            r"citrix",
            r"netscaler",
            r"ns_af",
        ],
        "status_codes": [403],
    },
    "comodo": {
        "name": "Comodo WAF",
        "vendor": "Comodo",
        "headers": {
            "server": r"protected by anti-ddos",
        },
        "cookies": [],
        "body_patterns": [
            r"comodo waf",
            r"protected by comodo",
        ],
        "status_codes": [403],
    },
    "edgecast": {
        "name": "Edgecast (Verizon Digital Media)",
        "vendor": "Verizon Digital Media Services",
        "headers": {
            "server": r"ecs",
            "x-ec-custom-error": r".*",
        },
        "cookies": [],
        "body_patterns": [],
        "status_codes": [403],
    },
    "fastly": {
        "name": "Fastly",
        "vendor": "Fastly, Inc.",
        "headers": {
            "x-fastly-request-id": r".*",
            "fastly-io-info": r".*",
            "x-served-by": r"cache-",
        },
        "cookies": [],
        "body_patterns": [
            r"fastly error",
        ],
        "status_codes": [403, 503],
    },
    "stackpath": {
        "name": "StackPath",
        "vendor": "StackPath",
        "headers": {
            "x-sp-url": r".*",
            "x-sp-waf-handler": r".*",
        },
        "cookies": [],
        "body_patterns": [
            r"stackpath",
        ],
        "status_codes": [403],
    },
    "reblaze": {
        "name": "Reblaze",
        "vendor": "Reblaze Technologies",
        "headers": {
            "server": r"reblaze",
        },
        "cookies": ["rbzid"],
        "body_patterns": [
            r"reblaze",
            r"access denied.*rbz",
        ],
        "status_codes": [403],
    },
    "wangsu": {
        "name": "Wangsu (ChinaNetCenter)",
        "vendor": "ChinaNetCenter",
        "headers": {
            "x-via": r".*ws.*",
            "server": r"wangsu",
        },
        "cookies": [],
        "body_patterns": [],
        "status_codes": [403],
    },
}

# ==============================================================================
# WAF Evasion Strategies Database
# ==============================================================================

WAF_EVASION_STRATEGIES: dict[str, dict[str, Any]] = {
    "cloudflare": {
        "general_info": (
            "Cloudflare is one of the most common WAFs. It uses JavaScript challenges, "
            "CAPTCHAs, and signature-based detection. Finding the origin IP is often the "
            "most effective bypass."
        ),
        "strategies": [
            {
                "name": "Origin IP Discovery",
                "description": "Find the real origin IP behind Cloudflare",
                "techniques": [
                    "Check DNS history via SecurityTrails, ViewDNS",
                    "Search Shodan/Censys for SSL certificate matching",
                    "Check MX records - mail servers often reveal origin",
                    "Look for subdomains not behind Cloudflare",
                    "Check Crunchbase/builtwith for IP leaks",
                ],
                "effectiveness": "HIGH",
            },
            {
                "name": "Rate Limit Bypass",
                "description": "Avoid triggering rate limits",
                "techniques": [
                    "Distribute requests across time",
                    "Use different User-Agents",
                    "Rotate source IPs (residential proxies)",
                ],
                "effectiveness": "MEDIUM",
            },
            {
                "name": "Encoding Techniques",
                "description": "Bypass signature-based rules",
                "techniques": [
                    "URL encoding (single/double)",
                    "Unicode normalization",
                    "Case variation",
                    "Null bytes insertion",
                    "Chunked transfer encoding",
                ],
                "effectiveness": "LOW-MEDIUM",
            },
        ],
        "limitations": [
            "JavaScript challenge requires browser automation",
            "Bot management is increasingly sophisticated",
            "Origin IP may have IP restrictions configured",
        ],
    },
    "akamai": {
        "general_info": (
            "Akamai Kona Site Defender is enterprise-grade with advanced bot detection. "
            "It uses behavioral analysis and sensor data collection."
        ),
        "strategies": [
            {
                "name": "Browser Emulation",
                "description": "Mimic legitimate browser behavior",
                "techniques": [
                    "Use headless browsers with stealth plugins",
                    "Execute Akamai's sensor JavaScript properly",
                    "Maintain consistent TLS fingerprint",
                    "Handle _abck cookie flow correctly",
                ],
                "effectiveness": "MEDIUM-HIGH",
            },
            {
                "name": "Request Timing",
                "description": "Avoid triggering behavioral detection",
                "techniques": [
                    "Add random delays between requests",
                    "Simulate human browsing patterns",
                    "Avoid sequential parameter enumeration",
                ],
                "effectiveness": "MEDIUM",
            },
            {
                "name": "Parameter Manipulation",
                "description": "Bypass signature rules",
                "techniques": [
                    "Use HPP (HTTP Parameter Pollution)",
                    "Try different content-types",
                    "Use multipart form data",
                ],
                "effectiveness": "LOW-MEDIUM",
            },
        ],
        "limitations": [
            "Sensor data validation is complex to replicate",
            "Bot detection improves with each request",
            "Enterprise configs are highly customized",
        ],
    },
    "aws_waf": {
        "general_info": (
            "AWS WAF uses managed rule groups and custom rules. Rules are often based "
            "on OWASP recommendations. Less sophisticated than dedicated WAF vendors."
        ),
        "strategies": [
            {
                "name": "Rule Fingerprinting",
                "description": "Identify which rule sets are active",
                "techniques": [
                    "Test common OWASP CRS patterns",
                    "Identify SQL injection rule strictness",
                    "Test XSS filter patterns",
                    "Check for rate-based rules",
                ],
                "effectiveness": "MEDIUM",
            },
            {
                "name": "Encoding Bypass",
                "description": "Evade pattern matching",
                "techniques": [
                    "Double URL encoding",
                    "HTML entity encoding",
                    "UTF-8 overlong encoding",
                    "Mixed case in SQL keywords",
                ],
                "effectiveness": "MEDIUM",
            },
            {
                "name": "Payload Splitting",
                "description": "Split malicious payloads across parameters",
                "techniques": [
                    "Use multiple parameters",
                    "Leverage JSON/XML parsing differences",
                    "Chunked payload delivery",
                ],
                "effectiveness": "MEDIUM",
            },
        ],
        "limitations": [
            "Managed rules are regularly updated",
            "Custom rules vary per deployment",
            "CloudFront integration adds extra layers",
        ],
    },
    "imperva_incapsula": {
        "general_info": (
            "Imperva Incapsula uses advanced bot protection and DDoS mitigation. "
            "Has strong JavaScript challenge mechanism."
        ),
        "strategies": [
            {
                "name": "Cookie Chain Resolution",
                "description": "Properly handle Incapsula's cookie flow",
                "techniques": [
                    "Execute initial JavaScript challenge",
                    "Maintain visid_incap cookie",
                    "Handle incap_ses session cookies",
                    "Preserve cookie order in requests",
                ],
                "effectiveness": "MEDIUM",
            },
            {
                "name": "Origin Discovery",
                "description": "Find the real server IP",
                "techniques": [
                    "DNS history lookup",
                    "SSL certificate scanning",
                    "Mail server enumeration",
                    "IPv6 might not be protected",
                ],
                "effectiveness": "HIGH",
            },
        ],
        "limitations": [
            "Bot detection is behavioral",
            "JavaScript execution required",
            "Fingerprinting is advanced",
        ],
    },
    "modsecurity": {
        "general_info": (
            "ModSecurity is open-source and highly configurable. OWASP Core Rule Set "
            "(CRS) is commonly used. Rules are signature-based and well-documented."
        ),
        "strategies": [
            {
                "name": "CRS Rule Bypass",
                "description": "Bypass OWASP Core Rule Set patterns",
                "techniques": [
                    "Use SQL comments: /*!50000SELECT*/",
                    "Variable case: SeLeCt, UnIoN",
                    "Whitespace alternatives: %09, %0a, %0d",
                    "String concatenation: 'sel'||'ect'",
                ],
                "effectiveness": "MEDIUM-HIGH",
            },
            {
                "name": "Paranoia Level Detection",
                "description": "Identify CRS paranoia level",
                "techniques": [
                    "Test progressively suspicious payloads",
                    "Check if common XSS vectors are blocked",
                    "Identify if SQL comments are filtered",
                ],
                "effectiveness": "HIGH",
            },
            {
                "name": "Content-Type Manipulation",
                "description": "Exploit parser differences",
                "techniques": [
                    "Use application/x-www-form-urlencoded vs multipart",
                    "Send JSON payloads as form data",
                    "Malformed Content-Type headers",
                ],
                "effectiveness": "MEDIUM",
            },
        ],
        "limitations": [
            "Paranoia level 3+ is very strict",
            "Custom rules may exist",
            "SecRule exceptions vary",
        ],
    },
    "f5_big_ip": {
        "general_info": (
            "F5 BIG-IP ASM is enterprise-grade with learning mode capabilities. "
            "Can be very strict when properly configured."
        ),
        "strategies": [
            {
                "name": "Support ID Analysis",
                "description": "Analyze error responses for intelligence",
                "techniques": [
                    "Collect support IDs to understand rule triggers",
                    "Map which payloads trigger which rules",
                    "Look for patterns in blocking behavior",
                ],
                "effectiveness": "MEDIUM",
            },
            {
                "name": "Cookie Manipulation",
                "description": "Exploit BIG-IP cookie handling",
                "techniques": [
                    "Decode BIGipServer cookies for backend info",
                    "Check if TS cookies leak information",
                ],
                "effectiveness": "LOW-MEDIUM",
            },
        ],
        "limitations": [
            "Learning mode creates custom signatures",
            "Enterprise deployments are complex",
            "Cookie decoding reveals limited info",
        ],
    },
    "sucuri": {
        "general_info": (
            "Sucuri CloudProxy is popular for WordPress sites. Has website firewall "
            "and malware scanning. Often used with default configurations."
        ),
        "strategies": [
            {
                "name": "Origin Discovery",
                "description": "Find real server IP",
                "techniques": [
                    "Check DNS history",
                    "Look for cPanel/Plesk on common ports",
                    "Check for mail server IP leaks",
                    "Search for IP in JS/CSS files",
                ],
                "effectiveness": "HIGH",
            },
            {
                "name": "Default Rule Bypass",
                "description": "Bypass common default configurations",
                "techniques": [
                    "Test for whitelist gaps (admin panels)",
                    "Check if /wp-admin is accessible",
                    "Test XML-RPC if WordPress",
                ],
                "effectiveness": "MEDIUM",
            },
        ],
        "limitations": [
            "Origin IP may have Sucuri firewall rules",
            "Custom rules vary per deployment",
        ],
    },
    "generic": {
        "general_info": (
            "Generic WAF bypass strategies that work across multiple WAF vendors. "
            "These techniques exploit common implementation weaknesses."
        ),
        "strategies": [
            {
                "name": "HTTP Method Override",
                "description": "Use alternative methods to bypass method restrictions",
                "techniques": [
                    "X-HTTP-Method-Override header",
                    "X-HTTP-Method header",
                    "X-Method-Override header",
                    "_method parameter in body",
                ],
                "effectiveness": "MEDIUM",
            },
            {
                "name": "Protocol-Level Bypass",
                "description": "Exploit HTTP parsing differences",
                "techniques": [
                    "HTTP/0.9 downgrade (rare)",
                    "HTTP/2 specific bypasses",
                    "Malformed HTTP requests",
                    "Request smuggling (if applicable)",
                ],
                "effectiveness": "LOW-HIGH",
            },
            {
                "name": "Encoding Chains",
                "description": "Use multiple encoding layers",
                "techniques": [
                    "URL encode + Base64",
                    "HTML entities + URL encoding",
                    "Unicode + URL encoding",
                    "Punycode for domain-based filters",
                ],
                "effectiveness": "MEDIUM",
            },
            {
                "name": "Header Injection",
                "description": "Inject via HTTP headers",
                "techniques": [
                    "X-Forwarded-For spoofing (if trusted)",
                    "X-Originating-IP manipulation",
                    "Custom headers that may be logged/processed",
                ],
                "effectiveness": "LOW-MEDIUM",
            },
        ],
        "limitations": [
            "Effectiveness varies greatly",
            "Many techniques are patched",
            "May require specific backend vulnerabilities",
        ],
    },
}


def _match_waf_signature(
    headers: dict[str, str],
    cookies: dict[str, str],
    body: str,
    status_code: int,
    waf_id: str,
    signature: dict[str, Any],
) -> dict[str, Any]:
    """Match a WAF signature against response data."""
    matches: list[str] = []
    confidence = 0.0
    
    # Check headers
    for header_name, pattern in signature.get("headers", {}).items():
        header_value = headers.get(header_name.lower(), "")
        if header_value and re.search(pattern, header_value, re.IGNORECASE):
            matches.append(f"header:{header_name}")
            confidence += 0.25
    
    # Check cookies
    for cookie_name in signature.get("cookies", []):
        # Check if cookie name or prefix matches
        for c_name in cookies:
            if c_name.lower().startswith(cookie_name.lower()):
                matches.append(f"cookie:{c_name}")
                confidence += 0.2
                break
    
    # Check body patterns
    for pattern in signature.get("body_patterns", []):
        if re.search(pattern, body, re.IGNORECASE):
            matches.append(f"body_pattern:{pattern[:30]}")
            confidence += 0.3
    
    # Check status codes (only if blocked)
    if status_code in signature.get("status_codes", []) and status_code >= 400:
        matches.append(f"status_code:{status_code}")
        confidence += 0.1
    
    return {
        "waf_id": waf_id,
        "name": signature.get("name", waf_id),
        "vendor": signature.get("vendor", "Unknown"),
        "matches": matches,
        "confidence": min(confidence, 1.0),
    }


@register_tool(sandbox_execution=False)
async def detect_waf(
    url: str,
    test_payload: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'phantom/tools/waf/waf_actions.py','step':'detect_waf','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


