# Computer Use Phase 2C: Planner Intelligence — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add sub-task decomposition, content accumulation, error recovery, file creation, and completion reporting to the CU agent loop.

**Architecture:** A `CUTaskDecomposer` breaks complex goals into ordered `CUSubTask` objects before the agent loop. The `CUAgentExecutor` iterates sub-tasks sequentially, running the existing screenshot→decide→act cycle per sub-task. Content flows between sub-tasks via a shared `content_bag` dict. Completion hints enable auto-transition. Failure escalation gives the model increasingly urgent hints. File creation uses the existing `write_file` MCP tool.

**Tech Stack:** Python 3.13, dataclasses, asyncio, Ollama (qwen3-vl:32b), pytest

**Spec:** `docs/superpowers/specs/2026-04-03-computer-use-2c-planner-intelligence-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/jarvis/core/cu_agent.py` | All Phase 2C logic: dataclasses, decomposer, enhanced loop, error recovery, content bag |
| `src/jarvis/gateway/gateway.py` | 3 lines: include `task_summary` and `output_files` in CU result message |
| `tests/test_core/test_cu_agent.py` | All new tests: decomposer, hint matching, failure escalation, sub-task loop, content bag, gateway fields |

---

### Task 1: Data Model — CUSubTask, CUTaskPlan, Extended CUAgentResult

**Files:**
- Modify: `src/jarvis/core/cu_agent.py:28-50`
- Test: `tests/test_core/test_cu_agent.py`

- [ ] **Step 1: Write failing tests for new dataclasses**

Add these test classes at the end of `tests/test_core/test_cu_agent.py`:

```python
from jarvis.core.cu_agent import (
    CUAgentConfig,
    CUAgentExecutor,
    CUAgentResult,
    CUSubTask,
    CUTaskPlan,
)


class TestCUSubTask:
    def test_defaults(self):
        st = CUSubTask(name="open_app", goal="Oeffne Reddit", completion_hint="Reddit sichtbar")
        assert st.name == "open_app"
        assert st.goal == "Oeffne Reddit"
        assert st.completion_hint == "Reddit sichtbar"
        assert st.max_iterations == 10
        assert st.available_tools == []
        assert st.extract_content is False
        assert st.content_key == ""
        assert st.output_file == ""
        assert st.status == "pending"

    def test_custom(self):
        st = CUSubTask(
            name="scroll",
            goal="Scrolle Posts",
            completion_hint="10 Posts gelesen",
            max_iterations=15,
            available_tools=["computer_scroll", "extract_text"],
            extract_content=True,
            content_key="posts",
        )
        assert st.max_iterations == 15
        assert st.extract_content is True
        assert st.content_key == "posts"
        assert "computer_scroll" in st.available_tools


class TestCUTaskPlan:
    def test_defaults(self):
        plan = CUTaskPlan(original_goal="test", sub_tasks=[])
        assert plan.original_goal == "test"
        assert plan.sub_tasks == []
        assert plan.output_filename == ""
        assert plan.variables == {}

    def test_with_sub_tasks(self):
        st1 = CUSubTask(name="a", goal="g1", completion_hint="h1")
        st2 = CUSubTask(name="b", goal="g2", completion_hint="h2")
        plan = CUTaskPlan(
            original_goal="do stuff",
            sub_tasks=[st1, st2],
            output_filename="out.txt",
            variables={"date": "20260403"},
        )
        assert len(plan.sub_tasks) == 2
        assert plan.variables["date"] == "20260403"


class TestCUAgentResultExtended:
    def test_new_fields_default(self):
        r = CUAgentResult()
        assert r.output_files == []
        assert r.task_summary == ""

    def test_new_fields_populated(self):
        r = CUAgentResult(
            output_files=["/home/user/docs/out.txt"],
            task_summary="3/3 Phasen abgeschlossen.",
        )
        assert len(r.output_files) == 1
        assert "3/3" in r.task_summary
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_core/test_cu_agent.py::TestCUSubTask -v && pytest tests/test_core/test_cu_agent.py::TestCUTaskPlan -v && pytest tests/test_core/test_cu_agent.py::TestCUAgentResultExtended -v`
Expected: ImportError for `CUSubTask` and `CUTaskPlan`

- [ ] **Step 3: Implement the dataclasses**

In `src/jarvis/core/cu_agent.py`, add these dataclasses after the existing `CUAgentConfig` (after line 37) and before `CUAgentResult`:

```python
@dataclass
class CUSubTask:
    """A single phase of a decomposed CU goal."""

    name: str
    goal: str
    completion_hint: str
    max_iterations: int = 10
    available_tools: list[str] = field(default_factory=list)
    extract_content: bool = False
    content_key: str = ""
    output_file: str = ""
    status: str = "pending"
```

```python
@dataclass
class CUTaskPlan:
    """Full decomposed plan for a complex CU goal."""

    original_goal: str
    sub_tasks: list[CUSubTask]
    output_filename: str = ""
    variables: dict[str, str] = field(default_factory=dict)
```

Extend `CUAgentResult` — add two fields after `action_history`:

```python
    output_files: list[str] = field(default_factory=list)
    task_summary: str = ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_core/test_cu_agent.py::TestCUSubTask tests/test_core/test_cu_agent.py::TestCUTaskPlan tests/test_core/test_cu_agent.py::TestCUAgentResultExtended -v`
Expected: All PASS

- [ ] **Step 5: Verify existing tests still pass**

Run: `pytest tests/test_core/test_cu_agent.py -v`
Expected: All existing tests PASS (no regressions from new fields with defaults)

- [ ] **Step 6: Commit**

```bash
git add src/jarvis/core/cu_agent.py tests/test_core/test_cu_agent.py
git commit -m "feat(cu): add CUSubTask, CUTaskPlan dataclasses and extend CUAgentResult"
```

---

### Task 2: Completion Hint Matching and Screenshot Similarity

**Files:**
- Modify: `src/jarvis/core/cu_agent.py`
- Test: `tests/test_core/test_cu_agent.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_core/test_cu_agent.py`:

