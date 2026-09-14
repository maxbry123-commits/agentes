"""AACS Token Validator — signature, expiry, nonce and revocation checks."""

from __future__ import annotations

import time
import typing
from collections import OrderedDict
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature

from cognithor.aacs.config import AACS_CONFIG

if typing.TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    from cognithor.aacs.tokens.capability_token import CapabilityToken

__all__ = [
    "DIDResolver",
    "NonceCache",
    "RevokedTokenStore",
    "TokenValidator",
    "ValidationResult",
]


class NonceCache:
    """LRU cache for replay protection."""

    def __init__(self, max_size: int = AACS_CONFIG.nonce_cache_size) -> None:
        self._cache: OrderedDict[str, float] = OrderedDict()
        self._max_size = max_size

    def check_and_store(self, nonce: str) -> bool:
        """Return True if *nonce* is new, False if it is a replay."""
        now = time.monotonic()
        self._evict_expired(now)

        if nonce in self._cache:
            return False

        # Evict oldest if at capacity
        while len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)

        self._cache[nonce] = now
        return True

    def _evict_expired(self, now: float) -> None:
        """Remove entries older than ``AACS_CONFIG.nonce_expiry_seconds``."""
        expiry = AACS_CONFIG.nonce_expiry_seconds
        to_delete: list[str] = []
        for nonce, ts in self._cache.items():
            if now - ts > expiry:
                to_delete.append(nonce)
            else:
                break  # OrderedDict is insertion-ordered; rest are newer
        for nonce in to_delete:
            del self._cache[nonce]


class RevokedTokenStore:
    """In-memory set of revoked token IDs."""

    def __init__(self) -> None:
        self._revoked: set[str] = set()

    def revoke(self, token_id: str) -> None:
        """Mark *token_id* as revoked."""
        self._revoked.add(token_id)

    def is_revoked(self, token_id: str) -> bool:
        """Return True if *token_id* has been revoked."""
        return token_id in self._revoked


class DIDResolver:
    """Dict-based mapping of DID strings to Ed25519 public keys."""

    def __init__(self) -> None:
        self._keys: dict[str, Ed25519PublicKey] = {}

    def register(self, did: str, public_key: Ed25519PublicKey) -> None:
        """Register a public key for *did*."""
        self._keys[did] = public_key

    def resolve(self, did: str) -> Ed25519PublicKey | None:
        """Return the public key for *did*, or ``None`` if unknown."""
        return self._keys.get(did)


@dataclass
class ValidationResult:
    """Result of token validation."""

    valid: bool
    token: CapabilityToken | None = None
    error: str = ""
    error_type: str = ""


class TokenValidator:
    """Validates capability tokens in fail-fast order.

    Checks: 1) Signature  2) Expiry  3) Nonce  4) Revocation
    """

    def __init__(
        self,
        did_resolver: DIDResolver | None = None,
        nonce_cache: NonceCache | None = None,
        revoked_store: RevokedTokenStore | None = None,
    ) -> None:
        self._did_resolver = did_resolver or DIDResolver()
        self._nonce_cache = nonce_cache or NonceCache()
        self._revoked_store = revoked_store or RevokedTokenStore()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, token: CapabilityToken) -> ValidationResult:
        """Run all checks in fail-fast order and return a :class:`ValidationResult`."""
        # 1. Signature
        public_key = self._did_resolver.resolve(token.issuer_did)
        if public_key is None:
            return ValidationResult(
                valid=False,
                error=f"Unknown issuer DID: {token.issuer_did}",
                error_type="UNKNOWN_ISSUER",
            )
        try:
            public_key.verify(token.signature, token.payload_bytes())
        except InvalidSignature:
            return ValidationResult(
                valid=False,
                error="Ed25519 signature verification failed.",
                error_type="INVALID_SIGNATURE",
            )

        # 2. Expiry
        if token.is_expired:
            return ValidationResult(
                valid=False,
                error="Token has expired.",
                error_type="EXPIRED",
            )

        # 3. Nonce (replay protection)
        if not self._nonce_cache.check_and_store(token.nonce):
            return ValidationResult(
                valid=False,
                error=f"Nonce replay detected: {token.nonce}",
                error_type="REPLAY_ATTACK",
            )

        # 4. Revocation
        if self._revoked_store.is_revoked(token.token_id):
            return ValidationResult(
                valid=False,
                error=f"Token {token.token_id} has been revoked.",
                error_type="REVOKED",
            )

        return ValidationResult(valid=True, token=token)

    def revoke_token(self, token_id: str) -> None:
        """Revoke a token by its ID."""
        self._revoked_store.revoke(token_id)
