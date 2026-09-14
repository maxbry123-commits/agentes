# ARC-AGI-3 Redesign: DSL + LLM Hybrid Solver — Design Spec

**Date:** 2026-04-04
**Status:** Approved
**Replaces:** The existing RL/State-Graph agent (0 wins on 12 games)

## Goal

Replace the fundamentally flawed RL-based ARC agent with a pattern-recognition approach: DSL-based combinatorial search for simple transformations, LLM code-generation fallback for complex ones. Validate against example pairs, rank by Occam's Razor, submit top 3 candidates.

## Why the Current Agent Fails

The existing agent treats ARC-AGI-3 as a reinforcement learning problem (state graphs, CNN action prediction, exploration phases). ARC is actually a pattern-recognition problem: given example input→output grid pairs, infer the transformation rule and apply it to a test input. The RL approach has 11 root causes for failure, the most critical being:

1. State detection never recognizes WIN → cascading failure through all systems
2. CNN untrained and reset every level → predictions useless
3. Action space discovery incomplete → explorer can't learn mechanics
4. LLM planner disabled by default → no strategic guidance

## Architecture

```
ArcTask (2-3 example pairs + test input)
  │
  ├─ Phase 1: DSL Search (fast, deterministic)
  │   ├─ Depth 1: single primitives (~150 candidates)
  │   ├─ Depth 2: 2-combinations (~22,500 candidates)
  │   ├─ Depth 3: 3-combinations (~3.3M candidates, ~3s)
  │   ├─ Validate each against ALL example pairs
  │   └─ Found? → Rank by simplicity → Submit top 3
  │
  ├─ Phase 2: LLM Code Generation (fallback)
  │   ├─ Format grids as text for qwen3.5:27b
  │   ├─ Prompt: describe transformation + generate Python
  │   ├─ Execute in sandbox (5s timeout, restricted imports)
  │   ├─ Validate against example pairs
  │   └─ Found? → Submit
  │
  └─ Phase 3: No solution found → skip task
```

## 1. Data Model

```python
Grid = list[list[int]]  # 2D array, values 0-9 (10 colors)

@dataclass
class ArcTask:
    task_id: str
    examples: list[tuple[Grid, Grid]]  # (input, output) pairs
    test_input: Grid

@dataclass
class Solution:
    output: Grid
    method: str         # "dsl" or "llm"
    description: str    # human-readable (e.g. "rotate_90 → recolor(3,7)")
    complexity: int     # number of primitives (for Occam ranking)
    transform_fn: Callable[[Grid], Grid] | None

@dataclass
class GameResult:
    win: bool
    attempts: int       # 1-3
    task_id: str
    solutions_tried: list[Solution]
```

## 2. DSL Primitives (`dsl.py`)

25-30 pure functions, each `(Grid, *params) → Grid`:

### Geometry (6)
- `rotate_90(grid)` → 90° clockwise
- `rotate_180(grid)` → 180°
- `rotate_270(grid)` → 270° clockwise
- `flip_h(grid)` → horizontal mirror
- `flip_v(grid)` → vertical mirror
- `transpose(grid)` → swap rows/columns

### Color (5)
- `recolor(grid, from_color, to_color)` → replace one color with another
- `fill(grid, color)` → fill entire grid with one color
- `swap_colors(grid, a, b)` → swap two colors
- `replace_background(grid, new_bg)` → replace the most common color
- `invert_colors(grid)` → each cell becomes `9 - cell`

### Shape (5)
- `crop_to_content(grid)` → remove surrounding background
- `pad(grid, n, color=0)` → add n-cell border
- `tile(grid, nx, ny)` → repeat grid nx×ny times
- `scale_up(grid, factor)` → enlarge each cell to factor×factor block
- `scale_down(grid, factor)` → shrink by averaging/majority

### Extraction (5)
- `get_objects(grid)` → list of connected components (flood-fill)
- `get_largest_object(grid)` → largest connected component as grid
- `get_by_color(grid, color)` → mask: only cells of that color
- `count_by_color(grid)` → dict of color→count
- `get_bounding_box(grid, color)` → cropped region around color

### Composition (5)
- `overlay(base, top, transparent=0)` → place top over base
- `stack_h(a, b)` → concatenate horizontally
- `stack_v(a, b)` → concatenate vertically
- `mask_where(grid, condition_fn)` → zero out cells not matching condition
- `gravity(grid, direction)` → drop non-zero cells in direction

All primitives are pure, deterministic, tested independently. ~500 LOC total.

## 3. DSL Search (`dsl_search.py`)

Combinatorial search over primitive sequences:

```python
class DSLSearch:
    def search(self, task: ArcTask, max_depth: int = 3) -> list[Solution]:
        """Find primitive combinations that solve all examples."""
        for depth in range(1, max_depth + 1):
            candidates = self._generate_candidates(depth)
            for candidate in candidates:
                transform_fn = self._compose(candidate)
                if self._validates(transform_fn, task):
                    solutions.append(Solution(...))
        return solutions
```

### Parameter Generation

Each primitive has a finite parameter space:
- No-param (rotate, flip, transpose): 1 variant each
- Single-color param (recolor, fill, get_by_color): 10 variants (colors 0-9)
- Two-color param (swap_colors, recolor): 90 variants (10×9)
- Integer param (pad, scale, tile): 3-5 variants

Total Depth-1 candidates: ~150. Depth-2: ~22,500. Depth-3: ~3.3M.

### Early Termination

