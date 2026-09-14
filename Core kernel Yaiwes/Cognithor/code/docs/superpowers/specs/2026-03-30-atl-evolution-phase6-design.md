# Evolution Engine Phase 6: Autonomous Thinking Loop (ATL)

**Spec v2.0** — 30.03.2026
**Status:** Approved Design — **Priority:** Feature Enhancement
**Basis:** `SPEC_autonomous_thinking_loop.md` (Tomi), ueberarbeitet fuer Integration in bestehende Evolution Engine

---

## 1. Motivation

Cognithor hat bereits einen autonomen Lern-Loop (Evolution Engine, Phasen 1-5). Dieser ist aber **rein wissensorientiert**: Scout -> Research -> Build -> Reflect. Er recherchiert Themen und baut Wissen auf — aber er **denkt nicht nach**.

ATL erweitert die Evolution Engine um eine **Denkschicht**: Der Agent evaluiert proaktiv Ziele, ergreift Massnahmen, benachrichtigt den User bei wichtigen Erkenntnissen und fuehrt ein tagesbasiertes Journal. Statt nur zu lernen, **handelt** er.

**Was sich aendert:**
- Evolution Loop bekommt einen neuen Cycle-Typ: `thinking` (neben `learning`)
- Neues Goal-Management-System ersetzt die flachen `learning_goals` Strings
- Proaktive User-Notifications ueber bestehende Channels
- ATL-Journal als neuer Episodic-Memory-Typ
- Risk Ceiling im Gatekeeper fuer autonome Aktionen

**Was NICHT neu gebaut wird (bereits vorhanden):**
- Cron/Idle-Trigger (IdleDetector, APScheduler) — existiert
- Context Assembly (ContextPipeline, 3-Wave) — existiert
- PGE-Loop (Planner, Gatekeeper, Executor) — existiert
- Checkpoint/Resume — existiert
- Resource Monitoring — existiert
- Reflection (Reflector, Narrative Self) — existiert

---

## 2. Architektur

```
 Evolution Engine (bestehend)
 ┌──────────────────────────────────────────────┐
 │  IdleDetector ──> EvolutionLoop              │
 │                    │                          │
 │         ┌─────────┴──────────┐               │
 │         ▼                    ▼               │
 │   LEARNING CYCLE        THINKING CYCLE       │ <── NEU
 │   (Phase 1-5)           (Phase 6 / ATL)      │
 │   Scout->Research->     GoalEval->Think->    │
 │   Build->Reflect        Act->Journal->       │
 │                         Notify               │
 │         │                    │               │
 │         ▼                    ▼               │
 │   DeepLearner          GoalManager           │ <── NEU
 │   KnowledgeBuilder     ActionQueue           │ <── NEU
 │   QualityAssessor      ATLJournal            │ <── NEU
 │   HorizonScanner                             │
 │         │                    │               │
 │         └────────┬───────────┘               │
 │                  ▼                           │
 │            6-Tier Memory                     │
 │            Gatekeeper (risk_ceiling)         │
 │            Executor (sandboxed)              │
 └──────────────────────────────────────────────┘
```

---

## 3. Neue Dateien

```
src/jarvis/evolution/
├── goal_manager.py        # Goal CRUD + YAML Persistenz + Scoring
├── action_queue.py        # Priorisierte Aktions-Warteschlange
├── atl_journal.py         # Tagesbasiertes Markdown-Journal
├── atl_prompt.py          # ATL System Prompt + Response Parsing
└── atl_config.py          # ATLConfig dataclass

~/.cognithor/
├── evolution/
│   ├── goals.yaml         # Persistente Ziele (NEU)
│   └── journal/           # Tagesbasierte Journal-Eintraege (NEU)
│       └── 2026-03-30.md
```

**Geaenderte Dateien:**
- `evolution/loop.py` — Neuer `_thinking_cycle()` neben `run_cycle()`
- `core/gatekeeper.py` — `risk_ceiling` Parameter in `_classify_risk()`
- `gateway/gateway.py` — ATL-Wiring in Phase 6 init
- `config.py` — `ATLConfig` dataclass + Defaults
- `mcp/skill_tools.py` — 3 neue MCP-Tools (atl_status, atl_goals, atl_journal)

---

## 4. Konfiguration

