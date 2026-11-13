# ARC-AGI-3 GameAnalyzer Design

**Date:** 2026-04-04
**Status:** Approved
**Scope:** 3 new files in `src/jarvis/arc/`, 1 modified file

## Problem

Die bestehenden ARC-AGI-3 Solver sind spezialisiert (Click-only, Keyboard-only, Vision-per-step) und wissen nichts über das Spiel, bevor sie loslegen. Jedes der 25 Spiele hat eigene Mechaniken, die im Tutorial erklärt werden. Wir brauchen eine Analyse-Schicht, die pro Spiel einmal die Mechanik versteht und dann den passenden Solver-Mix wählt.

## Architecture

Modularer Dreispalter — drei neue Dateien:

```
src/jarvis/arc/
├── game_profile.py      # Datenklasse + Persistenz + Metriken
├── game_analyzer.py     # Opferlevel + 2 Vision-Calls → GameProfile
└── per_game_solver.py   # Budget-basierter Strategie-Mix → Solve
```

Persistenz:
```
~/.cognithor/arc/
└── game_profiles/
    └── {game_id}.json
```

## Component 1: GameProfile (`game_profile.py`)

### Datenstruktur

```python
@dataclass
class StrategyMetrics:
    attempts: int = 0
    wins: int = 0
    total_levels_solved: int = 0
    avg_steps_to_win: float = 0.0
    avg_budget_ratio: float = 0.0     # Anteil des Budgets verbraucht (0-1)

@dataclass
class GameProfile:
    game_id: str
    game_type: Literal["click", "keyboard", "mixed"]
    available_actions: list[int]

    # Analyse-Ergebnisse
    click_zones: list[tuple[int, int]]
    target_colors: list[int]
    movement_effects: dict[int, str]   # {action_id: "moves_player"|"no_effect"|"transforms"}
    win_condition: str                 # "clear_board"|"reach_state"|"navigate"|"unknown"
    vision_description: str
    vision_strategy: str

    # Erfolgs-Metriken (lernt ueber Runs)
    strategy_metrics: dict[str, StrategyMetrics]
    total_runs: int = 0
    best_score: int = 0

    # Meta
    analyzed_at: str                   # ISO timestamp
    profile_version: int = 1
```

### Methoden

- `save()` — JSON-Serialisierung nach `~/.cognithor/arc/game_profiles/{game_id}.json`
- `load(game_id) -> GameProfile | None` — Laden aus Cache
- `exists(game_id) -> bool` — Pruefen ob Profil vorhanden
- `update_metrics(strategy_name, result)` — Metriken nach Solve-Versuch aktualisieren
- `ranked_strategies() -> list[str]` — Sortiert nach win_rate, mit Exploration-Bonus fuer wenig-versuchte Strategien

## Component 2: GameAnalyzer (`game_analyzer.py`)

Fuehrt ein Opferlevel durch und erstellt ein GameProfile via 2 Vision-Calls.

### Oeffentliche API

```python
class GameAnalyzer:
    def __init__(self, arcade: Arcade):
        ...

    async def analyze(self, game_id: str, force: bool = False) -> GameProfile:
        """Analysiert ein Spiel. Laedt aus Cache wenn vorhanden, sonst Opferlevel."""
        ...
```

### Interner Ablauf von `analyze()`

1. **Cache-Check** — `GameProfile.exists(game_id)` und `profile_version` pruefen. Bei Cache-Hit: Profil laden und zurueckgeben.
2. **Env erstellen** — `arcade.make(game_id)`, `env.reset()`, initiales Frame extrahieren.
3. **Vision-Call 1** — Initiales Frame (256x256 PNG) an qwen3-vl:
   - Prompt: "Was ist das fuer ein Spiel? Was ist das Ziel? Welche Farben sind interaktiv?"
   - Ollama mit `num_ctx=8192`, `num_predict=8192`
   - JSON-Antwort mit 3-Tier-Fallback-Parsing
