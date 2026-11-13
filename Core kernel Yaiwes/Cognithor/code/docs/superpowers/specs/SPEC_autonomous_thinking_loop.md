# Cognithor — Autonomous Thinking Loop (ATL)

**Module Spec v1.0** · März 2026  
**Status:** Draft · **Priority:** Feature Enhancement  
**Ziel:** Cognithor denkt proaktiv — ohne User-Input — evaluiert eigene Ziele, ergreift Maßnahmen und entwickelt sich weiter.

---

## 1. Motivation

Aktuell ist Cognithor **rein reaktiv**: Der Agent handelt nur, wenn ein User eine Nachricht schickt. Der Autonomous Thinking Loop (ATL) macht Cognithor **proaktiv** — er wacht regelmäßig auf, evaluiert seinen Zustand, verfolgt eigene Ziele und handelt selbstständig.

**Inspiration:** Jork (github.com/hirodefi/Jork) implementiert einen 5-Minuten-Denkzyklus. ATL geht weiter — es nutzt Cognithors bestehende PGE Trinity, 5-Tier Memory und Cron-Engine für einen architektonisch sauberen, sicheren und konfigurierbaren autonomen Loop.

---

## 2. Architektur-Übersicht

```
┌─────────────────────────────────────────────────────┐
│                   Cron Engine                        │
│              (APScheduler Trigger)                   │
├─────────────────────────────────────────────────────┤
│            Autonomous Thinking Loop                  │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Context   │→ │ Planner  │→ │ Goal Evaluator   │ │
│  │  Assembler │  │ (LLM)   │  │ (Scoring/Prio)   │ │
│  └───────────┘  └──────────┘  └──────────────────┘ │
│        ↓              ↓               ↓             │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Memory   │  │Gatekeeper│  │   Action Queue    │ │
│  │  Reader   │  │ (Policy) │  │  (Prioritized)    │ │
│  └───────────┘  └──────────┘  └──────────────────┘ │
│                       ↓                             │
│              ┌──────────────┐                       │
│              │   Executor   │                       │
│              │  (Sandboxed) │                       │
│              └──────────────┘                       │
│                       ↓                             │
│              ┌──────────────┐                       │
│              │  Reflector   │                       │
│              │ (Post-Cycle) │                       │
│              └──────────────┘                       │
├─────────────────────────────────────────────────────┤
│           5-Tier Cognitive Memory                    │
│     Core · Episodic · Semantic · Procedural · WM    │
└─────────────────────────────────────────────────────┘
```

---

## 3. Neue Dateien

```
src/jarvis/
├── atl/
│   ├── __init__.py
│   ├── loop.py              # Haupt-Loop-Logik
│   ├── context_assembler.py # Kontext für den Denkzyklus aufbauen
│   ├── goal_manager.py      # Ziel-CRUD + Priorisierung + Scoring
│   ├── action_queue.py      # Priorisierte Aktions-Warteschlange
│   ├── journal.py           # ATL-Journal (Markdown, tagesbasiert)
│   └── config.py            # ATL-spezifische Konfiguration
```

Dazu:

```
~/.cognithor/
├── atl/
│   ├── goals.yaml           # Persistente Ziele
│   ├── journal/             # Tagesbasierte Journal-Einträge
│   │   └── 2026-03-30.md
│   └── state.yaml           # Loop-State (letzte Ausführung, Cycle-Count)
```

---

## 4. Konfiguration

```yaml
# ~/.cognithor/config.yaml
atl:
  enabled: false                    # Opt-in, default aus
  interval_minutes: 15              # Denkzyklus-Intervall (5-60 Min)
  quiet_hours:                      # Keine Zyklen in dieser Zeit
    start: "23:00"
    end: "07:00"
  max_actions_per_cycle: 3          # Max Aktionen pro Denkzyklus
  max_tokens_per_cycle: 4000        # Token-Budget pro Zyklus
  notification_channel: "telegram"  # Wohin proaktive Nachrichten gehen
  notification_level: "important"   # all | important | critical
  goal_review_interval: "daily"     # Wie oft Ziele re-evaluiert werden
  allowed_action_types:             # Welche Aktionen der ATL ausführen darf
    - memory_update
    - research
    - notification
    - file_management
    - goal_management
  blocked_action_types:             # Explizit verboten
    - shell_exec
    - send_message_unprompted       # Keine Spam-Nachrichten
  risk_ceiling: "YELLOW"            # Max Gatekeeper-Level (GREEN/YELLOW)
```

