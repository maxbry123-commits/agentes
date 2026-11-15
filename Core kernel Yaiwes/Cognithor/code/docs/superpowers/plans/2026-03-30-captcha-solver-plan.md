# CAPTCHA Solver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add CAPTCHA detection, classification, and solving to Cognithor's browser automation — purely via local Vision-LLMs, no external services.

**Architecture:** New `browser/captcha/` package with detector (JS-based page scan), classifier (type determination), solver (orchestrator with retry), strategies (per-type Vision-LLM prompts), and stealth (anti-detection). Integrates into existing BrowserAgent (auto-detect after navigation) and exposes one MCP tool (`browser_solve_captcha`).

**Tech Stack:** Python 3.13, Playwright, Ollama Vision models (minicpm-v4.5, qwen3-vl:32b), existing VisionAnalyzer

---

### Task 1: Data Models

**Files:**
- Create: `src/jarvis/browser/captcha/__init__.py`
- Create: `src/jarvis/browser/captcha/models.py`
- Test: `tests/test_captcha/__init__.py`
- Test: `tests/test_captcha/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_captcha/__init__.py
# (empty)

# tests/test_captcha/test_models.py
"""Tests for CAPTCHA data models."""
from __future__ import annotations

from jarvis.browser.captcha.models import CaptchaType, CaptchaChallenge, SolveResult


def test_captcha_type_values():
    assert CaptchaType.TEXT == "text"
    assert CaptchaType.RECAPTCHA_V2_CHECKBOX == "recaptcha_v2_checkbox"
    assert CaptchaType.RECAPTCHA_V2_IMAGE == "recaptcha_v2_image"
    assert CaptchaType.RECAPTCHA_V3 == "recaptcha_v3"
    assert CaptchaType.HCAPTCHA == "hcaptcha"
    assert CaptchaType.TURNSTILE == "turnstile"
    assert CaptchaType.FUNCAPTCHA == "funcaptcha"
    assert CaptchaType.UNKNOWN == "unknown"


def test_captcha_challenge_defaults():
    c = CaptchaChallenge(captcha_type=CaptchaType.TEXT, selector="img.captcha")
    assert c.sitekey == ""
    assert c.iframe_url == ""
    assert c.page_url == ""
    assert c.screenshot_b64 == ""


def test_solve_result_success():
    r = SolveResult(
        success=True, captcha_type=CaptchaType.TEXT,
        model_used="minicpm-v4.5", attempts=1, duration_ms=1200,
        answer="abc123",
    )
    assert r.success
    assert r.error == ""


def test_solve_result_failure():
    r = SolveResult(
        success=False, captcha_type=CaptchaType.RECAPTCHA_V2_IMAGE,
        model_used="qwen3-vl:32b", attempts=3, duration_ms=15000,
        error="Vision model could not identify images",
    )
    assert not r.success
    assert r.attempts == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /d/Jarvis/jarvis\ complete\ v20 && python -m pytest tests/test_captcha/test_models.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement models**

```python
# src/jarvis/browser/captcha/__init__.py
"""CAPTCHA detection and solving for Cognithor browser automation."""
from __future__ import annotations

from jarvis.browser.captcha.models import CaptchaChallenge, CaptchaType, SolveResult