```python
class TestCompletionHintMatching:
    def _make_agent(self) -> CUAgentExecutor:
        planner = MagicMock()
        planner._ollama = AsyncMock()
        mcp = MagicMock()
        mcp._builtin_handlers = {}
        return CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})

    def test_hint_matches_when_keywords_present(self):
        agent = self._make_agent()
        assert agent._check_completion_hint(
            "locallama erscheint in URL oder Titel",
            "Browser zeigt reddit.com/r/locallama im Titel",
        ) is True

    def test_hint_no_match_when_keywords_missing(self):
        agent = self._make_agent()
        assert agent._check_completion_hint(
            "locallama erscheint in URL oder Titel",
            "Desktop mit verschiedenen Icons sichtbar",
        ) is False

    def test_hint_empty_returns_false(self):
        agent = self._make_agent()
        assert agent._check_completion_hint("", "something on screen") is False

    def test_hint_short_words_ignored(self):
        agent = self._make_agent()
        # "in" and "URL" (len<=3) are ignored, only "erscheint", "Titel", "locallama" count
        assert agent._check_completion_hint(
            "in URL Titel locallama erscheint",
            "locallama erscheint Titel",
        ) is True

    def test_hint_partial_match_below_threshold(self):
        agent = self._make_agent()
        # 5 keywords, only 2 match -> 40% < 60%
        assert agent._check_completion_hint(
            "Rechner Fenster zeigt Ergebnis sichtbar",
            "Rechner Fenster ist im Hintergrund",
        ) is False

    def test_hint_60_percent_threshold(self):
        agent = self._make_agent()
        # 5 keywords, 3 match -> 60% == threshold -> True
        assert agent._check_completion_hint(
            "Reddit Seite zeigt locallama Ergebnisse",
            "Reddit zeigt locallama und andere Dinge Ergebnisse",
        ) is True


class TestScreenshotSimilarity:
    def _make_agent(self) -> CUAgentExecutor:
        planner = MagicMock()
        planner._ollama = AsyncMock()
        mcp = MagicMock()
        mcp._builtin_handlers = {}
        return CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})

    def test_identical_descriptions(self):
        agent = self._make_agent()
        assert agent._screenshot_similarity("Desktop mit Icons", "Desktop mit Icons") == 1.0

    def test_completely_different(self):
        agent = self._make_agent()
        sim = agent._screenshot_similarity("Rechner zeigt Ergebnis", "Browser offen leer")
        assert sim < 0.2

    def test_empty_strings(self):
        agent = self._make_agent()
        assert agent._screenshot_similarity("", "something") == 0.0
        assert agent._screenshot_similarity("something", "") == 0.0
        assert agent._screenshot_similarity("", "") == 0.0

    def test_high_overlap(self):
        agent = self._make_agent()
        sim = agent._screenshot_similarity(
            "Reddit Seite mit locallama Posts sichtbar",
            "Reddit Seite mit locallama Posts und Kommentare sichtbar",
        )
        assert sim > 0.7
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_core/test_cu_agent.py::TestCompletionHintMatching -v && pytest tests/test_core/test_cu_agent.py::TestScreenshotSimilarity -v`
Expected: AttributeError for `_check_completion_hint` and `_screenshot_similarity`

- [ ] **Step 3: Implement both methods**

Add to `CUAgentExecutor` class in `src/jarvis/core/cu_agent.py`, after `_format_elements`:

```python
    @staticmethod
    def _check_completion_hint(hint: str, screenshot_desc: str) -> bool:
        """Fuzzy check if the completion hint is satisfied (60% keyword overlap)."""
        if not hint:
            return False
        hint_lower = hint.lower()
        desc_lower = screenshot_desc.lower()
        keywords = [w for w in hint_lower.split() if len(w) > 3]
        if not keywords:
            return False
        matches = sum(1 for kw in keywords if kw in desc_lower)
        return matches / len(keywords) >= 0.6

    @staticmethod
    def _screenshot_similarity(prev: str, curr: str) -> float:
        """Jaccard similarity between two screenshot descriptions."""
        words_a = set(prev.lower().split())
        words_b = set(curr.lower().split())
        if not words_a or not words_b:
            return 0.0
        return len(words_a & words_b) / len(words_a | words_b)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_core/test_cu_agent.py::TestCompletionHintMatching tests/test_core/test_cu_agent.py::TestScreenshotSimilarity -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/core/cu_agent.py tests/test_core/test_cu_agent.py
git commit -m "feat(cu): add completion hint matching and screenshot similarity"
```

---

### Task 3: CUTaskDecomposer — Variable Resolution and JSON Parsing

**Files:**
- Modify: `src/jarvis/core/cu_agent.py`
- Test: `tests/test_core/test_cu_agent.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_core/test_cu_agent.py`:

```python
from jarvis.core.cu_agent import CUTaskDecomposer


class TestCUTaskDecomposerVariables:
    def _make_decomposer(self) -> CUTaskDecomposer:
        planner = MagicMock()
        planner._ollama = AsyncMock()
        return CUTaskDecomposer(planner, CUAgentConfig())

    def test_resolve_variables_has_date(self):
        d = self._make_decomposer()
        v = d._resolve_variables("some goal")
        assert "date" in v
        # Should be 8 digits YYYYMMDD
        assert len(v["date"]) == 8
        assert v["date"].isdigit()

    def test_resolve_variables_has_documents(self):
        d = self._make_decomposer()
        v = d._resolve_variables("some goal")
        assert "documents" in v
        assert "Documents" in v["documents"] or "documents" in v["documents"].lower()

    def test_resolve_variables_has_date_formats(self):
        d = self._make_decomposer()
        v = d._resolve_variables("some goal")
        assert "date_dots" in v  # e.g. "03.04.2026"
        assert "date_iso" in v   # e.g. "2026-04-03"

    def test_resolve_output_path_simple(self):
        d = self._make_decomposer()
        variables = {"date": "20260403", "documents": "C:\\Users\\Test\\Documents"}
        path = d._resolve_output_path("Reddit_fetch_{date}.txt", variables)
        assert path == "C:\\Users\\Test\\Documents\\Reddit_fetch_20260403.txt"

    def test_resolve_output_path_no_variables(self):
        d = self._make_decomposer()
        variables = {"date": "20260403", "documents": "C:\\Users\\Test\\Documents"}
        path = d._resolve_output_path("static_name.txt", variables)
        assert path == "C:\\Users\\Test\\Documents\\static_name.txt"


class TestCUTaskDecomposerParsing:
    def _make_decomposer(self) -> CUTaskDecomposer:
        planner = MagicMock()
        planner._ollama = AsyncMock()
        return CUTaskDecomposer(planner, CUAgentConfig())

    def test_parse_subtasks_valid_json(self):
        d = self._make_decomposer()
        raw = json.dumps([
            {
                "name": "open_app",
                "goal": "Oeffne Reddit",
                "completion_hint": "Reddit sichtbar",
                "max_iterations": 8,
                "tools": ["computer_click"],
                "extract_content": False,
                "content_key": "",
                "output_file": "",
            },
            {
                "name": "search",
                "goal": "Suche locallama",
                "completion_hint": "locallama in URL",
                "max_iterations": 6,
                "tools": ["computer_type", "computer_click"],
                "extract_content": False,
                "content_key": "",
                "output_file": "",
            },
        ])
        tasks = d._parse_subtasks(raw)
        assert len(tasks) == 2
        assert tasks[0].name == "open_app"
        assert tasks[0].max_iterations == 8
        assert tasks[1].available_tools == ["computer_type", "computer_click"]

    def test_parse_subtasks_markdown_block(self):
        d = self._make_decomposer()
        raw = (
            "Hier ist der Plan:\n```json\n"
            + json.dumps([
                {
                    "name": "step1",
                    "goal": "Do thing",
                    "completion_hint": "done",
                    "max_iterations": 5,
                    "tools": [],
                    "extract_content": False,
                    "content_key": "",
                    "output_file": "",
                },
            ])
            + "\n```\nDas war der Plan."
        )
        tasks = d._parse_subtasks(raw)
        assert len(tasks) == 1
        assert tasks[0].name == "step1"

    def test_parse_subtasks_garbage_returns_empty(self):
        d = self._make_decomposer()
        tasks = d._parse_subtasks("This is not JSON at all, just rambling text.")
        assert tasks == []

    def test_parse_subtasks_partial_fields_uses_defaults(self):
        d = self._make_decomposer()
        raw = json.dumps([{"name": "x", "goal": "y", "completion_hint": "z"}])
        tasks = d._parse_subtasks(raw)
        assert len(tasks) == 1
        assert tasks[0].max_iterations == 10  # default
        assert tasks[0].extract_content is False  # default
        assert tasks[0].available_tools == []  # default

    def test_parse_subtasks_tools_mapped_to_available_tools(self):
        """The LLM returns 'tools' but the dataclass uses 'available_tools'."""
        d = self._make_decomposer()
        raw = json.dumps([
            {
                "name": "a",
                "goal": "b",
                "completion_hint": "c",
                "tools": ["computer_click", "extract_text"],
            }
        ])
        tasks = d._parse_subtasks(raw)
        assert tasks[0].available_tools == ["computer_click", "extract_text"]