---

## 5. Kernkomponenten

### 5.1 Loop (`atl/loop.py`)

```python
class AutonomousThinkingLoop:
    """
    Hauptklasse — wird als Cron-Job registriert.
    Orchestriert einen einzelnen Denkzyklus.
    """

    def __init__(self, gateway, config: ATLConfig):
        self.gateway = gateway
        self.config = config
        self.context_assembler = ContextAssembler(gateway.memory)
        self.goal_manager = GoalManager(config.atl_home)
        self.action_queue = ActionQueue(max_actions=config.max_actions_per_cycle)
        self.journal = ATLJournal(config.atl_home / "journal")
        self.cycle_count = 0

    async def run_cycle(self) -> CycleResult:
        """Ein vollständiger Denkzyklus."""

        # 1. Quiet Hours prüfen
        if self._in_quiet_hours():
            return CycleResult(skipped=True, reason="quiet_hours")

        # 2. Kontext aufbauen
        context = await self.context_assembler.build(
            goals=self.goal_manager.active_goals(),
            recent_episodes=5,
            include_pending_tasks=True,
        )

        # 3. Planner fragen: "Was sollte ich jetzt tun?"
        thought = await self.gateway.planner.think_autonomous(
            context=context,
            system_prompt=ATL_SYSTEM_PROMPT,
            token_budget=self.config.max_tokens_per_cycle,
        )

        # 4. Ziele evaluieren und updaten
        goal_updates = await self.goal_manager.evaluate(
            thought=thought,
            context=context,
        )

        # 5. Aktionen in Queue einstellen
        actions = thought.proposed_actions
        for action in actions:
            self.action_queue.enqueue(action)

        # 6. Aktionen durch Gatekeeper + Executor
        results = []
        while not self.action_queue.empty():
            action = self.action_queue.dequeue()
            # Gatekeeper prüft mit ATL-spezifischem risk_ceiling
            approved = await self.gateway.gatekeeper.validate(
                action, risk_ceiling=self.config.risk_ceiling
            )
            if approved:
                result = await self.gateway.executor.execute(action)
                results.append(result)

        # 7. Journal-Eintrag schreiben
        await self.journal.log_cycle(
            cycle=self.cycle_count,
            thought_summary=thought.summary,
            goal_updates=goal_updates,
            actions_taken=results,
        )

        # 8. Ggf. User benachrichtigen
        if thought.wants_to_notify and self._should_notify(thought.priority):
            await self._notify_user(thought.notification)

        # 9. Reflector triggern
        await self.gateway.reflector.reflect_on_cycle(
            context=context, results=results
        )

        self.cycle_count += 1
        return CycleResult(
            skipped=False,
            thought=thought.summary,
            actions=len(results),
            goal_updates=goal_updates,
        )
```

### 5.2 Context Assembler (`atl/context_assembler.py`)

Baut den Kontext für den Planner-Prompt auf:

```python
class ContextAssembler:
    """Sammelt relevanten Kontext aus allen 5 Memory-Tiers."""

    async def build(self, goals, recent_episodes, include_pending_tasks):
        context = ATLContext()

        # Tier 1: Core Identity — Wer bin ich? Was sind meine Regeln?
        context.identity = await self.memory.core.read()

        # Tier 2: Episodic — Was ist zuletzt passiert?
        context.recent_events = await self.memory.episodic.recent(
            n=recent_episodes
        )

        # Tier 3: Semantic — Relevantes Wissen zu aktiven Zielen
        for goal in goals:
            related = await self.memory.semantic.search(
                query=goal.description, limit=3
            )
            context.goal_knowledge[goal.id] = related

        # Tier 4: Procedural — Welche Skills habe ich?
        context.available_skills = await self.memory.procedural.list_active()

        # Tier 5: Working — Aktive Session-Daten
        context.working = self.memory.working.snapshot()

        # Zusätzlich: Aktuelle Uhrzeit, Wochentag, Wetter (optional)
        context.temporal = TemporalContext.now()

        return context
```