__all__ = ["CaptchaChallenge", "CaptchaType", "SolveResult"]
```

```python
# src/jarvis/browser/captcha/models.py
"""CAPTCHA data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

__all__ = ["CaptchaType", "CaptchaChallenge", "SolveResult"]


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
    challenge_text: str = ""  # e.g. "Select all images with traffic lights"


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_captcha/test_models.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/browser/captcha/ tests/test_captcha/
git commit -m "feat(captcha): data models — CaptchaType, CaptchaChallenge, SolveResult"
```

---

### Task 2: Stealth Module

**Files:**
- Create: `src/jarvis/browser/captcha/stealth.py`
- Test: `tests/test_captcha/test_stealth.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_captcha/test_stealth.py
"""Tests for browser stealth configuration."""
from __future__ import annotations

from jarvis.browser.captcha.stealth import (
    STEALTH_ARGS,
    STEALTH_JS,
    REALISTIC_USER_AGENT,
    DEFAULT_VIEWPORT,
    get_stealth_launch_opts,
    get_stealth_context_opts,
)


def test_stealth_args_disables_automation():
    assert any("AutomationControlled" in a for a in STEALTH_ARGS)


def test_stealth_js_hides_webdriver():
    assert "webdriver" in STEALTH_JS
    assert "false" in STEALTH_JS


def test_realistic_user_agent():
    assert "Chrome/" in REALISTIC_USER_AGENT
    assert "Windows NT" in REALISTIC_USER_AGENT


def test_default_viewport():
    assert DEFAULT_VIEWPORT["width"] == 1280
    assert DEFAULT_VIEWPORT["height"] == 720


def test_get_stealth_launch_opts():
    opts = get_stealth_launch_opts(headless=True)
    assert opts["headless"] is True
    assert "args" in opts
    assert any("AutomationControlled" in a for a in opts["args"])


def test_get_stealth_context_opts():
    opts = get_stealth_context_opts()
    assert "user_agent" in opts
    assert "viewport" in opts
    assert opts["viewport"]["width"] == 1280


def test_stealth_disabled():
    opts = get_stealth_launch_opts(headless=True, stealth=False)
    assert "args" not in opts or not any(
        "AutomationControlled" in a for a in opts.get("args", [])
    )
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement stealth.py**

```python
# src/jarvis/browser/captcha/stealth.py
"""Browser stealth — anti-bot-detection basics for Playwright."""
from __future__ import annotations

from typing import Any

__all__ = [
    "STEALTH_ARGS",
    "STEALTH_JS",
    "REALISTIC_USER_AGENT",
    "DEFAULT_VIEWPORT",
    "get_stealth_launch_opts",
    "get_stealth_context_opts",
]

STEALTH_ARGS: list[str] = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-dev-shm-usage",
]

STEALTH_JS = """\
Object.defineProperty(navigator, 'webdriver', {get: () => false});
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});
Object.defineProperty(navigator, 'languages', {
    get: () => ['de-DE', 'de', 'en-US', 'en'],
});
if (!window.chrome) window.chrome = {runtime: {}};
"""

REALISTIC_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

DEFAULT_VIEWPORT = {"width": 1280, "height": 720}


def get_stealth_launch_opts(
    *, headless: bool = True, stealth: bool = True,
) -> dict[str, Any]:
    """Return Playwright launch kwargs with optional stealth args."""
    opts: dict[str, Any] = {"headless": headless}
    if stealth:
        opts["args"] = list(STEALTH_ARGS)
    return opts


def get_stealth_context_opts(*, stealth: bool = True) -> dict[str, Any]:
    """Return Playwright context kwargs with stealth user-agent + viewport."""
    opts: dict[str, Any] = {
        "viewport": dict(DEFAULT_VIEWPORT),
        "locale": "de-DE",
        "timezone_id": "Europe/Berlin",
    }
    if stealth:
        opts["user_agent"] = REALISTIC_USER_AGENT
    return opts
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/browser/captcha/stealth.py tests/test_captcha/test_stealth.py
git commit -m "feat(captcha): browser stealth — launch args + JS injection"
```

---

### Task 3: Detector

**Files:**
- Create: `src/jarvis/browser/captcha/detector.py`
- Test: `tests/test_captcha/test_detector.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_captcha/test_detector.py
"""Tests for CAPTCHA detector."""
from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from jarvis.browser.captcha.detector import detect_captcha, DETECT_JS
from jarvis.browser.captcha.models import CaptchaType


def _mock_page(js_result: list[dict]) -> MagicMock:
    page = MagicMock()
    page.evaluate = AsyncMock(return_value=js_result)
    page.url = "https://example.com/login"
    return page


@pytest.mark.asyncio
async def test_detect_recaptcha_v2():
    page = _mock_page([{
        "type": "recaptcha_v2",
        "selector": ".g-recaptcha",
        "sitekey": "6Le-ABC",
    }])
    challenges = await detect_captcha(page)
    assert len(challenges) == 1
    assert challenges[0].captcha_type == CaptchaType.RECAPTCHA_V2_CHECKBOX
    assert challenges[0].sitekey == "6Le-ABC"


@pytest.mark.asyncio
async def test_detect_hcaptcha():
    page = _mock_page([{
        "type": "hcaptcha",
        "selector": ".h-captcha",
        "sitekey": "abc-123",
    }])
    challenges = await detect_captcha(page)
    assert len(challenges) == 1
    assert challenges[0].captcha_type == CaptchaType.HCAPTCHA


@pytest.mark.asyncio
async def test_detect_turnstile():
    page = _mock_page([{
        "type": "turnstile",
        "selector": ".cf-turnstile",
        "sitekey": "0x4AAA",
    }])
    challenges = await detect_captcha(page)
    assert len(challenges) == 1
    assert challenges[0].captcha_type == CaptchaType.TURNSTILE


@pytest.mark.asyncio
async def test_detect_text_captcha():
    page = _mock_page([{
        "type": "text",
        "selector": "img.captcha-image",
        "sitekey": "",
    }])
    challenges = await detect_captcha(page)
    assert len(challenges) == 1
    assert challenges[0].captcha_type == CaptchaType.TEXT


@pytest.mark.asyncio
async def test_detect_none():
    page = _mock_page([])
    challenges = await detect_captcha(page)
    assert len(challenges) == 0


@pytest.mark.asyncio
async def test_detect_multiple():
    page = _mock_page([
        {"type": "recaptcha_v2", "selector": ".g-recaptcha", "sitekey": "abc"},
        {"type": "hcaptcha", "selector": ".h-captcha", "sitekey": "def"},
    ])
    challenges = await detect_captcha(page)
    assert len(challenges) == 2


@pytest.mark.asyncio
async def test_detect_js_error_returns_empty():
    page = MagicMock()
    page.evaluate = AsyncMock(side_effect=Exception("JS error"))
    page.url = "https://example.com"
    challenges = await detect_captcha(page)
    assert len(challenges) == 0


def test_detect_js_contains_selectors():
    assert "g-recaptcha" in DETECT_JS
    assert "h-captcha" in DETECT_JS
    assert "cf-turnstile" in DETECT_JS
    assert "FunCaptcha" in DETECT_JS
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement detector.py**

```python
# src/jarvis/browser/captcha/detector.py
"""CAPTCHA detection — JS-based page scan."""
from __future__ import annotations

from typing import Any

from jarvis.browser.captcha.models import CaptchaChallenge, CaptchaType
from jarvis.utils.logging import get_logger

log = get_logger(__name__)

__all__ = ["detect_captcha", "DETECT_JS"]

_TYPE_MAP = {
    "recaptcha_v2": CaptchaType.RECAPTCHA_V2_CHECKBOX,
    "recaptcha_v3": CaptchaType.RECAPTCHA_V3,
    "hcaptcha": CaptchaType.HCAPTCHA,
    "turnstile": CaptchaType.TURNSTILE,
    "funcaptcha": CaptchaType.FUNCAPTCHA,
    "text": CaptchaType.TEXT,
}

DETECT_JS = """\
(() => {
    const results = [];

    // reCAPTCHA v2
    const rc2 = document.querySelector('.g-recaptcha, [data-sitekey]:not(.cf-turnstile):not(.h-captcha)');
    if (rc2) {
        results.push({
            type: 'recaptcha_v2',
            selector: rc2.className ? '.' + rc2.className.split(' ')[0] : '[data-sitekey]',
            sitekey: rc2.getAttribute('data-sitekey') || '',
        });
    }

    // reCAPTCHA v3 (invisible — script present but no visible widget)
    if (!rc2 && document.querySelector('script[src*="recaptcha"]')) {
        const v3 = typeof grecaptcha !== 'undefined';
        if (v3) results.push({type: 'recaptcha_v3', selector: '', sitekey: ''});
    }

    // hCaptcha
    const hc = document.querySelector('.h-captcha, [data-hcaptcha-sitekey]');
    if (hc) {
        results.push({
            type: 'hcaptcha',
            selector: hc.className ? '.' + hc.className.split(' ')[0] : '.h-captcha',
            sitekey: hc.getAttribute('data-sitekey') || hc.getAttribute('data-hcaptcha-sitekey') || '',
        });
    }

    // Cloudflare Turnstile
    const ts = document.querySelector('.cf-turnstile, [data-sitekey][data-appearance]');
    if (ts) {
        results.push({
            type: 'turnstile',
            selector: ts.className ? '.' + ts.className.split(' ')[0] : '.cf-turnstile',
            sitekey: ts.getAttribute('data-sitekey') || '',
        });
    }

    // FunCaptcha / Arkose Labs
    const fc = document.querySelector('#FunCaptcha, [data-pkey], iframe[src*="arkoselabs"]');
    if (fc) {
        results.push({
            type: 'funcaptcha',
            selector: fc.id ? '#' + fc.id : '[data-pkey]',
            sitekey: fc.getAttribute('data-pkey') || '',
        });
    }

    // Text CAPTCHA (heuristic: img near a short text input)
    if (results.length === 0) {
        const imgs = document.querySelectorAll('img[src*="captcha"], img[alt*="captcha"], img[class*="captcha"]');
        for (const img of imgs) {
            const input = img.parentElement?.querySelector('input[type="text"]')
                       || img.closest('form')?.querySelector('input[type="text"]');
            if (input) {
                results.push({
                    type: 'text',
                    selector: img.className ? 'img.' + img.className.split(' ')[0] : 'img[src*="captcha"]',
                    sitekey: '',
                });
                break;
            }
        }
    }

    return results;
})()
"""


async def detect_captcha(page: Any) -> list[CaptchaChallenge]:
    """Run JS detection on a Playwright page, return found CAPTCHAs."""
    try:
        raw = await page.evaluate(DETECT_JS)
    except Exception:
        log.debug("captcha_detect_js_failed", exc_info=True)
        return []

    if not raw or not isinstance(raw, list):
        return []

    challenges = []
    for entry in raw:
        ctype = _TYPE_MAP.get(entry.get("type", ""), CaptchaType.UNKNOWN)
        challenges.append(CaptchaChallenge(
            captcha_type=ctype,
            selector=entry.get("selector", ""),
            sitekey=entry.get("sitekey", ""),
            page_url=getattr(page, "url", ""),
        ))

    if challenges:
        log.info("captcha_detected", count=len(challenges),
                 types=[c.captcha_type.value for c in challenges])

    return challenges
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/browser/captcha/detector.py tests/test_captcha/test_detector.py
git commit -m "feat(captcha): JS-based CAPTCHA detector — 7 types supported"
```

---

### Task 4: Classifier

**Files:**
- Create: `src/jarvis/browser/captcha/classifier.py`
- Test: `tests/test_captcha/test_classifier.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_captcha/test_classifier.py
"""Tests for CAPTCHA classifier."""
from __future__ import annotations

from jarvis.browser.captcha.classifier import classify_challenge, select_vision_model
from jarvis.browser.captcha.models import CaptchaChallenge, CaptchaType


def test_classify_text():
    c = CaptchaChallenge(captcha_type=CaptchaType.TEXT, selector="img.captcha")
    result = classify_challenge(c)
    assert result.needs_vision is True
    assert result.needs_click is False
    assert result.complexity == "simple"


def test_classify_recaptcha_v2_checkbox():
    c = CaptchaChallenge(
        captcha_type=CaptchaType.RECAPTCHA_V2_CHECKBOX, selector=".g-recaptcha",
    )
    result = classify_challenge(c)
    assert result.needs_click is True
    assert result.may_escalate is True  # might become image challenge


def test_classify_recaptcha_v2_image():
    c = CaptchaChallenge(
        captcha_type=CaptchaType.RECAPTCHA_V2_IMAGE, selector=".g-recaptcha",
    )
    result = classify_challenge(c)
    assert result.needs_vision is True
    assert result.complexity == "complex"


def test_classify_recaptcha_v3():
    c = CaptchaChallenge(captcha_type=CaptchaType.RECAPTCHA_V3, selector="")
    result = classify_challenge(c)
    assert result.needs_vision is False
    assert result.needs_stealth is True


def test_select_model_simple():
    model = select_vision_model(CaptchaType.TEXT)
    assert "minicpm" in model


def test_select_model_complex():
    model = select_vision_model(CaptchaType.RECAPTCHA_V2_IMAGE)
    assert "qwen3-vl" in model


def test_select_model_no_vision():
    model = select_vision_model(CaptchaType.RECAPTCHA_V3)
    assert model == ""
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement classifier.py**

```python
# src/jarvis/browser/captcha/classifier.py
"""CAPTCHA classifier — determines strategy and model for each type."""
from __future__ import annotations

from dataclasses import dataclass

from jarvis.browser.captcha.models import CaptchaChallenge, CaptchaType

__all__ = ["ChallengeProfile", "classify_challenge", "select_vision_model"]

# Model selection: simple → small parallel model, complex → large model
_MODEL_MAP: dict[CaptchaType, str] = {
    CaptchaType.TEXT: "openbmb/minicpm-v4.5:latest",
    CaptchaType.RECAPTCHA_V2_CHECKBOX: "",  # click only, no vision initially
    CaptchaType.RECAPTCHA_V2_IMAGE: "qwen3-vl:32b",
    CaptchaType.RECAPTCHA_V3: "",  # stealth only
    CaptchaType.HCAPTCHA: "qwen3-vl:32b",
    CaptchaType.TURNSTILE: "openbmb/minicpm-v4.5:latest",
    CaptchaType.FUNCAPTCHA: "qwen3-vl:32b",
    CaptchaType.UNKNOWN: "qwen3-vl:32b",
}


@dataclass
class ChallengeProfile:
    """Classification result for a CAPTCHA challenge."""

    needs_vision: bool = False
    needs_click: bool = False
    needs_stealth: bool = False
    may_escalate: bool = False  # checkbox might become image challenge
    complexity: str = "simple"  # simple | complex


def classify_challenge(challenge: CaptchaChallenge) -> ChallengeProfile:
    """Determine the strategy profile for a detected CAPTCHA."""
    t = challenge.captcha_type

    if t == CaptchaType.TEXT:
        return ChallengeProfile(needs_vision=True, complexity="simple")

    if t == CaptchaType.RECAPTCHA_V2_CHECKBOX:
        return ChallengeProfile(
            needs_click=True, may_escalate=True, needs_stealth=True,
            complexity="simple",
        )

    if t == CaptchaType.RECAPTCHA_V2_IMAGE:
        return ChallengeProfile(
            needs_vision=True, needs_click=True, complexity="complex",
        )

    if t == CaptchaType.RECAPTCHA_V3:
        return ChallengeProfile(needs_stealth=True, complexity="simple")

    if t == CaptchaType.HCAPTCHA:
        return ChallengeProfile(
            needs_vision=True, needs_click=True, may_escalate=True,
            complexity="complex",
        )

    if t == CaptchaType.TURNSTILE:
        return ChallengeProfile(
            needs_stealth=True, needs_click=True, complexity="simple",
        )

    if t == CaptchaType.FUNCAPTCHA:
        return ChallengeProfile(
            needs_vision=True, needs_click=True, complexity="complex",
        )

    return ChallengeProfile(needs_vision=True, complexity="complex")


def select_vision_model(captcha_type: CaptchaType) -> str:
    """Select the appropriate vision model for a CAPTCHA type."""
    return _MODEL_MAP.get(captcha_type, "qwen3-vl:32b")
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/browser/captcha/classifier.py tests/test_captcha/test_classifier.py
git commit -m "feat(captcha): classifier — challenge profiling + model selection"
```

---

### Task 5: Solve Strategies

**Files:**
- Create: `src/jarvis/browser/captcha/strategies.py`
- Test: `tests/test_captcha/test_strategies.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_captcha/test_strategies.py
"""Tests for CAPTCHA solve strategies."""
from __future__ import annotations

import pytest
from jarvis.browser.captcha.strategies import (
    build_text_captcha_prompt,
    build_image_grid_prompt,
    parse_text_answer,
    parse_grid_coordinates,
    get_strategy,
)
from jarvis.browser.captcha.models import CaptchaType


def test_build_text_prompt():
    prompt = build_text_captcha_prompt()
    assert "verzerrten Text" in prompt or "distorted text" in prompt.lower()


def test_build_image_grid_prompt():
    prompt = build_image_grid_prompt("Select all images with traffic lights")
    assert "traffic lights" in prompt


def test_parse_text_answer_clean():
    assert parse_text_answer("abc123") == "abc123"


def test_parse_text_answer_strips_quotes():
    assert parse_text_answer('"abc123"') == "abc123"


def test_parse_text_answer_strips_explanation():
    assert parse_text_answer("The text reads: abc123") == "abc123"


def test_parse_grid_coordinates_valid():
    coords = parse_grid_coordinates("[[0,1],[1,2],[2,0]]")
    assert coords == [(0, 1), (1, 2), (2, 0)]


def test_parse_grid_coordinates_from_text():
    coords = parse_grid_coordinates(
        "The matching images are at positions [[0,2],[1,1]]"
    )
    assert coords == [(0, 2), (1, 1)]


def test_parse_grid_coordinates_empty():
    coords = parse_grid_coordinates("I cannot identify any matching images")
    assert coords == []


def test_get_strategy_returns_callable():
    for ct in [CaptchaType.TEXT, CaptchaType.RECAPTCHA_V2_CHECKBOX,
               CaptchaType.RECAPTCHA_V2_IMAGE, CaptchaType.HCAPTCHA,
               CaptchaType.TURNSTILE]:
        s = get_strategy(ct)
        assert s is not None
        assert callable(s)
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement strategies.py**

Create `src/jarvis/browser/captcha/strategies.py` containing:

- `build_text_captcha_prompt() -> str` — German prompt for Vision-LLM to read distorted text
- `build_image_grid_prompt(challenge_text: str) -> str` — prompt for image grid selection
- `parse_text_answer(raw: str) -> str` — extract clean text from LLM response
- `parse_grid_coordinates(raw: str) -> list[tuple[int, int]]` — extract [[row,col]] coordinates from LLM response via regex
- `get_strategy(captcha_type: CaptchaType) -> Callable` — returns the async strategy function for each type

Each strategy function has signature: `async def strategy(page, challenge, vision_fn) -> SolveResult`

Strategy implementations:
- **text_strategy**: screenshot element → vision prompt → parse answer → fill input → submit
- **checkbox_strategy**: click checkbox → wait → check if solved or escalated to image
- **image_grid_strategy**: screenshot iframe → extract challenge text → vision prompt → parse coords → click cells → verify
- **stealth_strategy**: wait for auto-solve (turnstile, recaptcha v3) → check token
- **generic_strategy**: screenshot → generic vision prompt → attempt interaction

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/browser/captcha/strategies.py tests/test_captcha/test_strategies.py
git commit -m "feat(captcha): solve strategies — text, checkbox, image grid, stealth"
```

---

### Task 6: Solver Orchestrator

**Files:**
- Create: `src/jarvis/browser/captcha/solver.py`
- Test: `tests/test_captcha/test_solver.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_captcha/test_solver.py
"""Tests for CAPTCHA solver orchestrator."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from jarvis.browser.captcha.solver import CaptchaSolver, CaptchaConfig
from jarvis.browser.captcha.models import CaptchaType, CaptchaChallenge, SolveResult