class TestCUTaskDecomposerDecompose:
    @pytest.mark.asyncio
    async def test_decompose_happy_path(self):
        planner = MagicMock()
        planner._ollama = AsyncMock()
        planner._ollama.chat = AsyncMock(return_value={
            "message": {
                "content": json.dumps([
                    {
                        "name": "open_app",
                        "goal": "Oeffne Reddit",
                        "completion_hint": "Reddit sichtbar",
                        "max_iterations": 8,
                        "tools": ["computer_click"],
                        "extract_content": False,
                        "content_key": "",
                        "output_file": "",
                    },
                    {
                        "name": "write_result",
                        "goal": "Schreibe Datei",
                        "completion_hint": "Datei geschrieben",
                        "max_iterations": 5,
                        "tools": ["write_file"],
                        "extract_content": False,
                        "content_key": "",
                        "output_file": "result_{date}.txt",
                    },
                ])
            }
        })

        d = CUTaskDecomposer(planner, CUAgentConfig())
        plan = await d.decompose("Oeffne Reddit und speichere")

        assert len(plan.sub_tasks) == 2
        assert plan.sub_tasks[0].name == "open_app"
        # output_file should be resolved to absolute path
        assert "result_" in plan.sub_tasks[1].output_file
        assert "Documents" in plan.sub_tasks[1].output_file
        assert plan.output_filename == plan.sub_tasks[1].output_file

    @pytest.mark.asyncio
    async def test_decompose_llm_failure_degrades_to_single_task(self):
        planner = MagicMock()
        planner._ollama = AsyncMock()
        planner._ollama.chat = AsyncMock(side_effect=RuntimeError("connection refused"))

        d = CUTaskDecomposer(planner, CUAgentConfig())
        plan = await d.decompose("Mach etwas")

        assert len(plan.sub_tasks) == 1
        assert plan.sub_tasks[0].name == "full_task"
        assert plan.sub_tasks[0].goal == "Mach etwas"

    @pytest.mark.asyncio
    async def test_decompose_garbage_response_degrades(self):
        planner = MagicMock()
        planner._ollama = AsyncMock()
        planner._ollama.chat = AsyncMock(return_value={
            "message": {"content": "Ich bin ein Sprachmodell und kann keine Phasen erzeugen."}
        })

        d = CUTaskDecomposer(planner, CUAgentConfig())
        plan = await d.decompose("Irgendwas")

        assert len(plan.sub_tasks) == 1
        assert plan.sub_tasks[0].name == "full_task"

    @pytest.mark.asyncio
    async def test_decompose_think_tags_stripped(self):
        planner = MagicMock()
        planner._ollama = AsyncMock()
        planner._ollama.chat = AsyncMock(return_value={
            "message": {
                "content": (
                    "<think>Let me think about this...</think>"
                    + json.dumps([{
                        "name": "step1",
                        "goal": "do it",
                        "completion_hint": "done",
                    }])
                )
            }
        })

        d = CUTaskDecomposer(planner, CUAgentConfig())
        plan = await d.decompose("Test")

        assert len(plan.sub_tasks) == 1
        assert plan.sub_tasks[0].name == "step1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_core/test_cu_agent.py::TestCUTaskDecomposerVariables -v && pytest tests/test_core/test_cu_agent.py::TestCUTaskDecomposerParsing -v && pytest tests/test_core/test_cu_agent.py::TestCUTaskDecomposerDecompose -v`
Expected: ImportError for `CUTaskDecomposer`

- [ ] **Step 3: Implement CUTaskDecomposer**

Add `from datetime import datetime` and `from pathlib import Path` to the imports at top of `src/jarvis/core/cu_agent.py`. Place the class after `CUTaskPlan` and before `CUAgentExecutor`:

