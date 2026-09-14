# Evolution Engine Phase 2: Idle Learning Loop

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Orchestrate CuriosityEngine, SkillGenerator, and ActiveLearner into a single EvolutionLoop that runs during idle time, instantly yields to user activity, and tracks what it learned.

**Architecture:** New `src/jarvis/evolution/` module. `IdleDetector` monitors user activity. `EvolutionLoop` runs cycles: Scout (find gaps) → Research (deep_research) → Build (create skill) → Reflect (evaluate). Each step checks idle status and aborts if user returns. Budget-aware with configurable daily limits.

**Tech Stack:** Python 3.12+ (asyncio, sqlite3), pytest

**CRITICAL:** This builds ON TOP of existing components. CuriosityEngine, SkillGenerator, ActiveLearner are NOT rebuilt — they are orchestrated.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/jarvis/evolution/__init__.py` | Package exports |
| Create | `src/jarvis/evolution/idle_detector.py` | Tracks user activity, signals idle/active |
| Create | `src/jarvis/evolution/loop.py` | EvolutionLoop: Scout→Research→Build→Reflect cycle |
| Modify | `src/jarvis/config.py` | EvolutionConfig |
| Modify | `src/jarvis/gateway/gateway.py` | Start/stop EvolutionLoop, idle tracking |
| Create | `tests/unit/test_evolution.py` | Tests |

---

### Task 1: IdleDetector + EvolutionConfig

**Files:**
- Create: `src/jarvis/evolution/__init__.py`
- Create: `src/jarvis/evolution/idle_detector.py`
- Modify: `src/jarvis/config.py`
- Create: `tests/unit/test_evolution.py`

IdleDetector:
```python
class IdleDetector:
    def __init__(self, idle_threshold_seconds: int = 300):
        self._last_activity = time.time()
        self._threshold = idle_threshold_seconds

    def notify_activity(self):
        """Called on every user message."""
        self._last_activity = time.time()

    @property
    def is_idle(self) -> bool:
        return (time.time() - self._last_activity) > self._threshold

    @property
    def idle_seconds(self) -> float:
        return max(0, time.time() - self._last_activity)
```

EvolutionConfig in config.py:
```python
class EvolutionConfig(BaseModel):
    enabled: bool = Field(default=False, description="Enable autonomous evolution during idle time")
    idle_minutes: int = Field(default=5, ge=1, le=60)
    max_cycles_per_day: int = Field(default=10, ge=1, le=100)
    cycle_cooldown_seconds: int = Field(default=300, ge=60, le=3600)
    max_cost_per_cycle_usd: float = Field(default=0.0, ge=0.0)
```

Tests: is_idle after threshold, not_idle after activity, idle_seconds accuracy.

---

### Task 2: EvolutionLoop Core

**Files:**
- Create: `src/jarvis/evolution/loop.py`
- Modify: `tests/unit/test_evolution.py`

EvolutionLoop orchestrates 4 steps per cycle:

```python
class EvolutionLoop:
    def __init__(self, idle_detector, curiosity_engine, skill_generator,
                 gateway_handle_message, config):
        ...

    async def run_cycle(self) -> EvolutionCycleResult:
        """Run one Scout→Research→Build→Reflect cycle."""
        if not self._idle_detector.is_idle:
            return EvolutionCycleResult(skipped=True, reason="not_idle")

        # Step 1: Scout — find knowledge gaps
        gaps = await self._scout()
        if not gaps or not self._idle_detector.is_idle:
            return EvolutionCycleResult(skipped=True, reason="no_gaps_or_interrupted")

        # Step 2: Research — deep research on top gap
        research = await self._research(gaps[0])
        if not research or not self._idle_detector.is_idle:
            return ...

        # Step 3: Build — create skill from research
        skill = await self._build(gaps[0], research)

        # Step 4: Reflect — log what was learned
        return self._reflect(gaps[0], research, skill)

    async def start(self):
        """Background loop: wait for idle → run cycle → cooldown → repeat."""
        self._running = True
        while self._running:
            if self._idle_detector.is_idle and self._can_run_cycle():
                result = await self.run_cycle()
                self._cycles_today += 1
                self._log_result(result)
                await asyncio.sleep(self._config.cycle_cooldown_seconds)
            else:
                await asyncio.sleep(30)  # Check every 30s

    def stop(self):
        self._running = False
```

Tests: run_cycle skips when not idle, run_cycle completes when idle, daily limit respected.

---

### Task 3: Gateway Integration

**Files:**
- Modify: `src/jarvis/gateway/gateway.py`

Wire EvolutionLoop into gateway:
1. Create IdleDetector + EvolutionLoop in startup
2. Call `idle_detector.notify_activity()` on every user message (alongside existing ActiveLearner.notify_activity)
3. Start EvolutionLoop as background task
4. Stop on shutdown

---

### Task 4: Full Test Suite

Run all tests, verify no regressions, commit.