@pytest.fixture
def solver():
    return CaptchaSolver(
        vision_fn=AsyncMock(return_value="abc123"),
        config=CaptchaConfig(),
    )


@pytest.fixture
def mock_page():
    page = MagicMock()
    page.evaluate = AsyncMock(return_value=[])
    page.url = "https://example.com"
    return page


@pytest.mark.asyncio
async def test_solve_no_captcha(solver, mock_page):
    result = await solver.solve(mock_page)
    assert result.success is True
    assert result.captcha_type == CaptchaType.UNKNOWN
    assert "no captcha" in result.answer.lower() or result.answer == ""


@pytest.mark.asyncio
async def test_solve_with_detected_challenge(solver, mock_page):
    mock_page.evaluate = AsyncMock(return_value=[{
        "type": "text", "selector": "img.captcha", "sitekey": "",
    }])
    # Mock the strategy execution
    with patch(
        "jarvis.browser.captcha.solver.get_strategy"
    ) as mock_strat:
        async def fake_strategy(page, challenge, vision_fn):
            return SolveResult(
                success=True, captcha_type=CaptchaType.TEXT,
                model_used="minicpm-v4.5", attempts=1,
                duration_ms=500, answer="abc123",
            )
        mock_strat.return_value = fake_strategy
        result = await solver.solve(mock_page)
        assert result.success


