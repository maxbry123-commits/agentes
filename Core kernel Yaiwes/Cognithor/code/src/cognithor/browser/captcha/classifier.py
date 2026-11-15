"""CAPTCHA classifier — determines strategy and model for each type."""

from __future__ import annotations

from dataclasses import dataclass

from cognithor.browser.captcha.models import CaptchaChallenge, CaptchaType

__all__ = ["ChallengeProfile", "classify_challenge", "select_vision_model"]

_MODEL_MAP: dict[CaptchaType, str] = {
    CaptchaType.TEXT: "openbmb/minicpm-v4.5:latest",
    CaptchaType.RECAPTCHA_V2_CHECKBOX: "",
    CaptchaType.RECAPTCHA_V2_IMAGE: "qwen3-vl:32b",
    CaptchaType.RECAPTCHA_V3: "",
    CaptchaType.HCAPTCHA: "qwen3-vl:32b",
    CaptchaType.TURNSTILE: "openbmb/minicpm-v4.5:latest",
    CaptchaType.FUNCAPTCHA: "qwen3-vl:32b",
    CaptchaType.UNKNOWN: "qwen3-vl:32b",
}


@dataclass
class ChallengeProfile:
    needs_vision: bool = False
    needs_click: bool = False
    needs_stealth: bool = False
    may_escalate: bool = False
    complexity: str = "simple"


def classify_challenge(challenge: CaptchaChallenge) -> ChallengeProfile:
    t = challenge.captcha_type
    if t == CaptchaType.TEXT:
        return ChallengeProfile(needs_vision=True, complexity="simple")
    if t == CaptchaType.RECAPTCHA_V2_CHECKBOX:
        return ChallengeProfile(
            needs_click=True,
            may_escalate=True,
            needs_stealth=True,
            complexity="simple",
        )
    if t == CaptchaType.RECAPTCHA_V2_IMAGE:
        return ChallengeProfile(needs_vision=True, needs_click=True, complexity="complex")
    if t == CaptchaType.RECAPTCHA_V3:
        return ChallengeProfile(needs_stealth=True, complexity="simple")
    if t == CaptchaType.HCAPTCHA:
        return ChallengeProfile(
            needs_vision=True,
            needs_click=True,
            may_escalate=True,
            complexity="complex",
        )
    if t == CaptchaType.TURNSTILE:
        return ChallengeProfile(needs_stealth=True, needs_click=True, complexity="simple")
    if t == CaptchaType.FUNCAPTCHA:
        return ChallengeProfile(needs_vision=True, needs_click=True, complexity="complex")
    return ChallengeProfile(needs_vision=True, complexity="complex")


def select_vision_model(captcha_type: CaptchaType) -> str:
    return _MODEL_MAP.get(captcha_type, "qwen3-vl:32b")