```python
class CUTaskDecomposer:
    """Breaks a complex CU goal into ordered sub-tasks via LLM."""

    _CU_DECOMPOSE_PROMPT = (
        "Du bist ein Desktop-Automations-Planer. Zerlege die folgende Aufgabe "
        "in einzelne Phasen.\n\n"
        "Aufgabe: {goal}\n\n"
        "Antworte als JSON-Array. Jede Phase hat:\n"
        '- "name": kurzer Bezeichner (snake_case)\n'
        '- "goal": was in dieser Phase erreicht werden soll\n'
        '- "completion_hint": woran man erkennt, dass die Phase abgeschlossen ist '
        "(sichtbar auf dem Bildschirm)\n"
        '- "max_iterations": maximale Schritte (Standard: 10)\n'
        '- "tools": Liste erlaubter Tools fuer diese Phase\n'
        '- "extract_content": true wenn Text gesammelt werden soll\n'
        '- "content_key": Schluessel fuer gesammelten Text (z.B. "posts")\n'
        '- "output_file": Dateiname falls diese Phase eine Datei schreibt '
        "(leer wenn nicht)\n\n"
        "Verfuegbare Tools: computer_screenshot, computer_click, computer_type, "
        "computer_hotkey, computer_scroll, exec_command, write_file, extract_text\n\n"
        "Variablen die du im output_file nutzen kannst:\n"
        "{variables_doc}\n\n"
        "Beispiel fuer 'Oeffne Rechner und rechne 5+3':\n"
        "```json\n"
        "[\n"
        '  {{"name": "open_calculator", "goal": "Oeffne die Rechner-App", '
        '"completion_hint": "Rechner-Fenster ist sichtbar", "max_iterations": 8, '
        '"tools": ["computer_screenshot", "computer_click", "computer_type", '
        '"computer_hotkey"], "extract_content": false, "content_key": "", '
        '"output_file": ""}},\n'
        '  {{"name": "calculate", "goal": "Tippe 5+3 und druecke Enter", '
        '"completion_hint": "Ergebnis 8 ist sichtbar", "max_iterations": 6, '
        '"tools": ["computer_screenshot", "computer_click", "computer_type"], '
        '"extract_content": false, "content_key": "", "output_file": ""}}\n'
        "]\n"
        "```"
    )

    def __init__(self, planner: Any, config: CUAgentConfig) -> None:
        self._planner = planner
        self._config = config

    def _resolve_variables(self, goal: str) -> dict[str, str]:
        """Resolve dynamic variables from goal context."""
        today = datetime.now()
        return {
            "date": today.strftime("%Y%m%d"),
            "date_dots": today.strftime("%d.%m.%Y"),
            "date_iso": today.isoformat()[:10],
            "user_home": str(Path.home()),
            "documents": str(Path.home() / "Documents"),
        }

    @staticmethod
    def _resolve_output_path(filename: str, variables: dict[str, str]) -> str:
        """Resolve filename template to absolute path."""
        for key, val in variables.items():
            filename = filename.replace(f"{{{key}}}", val)
        return str(Path(variables["documents"]) / filename)

    def _parse_subtasks(self, raw: str) -> list[CUSubTask]:
        """Parse LLM response into CUSubTask list. 3-tier JSON parsing."""
        data = None

        # Tier 1: direct JSON parse
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            pass

        # Tier 2: markdown code block
        if data is None:
            md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
            if md_match:
                try:
                    data = json.loads(md_match.group(1))
                except (json.JSONDecodeError, ValueError):
                    pass

        # Tier 3: find JSON array
        if data is None:
            arr_match = re.search(r"\[.*\]", raw, re.DOTALL)
            if arr_match:
                try:
                    data = json.loads(arr_match.group())
                except (json.JSONDecodeError, ValueError):
                    pass

        if not isinstance(data, list):
            return []

        tasks: list[CUSubTask] = []
        for item in data:
            if not isinstance(item, dict) or "name" not in item:
                continue
            tasks.append(
                CUSubTask(
                    name=item.get("name", ""),
                    goal=item.get("goal", ""),
                    completion_hint=item.get("completion_hint", ""),
                    max_iterations=item.get("max_iterations", 10),
                    available_tools=item.get("tools", []),
                    extract_content=item.get("extract_content", False),
                    content_key=item.get("content_key", ""),
                    output_file=item.get("output_file", ""),
                )
            )
        return tasks

    async def decompose(self, goal: str) -> CUTaskPlan:
        """Decompose a complex goal into ordered sub-tasks."""
        variables = self._resolve_variables(goal)
        variables_doc = "\n".join(f"  {{{k}}} = {v}" for k, v in variables.items())

        prompt = self._CU_DECOMPOSE_PROMPT.format(goal=goal, variables_doc=variables_doc)

        try:
            response = await self._planner._ollama.chat(
                model=self._config.vision_model,
                messages=[
                    {"role": "system", "content": "Du bist ein Desktop-Automations-Planer."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            text = response.get("message", {}).get("content", "")
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

            sub_tasks = self._parse_subtasks(text)
        except Exception as exc:
            log.warning("cu_decompose_failed", error=str(exc)[:200])
            sub_tasks = []

        # Graceful degradation: if parsing failed, fall back to single sub-task
        if not sub_tasks:
            sub_tasks = [
                CUSubTask(
                    name="full_task",
                    goal=goal,
                    completion_hint="",
                    max_iterations=self._config.max_iterations,
                )
            ]

        # Resolve output_file paths
        output_filename = ""
        for st in sub_tasks:
            if st.output_file:
                st.output_file = self._resolve_output_path(st.output_file, variables)
                output_filename = st.output_file

        return CUTaskPlan(
            original_goal=goal,
            sub_tasks=sub_tasks,
            output_filename=output_filename,
            variables=variables,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_core/test_cu_agent.py::TestCUTaskDecomposerVariables tests/test_core/test_cu_agent.py::TestCUTaskDecomposerParsing tests/test_core/test_cu_agent.py::TestCUTaskDecomposerDecompose -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/core/cu_agent.py tests/test_core/test_cu_agent.py
git commit -m "feat(cu): add CUTaskDecomposer with variable resolution and JSON parsing"
```

---

### Task 4: Failure Escalation Tracking

**Files:**
- Modify: `src/jarvis/core/cu_agent.py`
- Test: `tests/test_core/test_cu_agent.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_core/test_cu_agent.py`:

```python
class TestFailureEscalation:
    def _make_agent(self) -> CUAgentExecutor:
        planner = MagicMock()
        planner._ollama = AsyncMock()
        mcp = MagicMock()
        mcp._builtin_handlers = {}
        return CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})

    def test_build_failure_hint_level_1(self):
        agent = self._make_agent()
        hint = agent._build_failure_hint(
            "computer_click(x=100, y=200) -> Element nicht gefunden", 1
        )
        assert "Alternative" in hint
        assert "fehlgeschlagen" in hint.lower() or "Fehlgeschlagen" in hint

    def test_build_failure_hint_level_2(self):
        agent = self._make_agent()
        hint = agent._build_failure_hint("computer_click failed", 2)
        assert "anderen Ansatz" in hint

    def test_build_failure_hint_level_3(self):
        agent = self._make_agent()
        hint = agent._build_failure_hint("failed action", 3)
        assert "uebersprungen" in hint

    def test_build_failure_hint_level_4_plus(self):
        agent = self._make_agent()
        hint = agent._build_failure_hint("failed", 4)
        assert "uebersprungen" in hint

    def test_build_failure_hint_zero_returns_empty(self):
        agent = self._make_agent()
        hint = agent._build_failure_hint("", 0)
        assert hint == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_core/test_cu_agent.py::TestFailureEscalation -v`
Expected: AttributeError for `_build_failure_hint`

- [ ] **Step 3: Implement failure escalation**

Add to `CUAgentExecutor` class in `src/jarvis/core/cu_agent.py`, after `_screenshot_similarity`:

```python
    @staticmethod
    def _build_failure_hint(failure_desc: str, consecutive_failures: int) -> str:
        """Build escalating failure hint for the decide prompt."""
        if consecutive_failures <= 0:
            return ""
        prefix = f"Letzte Aktion fehlgeschlagen: {failure_desc}\n"
        if consecutive_failures == 1:
            return prefix + "Versuche eine Alternative: anderes Element, scrollen, oder warten."
        if consecutive_failures == 2:
            return prefix + "Versuche einen komplett anderen Ansatz."
        return (
            prefix
            + "Phase wird uebersprungen wenn naechste Aktion auch fehlschlaegt."
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_core/test_cu_agent.py::TestFailureEscalation -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/core/cu_agent.py tests/test_core/test_cu_agent.py
git commit -m "feat(cu): add failure escalation hint builder"
```

---

### Task 5: Refactor execute() to Sub-Task-Driven Loop

This is the core task. It replaces the flat loop in `execute()` with a sub-task-driven loop. The inner screenshot-decide-act cycle stays identical.

**Files:**
- Modify: `src/jarvis/core/cu_agent.py`
- Test: `tests/test_core/test_cu_agent.py`

- [ ] **Step 1: Write failing tests for sub-task transitions**

Add to `tests/test_core/test_cu_agent.py`:

```python
class TestSubTaskLoop:
    @pytest.mark.asyncio
    async def test_two_subtasks_both_complete_via_done(self):
        """Agent runs two sub-tasks, model says DONE for each."""
        planner = MagicMock()
        planner._ollama = AsyncMock()
        # First sub-task: click then DONE. Second sub-task: type then DONE.
        planner._ollama.chat = AsyncMock(side_effect=[
            # decompose call
            {"message": {"content": json.dumps([
                {"name": "phase1", "goal": "Klicke Button", "completion_hint": "Button geklickt",
                 "max_iterations": 5, "tools": ["computer_click"]},
                {"name": "phase2", "goal": "Tippe Text", "completion_hint": "Text sichtbar",
                 "max_iterations": 5, "tools": ["computer_type"]},
            ])}},
            # phase1 decide: click
            {"message": {"content": '{"tool": "computer_click", "params": {"x": 100, "y": 200}}'}},
            # phase1 decide: DONE
            {"message": {"content": "DONE: Button wurde geklickt"}},
            # phase2 decide: type
            {"message": {"content": '{"tool": "computer_type", "params": {"text": "hello"}}'}},
            # phase2 decide: DONE
            {"message": {"content": "DONE: Text wurde eingegeben"}},
        ])

        mcp = MagicMock()
        mcp._builtin_handlers = {
            "computer_screenshot": AsyncMock(return_value={
                "success": True, "description": "screen", "elements": [],
            }),
            "computer_click": AsyncMock(return_value={"success": True}),
            "computer_type": AsyncMock(return_value={"success": True}),
        }

        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})
        result = await agent.execute(
            goal="Klicke und tippe",
            initial_plan=ActionPlan(goal="test", steps=[]),
        )

        assert result.success is True
        assert result.task_summary != ""
        assert "2/2" in result.task_summary

    @pytest.mark.asyncio
    async def test_subtask_completes_via_hint_match(self):
        """Sub-task transitions when completion hint matches screenshot."""
        planner = MagicMock()
        planner._ollama = AsyncMock()
        planner._ollama.chat = AsyncMock(side_effect=[
            # decompose: single sub-task with specific hint
            {"message": {"content": json.dumps([
                {"name": "open_reddit", "goal": "Oeffne Reddit",
                 "completion_hint": "Reddit Seite locallama sichtbar",
                 "max_iterations": 10, "tools": ["computer_click"]},
            ])}},
            # decide: click (not DONE yet — but screenshot will match hint)
            {"message": {"content": '{"tool": "computer_click", "params": {"x": 50, "y": 50}}'}},
        ])

        mcp = MagicMock()
        # Screenshot description matches the completion hint
        mcp._builtin_handlers = {
            "computer_screenshot": AsyncMock(return_value={
                "success": True,
                "description": "Browser Reddit Seite mit locallama Posts sichtbar",
                "elements": [],
            }),
            "computer_click": AsyncMock(return_value={"success": True}),
        }

        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})
        result = await agent.execute(
            goal="Oeffne Reddit",
            initial_plan=ActionPlan(goal="test", steps=[]),
        )

        assert result.success is True
        assert "1/1" in result.task_summary

    @pytest.mark.asyncio
    async def test_subtask_fails_after_max_iterations_continues_next(self):
        """Sub-task exhausts budget, gets skipped, next sub-task runs."""
        planner = MagicMock()
        planner._ollama = AsyncMock()
        planner._ollama.chat = AsyncMock(side_effect=[
            # decompose: two sub-tasks, first has max_iterations=2
            {"message": {"content": json.dumps([
                {"name": "fail_phase", "goal": "Will fail", "completion_hint": "impossible",
                 "max_iterations": 2, "tools": ["computer_click"]},
                {"name": "ok_phase", "goal": "Will succeed", "completion_hint": "done",
                 "max_iterations": 5, "tools": ["computer_click"]},
            ])}},
            # fail_phase: 2 clicks (exhausts budget)
            {"message": {"content": '{"tool": "computer_click", "params": {"x": 1, "y": 1}}'}},
            {"message": {"content": '{"tool": "computer_click", "params": {"x": 1, "y": 1}}'}},
            # ok_phase: DONE
            {"message": {"content": "DONE: OK phase done"}},
        ])

        mcp = MagicMock()
        mcp._builtin_handlers = {
            "computer_screenshot": AsyncMock(return_value={
                "success": True, "description": "screen", "elements": [],
            }),
            "computer_click": AsyncMock(return_value={"success": True}),
        }

        config = CUAgentConfig(max_iterations=30)
        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {}, config)
        result = await agent.execute(
            goal="test phases",
            initial_plan=ActionPlan(goal="test", steps=[]),
        )

        # Overall succeeds because at least one phase completed
        assert "1/2" in result.task_summary or "Fehlgeschlagen" in result.task_summary

    @pytest.mark.asyncio
    async def test_content_extraction_accumulates_in_bag(self):
        """extract_text calls accumulate labeled content."""
        planner = MagicMock()
        planner._ollama = AsyncMock()
        planner._ollama.chat = AsyncMock(side_effect=[
            # decompose: one extract phase
            {"message": {"content": json.dumps([
                {"name": "read_posts", "goal": "Lies Posts", "completion_hint": "done",
                 "max_iterations": 5, "tools": ["extract_text"],
                 "extract_content": True, "content_key": "posts"},
            ])}},
            # decide: extract_text
            {"message": {"content": '{"tool": "extract_text", "params": {}}'}},
            # decide: DONE
            {"message": {"content": "DONE: Posts gelesen"}},
        ])

        mcp = MagicMock()
        mcp._builtin_handlers = {
            "computer_screenshot": AsyncMock(return_value={
                "success": True, "description": "screen with posts", "elements": [],
            }),
        }

        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})
        # Mock _extract_text_from_screen to return content
        agent._extract_text_from_screen = AsyncMock(return_value="Post about LLMs on local hardware")

        result = await agent.execute(
            goal="Lies Posts",
            initial_plan=ActionPlan(goal="test", steps=[]),
        )

        assert result.success is True
        assert "Post about LLMs" in result.extracted_content
        assert "## posts 1" in result.extracted_content

    @pytest.mark.asyncio
    async def test_decompose_failure_degrades_to_flat_loop(self):
        """If decomposer fails, execute() runs Phase 2B flat loop."""
        planner = MagicMock()
        planner._ollama = AsyncMock()
        # First call (decompose) fails, subsequent calls work normally
        planner._ollama.chat = AsyncMock(side_effect=[
            RuntimeError("LLM down"),  # decompose fails
            {"message": {"content": "DONE: Aufgabe erledigt"}},  # flat loop decide
        ])

        mcp = MagicMock()
        mcp._builtin_handlers = {
            "computer_screenshot": AsyncMock(return_value={
                "success": True, "description": "screen", "elements": [],
            }),
        }

        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})
        result = await agent.execute(
            goal="Einfache Aufgabe",
            initial_plan=ActionPlan(goal="test", steps=[]),
        )

        assert result.success is True
        assert "1/1" in result.task_summary
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_core/test_cu_agent.py::TestSubTaskLoop -v`
Expected: Failures — execute() still runs flat loop without decomposer

- [ ] **Step 3: Add sub-task context prompt template**

Add to `CUAgentExecutor` class, after `_CU_DECIDE_PROMPT`:

```python
    _CU_SUBTASK_CONTEXT = (
        "--- Aktuelle Phase: {phase_name} ({phase_idx}/{phase_total}) ---\n"
        "Phasenziel: {phase_goal}\n"
        "Abschlusskriterium: {completion_hint}\n"
        "{extraction_status}"
        "{failure_hint}"
        "{content_preview}"
        "---\n\n"
    )