### 5.3 Goal Manager (`atl/goal_manager.py`)

```python
@dataclass
class Goal:
    id: str
    title: str
    description: str
    priority: int                    # 1 (höchste) bis 5
    status: str                      # active | paused | completed | abandoned
    created_at: datetime
    updated_at: datetime
    deadline: datetime | None
    progress: float                  # 0.0 bis 1.0
    sub_goals: list[str]             # IDs von Sub-Goals
    success_criteria: list[str]      # Wann ist das Ziel erreicht?
    tags: list[str]
    source: str                      # "user" | "self" | "reflection"

class GoalManager:
    """CRUD + intelligente Evaluation von Zielen."""

    def active_goals(self) -> list[Goal]:
        """Alle aktiven Ziele, sortiert nach Priorität."""

    async def evaluate(self, thought, context) -> list[GoalUpdate]:
        """
        Evaluiert Ziele basierend auf dem Denkzyklus.
        - Progress aktualisieren
        - Ziele als completed/abandoned markieren
        - Neue Sub-Goals vorschlagen
        """

    def add_goal(self, goal: Goal, source: str = "self"):
        """Neues Ziel hinzufügen. User-Ziele haben Vorrang."""

    def user_set_goal(self, title, description, deadline=None):
        """User setzt ein Ziel — höchste Priorität, source='user'."""
```

**Persistenz:** `~/.cognithor/atl/goals.yaml`

```yaml
goals:
  - id: "g_001"
    title: "Wissens-Datenbank zu BU-Produkten aufbauen"
    description: "Alle WWK BU-Tarife strukturiert in der Knowledge Base erfassen"
    priority: 2
    status: active
    progress: 0.35
    created_at: "2026-03-28T10:00:00"
    deadline: "2026-04-15"
    success_criteria:
      - "Alle aktuellen BU-Tarife erfasst"
      - "Vergleichstabelle erstellt"
    source: "user"
    tags: ["versicherung", "wwk", "bu"]
```

### 5.4 ATL System Prompt

```python
ATL_SYSTEM_PROMPT = """
Du bist Cognithor im autonomen Denkmodus. Du wurdest NICHT von einem User
angesprochen — du denkst eigenständig.

DEIN KONTEXT:
{context.identity}

AKTIVE ZIELE:
{context.goals_formatted}

LETZTE EREIGNISSE:
{context.recent_events_formatted}

RELEVANTES WISSEN:
{context.goal_knowledge_formatted}

AKTUELLE ZEIT: {context.temporal.now}

DEINE AUFGABE in diesem Denkzyklus:
1. Evaluiere den Fortschritt deiner aktiven Ziele
2. Identifiziere, welche konkreten Schritte jetzt sinnvoll wären
3. Entscheide, ob du den User über etwas informieren solltest
4. Schlage max. {max_actions} Aktionen vor

ANTWORTE im folgenden JSON-Format:
{
  "summary": "Kurze Zusammenfassung deiner Gedanken",
  "goal_evaluations": [
    {"goal_id": "...", "progress_delta": 0.05, "note": "..."}
  ],
  "proposed_actions": [
    {"type": "research|memory_update|notification|...", "params": {...}}
  ],
  "wants_to_notify": false,
  "notification": null,
  "priority": "low|medium|important|critical"
}

REGELN:
- Sei sparsam mit Aktionen — nur wenn wirklich sinnvoll
- Keine Nachrichten an den User außer bei wichtigen Erkenntnissen
- User-Ziele (source: "user") haben immer Vorrang
- Du darfst neue Sub-Goals vorschlagen, aber nicht eigenmächtig löschen
- Respektiere das Token-Budget
"""
```

### 5.5 Journal (`atl/journal.py`)