```yaml
# In config.yaml (neuer Abschnitt)
atl:
  enabled: false                    # Opt-in, default aus
  interval_minutes: 15              # Denkzyklus-Intervall (5-60 Min)
  quiet_hours:
    start: "23:00"
    end: "07:00"
  max_actions_per_cycle: 3
  max_tokens_per_cycle: 4000
  notification_channel: ""          # Leer = kein Notify, "telegram", "cli", etc.
  notification_level: "important"   # all | important | critical
  goal_review_interval: "daily"
  risk_ceiling: "YELLOW"            # GREEN | YELLOW (max erlaubtes Gatekeeper-Level)
  allowed_action_types:
    - memory_update
    - research
    - notification
    - file_management
    - goal_management
  blocked_action_types:
    - shell_exec
    - send_message_unprompted
```

---

## 5. Kernkomponenten

### 5.1 GoalManager (`evolution/goal_manager.py`)

Ersetzt die flachen `learning_goals: [str]` in config.yaml durch strukturierte Ziele.

```python
@dataclass
class Goal:
    id: str                          # "g_001"
    title: str
    description: str
    priority: int                    # 1 (hoechste) bis 5
    status: str                      # active | paused | completed | abandoned
    created_at: str                  # ISO datetime
    updated_at: str
    deadline: str | None             # ISO datetime or None
    progress: float                  # 0.0 bis 1.0
    sub_goals: list[str]             # IDs
    success_criteria: list[str]
    tags: list[str]
    source: str                      # "user" | "self" | "evolution" | "reflection"

class GoalManager:
    def __init__(self, goals_path: Path):
        # Loads/saves goals.yaml

    def active_goals(self) -> list[Goal]: ...
    def add_goal(self, goal: Goal) -> None: ...
    def update_progress(self, goal_id: str, delta: float, note: str) -> None: ...
    def complete_goal(self, goal_id: str) -> None: ...
    def pause_goal(self, goal_id: str) -> None: ...

    def migrate_learning_goals(self, old_goals: list[str]) -> None:
        """One-time migration: convert config.yaml learning_goals to Goal objects."""
```

**Persistenz:** `~/.cognithor/evolution/goals.yaml`

**Migration:** Beim ersten Start mit ATL enabled werden die bestehenden
`config.evolution.learning_goals` Strings automatisch zu Goal-Objekten konvertiert
(priority=3, source="user", progress=geschaetzt aus DeepLearner-Coverage).

### 5.2 ActionQueue (`evolution/action_queue.py`)

```python
@dataclass
class ATLAction:
    type: str                        # research | memory_update | notification | ...
    params: dict[str, Any]
    priority: int                    # 1-5
    rationale: str

class ActionQueue:
    def __init__(self, max_actions: int = 3):
        self._queue: list[ATLAction] = []
        self._max = max_actions

    def enqueue(self, action: ATLAction) -> bool: ...
    def dequeue(self) -> ATLAction | None: ...
    def empty(self) -> bool: ...
```

### 5.3 ATLJournal (`evolution/atl_journal.py`)

```python
class ATLJournal:
    def __init__(self, journal_dir: Path): ...

    async def log_cycle(self, cycle: int, summary: str,
                        goal_updates: list, actions: list) -> None:
        """Append to ~/.cognithor/evolution/journal/YYYY-MM-DD.md"""

    def today(self) -> str | None:
        """Read today's journal."""

    def recent(self, days: int = 7) -> list[str]:
        """Read last N days of journal entries."""
```

### 5.4 ATL System Prompt (`evolution/atl_prompt.py`)

```python
ATL_SYSTEM_PROMPT = """\
Du bist Cognithor im autonomen Denkmodus. Du wurdest NICHT von einem User
angesprochen — du denkst eigenstaendig.

DEIN KONTEXT:
{identity}

AKTIVE ZIELE:
{goals_formatted}

LETZTE EREIGNISSE:
{recent_events}

RELEVANTES WISSEN:
{goal_knowledge}

AKTUELLE ZEIT: {now}

DEINE AUFGABE in diesem Denkzyklus:
1. Evaluiere den Fortschritt deiner aktiven Ziele
2. Identifiziere, welche konkreten Schritte jetzt sinnvoll waeren
3. Entscheide, ob du den User ueber etwas informieren solltest
4. Schlage max. {max_actions} Aktionen vor

ANTWORTE NUR mit validem JSON:
{{
  "summary": "Kurze Zusammenfassung deiner Gedanken",
  "goal_evaluations": [
    {{"goal_id": "...", "progress_delta": 0.05, "note": "..."}}
  ],
  "proposed_actions": [
    {{"type": "research|memory_update|notification", "params": {{}}, "rationale": "..."}}
  ],
  "wants_to_notify": false,
  "notification": null,
  "priority": "low"
}}

REGELN:
- Sei sparsam mit Aktionen — nur wenn wirklich sinnvoll
- Keine Nachrichten an den User ausser bei wichtigen Erkenntnissen
- User-Ziele (source: "user") haben immer Vorrang
- Du darfst neue Sub-Goals vorschlagen, aber nicht eigenmaechtig loeschen
- Respektiere das Token-Budget
"""
```