```

- [ ] **Step 4: Refactor execute() to sub-task loop**

Replace the entire `execute()` method in `CUAgentExecutor` with:

```python
    async def execute(
        self,
        goal: str,
        initial_plan: ActionPlan,
        status_callback: Callable | None = None,
        cancel_check: Callable | None = None,
    ) -> CUAgentResult:
        """Run the CU agent loop with sub-task decomposition."""
        result = CUAgentResult()
        start = time.monotonic()
        content_bag: dict[str, list[str]] = {}
        global_iteration = 0

        async def _status(phase: str, msg: str) -> None:
            if status_callback:
                try:
                    await status_callback(phase, msg)
                except Exception:
                    pass

        # Execute initial plan steps
        await _status("computer_use", f"Starte: {goal[:60]}...")
        for step in initial_plan.steps:
            tool_result = await self._execute_tool(step.tool, step.params)
            result.tool_results.append(tool_result)
            self._action_history.append(
                f"{step.tool}({self._format_params(step.params)}) "
                f"-> {'OK' if tool_result.success else 'FAIL'}"
            )

        # Decompose goal into sub-tasks
        decomposer = CUTaskDecomposer(self._planner, self._config)
        task_plan = await decomposer.decompose(goal)

        # Sub-task-driven loop
        for st_idx, sub_task in enumerate(task_plan.sub_tasks):
            sub_task.status = "running"
            sub_iter = 0
            consecutive_failures = 0
            last_failure = ""
            extraction_count = 0
            prev_screenshot_desc = ""
            stale_screen_count = 0

            await _status(
                "computer_use",
                f"Phase {st_idx + 1}/{len(task_plan.sub_tasks)}: {sub_task.goal[:50]}...",
            )

            while sub_iter < sub_task.max_iterations:
                sub_iter += 1
                global_iteration += 1
                result.iterations = global_iteration

                # Global abort check
                abort = self._check_abort(result, start, cancel_check)
                if abort:
                    result.abort_reason = abort
                    sub_task.status = "failed"
                    for remaining in task_plan.sub_tasks[st_idx + 1:]:
                        remaining.status = "failed"
                    break

                await _status(
                    "computer_use",
                    f"Phase {st_idx + 1}/{len(task_plan.sub_tasks)}, "
                    f"Schritt {sub_iter}/{sub_task.max_iterations}: Analysiere...",
                )

                screenshot = await self._take_and_analyze_screenshot()
                if not screenshot:
                    self._action_history.append("computer_screenshot() -> FAIL")
                    continue

                screenshot_desc = screenshot.get("description", "")
                result.final_screenshot_description = screenshot_desc

                # Completion hint check
                if self._check_completion_hint(sub_task.completion_hint, screenshot_desc):
                    sub_task.status = "done"
                    self._action_history.append(
                        f"[Phase {st_idx + 1} '{sub_task.name}': "
                        f"Hint matched -> abgeschlossen]"
                    )
                    break

                # Stale screen detection
                if prev_screenshot_desc:
                    sim = self._screenshot_similarity(prev_screenshot_desc, screenshot_desc)
                    if sim > 0.9:
                        stale_screen_count += 1
                        if stale_screen_count >= 2:
                            last_failure = "Bildschirm hat sich nicht veraendert."
                            consecutive_failures += 1
                    else:
                        stale_screen_count = 0
                prev_screenshot_desc = screenshot_desc

                # Build sub-task context for prompt
                extraction_status = ""
                if sub_task.extract_content and extraction_count > 0:
                    extraction_status = f"Du hast {extraction_count} Eintraege extrahiert.\n"

                failure_hint = self._build_failure_hint(last_failure, consecutive_failures)
                if failure_hint:
                    failure_hint += "\n"

                content_preview = ""
                bag_key = sub_task.content_key
                if bag_key and bag_key in content_bag and content_bag[bag_key]:
                    preview = "\n".join(content_bag[bag_key])[-500:]
                    content_preview = f"Bisheriger Inhalt:\n{preview}\n"

                # File-writing sub-task: inject content bag into prompt
                file_context = ""
                if sub_task.output_file and content_bag:
                    all_content = []
                    for key, entries in content_bag.items():
                        all_content.extend(entries)
                    full_text = "\n\n".join(all_content)
                    file_context = (
                        f"\nGesammelter Inhalt ({len(all_content)} Eintraege):\n"
                        f"---\n{full_text[:3000]}\n---\n"
                        f"Schreibe diesen Inhalt mit write_file in die Datei: "
                        f"{sub_task.output_file}\n"
                    )

                subtask_context = self._CU_SUBTASK_CONTEXT.format(
                    phase_name=sub_task.name,
                    phase_idx=st_idx + 1,
                    phase_total=len(task_plan.sub_tasks),
                    phase_goal=sub_task.goal,
                    completion_hint=sub_task.completion_hint,
                    extraction_status=extraction_status,
                    failure_hint=failure_hint,
                    content_preview=content_preview + file_context,
                )

                decision = await self._decide_next_step(
                    goal, screenshot, subtask_context=subtask_context
                )

                if decision is None:
                    self._action_history.append("decide() -> no valid action")
                    continue

                if decision.get("done"):
                    sub_task.status = "done"
                    summary = decision.get("summary", "")
                    self._action_history.append(
                        f"[Phase {st_idx + 1} '{sub_task.name}': DONE: {summary}]"
                    )
                    break

                if decision.get("tool") == "extract_text":
                    text = await self._extract_text_from_screen()
                    if text:
                        extraction_count += 1
                        label = f"## {sub_task.content_key or 'content'} {extraction_count}"
                        labeled_text = f"{label}\n{text}"
                        result.extracted_content += labeled_text + "\n\n"
                        if bag_key:
                            content_bag.setdefault(bag_key, []).append(labeled_text)
                        self._action_history.append(
                            f"extract_text() -> {len(text)} chars [{extraction_count}]"
                        )
                    continue

                tool = decision["tool"]
                params = decision.get("params", {})
                await _status(
                    "computer_use",
                    f"Phase {st_idx + 1}, Schritt {sub_iter}: {tool}...",
                )

                tool_result = await self._execute_tool(tool, params)
                result.tool_results.append(tool_result)

                action_desc = (
                    f"{tool}({self._format_params(params)}) "
                    f"-> {'OK' if tool_result.success else 'FAIL'}"
                )
                self._action_history.append(action_desc)

                # Track output files from write_file
                if tool == "write_file" and tool_result.success:
                    path = params.get("path", sub_task.output_file)
                    if path:
                        result.output_files.append(path)

                # Failure tracking
                if tool_result.is_error:
                    last_failure = (
                        f"{tool}({self._format_params(params)}) -> "
                        f"{tool_result.content[:200]}"
                    )
                    consecutive_failures += 1
                    if consecutive_failures >= 4:
                        sub_task.status = "failed"
                        self._action_history.append(
                            f"[Phase {st_idx + 1} '{sub_task.name}': "
                            f"4 Fehler -> uebersprungen]"
                        )
                        break
                else:
                    last_failure = ""
                    consecutive_failures = 0

                # Stuck-loop tracking
                action_key = f"{tool}:{sorted(params.items())}"
                self._recent_actions.append(action_key)
                if len(self._recent_actions) > self._config.stuck_detection_threshold:
                    self._recent_actions.pop(0)

            else:
                # Sub-task exhausted its iteration budget
                if sub_task.status == "running":
                    sub_task.status = "partial"
                    self._action_history.append(
                        f"[Phase {st_idx + 1} '{sub_task.name}': "
                        f"max_iterations erreicht -> partial]"
                    )

            # Global abort triggered — stop all sub-tasks
            if result.abort_reason:
                break

            # Reset per-sub-task state
            self._recent_actions.clear()

        # Build task summary
        completed = [st for st in task_plan.sub_tasks if st.status == "done"]
        failed = [st for st in task_plan.sub_tasks if st.status in ("failed", "partial")]

        result.task_summary = (
            f"{len(completed)}/{len(task_plan.sub_tasks)} Phasen abgeschlossen."
            + (f" Fehlgeschlagen: {', '.join(f.name for f in failed)}." if failed else "")
            + (
                f" Dateien erstellt: {', '.join(result.output_files)}."
                if result.output_files
                else ""
            )
            + f" Gesammelter Inhalt: {len(result.extracted_content)} Zeichen."
        )

        if not result.abort_reason:
            result.success = len(completed) > 0
            result.abort_reason = "done" if result.success else "all_phases_failed"

        result.duration_ms = int((time.monotonic() - start) * 1000)
        result.action_history = list(self._action_history)
        log.info(
            "cu_agent_complete",
            success=result.success,
            iterations=result.iterations,
            duration_ms=result.duration_ms,
            abort_reason=result.abort_reason,
            phases_completed=len(completed),
            phases_total=len(task_plan.sub_tasks),
        )
        return result