```python
class ATLJournal:
    """Tagesbasiertes Journal — Markdown-Dateien."""

    async def log_cycle(self, cycle, thought_summary, goal_updates, actions_taken):
        """
        Schreibt einen Journal-Eintrag.
        Datei: ~/.cognithor/atl/journal/2026-03-30.md
        """

    def today(self) -> str | None:
        """Heutiges Journal lesen."""

    def search(self, query: str, days: int = 7) -> list[JournalEntry]:
        """Journal durchsuchen (wird in den Indexer integriert)."""
```

**Beispiel-Journal:**

```markdown
# ATL Journal — 2026-03-30

## Zyklus #1 — 08:15

**Gedanken:** Ziel "BU-Wissensdatenbank" ist bei 35%. Die letzten
Episoden zeigen, dass der User gestern WWK Tarif BU Protect besprochen
hat. Ich sollte diese Infos in die Knowledge Base übernehmen.

**Ziel-Updates:**
- g_001: +5% → 40% (BU Protect Tarif-Details erfasst)

**Aktionen:**
- ✅ memory_update: BU Protect Tarif in Semantic Memory gespeichert
- ✅ research: Aktuelle BU-Marktvergleiche recherchiert

**Notification:** Keine

---

## Zyklus #2 — 08:30

**Gedanken:** Keine dringenden Aktionen. Warte auf User-Input zu
den recherchierten Marktvergleichen.

**Aktionen:** Keine

---
```

---

## 6. Integration in bestehende Module

### 6.1 Cron Engine Registration

```python
# In gateway.py oder cron/jobs.py
from jarvis.atl.loop import AutonomousThinkingLoop

if config.atl.enabled:
    atl = AutonomousThinkingLoop(gateway=self, config=config.atl)
    cron_engine.add_job(
        func=atl.run_cycle,
        trigger="interval",
        minutes=config.atl.interval_minutes,
        id="atl_thinking_loop",
        name="Autonomous Thinking Loop",
        misfire_grace_time=60,
    )
```

### 6.2 Planner-Erweiterung

```python
# In core/planner.py — neue Methode
class Planner:
    async def think_autonomous(self, context: ATLContext,
                                system_prompt: str,
                                token_budget: int) -> AutonomousThought:
        """
        Spezieller Planner-Modus für autonomes Denken.
        Nutzt den Executor-LLM (kleiner/günstiger) statt den Planner-LLM,
        es sei denn, eine komplexe Entscheidung ist nötig.
        """
```

### 6.3 Gatekeeper — ATL Risk Ceiling

```python
# In core/gatekeeper.py — ATL-spezifische Policy
class Gatekeeper:
    def validate(self, action, risk_ceiling="ORANGE"):
        """
        Für ATL: risk_ceiling default auf YELLOW.
        ATL darf nur GREEN und YELLOW Aktionen ausführen.
        Keine ORANGE/RED ohne explizite User-Freigabe.
        """
```

### 6.4 Memory Integration

Der ATL Journal wird vom **Indexer** automatisch indiziert (via Watcher):

```python
# In memory/watcher.py — neuer Watch-Pfad
watch_paths.append(config.atl_home / "journal")
```

ATL-Gedanken fließen so in die **Hybrid Search** ein und sind für den regulären Planner bei User-Anfragen sichtbar.

---

## 7. User-Interaktion

### 7.1 CLI/Chat Commands

```
/atl status          → Zeigt ATL-Status, letzte Zyklen, aktive Ziele
/atl goals           → Liste aller Ziele mit Fortschritt
/atl goal add "..."  → Neues Ziel setzen
/atl goal pause g_001 → Ziel pausieren
/atl journal         → Heutiges Journal anzeigen
/atl journal 3       → Journal der letzten 3 Tage
/atl pause           → ATL temporär pausieren
/atl resume          → ATL fortsetzen
/atl config          → ATL-Konfiguration anzeigen/ändern
```

### 7.2 Notifications

