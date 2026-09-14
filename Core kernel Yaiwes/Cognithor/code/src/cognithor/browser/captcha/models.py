"""CAPTCHA data models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = ["CaptchaChallenge", "CaptchaType", "SolveResult"]


class CaptchaType(StrEnum):
    TEXT = "text"
    RECAPTCHA_V2_CHECKBOX = "recaptcha_v2_checkbox"
    RECAPTCHA_V2_IMAGE = "recaptcha_v2_image"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    TURNSTILE = "turnstile"
    FUNCAPTCHA = "funcaptcha"
    UNKNOWN = "unknown"


@dataclass
class CaptchaChallenge:
    """Detected CAPTCHA on a page."""

    captcha_type: CaptchaType
    selector: str
    sitekey: str = ""
    iframe_url: str = ""
    page_url: str = ""
    screenshot_b64: str = ""
    challenge_text: str = ""


@dataclass
class SolveResult:
    """Result of a CAPTCHA solve attempt."""

    success: bool
    captcha_type: CaptchaType
    model_used: str
    attempts: int
    duration_ms: int
    answer: str = ""
    error: str = ""
