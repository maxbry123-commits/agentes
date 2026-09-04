# -*- coding: utf-8 -*-
"""VersionPin normalizer — A-SE-01. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SOURCE_TYPES = frozenset({"git", "hf", "release", "package", "url", "local"})
DIGEST_ALGOS = frozenset({"sha256", "git_commit"})
SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
GIT_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)


class VersionPinError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _require(obj: dict, key: str) -> Any:
    if key not in obj or obj[key] is None or obj[key] == "":
        raise VersionPinError("MISSING_FIELD", key)
    return obj[key]


def normalize_pin(raw: dict[str, Any] | None) -> dict[str, Any]:
    if raw is None or not isinstance(raw, dict):
        raise VersionPinError("MISSING_PIN")

    if _require(raw, "schema_version") != "1.0":
        raise VersionPinError("INVALID_SCHEMA", "schema_version")

    pin_id = str(_require(raw, "pin_id"))
    source_type = _require(raw, "source_type")
    if source_type not in SOURCE_TYPES:
        raise VersionPinError("INVALID_SOURCE_TYPE", str(source_type))

    locator = _require(raw, "locator")
    if not isinstance(locator, dict) or not locator.get("uri"):
        raise VersionPinError("INVALID_LOCATOR", "uri required")

    digest = _require(raw, "digest")
    if not isinstance(digest, dict):
        raise VersionPinError("INVALID_DIGEST")
    algo = digest.get("algo")
    value = digest.get("value")
    if algo not in DIGEST_ALGOS:
        raise VersionPinError("INVALID_DIGEST_ALGO", str(algo))
    if not value or not isinstance(value, str):
        raise VersionPinError("INVALID_DIGEST_VALUE")
    if algo == "sha256" and not SHA256_RE.match(value):
        raise VersionPinError("INVALID_DIGEST_VALUE", "sha256 must be 64 hex")
    if algo == "git_commit" and not GIT_SHA_RE.match(value):
        raise VersionPinError("INVALID_DIGEST_VALUE", "git_commit 7-40 hex")

    pin: dict[str, Any] = {
        "schema_version": "1.0",
        "pin_id": pin_id,
        "source_type": source_type,
        "locator": {
            "uri": locator["uri"],
            "ref": locator.get("ref"),
            "path": locator.get("path"),
            "package_name": locator.get("package_name"),
            "version": locator.get("version"),
        },
        "digest": {"algo": algo, "value": value.lower()},
        "license": raw.get("license"),
        "llm_control": raw.get("llm_control") or "DENY",
        "meta": dict(raw.get("meta") or {}),
    }
    pin["pin_hash"] = pin_hash(pin)
    return pin


def pin_hash(pin: dict[str, Any]) -> str:
    body = {k: v for k, v in pin.items() if k != "pin_hash"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def pins_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    da = a.get("digest") or {}
    db = b.get("digest") or {}
    return da.get("algo") == db.get("algo") and da.get("value") == db.get("value")