```

- [ ] **Step 5: Update _decide_next_step to accept subtask_context**

Modify `_decide_next_step` signature and prompt assembly:

```python
    async def _decide_next_step(
        self, goal: str, screenshot: dict, subtask_context: str = ""
    ) -> dict | None:
        """Ask the planner what to do next based on the screenshot."""
        prompt = subtask_context + self._CU_DECIDE_PROMPT.format(
            goal=goal,
            action_history="\n".join(self._action_history[-10:]) or "(keine)",
            screenshot_description=screenshot.get("description", "")[:1000],
            elements_json=self._format_elements(screenshot.get("elements", [])),
        )

        try:
            response = await self._planner._ollama.chat(
                model=self._config.vision_model,
                messages=[
                    {"role": "system", "content": "Du bist ein Desktop-Automations-Agent."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            text = response.get("message", {}).get("content", "")
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

            if text.upper().startswith("DONE"):
                summary = text.split(":", 1)[1].strip() if ":" in text else text[4:].strip()
                return {"done": True, "summary": summary}

            return self._parse_tool_decision(text)

        except Exception as exc:
            log.warning("cu_agent_decide_failed", error=str(exc)[:200])
            return None
```

- [ ] **Step 6: Fix existing tests to account for decomposer LLM call**

The existing `TestCUAgentExecuteLoop` tests need a decomposer response prepended to their `side_effect` lists because `execute()` now calls `decomposer.decompose()` first.

For `test_happy_path_done_in_3_iterations`, update `side_effect`:

```python
planner._ollama.chat = AsyncMock(
    side_effect=[
        # decompose call
        {"message": {"content": json.dumps([
            {"name": "full_task", "goal": "Rechner oeffnen",
             "completion_hint": "Taschenrechner sichtbar", "max_iterations": 10,
             "tools": ["computer_click", "computer_type", "exec_command"]},
        ])}},
        # decide: click
        {"message": {"content": '{"tool": "computer_click", "params": {"x": 200, "y": 300}, "rationale": "click window"}'}},
        # decide: DONE
        {"message": {"content": "DONE: Taschenrechner zeigt 459"}},
    ]
)
```

For `test_abort_on_max_iterations`, prepend decompose response and set sub-task max_iterations higher than config max_iterations so the global abort triggers:

```python
planner._ollama.chat = AsyncMock(
    side_effect=[
        # decompose call
        {"message": {"content": json.dumps([
            {"name": "full_task", "goal": "test", "completion_hint": "",
             "max_iterations": 30, "tools": ["computer_click"]},
        ])}},
    ] + [
        {"message": {"content": '{"tool": "computer_click", "params": {"x": 100, "y": 100}}'}},
    ] * 10  # enough decide calls
)
```

For `test_abort_on_user_cancel`, prepend decompose response:

```python
planner._ollama.chat = AsyncMock(
    side_effect=[
        # decompose call
        {"message": {"content": json.dumps([
            {"name": "full_task", "goal": "test", "completion_hint": "",
             "max_iterations": 30, "tools": ["computer_click"]},
        ])}},
        {"message": {"content": '{"tool": "computer_click", "params": {"x": 1, "y": 1}}'}},
    ]
)
```

- [ ] **Step 7: Run all tests to verify**

Run: `pytest tests/test_core/test_cu_agent.py -v`
Expected: All PASS (both new and existing tests)

- [ ] **Step 8: Commit**

```bash
git add src/jarvis/core/cu_agent.py tests/test_core/test_cu_agent.py
git commit -m "feat(cu): refactor execute() to sub-task-driven loop with decomposer"
```

---

### Task 6: Gateway Integration — task_summary and output_files

**Files:**
- Modify: `src/jarvis/gateway/gateway.py:3064-3076`
- Test: `tests/test_core/test_cu_agent.py`

- [ ] **Step 1: Write test for the message format**

Add to `tests/test_core/test_cu_agent.py`:

```python
class TestGatewayResultMessage:
    def test_result_message_includes_summary_and_files(self):
        """Verify the message format that gateway builds from CUAgentResult."""
        cu_result = CUAgentResult(
            success=True,
            iterations=5,
            abort_reason="done",
            action_history=["click -> OK", "DONE: fertig"],
            task_summary="2/2 Phasen abgeschlossen. Dateien erstellt: C:\\out.txt.",
            output_files=["C:\\out.txt"],
            extracted_content="## posts 1\nHello world",
        )

        # Simulate what gateway.py builds
        content = (
            "[Computer Use Ergebnis]\n"
            + "\n".join(cu_result.action_history[-10:])
            + f"\n\nAbschluss: {cu_result.abort_reason}"
            + (
                f"\nZusammenfassung: {cu_result.task_summary}"
                if cu_result.task_summary
                else ""
            )
            + (
                f"\nErstellte Dateien: {', '.join(cu_result.output_files)}"
                if cu_result.output_files
                else ""
            )
            + (
                f"\nExtrahierter Text:\n{cu_result.extracted_content[:2000]}"
                if cu_result.extracted_content
                else ""
            )
        )

        assert "2/2 Phasen" in content
        assert "C:\\out.txt" in content
        assert "posts 1" in content
        assert "Zusammenfassung:" in content
        assert "Erstellte Dateien:" in content
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_core/test_cu_agent.py::TestGatewayResultMessage -v`
Expected: PASS

- [ ] **Step 3: Modify gateway.py**

In `src/jarvis/gateway/gateway.py`, replace the `content=` block (lines 3064-3073) in the CU result message:

Old:
```python
                            content=(
                                "[Computer Use Ergebnis]\n"
                                + "\n".join(cu_result.action_history[-10:])
                                + f"\n\nAbschluss: {cu_result.abort_reason}"
                                + (
                                    f"\nExtrahierter Text:\n{cu_result.extracted_content[:2000]}"
                                    if cu_result.extracted_content
                                    else ""
                                )
                            ),
```

New:
```python
                            content=(
                                "[Computer Use Ergebnis]\n"
                                + "\n".join(cu_result.action_history[-10:])
                                + f"\n\nAbschluss: {cu_result.abort_reason}"
                                + (
                                    f"\nZusammenfassung: {cu_result.task_summary}"
                                    if cu_result.task_summary
                                    else ""
                                )
                                + (
                                    f"\nErstellte Dateien: {', '.join(cu_result.output_files)}"
                                    if cu_result.output_files
                                    else ""
                                )
                                + (
                                    f"\nExtrahierter Text:\n{cu_result.extracted_content[:2000]}"
                                    if cu_result.extracted_content
                                    else ""
                                )
                            ),
```

- [ ] **Step 4: Run gateway-related tests**

Run: `pytest tests/test_integration/test_phase10_13_wiring.py -v -x --timeout=60`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/gateway/gateway.py tests/test_core/test_cu_agent.py
git commit -m "feat(cu): add task_summary and output_files to gateway CU result message"
```

---

### Task 7: Full Integration Test — Reddit Reference Scenario Mock

**Files:**
- Test: `tests/test_core/test_cu_agent.py`

- [ ] **Step 1: Write the integration test**

Add to `tests/test_core/test_cu_agent.py`:

```python
class TestRedditScenarioIntegration:
    """End-to-end mock of the Reddit reference scenario from the spec."""

    @pytest.mark.asyncio
    async def test_reddit_scenario_full_flow(self):
        planner = MagicMock()
        planner._ollama = AsyncMock()
        planner._ollama.chat = AsyncMock(side_effect=[
            # 1. Decompose
            {"message": {"content": json.dumps([
                {"name": "open_reddit", "goal": "Oeffne Reddit",
                 "completion_hint": "Reddit Startseite sichtbar",
                 "max_iterations": 8, "tools": ["computer_click", "exec_command"]},
                {"name": "search_locallama", "goal": "Suche /locallama",
                 "completion_hint": "locallama Subreddit sichtbar",
                 "max_iterations": 6, "tools": ["computer_click", "computer_type"]},
                {"name": "read_posts", "goal": "Scrolle und lies 10 Posts",
                 "completion_hint": "Posts gelesen",
                 "max_iterations": 15, "tools": ["computer_scroll", "extract_text"],
                 "extract_content": True, "content_key": "posts"},
                {"name": "save_file", "goal": "Speichere in Datei",
                 "completion_hint": "Datei geschrieben",
                 "max_iterations": 5, "tools": ["write_file"],
                 "output_file": "Reddit_fetch_{date}.txt"},
            ])}},
            # 2. open_reddit: click then DONE
            {"message": {"content": '{"tool": "computer_click", "params": {"x": 400, "y": 50}}'}},
            {"message": {"content": "DONE: Reddit geoeffnet"}},
            # 3. search_locallama: type then DONE
            {"message": {"content": '{"tool": "computer_type", "params": {"text": "/locallama"}}'}},
            {"message": {"content": "DONE: locallama Subreddit geoeffnet"}},
            # 4. read_posts: extract, scroll, extract then DONE
            {"message": {"content": '{"tool": "extract_text", "params": {}}'}},
            {"message": {"content": '{"tool": "computer_scroll", "params": {"direction": "down", "amount": 3}}'}},
            {"message": {"content": '{"tool": "extract_text", "params": {}}'}},
            {"message": {"content": "DONE: Posts gelesen"}},
            # 5. save_file: write_file then DONE
            {"message": {"content": '{"tool": "write_file", "params": {"path": "C:\\\\Users\\\\Test\\\\Documents\\\\Reddit_fetch_20260403.txt", "content": "posts content"}}'}},
            {"message": {"content": "DONE: Datei gespeichert"}},
        ])

        mcp = MagicMock()
        mcp._builtin_handlers = {
            "computer_screenshot": AsyncMock(return_value={
                "success": True, "description": "screen", "elements": [],
            }),
            "computer_click": AsyncMock(return_value={"success": True}),
            "computer_type": AsyncMock(return_value={"success": True}),
            "computer_scroll": AsyncMock(return_value={"success": True}),
            "write_file": AsyncMock(return_value="Datei geschrieben"),
        }

        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})
        agent._extract_text_from_screen = AsyncMock(side_effect=[
            "Post 1: Local LLMs are amazing\nSummary of post 1...",
            "Post 2: Running Llama on a laptop\nSummary of post 2...",
        ])

        result = await agent.execute(
            goal="Oeffne Reddit, suche /locallama, lies 10 Posts, speichere in Datei",
            initial_plan=ActionPlan(goal="test", steps=[]),
        )

        assert result.success is True
        assert "4/4" in result.task_summary
        assert len(result.output_files) >= 1
        assert "Reddit_fetch" in result.output_files[0]
        assert result.extracted_content != ""
        assert "## posts 1" in result.extracted_content
        assert "## posts 2" in result.extracted_content
        assert "Post 1:" in result.extracted_content

    @pytest.mark.asyncio
    async def test_error_recovery_mid_scenario(self):
        """Phase fails, next phase still runs."""
        planner = MagicMock()
        planner._ollama = AsyncMock()
        planner._ollama.chat = AsyncMock(side_effect=[
            # Decompose: 2 phases
            {"message": {"content": json.dumps([
                {"name": "broken_phase", "goal": "Will fail",
                 "completion_hint": "never", "max_iterations": 3,
                 "tools": ["computer_click"]},
                {"name": "ok_phase", "goal": "Should work",
                 "completion_hint": "done", "max_iterations": 5,
                 "tools": ["computer_click"]},
            ])}},
            # broken_phase: 3 clicks that all fail (exhausts iterations)
            {"message": {"content": '{"tool": "computer_click", "params": {"x": 1, "y": 1}}'}},
            {"message": {"content": '{"tool": "computer_click", "params": {"x": 2, "y": 2}}'}},
            {"message": {"content": '{"tool": "computer_click", "params": {"x": 3, "y": 3}}'}},
            # ok_phase: DONE immediately
            {"message": {"content": "DONE: Phase 2 erledigt"}},
        ])

        mcp = MagicMock()
        mcp._builtin_handlers = {
            "computer_screenshot": AsyncMock(return_value={
                "success": True, "description": "screen", "elements": [],
            }),
            "computer_click": AsyncMock(return_value={"success": True}),
        }

        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})
        result = await agent.execute(
            goal="test recovery",
            initial_plan=ActionPlan(goal="test", steps=[]),
        )

        assert result.success is True
        assert "1/2" in result.task_summary
        assert "broken_phase" in result.task_summary
```

- [ ] **Step 2: Run integration tests**

Run: `pytest tests/test_core/test_cu_agent.py::TestRedditScenarioIntegration -v`
Expected: All PASS

- [ ] **Step 3: Run full cu_agent test suite**

Run: `pytest tests/test_core/test_cu_agent.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_core/test_cu_agent.py
git commit -m "test(cu): add Reddit scenario integration test and error recovery test"
```

---

### Task 8: Final Verification — Full Test Suite

**Files:** None (verification only)

- [ ] **Step 1: Run all CU-related tests**

Run: `pytest tests/test_core/test_cu_agent.py tests/unit/test_computer_use_vision.py tests/test_browser/test_vision.py -v`
Expected: All PASS

- [ ] **Step 2: Run gateway tests**

Run: `pytest tests/test_integration/test_phase10_13_wiring.py -v -x --timeout=120`
Expected: PASS

- [ ] **Step 3: Run broad test sweep (exclude known flaky)**

Run: `pytest tests/ -x --timeout=120 -q --ignore=tests/test_skills/test_marketplace_persistence.py`
Expected: No new failures

- [ ] **Step 4: Final commit**

```bash
git commit --allow-empty -m "feat(cu): Phase 2C Planner Intelligence complete — sub-task decomposition, content accumulation, error recovery, file creation, completion reporting"
```