4. **Opferlevel ausfuehren** — Systematische Exploration:
   - `available_actions` auslesen → `game_type` ableiten (6 dabei = click/mixed, sonst keyboard)
   - **Keyboard-Test:** Jede Richtung (1-4) 3x ausfuehren, Pixel-Diff messen → `movement_effects`
   - **Click-Test:** `ClusterSolver.find_clusters()` fuer Kandidaten-Positionen, dann auf Cluster-Zentren klicken → `click_zones` + `target_colors`
   - Zustandsaenderungen tracken via Frame-Diffs
   - Bei GAME_OVER: notieren was es ausgeloest hat, abbrechen
   - Ergebnis: `SacrificeReport`
5. **Vision-Call 2** — Initial-Frame + letztes Frame + Diff-Bild (256x256):
   - Prompt: "Was hat sich veraendert? War die erste Einschaetzung korrekt? Was ist die Win-Condition?"
   - Validiert/korrigiert die erste Vision-Einschaetzung
6. **GameProfile zusammenbauen** aus Vision-Antworten + Opferlevel-Daten
7. **Persistieren** — `profile.save()`

### SacrificeReport (intern)

```python
@dataclass
class SacrificeReport:
    clicks_tested: list[tuple[int, int, str]]   # (x, y, effect)
    movements_tested: dict[int, int]             # {action_id: pixel_diff}
    unique_states_seen: int
    game_over_trigger: str | None
    frames: list[ndarray]                        # Key-Frames fuer Vision
```

## Component 3: PerGameSolver (`per_game_solver.py`)

Budget-basierter Solver, der Strategien nach Ranking ausfuehrt.

### Oeffentliche API

```python
class PerGameSolver:
    def __init__(self, profile: GameProfile, arcade: Arcade):
        ...

    async def solve(self, max_levels: int = 10) -> SolveResult:
        """Loest das Spiel Level fuer Level mit Budget-basiertem Strategie-Mix."""
        ...
```

### Strategien

5 interne Strategien, nicht als eigene Klassen:

| Name | Beschreibung | Geeignet fuer |
|------|-------------|---------------|
| `cluster_click` | `find_clusters()` → Subset-Suche mit `arcade.make()` pro Combo | Click-Spiele |
| `targeted_click` | Nur auf `click_zones` aus GameProfile klicken | Click-Spiele mit bekannten Zonen |
| `keyboard_explore` | Explorer + StateGraph fuer Navigation | Keyboard-Spiele |
| `keyboard_sequence` | Vision-empfohlene Sequenz abspielen | Keyboard mit klarer Loesung |
| `hybrid` | Keyboard-Navigation + Click an Zielposition | Mixed-Spiele |

### Budget-Verteilung

Gesamt-Budget pro Level geschaetzt aus GameProfile:
- Click-Spiele: ~20 Actions
- Keyboard-Spiele: ~200 Actions
- Mixed: ~100 Actions

Verteilung nach `profile.ranked_strategies()`:
- Rang 1: 50% des Budgets
- Rang 2: 30%
- Rang 3: 20%

**Defaults bei erstem Run (keine Metriken):**
- click → `cluster_click: 50%, targeted_click: 30%, hybrid: 20%`
- keyboard → `keyboard_explore: 50%, keyboard_sequence: 30%, hybrid: 20%`
- mixed → `hybrid: 50%, targeted_click: 30%, keyboard_explore: 20%`

### Stagnations-Erkennung

Sliding window ueber die letzten 5 Frames. Wenn Pixel-Diff < 10 geaenderte Pixel ueber das ganze Fenster → Strategie-Wechsel zum naechsten Budget-Slot.

### Level-Loop

1. `env.reset()` (oder naechstes Level nach WIN)
2. Budget-Slots berechnen via `_allocate_budget(level_num)`
3. Fuer jeden Slot in Prioritaets-Reihenfolge:
   - Strategie ausfuehren bis Budget aufgebraucht ODER WIN ODER Stagnation
   - Bei WIN → Metriken updaten, naechstes Level
   - Bei Stagnation → naechster Slot
   - Bei GAME_OVER → Level-Reset, naechster Slot (oder Retry gleicher Slot wenn Budget uebrig)