ATL kann den User proaktiv benachrichtigen, aber **nur wenn**:
- `notification_level` passt (important/critical)
- Nicht in Quiet Hours
- Max 1 Notification pro Stunde (Rate Limiting)
- Gatekeeper erlaubt es

Beispiel Telegram-Notification:

```
🤔 Cognithor ATL

Ich habe beim Research festgestellt, dass sich die
BU-Bedingungen bei der WWK zum 01.04. ändern.
Das könnte für deine Kundenberatung relevant sein.

Details habe ich in der Knowledge Base gespeichert.
→ /atl journal für den vollständigen Bericht
```

---

## 8. Sicherheit

| Maßnahme | Beschreibung |
|-----------|-------------|
| **Opt-in** | ATL ist default deaktiviert |
| **Risk Ceiling** | Max YELLOW — keine destruktiven Aktionen |
| **Token Budget** | Begrenztes Token-Budget pro Zyklus |
| **Action Whitelist** | Nur erlaubte Aktionstypen |
| **Rate Limiting** | Max Notifications pro Stunde |
| **Quiet Hours** | Kein Denken nachts |
| **Audit Trail** | Jeder Zyklus wird im Audit Trail erfasst |
| **User-Ziel Vorrang** | ATL kann keine User-Ziele löschen |
| **No Spam** | send_message_unprompted default blockiert |
| **Gatekeeper** | Jede ATL-Aktion durchläuft den vollen PGE-Pfad |

---

## 9. Tests

```
tests/
├── test_atl/
│   ├── test_loop.py              # Loop-Zyklen (normal, quiet hours, errors)
│   ├── test_context_assembler.py # Kontext-Aufbau aus allen 5 Tiers
│   ├── test_goal_manager.py      # CRUD, Evaluation, Priorisierung
│   ├── test_action_queue.py      # Enqueue, Dequeue, Max-Limit
│   ├── test_journal.py           # Schreiben, Lesen, Suche
│   ├── test_config.py            # Konfiguration, Defaults, Validation
│   └── test_integration.py       # End-to-end mit Mock-Planner
```

**Geschätzt:** ~120 neue Tests

---

## 10. Implementierungs-Roadmap

| Phase | Aufgabe | Aufwand |
|-------|---------|---------|
| **Phase 1** | Goal Manager + YAML-Persistenz + CLI Commands | 1-2 Tage |
| **Phase 2** | Context Assembler + ATL System Prompt | 1 Tag |
| **Phase 3** | Loop-Klasse + Cron-Integration | 1 Tag |
| **Phase 4** | Journal + Indexer-Integration | 0.5 Tage |
| **Phase 5** | Notification-System + Rate Limiting | 0.5 Tage |
| **Phase 6** | Gatekeeper ATL-Policy + Security | 0.5 Tage |
| **Phase 7** | Tests (~120) + Integration Tests | 1-2 Tage |
| **Phase 8** | Dokumentation + README Update | 0.5 Tage |

**Gesamtaufwand:** ~6-8 Tage

---

## 11. Abgrenzung zu Jork

| Aspekt | Jork | Cognithor ATL |
|--------|------|---------------|
| Architektur | Monolithischer Loop in `jork.js` | Modulares `atl/` Package im PGE-Pfad |
| Sicherheit | Keine Einschränkungen | Gatekeeper + Risk Ceiling + Audit |
| Ziel-System | Einfaches `goals.json` | Strukturiertes YAML mit Priorisierung, Sub-Goals, Success Criteria |
| Memory | Flat-Files (SELF.md, SNAPSHOT.md) | 5-Tier Cognitive Memory mit Hybrid Search |
| Konfigurierbarkeit | Hardcoded 5 Min | Flexibel (5-60 Min), Quiet Hours, Action Whitelist |
| Notifications | Telegram-only, ungefiltert | Multi-Channel, Rate Limited, Level-basiert |
| Journal | Einfaches Markdown | Indexiert, durchsuchbar, in Hybrid Search integriert |
| Identität | Jork "schreibt sich selbst um" | CORE.md + kontrollierte Updates via Gatekeeper |

---

*Spec erstellt am 30.03.2026 — Cognithor ATL v1.0 Draft*