### 5.5 EvolutionLoop Erweiterung (`evolution/loop.py`)

Neuer Cycle-Typ in der bestehenden `_loop()` Methode:

```python
async def _loop(self):
    while self._running:
        await asyncio.sleep(self._interval)
        if not self._idle.is_idle:
            continue

        # Alterniere zwischen Learning und Thinking
        if self._atl_enabled and self._should_think():
            result = await self._thinking_cycle()
        else:
            result = await self.run_cycle()  # bestehender Learning Cycle
```

`_thinking_cycle()` baut den ATL-Kontext, ruft den Planner mit dem ATL-Prompt,
parsed die JSON-Antwort, fuehrt Aktionen durch Gatekeeper+Executor, schreibt
Journal, und sendet ggf. Notifications.

### 5.6 Gatekeeper Risk Ceiling

```python
# In _classify_risk() — neuer optionaler Parameter
def _classify_risk(self, tool_name, params, *, risk_ceiling=None):
    level = self._base_classify(tool_name, params)
    if risk_ceiling and level.value > RiskLevel[risk_ceiling].value:
        return RiskLevel.RED  # Block — exceeds ATL ceiling
    return level
```

### 5.7 MCP Tools (3 neue)

```
atl_status   → ATL-Status, letzte Zyklen, aktive Ziele (GREEN)
atl_goals    → Goal CRUD (add/pause/complete/list) (YELLOW)
atl_journal  → Journal lesen (GREEN)
```

---

## 6. Sicherheit

| Massnahme | Beschreibung |
|-----------|-------------|
| **Opt-in** | ATL ist default deaktiviert |
| **Risk Ceiling** | Max YELLOW — keine destruktiven Aktionen |
| **Token Budget** | Begrenztes Token-Budget pro Zyklus (4000 default) |
| **Action Whitelist** | Nur erlaubte Aktionstypen |
| **Rate Limiting** | Max 1 Notification pro Stunde |
| **Quiet Hours** | Kein Denken nachts (23:00-07:00 default) |
| **Audit Trail** | Jeder Zyklus im Journal + Audit Log |
| **User-Ziel Vorrang** | ATL kann keine User-Ziele loeschen |
| **No Spam** | send_message_unprompted default blockiert |
| **Gatekeeper** | Jede ATL-Aktion durchlaeuft den vollen PGE-Pfad |

---

## 7. Migration bestehender Learning Goals

Beim ersten Start mit `atl.enabled: true`:

1. Lese `config.evolution.learning_goals` (5 Strings aktuell)
2. Fuer jeden String: Erstelle Goal-Objekt mit `source="user"`, `priority=3`
3. Pruefe ob DeepLearner bereits Plans fuer den Goal hat
4. Wenn ja: Setze `progress` aus der Plan-Coverage
5. Speichere in `goals.yaml`
6. Lasse `learning_goals` in config.yaml bestehen (Backward-Kompatibilitaet)

---

## 8. Abgrenzung Learning Cycle vs Thinking Cycle

| Aspekt | Learning Cycle (Phase 1-5) | Thinking Cycle (Phase 6/ATL) |
|--------|---------------------------|------------------------------|
| **Trigger** | Idle + keine aktiven Deep Plans | Idle + ATL interval erreicht |
| **Fokus** | Wissen aufbauen | Ziele evaluieren + handeln |
| **LLM-Nutzung** | Entity Extraction, Quality Assessment | Strukturiertes Denken (JSON) |
| **Output** | Vault-Eintraege, Memory-Chunks, Entities | Goal-Updates, Aktionen, Journal, Notifications |
| **Gatekeeper** | Standard (ORANGE erlaubt) | Risk Ceiling (max YELLOW) |

Beide Cycles teilen: IdleDetector, Checkpoint, ResourceMonitor, Memory.

---

*Spec v2.0 — Evolution Phase 6 / ATL — 30.03.2026*