4. Alle Slots durch ohne WIN → Level gescheitert
5. Nach jedem Level: `profile.update_metrics()` + `profile.save()`

### SolveResult

```python
@dataclass
class SolveResult:
    game_id: str
    levels_completed: int
    total_steps: int
    strategy_log: list[dict]   # [{level, strategy, outcome, steps}]
    score: float
```

## Integration

### Entry-Point (`__main__.py` aendern)

Neuer Modus `--analyzer`:

```
python -m jarvis.arc --analyzer              # Alle 25 Spiele
python -m jarvis.arc --analyzer --game ft09  # Einzelnes Spiel
python -m jarvis.arc --analyzer --reanalyze  # Cache ignorieren
```

### Arcade-Instanz-Sharing

Ein einziger `arc_agi.Arcade()`-Call fuer alle Spiele. `arcade.make(game_id)` pro Spiel — spart ~100ms API-Key-Fetch pro make()-Aufruf gegenueber dem alten Pattern (arcade.make() pro Combo).

### Wiederverwendete Module (Import)

- `adapter.py` — `safe_frame_extract()` fuer Frame-Normalisierung
- `cluster_solver.py` — `find_clusters()` fuer Click-Zonen-Erkennung im Opferlevel
- `frame_analyzer.py` — Pixel-Diff-Berechnung fuer Stagnation

### Keine Aenderungen an bestehenden Solvern

Die Solver-Logik wird im PerGameSolver reimplementiert basierend auf den Patterns der bestehenden Solver, nicht durch direkte Aufrufe. Das vermeidet enge Kopplung an deren interne APIs.

## Error Handling

### Opferlevel-Abbruch
- GAME_OVER nach wenigen Clicks → Profil wird trotzdem erstellt. `win_condition = "unknown"`, Click-Budget als "niedrig" markiert.
- Spiel hat kein Click (nur Keyboard) → Click-Scan wird uebersprungen, `game_type = "keyboard"`.
- Vision-Call schlaegt fehl (Ollama nicht erreichbar) → Fallback auf rein datengetriebene Analyse (Pixel-Diffs, Action-Types). `vision_description = "unavailable"`.

### PerGameSolver
- Alle Strategien stagnieren → Level als gescheitert markieren, weiter zum naechsten Level.
- Level hat andere Mechanik als Opferlevel → Stagnations-Erkennung greift, wechselt zur naechsten Strategie. Profil wird mit `"mixed"` aktualisiert.
- Profil existiert aber falsche Version → `profile_version`-Check, bei Mismatch neu analysieren.

### Persistenz
- Disk-Write fehlgeschlagen → Warning loggen, im RAM weiterarbeiten.
- Korruptes JSON → Profil loeschen, neu analysieren.
- Concurrent Access → Nicht relevant, Analyzer laeuft sequenziell pro Spiel.

### Budget-Grenzen
- Gesamt-Timeout pro Spiel: 5 Minuten (inkl. Vision-Calls)
- Max Levels: konfigurierbar, Default 10
- Max Resets pro Level: 3 (dann Level ueberspringen)

## Testing

- `test_game_profile.py` — Serialisierung, Metriken-Update, ranked_strategies()
- `test_game_analyzer.py` — Opferlevel-Ablauf, Vision-Fallback, Cache-Hit/Miss
- `test_per_game_solver.py` — Budget-Verteilung, Stagnation, Strategie-Wechsel, Metriken-Lernen

## Files

### New
- `src/jarvis/arc/game_profile.py`
- `src/jarvis/arc/game_analyzer.py`
- `src/jarvis/arc/per_game_solver.py`

### Modified
- `src/jarvis/arc/__main__.py` — `--analyzer` + `--reanalyze` Flags
