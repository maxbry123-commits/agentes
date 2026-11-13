# Cognithor Autonomous Evolution Engine — Master Implementation Plan

> **For agentic workers:** This is a PHASED plan. Each phase is an independent implementation plan with its own tasks. Execute one phase per session. Each phase produces working, testable software.

**Goal:** Make Cognithor actively learn, research, and build new skills during idle time — with hardware-aware resource management, budget tracking per agent, and checkpoint/resume support.

**Architecture:** 4 phases, each building on the previous but independently valuable. Phase 1 gives Cognithor eyes (hardware detection). Phase 2 gives it purpose (idle learning loop). Phase 3 gives it discipline (per-agent budgets + resource monitoring). Phase 4 gives it resilience (checkpoint/resume for interrupted loops).

**Tech Stack:** Python 3.12+ (psutil, subprocess, sqlite3, asyncio), Flutter/Dart, pytest

---

## Phase Overview

| Phase | Name | Sessions | What It Delivers | Dependencies |
|-------|------|----------|-----------------|--------------|
| **1** | Hardware-Aware System Profile | 1 | Real GPU/CPU/RAM/Network detection, SystemProfile, mode recommendation, Flutter System page | None |
| **2** | Idle Learning Loop | 1-2 | Idle detection, Scout+SkillBuilder agents, autonomous learning cycle, user preemption | Phase 1 (optional) |
| **3** | Per-Agent Budget + Resource Monitor | 1 | Per-agent cost tracking, real-time CPU/GPU monitoring, budget alerts, cooperative scheduling | Phase 2 (optional) |
| **4** | Checkpoint/Resume Engine | 1 | Automatic checkpointing at loop boundaries, resume from interruption, delta snapshots | Phase 2 |

---

## Phase 1: Hardware-Aware System Profile

**Goal:** Replace the basic HardwareDetector with a comprehensive SystemDetector that queries real GPU info (nvidia-smi), measures network connectivity, profiles storage, and recommends the optimal operating mode.

### Files

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/jarvis/system/detector.py` | SystemDetector: 8 detection targets, SystemProfile |
| Create | `src/jarvis/system/__init__.py` | Package init |
| Modify | `src/jarvis/gateway/gateway.py` | Run SystemDetector on startup, store profile |
| Modify | `src/jarvis/channels/config_routes.py` | GET /api/v1/system/profile endpoint |
| Create | `flutter_app/lib/screens/config/system_profile_page.dart` | Flutter page showing hardware profile |
| Create | `tests/unit/test_system_detector.py` | Tests |

### Tasks

#### Task 1.1: SystemDetector Core + CPU/RAM/OS Detection

Create `src/jarvis/system/detector.py` with:

```python
@dataclass
class DetectionResult:
    key: str            # e.g., "gpu", "cpu", "ram"
    value: str          # Human-readable description
    status: str         # "ok" | "warn" | "fail"
    raw_data: dict      # Machine-readable details

@dataclass
class SystemProfile:
    results: dict[str, DetectionResult]
    detected_at: str    # ISO timestamp

    def get_available_modes(self) -> list[str]
    def get_recommended_mode(self) -> str
    def get_tier(self) -> str  # "minimal" | "standard" | "power" | "enterprise"

class SystemDetector:
    def detect_os(self) -> DetectionResult
    def detect_cpu(self) -> DetectionResult  # psutil.cpu_count, cpu_freq
    def detect_ram(self) -> DetectionResult  # psutil.virtual_memory
    def run_full_scan(self) -> SystemProfile
    def run_quick_scan(self) -> SystemProfile  # cached OS/CPU/RAM, fresh GPU/network
    def save_profile(self, path) -> None
    def load_cached_profile(self) -> SystemProfile | None
```

Tests: detect_os returns valid result, detect_cpu has core count, detect_ram has total_gb, run_full_scan returns all keys, save/load round-trips.

#### Task 1.2: GPU Detection (nvidia-smi / platform)

Add to SystemDetector:

```python
def detect_gpu(self) -> DetectionResult:
    # Try nvidia-smi first
    # Fallback: check for Apple Silicon (platform.processor)
    # Fallback: report "integrated" or "none"