@pytest.mark.asyncio
async def test_solve_retry_on_failure(solver, mock_page):
    mock_page.evaluate = AsyncMock(return_value=[{
        "type": "text", "selector": "img.captcha", "sitekey": "",
    }])
    call_count = 0
    with patch(
        "jarvis.browser.captcha.solver.get_strategy"
    ) as mock_strat:
        async def failing_then_success(page, challenge, vision_fn):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return SolveResult(
                    success=False, captcha_type=CaptchaType.TEXT,
                    model_used="test", attempts=call_count,
                    duration_ms=100, error="wrong",
                )
            return SolveResult(
                success=True, captcha_type=CaptchaType.TEXT,
                model_used="test", attempts=call_count,
                duration_ms=100, answer="ok",
            )
        mock_strat.return_value = failing_then_success
        result = await solver.solve(mock_page)
        assert result.success
        assert call_count == 3


def test_captcha_config_defaults():
    cfg = CaptchaConfig()
    assert cfg.enabled is False
    assert cfg.max_retries == 3
    assert cfg.stealth_enabled is True
    assert cfg.auto_solve is True
    assert cfg.solve_timeout_seconds == 30
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement solver.py**

Create `src/jarvis/browser/captcha/solver.py` containing:

- `CaptchaConfig` dataclass (enabled, max_retries, stealth_enabled, auto_solve, preferred_simple_model, preferred_complex_model, solve_timeout_seconds)
- `CaptchaSolver` class:
  - `__init__(self, vision_fn, config, tactical_memory=None)`
  - `async def solve(self, page, challenge=None) -> SolveResult` — main entry point: detect (if no challenge given) → classify → select model → call strategy with retries → record to tactical memory → return result
  - `async def _execute_strategy(self, page, challenge) -> SolveResult` — single attempt
  - Retry loop up to `config.max_retries`
  - Timing measurement
  - TacticalMemory recording on success/failure

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/browser/captcha/solver.py tests/test_captcha/test_solver.py
git commit -m "feat(captcha): solver orchestrator — detect, classify, solve, retry, learn"
```

---

### Task 7: MCP Tool + Gatekeeper + Config Integration

**Files:**
- Modify: `src/jarvis/browser/tools.py` — register `browser_solve_captcha`
- Modify: `src/jarvis/core/gatekeeper.py` — add `browser_solve_captcha` to ORANGE
- Modify: `src/jarvis/config.py` — add `captcha` config field
- Modify: `src/jarvis/browser/agent.py` — inject stealth + auto-detect
- Test: `tests/test_captcha/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_captcha/test_integration.py
"""Integration tests for CAPTCHA solver."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from jarvis.browser.captcha.solver import CaptchaSolver, CaptchaConfig
from jarvis.browser.captcha.models import CaptchaType
from jarvis.browser.captcha.stealth import STEALTH_ARGS, STEALTH_JS


@pytest.mark.asyncio
async def test_full_flow_no_captcha():
    """Page without CAPTCHA → success with no action."""
    page = MagicMock()
    page.evaluate = AsyncMock(return_value=[])
    page.url = "https://example.com"
    solver = CaptchaSolver(
        vision_fn=AsyncMock(return_value=""),
        config=CaptchaConfig(enabled=True),
    )
    result = await solver.solve(page)
    assert result.success


@pytest.mark.asyncio
async def test_full_flow_text_captcha():
    """Text CAPTCHA detected → vision model reads text → fills input."""
    page = MagicMock()
    page.evaluate = AsyncMock(side_effect=[
        # First call: detect_captcha JS
        [{"type": "text", "selector": "img.captcha", "sitekey": ""}],
        # Subsequent calls from strategy (element checks, etc.)
        None,
    ])
    page.url = "https://example.com"
    page.query_selector = AsyncMock(return_value=MagicMock(
        screenshot=AsyncMock(return_value=b"fake-png"),
    ))
    page.fill = AsyncMock()
    page.click = AsyncMock()

    solver = CaptchaSolver(
        vision_fn=AsyncMock(return_value="XY42Z"),
        config=CaptchaConfig(enabled=True),
    )
    # We need to let the strategy actually run, which requires
    # more elaborate mocking. For now test that solve() doesn't crash.
    result = await solver.solve(page)
    # Result depends on strategy implementation — at minimum no crash
    assert isinstance(result.captcha_type, CaptchaType)


def test_stealth_args_present():
    """Verify stealth constants are well-formed."""
    assert len(STEALTH_ARGS) >= 1
    assert "webdriver" in STEALTH_JS
```

- [ ] **Step 2: Add `browser_solve_captcha` MCP tool in `browser/tools.py`**

In `register_browser_use_tools()`, add after the last tool registration:

```python
async def _handle_solve_captcha(**kwargs: Any) -> str:
    if not agent:
        return "Browser nicht gestartet."
    from jarvis.browser.captcha.solver import CaptchaSolver, CaptchaConfig
    solver = CaptchaSolver(
        vision_fn=vision_analyzer.analyze_screenshot if vision_analyzer else None,
        config=CaptchaConfig(enabled=True, max_retries=kwargs.get("max_retries", 3)),
    )
    result = await solver.solve(agent.current_page)
    if result.success:
        return f"CAPTCHA geloest: {result.captcha_type} ({result.model_used}, {result.attempts} Versuch(e), {result.duration_ms}ms)"
    return f"CAPTCHA-Loesung fehlgeschlagen: {result.captcha_type} — {result.error}"

mcp_client.register_builtin_handler(
    tool_name="browser_solve_captcha",
    handler=_handle_solve_captcha,
    description="Erkennt und loest ein CAPTCHA auf der aktuellen Browser-Seite.",
    input_schema={
        "type": "object",
        "properties": {
            "max_retries": {"type": "integer", "default": 3, "description": "Max Versuche"},
        },
    },
)
```

- [ ] **Step 3: Add to Gatekeeper ORANGE set**

In `src/jarvis/core/gatekeeper.py`, add `"browser_solve_captcha"` to the `orange_tools` set.

- [ ] **Step 4: Add CaptchaConfig to JarvisConfig**

In `src/jarvis/config.py`, add a `captcha` dict field (same pattern as `atl`).

- [ ] **Step 5: Add stealth to BrowserAgent launch**

In `src/jarvis/browser/agent.py`, in the `start()` method where `chromium.launch()` is called, merge stealth args and inject stealth JS on new pages.

- [ ] **Step 6: Run all tests**

Run: `python -m pytest tests/test_captcha/ -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add src/jarvis/browser/tools.py src/jarvis/browser/agent.py src/jarvis/core/gatekeeper.py src/jarvis/config.py tests/test_captcha/test_integration.py
git commit -m "feat(captcha): MCP tool, gatekeeper ORANGE, config, stealth in agent"
```

---

### Task 8: Skill + Documentation

**Files:**
- Create: `~/.cognithor/skills/generated/captcha_solver.md`
- Modify: `src/jarvis/browser/captcha/__init__.py` — ensure clean exports
- Test: final dry-run

- [ ] **Step 1: Create the skill file**

```markdown
# captcha_solver

## Beschreibung
Erkennt und loest CAPTCHAs auf Webseiten — rein lokal via Vision-LLM.

## Wann verwenden
- Wenn bei Browser-Automatisierung ein CAPTCHA die Navigation blockiert
- Wenn bei Web-Recherche ein CAPTCHA-Schutz auftaucht
- Fuer Security-Audits: Bot-Schutz auf autorisierten Sites testen

## Tools
- `browser_solve_captcha` — Erkennt und loest das CAPTCHA auf der aktuellen Browser-Seite

## Workflow
1. Navigiere zur Seite mit `browser_navigate`
2. Wenn CAPTCHA erkannt: `browser_solve_captcha` aufrufen
3. Bei Erfolg: normal weiterarbeiten
4. Bei Misserfolg: dem User mitteilen (CAPTCHA zu komplex fuer lokales Vision-Modell)

## Unterstuetzte Typen
- Text-CAPTCHAs (verzerrter Text)
- reCAPTCHA v2 (Checkbox + Image Grid)
- reCAPTCHA v3 (unsichtbar, Stealth-basiert)
- hCaptcha (Checkbox + Image Challenges)
- Cloudflare Turnstile
- FunCaptcha / Arkose Labs

## Hinweise
- Gatekeeper-Level: ORANGE (erfordert User-Genehmigung)
- Stealth-Modus ist standardmaessig aktiviert
- Erfolgsrate variiert: Text-CAPTCHAs ~70%, Image-Grids ~20%
- Jeder Versuch wird in TacticalMemory gespeichert fuer Lerneffekt
```

- [ ] **Step 2: Run full test suite**

Run: `python -m pytest tests/test_captcha/ -v`
Expected: ALL PASS

- [ ] **Step 3: Run ruff lint**

Run: `ruff check src/jarvis/browser/captcha/ tests/test_captcha/`
Expected: 0 errors

- [ ] **Step 4: Commit**

```bash
git add ~/.cognithor/skills/generated/captcha_solver.md src/jarvis/browser/captcha/
git commit -m "feat(captcha): skill file + documentation complete"
```

---

## File Structure Summary

| File | Responsibility |
|------|---------------|
| `src/jarvis/browser/captcha/__init__.py` | Package exports |
| `src/jarvis/browser/captcha/models.py` | CaptchaType, CaptchaChallenge, SolveResult |
| `src/jarvis/browser/captcha/stealth.py` | Launch args, JS injection, user-agent |
| `src/jarvis/browser/captcha/detector.py` | JS-based page scan for 7 CAPTCHA types |
| `src/jarvis/browser/captcha/classifier.py` | Challenge profiling + vision model selection |
| `src/jarvis/browser/captcha/strategies.py` | Per-type solve strategies + vision prompts |
| `src/jarvis/browser/captcha/solver.py` | Orchestrator: detect → classify → solve → retry → learn |
| `tests/test_captcha/test_models.py` | 4 tests |
| `tests/test_captcha/test_stealth.py` | 7 tests |
| `tests/test_captcha/test_detector.py` | 8 tests |
| `tests/test_captcha/test_classifier.py` | 7 tests |
| `tests/test_captcha/test_strategies.py` | 9 tests |
| `tests/test_captcha/test_solver.py` | 4 tests |
| `tests/test_captcha/test_integration.py` | 3 tests |

**Total: ~42 tests across 7 test files**

## Spec Coverage Check

| Spec Section | Covered by Task |
|-------------|-----------------|
| 7 CAPTCHA types (Sec 2) | Task 1 (enum), Task 3 (detector), Task 4 (classifier) |
| Architecture flow (Sec 3) | Task 6 (solver orchestrator) |
| Data models (Sec 5) | Task 1 |
| Detector JS (Sec 6) | Task 3 |
| Solve strategies (Sec 7) | Task 5 |
| Dynamic model selection (Sec 8) | Task 4 |
| Stealth (Sec 9) | Task 2 |
| Browser integration (Sec 10.1-10.2) | Task 7 |
| Gatekeeper ORANGE (Sec 10.3) | Task 7 |
| Config (Sec 10.4) | Task 7 |
| TacticalMemory (Sec 10.5) | Task 6 |
| Skill (Sec 10.6) | Task 8 |
| Security (Sec 11) | Task 7 (gatekeeper + config opt-in) |
| Tests (Sec 12) | Tasks 1-8 |