- If Depth 1 finds solutions → skip Depth 2+3
- If a candidate fails on the first example → skip immediately (no need to check all)
- Timeout: 10s total for DSL search

## 4. LLM Solver (`llm_solver.py`)

Fallback when DSL search finds nothing:

```python
class LLMSolver:
    async def solve(self, task: ArcTask, max_attempts: int = 3) -> list[Solution]:
        prompt = self._format_task(task)
        for attempt in range(max_attempts):
            response = await self._llm_call(prompt)
            code = self._extract_python(response)
            if code:
                result = self._execute_in_sandbox(code, task.test_input)
                if result and self._validates(code_fn, task):
                    solutions.append(Solution(output=result, method="llm", ...))
```

### Prompt Format

```
Du siehst ARC-AGI Aufgaben. Jede Aufgabe hat Beispiel-Paare (Input→Output Grids).
Finde die Transformation und schreibe eine Python-Funktion.

Beispiel 1:
Input:
[[0,0,3],[0,3,0],[3,0,0]]
Output:
[[3,0,0],[0,3,0],[0,0,3]]

Beispiel 2:
...

Test-Input:
[[1,0,0],[0,1,0],[0,0,1]]

Schreibe eine Python-Funktion:
def transform(grid: list[list[int]]) -> list[list[int]]:
    # Deine Lösung hier
```

### Sandbox

Restricted execution:
- Allowed: list comprehensions, for/while, if/else, basic math, len, range, zip, enumerate
- Blocked: import, exec, eval, open, os, sys, subprocess, __import__
- Timeout: 5 seconds per execution
- Memory limit: 100MB

## 5. Validation + Ranking

```python
def validate(transform_fn, task: ArcTask) -> bool:
    """True if transform_fn reproduces ALL example outputs exactly."""
    for input_grid, expected in task.examples:
        try:
            actual = transform_fn(input_grid)
            if actual != expected:
                return False
        except Exception:
            return False
    return True

def rank_by_simplicity(solutions: list[Solution]) -> list[Solution]:
    """Occam's Razor: lower complexity = higher confidence."""
    return sorted(solutions, key=lambda s: (s.complexity, s.method != "dsl"))
```

DSL solutions ranked before LLM solutions at same complexity (DSL is more trustworthy).

3 attempts per task: submit top 3 candidates in order.

## 6. Refactored Agent (`agent.py`)

```python
class CognithorArcAgent:
    def __init__(self, adapter, solver, audit, episode_memory):
        self._adapter = adapter
        self._solver = solver       # NEW: ArcSolver
        self._audit = audit         # KEPT
        self._memory = episode_memory  # KEPT

    async def play_game(self, game_id: str) -> GameResult:
        task = self._adapter.load_task(game_id)
        solutions = await self._solver.solve(task)

        for i, solution in enumerate(solutions[:3]):
            result = self._adapter.submit(task.task_id, solution.output)
            self._audit.log_attempt(game_id, i, solution, result)
            if result.correct:
                self._memory.record_success(task, solution)
                return GameResult(win=True, attempts=i+1, ...)

        return GameResult(win=False, attempts=len(solutions), ...)
```

## 7. Files Changed

### New Files
| File | Purpose | Est. LOC |
|------|---------|----------|
| `src/jarvis/arc/solver.py` | ArcSolver orchestration (DSL → LLM) | ~100 |
| `src/jarvis/arc/dsl.py` | 25-30 grid primitives | ~500 |
| `src/jarvis/arc/dsl_search.py` | Combinatorial DSL search | ~200 |
| `src/jarvis/arc/llm_solver.py` | LLM code-generation + sandbox | ~250 |
| `src/jarvis/arc/task_parser.py` | ArcTask/Grid/Solution dataclasses | ~60 |
| `tests/test_arc/test_dsl.py` | Tests for each primitive | ~400 |
| `tests/test_arc/test_dsl_search.py` | Search tests | ~150 |
| `tests/test_arc/test_llm_solver.py` | LLM solver tests | ~150 |
| `tests/test_arc/test_solver.py` | Integration tests | ~100 |

### Kept Files (minor updates)
| File | Change |
|------|--------|
| `adapter.py` | Fix SDK format assumptions if needed |
| `audit.py` | Add Solution logging |
| `episode_memory.py` | Add success recording |
| `__main__.py` | Wire new solver |
| `validate_sdk.py` | Call at startup |

### Deleted Files
| File | Reason |
|------|--------|
| `explorer.py` | RL exploration — wrong approach |
| `state_graph.py` | State graph navigation — wrong approach |
| `mechanics_model.py` | RL rule learning — replaced by DSL |
| `cnn_model.py` | CNN predictor — replaced by DSL+LLM |
| `offline_trainer.py` | CNN training — no longer needed |
| `goal_inference.py` | RL goal inference — no longer needed |
| `swarm.py` | Multi-agent — overkill |

## 8. Expected Performance

- **DSL-only (Depth 1-3):** Should solve ~30-40% of ARC training tasks (geometric transforms, color swaps, simple compositions)
- **DSL + LLM:** Should solve ~50-60% of training tasks
- **Comparison:** Current agent: 0%. State-of-the-art (GPT-4 + program synthesis): ~75-85%.
- **Realistic local model (qwen3.5:27b):** 40-55% is a good target.

## 9. Degradation Guarantees

- If DSL search times out → LLM fallback
- If LLM fails to generate valid code → skip task (no crash)
- If sandbox execution fails → skip that attempt, try next
- If adapter format mismatch → validate_sdk.py catches it at startup
- All existing infrastructure (audit, memory, CLI) remains functional