```

Real `nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader` parsing. Graceful skip on Windows without NVIDIA. Tests with mocked subprocess.

#### Task 1.3: Network + Disk + Ollama/LMStudio Detection

```python
def detect_network(self) -> DetectionResult  # DNS + HTTPS to api.anthropic.com
def detect_disk(self) -> DetectionResult      # shutil.disk_usage on jarvis_home
def detect_ollama(self) -> DetectionResult    # HTTP GET localhost:11434/api/tags
def detect_lmstudio(self) -> DetectionResult  # HTTP GET localhost:1234/v1/models
```

#### Task 1.4: Mode Recommendation + Gateway Integration

`SystemProfile.get_recommended_mode()`:
- GPU >= 8GB VRAM + Ollama running → "offline"
- GPU < 8GB + API keys → "hybrid"
- No GPU + API keys → "online"
- No GPU + no keys → "offline" (slow but works)

Gateway startup: Run quick_scan, log profile, store as `self._system_profile`.

#### Task 1.5: REST API + Flutter System Profile Page

`GET /api/v1/system/profile` → returns full SystemProfile as JSON.

Flutter page under System showing: OS, CPU cores, RAM, GPU (name + VRAM), Disk free, Network status, Ollama models, recommended mode — with color-coded status badges.

---

## Phase 2: Idle Learning Loop

**Goal:** Cognithor autonomously discovers knowledge gaps, researches solutions, and builds skills when the user is idle — instantly yielding to any user interaction.

### Files

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/jarvis/evolution/idle_detector.py` | Detects when user is idle (no messages for N minutes) |
| Create | `src/jarvis/evolution/scout_agent.py` | Scout: discovers knowledge gaps, suggests research topics |
| Create | `src/jarvis/evolution/skill_builder.py` | SkillBuilder: creates skills from research results |
| Create | `src/jarvis/evolution/loop.py` | EvolutionLoop: orchestrates Scout→Research→Build cycle |
| Modify | `src/jarvis/gateway/gateway.py` | Start/stop EvolutionLoop, preempt on user message |
| Modify | `src/jarvis/config.py` | EvolutionConfig |
| Create | `tests/unit/test_evolution_loop.py` | Tests |

### Tasks

#### Task 2.1: IdleDetector

Tracks `last_user_message_time`. After configurable idle period (default: 5 minutes), signals "idle". Any incoming user message immediately signals "active" and preempts.

#### Task 2.2: Scout Agent

Uses `knowledge_gaps` + `search_procedures` + Memory stats to find areas where Cognithor lacks knowledge. Produces a ranked list of research topics.

#### Task 2.3: SkillBuilder Agent

Takes research results and creates new Skills via `create_skill`. Validates the skill, tests it with a sample query, and registers it.

#### Task 2.4: EvolutionLoop

```python
class EvolutionLoop:
    async def run_cycle(self):
        # 1. Scout: find knowledge gaps
        # 2. Research: deep_research_v2 on top gap
        # 3. Build: create skill from research
        # 4. Reflect: evaluate quality
        # 5. Checkpoint: save state
        # Each step checks idle_detector.is_idle — abort if user returns
```

Budget-aware: each cycle has a configurable max cost. Stops when daily budget exhausted.

#### Task 2.5: Gateway Integration

- Start EvolutionLoop as background task when IdleDetector triggers
- Cancel immediately on user message
- Log all autonomous actions in audit trail
- Config: `evolution.enabled`, `evolution.idle_minutes`, `evolution.max_cycles_per_day`

---

## Phase 3: Per-Agent Budget + Resource Monitor

**Goal:** Track costs per agent, monitor real-time CPU/GPU usage, and cooperatively schedule idle work around user activity.

### Files

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `src/jarvis/telemetry/cost_tracker.py` | Per-agent cost tracking |
| Create | `src/jarvis/system/resource_monitor.py` | Real-time CPU/RAM/GPU sampling via psutil |
| Modify | `src/jarvis/evolution/loop.py` | Respect resource limits, pause when system busy |
| Modify | `src/jarvis/channels/config_routes.py` | GET /api/v1/budget/agents, GET /api/v1/system/resources |
| Create | `flutter_app/lib/screens/config/budget_page.dart` | Flutter budget dashboard |
| Create | `tests/unit/test_resource_monitor.py` | Tests |

