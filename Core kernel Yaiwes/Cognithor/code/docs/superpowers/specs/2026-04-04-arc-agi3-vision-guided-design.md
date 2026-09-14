# ARC-AGI-3: Vision-Guided Action Selection — Design Spec

**Date:** 2026-04-04
**Status:** Approved
**Depends on:** ARC-AGI-3 RL agent + FrameAnalyzer + Telemetry

## Goal

Send game frames as images to qwen3-vl:32b to understand what's on screen and get strategic action recommendations. Bridges Computer Use vision infrastructure with the ARC agent.

## Proven Concept

Live test confirmed: qwen3-vl:32b correctly identifies "green blocky character with gray head", "red L-shaped object", "yellow background" from a 512x512 upscaled ARC frame. It suggests "maneuver the green character to reach the red L-shaped object" — which is likely the correct game goal.

## 1. ArcVisionGuide Module

New file: `src/jarvis/arc/vision_guide.py`

### grid_to_png_b64

Converts 64x64 color-index grid to 512x512 PNG base64:

```python
ARC_COLORS = {
    0: (0,0,0), 1: (0,116,217), 2: (255,65,54), 3: (46,204,64),
    4: (255,220,0), 5: (170,170,170), 6: (240,18,190), 7: (255,133,27),
    8: (127,219,255), 9: (135,12,37), 10: (255,255,255),
    11: (200,200,100), 12: (100,50,150),
}

def grid_to_png_b64(grid: np.ndarray, scale: int = 8) -> str:
    """Convert 64x64 color-index grid to 512x512 PNG base64."""
```

~3KB output. Trivial for the vision model.

### ArcVisionGuide

```python
class ArcVisionGuide:
    """Consults qwen3-vl:32b to understand game frames and suggest actions."""

    def __init__(self, model: str = "qwen3-vl:32b", call_interval: int = 50):
        self.model = model
        self.call_interval = call_interval
        self._steps_since_last_call = 0
        self._pixels_since_last_call = 0
        self._last_strategy: dict | None = None
        self._call_count = 0
```

### Call Strategy (C3: Adaptive-Regular)

`should_call(changed_pixels)` returns True when:
- `_steps_since_last_call >= call_interval` (default 50)
- AND `_pixels_since_last_call > 100` (screen actually changed)

Special cases:
- First call at step 1 (always, to understand the game)
- After GAME_OVER/reset: immediate call via `force_next_call()`
- Stagnation (0 pixel change): no call (saves tokens)

### Vision Prompt

```
Du siehst einen Frame aus einem Puzzle-Spiel.
Verfuegbare Aktionen: {action_names}

Bisherige Strategie: {previous_strategy_or_none}
Bisherige Aktionen: {recent_action_summary}

Beschreibe kurz:
1. Was siehst du? (Objekte, Farben, Layout)
2. Was ist das wahrscheinliche Ziel?
3. Welche Aktion empfiehlst du als naechstes?

Antworte als JSON:
{"goal": "...", "strategy": "...", "next_action": "ACTION1"}
```

Previous strategy is included for context continuity between calls.

### JSON Parsing

3-tier fallback (same pattern as CU agent):
1. Direct `json.loads`
2. Markdown code block extraction
3. Regex for `{"goal"...}` with balanced braces

Fallback: if parsing fails, return `None` (agent uses FrameAnalyzer/Explorer instead).

### analyze() Method

```python
async def analyze(self, grid: np.ndarray, action_names: list[str]) -> dict | None:
    """Send frame to vision model. Returns {goal, strategy, next_action} or None."""
```

Uses `ollama.chat()` with `images=[b64]`. Strips `<think>` tags. Resets step/pixel counters on success.

## 2. Integration in Agent

### Priority Order for Action Selection

```
1. Navigation mode (win path found)      — highest
2. CNN prediction (if trained)
3. Vision guide (if should_call)          — NEW
4. Frame analyzer suggestion
5. Pixel-reward explorer                  — lowest (fallback)
```

Vision guide has priority over FrameAnalyzer and Explorer but below Navigation and CNN (which are more precise when available).

### Wiring in _step()

After navigation check, before explorer fallback:

```python
# Vision guide: consult LLM if due
if (
    action_str is None
    and self.vision_guide is not None
    and self.vision_guide.should_call(self.current_obs.changed_pixels)
):
    import asyncio
    guidance = asyncio.run(self.vision_guide.analyze(
        self.current_obs.raw_grid,
        [getattr(a, "name", str(a)) for a in self.current_obs.available_actions],
    ))
    if guidance and guidance.get("next_action"):
        action = self._resolve_action(guidance["next_action"])
        data = {}
        action_str = self._action_to_str(action, data)
```

### GAME_OVER Handling

When GAME_OVER occurs, call `self.vision_guide.force_next_call()` so the next step immediately consults the vision model for the new state.

### Telemetry Extension

Add to ArcTelemetry:
- `vision_calls: int = 0`
- `vision_actions_followed: int = 0`

## 3. Files Changed

| File | Change |
|------|--------|
| `src/jarvis/arc/vision_guide.py` | **NEW** — ArcVisionGuide, grid_to_png_b64 |
| `src/jarvis/arc/agent.py` | Vision guide in __init__, _step(), GAME_OVER handling, telemetry |
| `tests/test_arc/test_vision_guide.py` | **NEW** — grid conversion, should_call logic, JSON parsing, mock LLM |

## 4. Degradation

- Ollama not running → `analyze()` returns None → fallback to FrameAnalyzer
- Model swap timeout → returns None → fallback
- JSON parse failure → returns None → fallback
- No PIL/numpy → grid_to_png_b64 raises ImportError at startup → vision guide disabled

## 5. Expected Performance

- ~10-15 LLM calls per 1000-step game
- ~15-30s per call (model swap + inference)
- Total LLM time: ~2-5 minutes per game
- Expected improvement: agent understands game goal, navigates toward objectives instead of random exploration