### Tasks

#### Task 3.1: Per-Agent Cost Tracking

Extend CostTracker with `agent_name` column. New methods: `get_agent_costs()`, `check_agent_budget()`. Config: per-agent daily limits.

#### Task 3.2: Real-Time Resource Monitor

```python
class ResourceMonitor:
    async def sample(self) -> ResourceSnapshot:
        # CPU percent (psutil.cpu_percent)
        # RAM used/total (psutil.virtual_memory)
        # GPU util + VRAM (nvidia-smi if available)
        # Returns snapshot with is_busy flag

    def should_yield(self) -> bool:
        # True if CPU > 80% or RAM > 90% or GPU util > 80%
```

#### Task 3.3: Cooperative Scheduling

EvolutionLoop checks ResourceMonitor before each step. If system is busy (user activity or high load), pause and wait. Resume when resources free up.

#### Task 3.4: Budget Dashboard

Flutter page showing: per-agent costs (today/week/month), budget remaining, resource usage graphs.

---

## Phase 4: Checkpoint/Resume Engine

**Goal:** Every idle loop step is checkpointable. Interrupted loops resume exactly where they stopped.

### Files

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `src/jarvis/evolution/loop.py` | Checkpoint after each step, resume from checkpoint |
| Modify | `src/jarvis/core/checkpointing.py` | Add auto-checkpoint, delta snapshots, compression |
| Create | `src/jarvis/evolution/resume.py` | Resume logic: load checkpoint, skip completed steps |
| Modify | `src/jarvis/channels/config_routes.py` | GET /api/v1/evolution/status, POST /api/v1/evolution/resume |
| Create | `tests/unit/test_evolution_resume.py` | Tests |

### Tasks

#### Task 4.1: Step-Level Checkpointing

Each EvolutionLoop step saves: `{cycle_id, step_name, step_index, data, timestamp}`. On resume, load last checkpoint and continue from next step.

#### Task 4.2: Delta Snapshots

Instead of full state dumps, save only what changed since last checkpoint. Reduces storage for large knowledge bases.

#### Task 4.3: Resume API + Status

`GET /api/v1/evolution/status` → current cycle, step, last activity, skills built today
`POST /api/v1/evolution/resume` → manually resume a paused cycle

#### Task 4.4: Flutter Evolution Dashboard

Show: current evolution status (idle/scouting/researching/building), skills built, cycles completed, next scheduled run.

---

## Implementation Order

```
Phase 1 (Session 1):  SystemDetector → GPU/Network → Mode Recommendation → API + Flutter
                       ↓
Phase 2 (Session 2):  IdleDetector → Scout → SkillBuilder → EvolutionLoop → Gateway
                       ↓
Phase 3 (Session 3):  Per-Agent Budget → ResourceMonitor → Cooperative Scheduling → Dashboard
                       ↓
Phase 4 (Session 4):  Step Checkpointing → Delta Snapshots → Resume API → Evolution Dashboard
```

Each phase is independently deployable and testable. Phase 1 gives immediate value (hardware visibility). Phase 2 is the core feature. Phases 3-4 are hardening.

---

## What Already Exists (DO NOT Rebuild)

| Component | File | Reuse Strategy |
|-----------|------|----------------|
| HardwareDetector (basic) | `core/installer.py` | Replace with SystemDetector |
| Preflight checks | `scripts/preflight_check.py` | Keep as-is, SystemDetector is complementary |
| CostTracker | `telemetry/cost_tracker.py` | Extend with agent_name column |
| CuriosityEngine | `learning/curiosity.py` | Feed into Scout agent |
| ActiveLearner | `learning/active_learner.py` | Feed into EvolutionLoop |
| SkillGenerator | `skills/generator.py` | Reuse in SkillBuilder agent |
| HeartbeatScheduler | `proactive/__init__.py` | EvolutionLoop replaces idle-time scheduling |
| CheckpointStore | `core/checkpointing.py` | Extend with delta snapshots |
| AutonomousOrchestrator | `core/autonomous_orchestrator.py` | Scout reuses task decomposition |
| ProcessMonitor | `mcp/background_tasks.py` | ResourceMonitor builds on this pattern |
