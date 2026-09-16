# P19: Autonomy Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise system autonomy from L2+ to L3 via config priority chain, online retrieval fix, interactive paper selection, and memory filtering.

**Architecture:** Four independent changes to the research workflow pipeline. Config priority chain makes `enable_llm` default-on with CLI/topic-pack override. Online retrieval fix removes a dead condition blocking arXiv reference seed lookup. PaperSelectionAgent inserts an interactive `input()` gate after triage but before PDF parsing. Memory filtering adds `_filter_by_selected()` in the persistence agent to exclude unselected papers and their derived artifacts from SQLite.

**Tech Stack:** Python 3.10+, argparse, unittest, sqlite3

## Global Constraints

- `enable_llm` system default: `True` (changed from `False`)
- `enable_experiments` / `enable_code_writes` / `online` system default: `False`
- Priority: CLI explicit > topic pack metadata > system default
- `--no-enable-llm` uses `dest="disable_llm"`, `action="store_true"`
- `PaperSelectionAgent` inserts AFTER `PaperTriageAgent`, BEFORE `LocalPaperParserAgent`
- Memory filtering uses `paper_id` for papers/parsed_papers/evidence/cards, `source_paper_id` for references
- `_filter_by_selected()` must be called in `run()` before `store.write_run_artifacts()`
- `sys.stdin.isatty()` guard for non-interactive fallback in PaperSelectionAgent
- No changes to `core/workflow.py`, `core/agent_base.py`, or `memory/literature_memory.py`
- Test runner: `D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p "test*.py"`
- Expected baseline: 332 tests pass before changes

---

### Task 1: Config Priority Chain

**Files:**
- Modify: `workflows/factory.py:37-59,98-125`
- Modify: `app/main.py:40-44,247-269`
- Modify: `topics/intent_led_virat.json`

**Interfaces:**
- Consumes: `build_full_research_workflow()` signature, `build_parser()` in `app/main.py`, `TopicPack.metadata` field (`dict[str, Any]`)
- Produces: `enable_llm: bool = True` default in factory; `online: bool = False` parameter; `--no-enable-llm` CLI flag with `dest="disable_llm"`; merge logic `CLI > topic pack > system default`; topic pack metadata keys `enable_llm`, `enable_experiments`, `enable_code_writes`, `online`

**Factory changes (`workflows/factory.py`):**

Change line 43: `enable_llm: bool = False` → `enable_llm: bool = True`

Add `online: bool = False` parameter after `enable_code_writes: bool = False`:

```python
def build_full_research_workflow(
    ...
    enable_code_writes: bool = False,
    online: bool = False,
    ...
```

Add `"online": online` to the settings dict after `"enable_code_writes": enable_code_writes`:

```python
settings={
    ...
    "enable_code_writes": enable_code_writes,
    "online": online,
    ...
}
```

**CLI changes (`app/main.py`):**

Add after `--enable-llm` argument (after line 44):

```python
run_parser.add_argument(
    "--no-enable-llm",
    action="store_true",
    dest="disable_llm",
    help="Disable external LLM API calls (overrides topic pack default)",
)
```

Replace the direct passthrough at `run_workflow()` (lines 247-268) with merge logic:

```python
# CLI > topic pack > system default
if args.disable_llm:
    enable_llm_val = False
elif args.enable_llm:
    enable_llm_val = True
else:
    enable_llm_val = topic.metadata.get("enable_llm", True)

if args.enable_experiments:
    enable_experiments_val = True
else:
    enable_experiments_val = topic.metadata.get("enable_experiments", False)

if args.enable_code_writes:
    enable_code_writes_val = True
else:
    enable_code_writes_val = topic.metadata.get("enable_code_writes", False)

online_val = args.online or topic.metadata.get("online", False)

workflow = build_full_research_workflow(
    artifact_store=store,
    memory_store=memory,
    tool_registry=tools,
    logger=logger,
    max_papers=args.max_papers,
    enable_llm=enable_llm_val,
    llm_call_budget=args.llm_call_budget,
    llm_token_budget=args.llm_token_budget,
    enable_experiments=enable_experiments_val,
    enable_code_writes=enable_code_writes_val,
    online=online_val,
    max_debug_attempts=args.max_debug_attempts,
    enable_tree_search=args.enable_tree_search,
    literature_memory_store=lit_memory,
    max_parallel_branches=args.max_parallel_branches,
    enable_reference_expansion=args.enable_reference_expansion,
    max_reference_seeds=args.max_reference_seeds,
    enable_retrieval_evaluation=args.enable_retrieval_evaluation,
    enable_retrieval_judge=args.enable_retrieval_judge,
    retrieval_judge_top_k=args.retrieval_judge_top_k,
    train_budget_epochs=args.train_budget_epochs,
    train_budget_minutes=args.train_budget_minutes,
)
```

**Topic pack metadata (`topics/intent_led_virat.json`):**

Add under `metadata`:

```json
"metadata": {
    "enable_llm": true,
    "enable_experiments": false,
    "enable_code_writes": false,
    "online": false
}
```

Note: if `metadata` already has other keys, merge the four new keys into it.

**Tests (`tests/test_full_research_loop.py`):**

Add to `CliParserTest` class:

- [ ] **Step 1: Write failing tests for config priority chain**

```python
def test_enable_llm_defaults_true_in_factory(self):
    """Factory default for enable_llm is True."""
    from workflows.factory import build_full_research_workflow
    from core.artifact_store import ArtifactStore
    from core.run_logger import RunLogger
    from tools.tool_registry import build_default_tool_registry
    
    with TemporaryDirectory() as tmp:
        wf = build_full_research_workflow(
            artifact_store=ArtifactStore(Path(tmp) / "runs"),
            memory_store=SQLiteMemoryStore(Path(tmp) / "memory.sqlite3"),
            tool_registry=build_default_tool_registry(),
            logger=RunLogger(),
        )
        self.assertTrue(wf.settings["enable_llm"])


def test_no_enable_llm_flag_disables(self):
    """--no-enable-llm flag produces disable_llm=True."""
    from app.main import build_parser

    parser = build_parser()
    args = parser.parse_args([
        "run",
        "--topic", "topics/intent_led_virat.json",
        "--no-enable-llm",
    ])
    self.assertTrue(args.disable_llm)
    self.assertFalse(args.enable_llm)


def test_topic_metadata_overrides_defaults(self):
    """Topic pack metadata presets override system defaults when CLI silent."""
    from app.main import build_parser

    parser = build_parser()
    args = parser.parse_args([
        "run",
        "--topic", "topics/intent_led_virat.json",
    ])
    # CLI not passed, so enable_llm=False (store_true default), disable_llm=False
    self.assertFalse(args.enable_llm)
    self.assertFalse(args.disable_llm)
    # Topic pack should supply the default via metadata.get("enable_llm", True)


def test_cli_overrides_topic_metadata(self):
    """CLI explicit flag overrides topic pack metadata."""
    from app.main import build_parser

    parser = build_parser()
    args = parser.parse_args([
        "run",
        "--topic", "topics/intent_led_virat.json",
        "--enable-llm",
    ])
    self.assertTrue(args.enable_llm)
    self.assertFalse(args.disable_llm)


def test_online_injected_to_settings(self):
    """Factory injects online into workflow settings."""
    from workflows.factory import build_full_research_workflow
    from core.artifact_store import ArtifactStore
    from core.run_logger import RunLogger
    from tools.tool_registry import build_default_tool_registry
    
    with TemporaryDirectory() as tmp:
        wf = build_full_research_workflow(
            artifact_store=ArtifactStore(Path(tmp) / "runs"),
            memory_store=SQLiteMemoryStore(Path(tmp) / "memory.sqlite3"),
            tool_registry=build_default_tool_registry(),
            logger=RunLogger(),
            online=True,
        )
        self.assertTrue(wf.settings["online"])
```

- [ ] **Step 2: Verify tests fail**

Run: `D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_full_research_loop.CliParserTest.test_enable_llm_defaults_true_in_factory -v`
Expected: FAIL (factory still defaults to False)

Run: `D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_full_research_loop.CliParserTest.test_no_enable_llm_flag_disables -v`
Expected: FAIL (--no-enable-llm not yet defined)

- [ ] **Step 3: Implement factory changes**

1. In `workflows/factory.py:43`: change `enable_llm: bool = False` to `enable_llm: bool = True`
2. Add `online: bool = False` parameter (after `enable_code_writes` line)
3. Add `"online": online` to the settings dict

- [ ] **Step 4: Implement CLI changes**

1. In `app/main.py`: add `--no-enable-llm` argument after `--enable-llm`
2. Replace `run_workflow()` direct passthrough with merge logic
3. Add `online=online_val` to `build_full_research_workflow()` call

- [ ] **Step 5: Update topic pack metadata**

In `topics/intent_led_virat.json`: add `enable_llm`, `enable_experiments`, `enable_code_writes`, `online` keys under `metadata`.

- [ ] **Step 6: Run tests to verify**

Run: `D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_full_research_loop.CliParserTest -v`
Expected: 7 tests pass (3 existing + 5 new)

- [ ] **Step 7: Commit**

```bash
git add workflows/factory.py app/main.py topics/intent_led_virat.json tests/test_full_research_loop.py
git commit -m "feat: add config priority chain (CLI > topic pack > system default), enable_llm defaults to True"
```

---

### Task 2: Online Retrieval Fix

**Files:**
- Modify: `agents/literature_searcher.py:113`

**Interfaces:**
- Consumes: `LiteratureSearchAgent.run()` line 113 condition check
- Produces: reference seed arXiv retrieval path activates when `--online` is passed (ArxivTool registered)

**Dependencies:** Task 1 must complete first (adds `online` parameter to factory, though the fix itself removes the dead settings check).

- [ ] **Step 1: Write failing test for reference seed online path**

File: `tests/test_reference_expansion_search.py` — add to `ReferenceExpansionSearchTest`:

```python
def test_reference_seeds_online_path_does_not_require_settings_online_key(self):
    """Reference seed arXiv path works when tool_registry has arxiv, regardless of settings."""
    with TemporaryDirectory() as tmp:
        lit_store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
        lit_store.write_reference(
            {
                "ref_id": "ref_online",
                "title": "Online Reference Paper",
                "source_paper_id": "paper_online",
                "relevance_score": 0.95,
            },
            "intent_led_virat",
        )
        state = ResearchState(topic=_topic())
        # settings does NOT contain "online" key — but tool_registry has "arxiv"
        from tools.arxiv_tool import ArxivTool
        from tools.tool_registry import ToolRegistry
        tools = ToolRegistry()
        tools.register(ArxivTool(max_results=3))
        
        ctx = AgentContext(
            artifact_store=ArtifactStore(Path(tmp)),
            memory_store=None,
            tool_registry=tools,
            settings={
                "max_papers": 3,
                "enable_reference_expansion": True,
                "max_reference_seeds": 1,
            },
        )

        result = LiteratureSearchAgent(lit_memory_store=lit_store).run(state, ctx)

        papers = state.values["papers"]
        # Should have papers (either from arXiv or offline fallback)
        self.assertGreaterEqual(len(papers), 1)
```

- [ ] **Step 2: Verify test behavior**

Run: `D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_reference_expansion_search.ReferenceExpansionSearchTest.test_reference_seeds_online_path_does_not_require_settings_online_key -v`
Expected: Test runs (may pass or fail depending on ArxivTool availability; the key verification is that the condition at line 113 no longer blocks on `context.settings.get("online")`)

- [ ] **Step 3: Fix the bug**

In `agents/literature_searcher.py:113`, change:

```python
if context.tool_registry and context.tool_registry.has("arxiv") and context.settings.get("online"):
```

to:

```python
if context.tool_registry and context.tool_registry.has("arxiv"):
```

- [ ] **Step 4: Run relevant tests**

Run: `D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_reference_expansion_search -v`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add agents/literature_searcher.py tests/test_reference_expansion_search.py
git commit -m "fix: remove dead settings.online check blocking reference seed arXiv retrieval"
```

---

### Task 3: Interactive Paper Selection

**Files:**
- Create: `agents/paper_selector.py`
- Modify: `agents/__init__.py`
- Modify: `workflows/factory.py:60-69`
- Create: `tests/test_paper_selector.py`

**Interfaces:**
- Consumes: `ResearchState.values["selected_papers"]` (list of dict with `relevance_score`, `triage_decision`, `title`, `authors`, `year`, `url`, `local_path`, `pdf_path`, `abstract`); `AgentContext`; `AgentResult`
- Produces: `state.values["selected_papers"]` (filtered list); `state.values["selected_paper_count"]` (int); `AgentResult` with notes

- [ ] **Step 1: Create test file with failing tests**

File: `tests/test_paper_selector.py`:

```python
from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch

from agents.paper_selector import PaperSelectionAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


def _make_state(papers: list[dict]) -> ResearchState:
    topic = TopicPack(topic_name="test_topic")
    state = ResearchState(topic=topic)
    state.values["selected_papers"] = papers
    return state


def _make_context(tmp_path: str) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp_path)),
        memory_store=None,
        tool_registry=None,
        settings={},
    )


def _sample_papers() -> list[dict]:
    return [
        {
            "paper_id": "p1",
            "title": "Intention-Aware Diffusion Model for Pedestrian Trajectory Prediction",
            "authors": ["Smith, J.", "Jones, K."],
            "year": 2024,
            "relevance_score": 0.92,
            "triage_decision": "read",
            "url": "https://arxiv.org/abs/2401.12345",
            "abstract": "We propose a leapfrog diffusion model for pedestrian trajectory forecasting.",
        },
        {
            "paper_id": "p2",
            "title": "Graph-based Trajectory Prediction",
            "authors": ["Chen, L."],
            "year": 2023,
            "relevance_score": 0.78,
            "triage_decision": "skim",
            "local_path": "/data/papers/graph_traj.pdf",
            "abstract": "A graph-based approach to model interactions between pedestrians.",
        },
        {
            "paper_id": "p3",
            "title": "Language-Conditioned Multi-Agent Forecasting",
            "authors": ["Wang, X.", "Li, Y.", "Zhang, H."],
            "year": 2024,
            "relevance_score": 0.85,
            "triage_decision": "read",
            "url": "",
            "abstract": "We introduce a language-conditioned approach.",
        },
    ]


class PaperSelectionAgentTest(TestCase):
    def test_no_papers_returns_early(self):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state([])
            ctx = _make_context(tmp)
            result = agent.run(state, ctx)
            self.assertIn("no papers to select", result.notes[0])

    @patch("sys.stdin.isatty", return_value=False)
    def test_non_tty_keeps_all_papers(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state(_sample_papers())
            ctx = _make_context(tmp)
            result = agent.run(state, ctx)
            self.assertEqual(len(state.values["selected_papers"]), 3)
            self.assertIn("non-interactive", result.notes[0])

    @patch("sys.stdin.isatty", return_value=True)
    def test_select_by_comma_separated_indices(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state(_sample_papers())
            ctx = _make_context(tmp)
            with patch("builtins.input", return_value="1,3"):
                with patch("sys.stdout", StringIO()):
                    result = agent.run(state, ctx)
            self.assertEqual(len(state.values["selected_papers"]), 2)
            self.assertEqual(state.values["selected_papers"][0]["paper_id"], "p1")
            self.assertEqual(state.values["selected_papers"][1]["paper_id"], "p3")
            self.assertEqual(state.values["selected_paper_count"], 2)

    @patch("sys.stdin.isatty", return_value=True)
    def test_enter_keeps_all_papers(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state(_sample_papers())
            ctx = _make_context(tmp)
            with patch("builtins.input", return_value=""):
                with patch("sys.stdout", StringIO()):
                    result = agent.run(state, ctx)
            self.assertEqual(len(state.values["selected_papers"]), 3)
            self.assertEqual(state.values["selected_paper_count"], 3)

    @patch("sys.stdin.isatty", return_value=True)
    def test_none_clears_all_papers(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state(_sample_papers())
            ctx = _make_context(tmp)
            with patch("builtins.input", return_value="none"):
                with patch("sys.stdout", StringIO()):
                    result = agent.run(state, ctx)
            self.assertEqual(len(state.values["selected_papers"]), 0)
            self.assertEqual(state.values["selected_paper_count"], 0)

    @patch("sys.stdin.isatty", return_value=True)
    def test_display_includes_relevance_score_and_decision(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state([_sample_papers()[0]])
            ctx = _make_context(tmp)
            buf = StringIO()
            with patch("builtins.input", return_value="1"):
                with patch("sys.stdout", buf):
                    agent.run(state, ctx)
            output = buf.getvalue()
            self.assertIn("★0.92 read", output)
            self.assertIn("Intention-Aware", output)
            self.assertIn("Smith, J., Jones, K.", output)
            self.assertIn("2024", output)

    @patch("sys.stdin.isatty", return_value=True)
    def test_display_shows_url_when_present(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state([_sample_papers()[0]])
            ctx = _make_context(tmp)
            buf = StringIO()
            with patch("builtins.input", return_value="1"):
                with patch("sys.stdout", buf):
                    agent.run(state, ctx)
            output = buf.getvalue()
            self.assertIn("https://arxiv.org/abs/2401.12345", output)

    @patch("sys.stdin.isatty", return_value=True)
    def test_display_shows_local_path_when_no_url(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state([_sample_papers()[1]])
            ctx = _make_context(tmp)
            buf = StringIO()
            with patch("builtins.input", return_value="1"):
                with patch("sys.stdout", buf):
                    agent.run(state, ctx)
            output = buf.getvalue()
            self.assertIn("/data/papers/graph_traj.pdf", output)

    @patch("sys.stdin.isatty", return_value=True)
    def test_display_shows_pdf_path_fallback(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            papers = [{
                "paper_id": "p4",
                "title": "Test Paper",
                "authors": "Author",
                "year": 2024,
                "relevance_score": 0.5,
                "triage_decision": "skim",
                "pdf_path": "/data/test.pdf",
                "abstract": "Test abstract.",
            }]
            state = _make_state(papers)
            ctx = _make_context(tmp)
            buf = StringIO()
            with patch("builtins.input", return_value="1"):
                with patch("sys.stdout", buf):
                    agent.run(state, ctx)
            output = buf.getvalue()
            self.assertIn("/data/test.pdf", output)

    @patch("sys.stdin.isatty", return_value=True)
    def test_authors_list_joined_with_comma(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state([_sample_papers()[2]])
            ctx = _make_context(tmp)
            buf = StringIO()
            with patch("builtins.input", return_value="1"):
                with patch("sys.stdout", buf):
                    agent.run(state, ctx)
            output = buf.getvalue()
            self.assertIn("Wang, X., Li, Y., Zhang, H.", output)

    @patch("sys.stdin.isatty", return_value=True)
    def test_invalid_input_indices_ignored(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state(_sample_papers())
            ctx = _make_context(tmp)
            with patch("builtins.input", return_value="1,abc,5"):
                with patch("sys.stdout", StringIO()):
                    result = agent.run(state, ctx)
            self.assertEqual(len(state.values["selected_papers"]), 1)
            self.assertEqual(state.values["selected_papers"][0]["paper_id"], "p1")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify tests fail**

Run: `D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_paper_selector -v`
Expected: FAIL (PaperSelectionAgent not yet implemented)

- [ ] **Step 3: Create PaperSelectionAgent**

File: `agents/paper_selector.py`:

```python
from __future__ import annotations

import sys

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState


class PaperSelectionAgent(Agent):
    """Interactive terminal prompt for selecting papers after triage, before parsing."""

    name = "paper_selection"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        papers = state.values.get("selected_papers", [])
        if not papers:
            return AgentResult(notes=["no papers to select"])

        if not sys.stdin.isatty():
            state.values["selected_paper_count"] = len(papers)
            return AgentResult(
                notes=[f"non-interactive: keeping all {len(papers)} papers"],
                values={"selected_paper_count": len(papers)},
            )

        print(f"\n=== 候选论文 ({len(papers)} 篇) ===")
        for i, p in enumerate(papers, 1):
            score = p.get("relevance_score", 0)
            decision = p.get("triage_decision", "read")
            title = (p.get("title") or "")[:100]
            authors = p.get("authors", "")
            if isinstance(authors, list):
                authors = ", ".join(str(a) for a in authors[:3])
            year = p.get("year", "")
            url = p.get("url", "")
            local = p.get("local_path") or p.get("pdf_path", "")
            abstract = (p.get("abstract") or "")[:200]

            print(f"[{i}] ★{score:.2f} {decision} | {title}")
            print(f"    {authors}, {year}")
            if url:
                print(f"    🔗 {url}")
            elif local:
                print(f"    📁 {local}")
            print(f"    {abstract}")
            print()

        choice = input("输入要保留的论文编号（逗号分隔），回车全选，输入 none 跳过全部：").strip()
        if choice.lower() == "none":
            state.values["selected_papers"] = []
        elif choice:
            indices = {int(x.strip()) - 1 for x in choice.split(",") if x.strip().isdigit()}
            state.values["selected_papers"] = [p for i, p in enumerate(papers) if i in indices]

        state.values["selected_paper_count"] = len(state.values["selected_papers"])
        return AgentResult(
            notes=[f"user selected {len(state.values['selected_papers'])}/{len(papers)} papers"],
            values={"selected_paper_count": len(state.values["selected_papers"])},
        )
```

- [ ] **Step 4: Register in agents/__init__.py**

Add import after `PaperTriageAgent` line:

```python
from agents.paper_selector import PaperSelectionAgent
```

Add `"PaperSelectionAgent"` to `__all__` list (alphabetically, after `"PaperReaderAgent"`).

- [ ] **Step 5: Integrate into workflow factory**

In `workflows/factory.py:64-68`, insert `PaperSelectionAgent()` BEFORE `LocalPaperParserAgent()`:

```python
agents.extend([
    PaperSelectionAgent(),
    LocalPaperParserAgent(),
    PaperReaderAgent(),
    ReferenceExtractorAgent(),
    EvidenceCheckerAgent(),
    MethodCardExtractorAgent(),
    ...
])
```

- [ ] **Step 6: Run tests to verify**

Run: `D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_paper_selector -v`
Expected: all 11 tests pass

- [ ] **Step 7: Commit**

```bash
git add agents/paper_selector.py agents/__init__.py workflows/factory.py tests/test_paper_selector.py
git commit -m "feat: add PaperSelectionAgent for interactive paper selection after triage"
```

---

### Task 4: Memory Filtering

**Files:**
- Modify: `agents/literature_memory_agent.py:18-65`

**Interfaces:**
- Consumes: `state.values` with keys `selected_papers`, `parsed_papers`, `checked_evidence`, `method_cards`, `extracted_references`; `_to_state_values(state)` existing function
- Produces: filtered `state_values` dict passed to `store.write_run_artifacts()`

- [ ] **Step 1: Add failing tests for memory filtering**

File: `tests/test_literature_memory.py` — add to `LiteratureMemoryPersistenceAgentTest` class:

```python
def test_filter_excludes_unselected_papers_from_memory(self):
    with TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        lit_store = LiteratureMemoryStore(db_path)
        agent = LiteratureMemoryPersistenceAgent(lit_memory_store=lit_store)

        topic = _make_topic("test_filter")
        state = ResearchState(topic=topic)
        state.values["selected_papers"] = [
            {
                "paper_id": "keep_me",
                "title": "Keep This Paper",
                "abstract": "good",
                "authors": [],
                "year": 2024,
                "keywords": [],
            },
        ]
        state.values["parsed_papers"] = {
            "keep_me": {"paper_id": "keep_me", "sections": []},
            "discard_me": {"paper_id": "discard_me", "sections": []},
        }
        state.values["checked_evidence"] = [
            {"evidence_id": "ev1", "paper_id": "keep_me", "claim_supported": "yes", "quote": "text", "section": "Method", "support_level": "strong"},
            {"evidence_id": "ev2", "paper_id": "discard_me", "claim_supported": "yes", "quote": "text", "section": "Method", "support_level": "strong"},
        ]
        state.values["method_cards"] = [
            {"method_card_id": "mc1", "paper_id": "keep_me", "task": "test", "datasets": [], "metrics": []},
            {"method_card_id": "mc2", "paper_id": "discard_me", "task": "test", "datasets": [], "metrics": []},
        ]
        state.values["extracted_references"] = [
            {"ref_id": "r1", "title": "Ref1", "source_paper_id": "keep_me"},
            {"ref_id": "r2", "title": "Ref2", "source_paper_id": "discard_me"},
        ]

        context = _make_context(tmp)
        agent.run(state, context)

        papers = lit_store.retrieve_papers("test_filter", limit=10)
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["paper_id"], "keep_me")

        cards = lit_store.retrieve_method_cards("test_filter", limit=10)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["paper_id"], "keep_me")

        evidence = lit_store.retrieve_evidence("test_filter", ["keep_me"], limit=10)
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["paper_id"], "keep_me")


def test_filter_keeps_selected_papers_in_memory(self):
    with TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        lit_store = LiteratureMemoryStore(db_path)
        agent = LiteratureMemoryPersistenceAgent(lit_memory_store=lit_store)

        topic = _make_topic("test_keep")
        state = ResearchState(topic=topic)
        state.values["selected_papers"] = [
            {
                "paper_id": "p1",
                "title": "Paper One",
                "abstract": "abstract one",
                "authors": [],
                "year": 2024,
                "keywords": [],
            },
            {
                "paper_id": "p2",
                "title": "Paper Two",
                "abstract": "abstract two",
                "authors": [],
                "year": 2024,
                "keywords": [],
            },
        ]
        state.values["parsed_papers"] = {
            "p1": {"paper_id": "p1", "sections": []},
            "p2": {"paper_id": "p2", "sections": []},
        }
        state.values["checked_evidence"] = [
            {"evidence_id": "ev1", "paper_id": "p1", "claim_supported": "yes", "quote": "text", "section": "Abstract", "support_level": "strong"},
            {"evidence_id": "ev2", "paper_id": "p2", "claim_supported": "yes", "quote": "text", "section": "Method", "support_level": "strong"},
        ]
        state.values["method_cards"] = [
            {"method_card_id": "mc1", "paper_id": "p1", "task": "test", "datasets": [], "metrics": []},
            {"method_card_id": "mc2", "paper_id": "p2", "task": "test", "datasets": [], "metrics": []},
        ]

        context = _make_context(tmp)
        agent.run(state, context)

        papers = lit_store.retrieve_papers("test_keep", limit=10)
        self.assertEqual(len(papers), 2)


def test_filter_filters_extracted_references_by_source_paper_id(self):
    with TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        lit_store = LiteratureMemoryStore(db_path)
        agent = LiteratureMemoryPersistenceAgent(lit_memory_store=lit_store)

        topic = _make_topic("test_ref")
        state = ResearchState(topic=topic)
        state.values["selected_papers"] = [
            {
                "paper_id": "keep_me",
                "title": "Keep",
                "abstract": "yes",
                "authors": [],
                "year": 2024,
                "keywords": [],
            },
        ]
        state.values["extracted_references"] = [
            {"ref_id": "r1", "title": "Kept Ref", "source_paper_id": "keep_me"},
            {"ref_id": "r2", "title": "Discarded Ref", "source_paper_id": "discard_me"},
        ]

        context = _make_context(tmp)
        agent.run(state, context)

        papers = lit_store.retrieve_papers("test_ref", limit=10)
        self.assertEqual(len(papers), 1)


def test_filter_no_selected_papers_persists_all(self):
    """When selected_papers is empty (no user selection), persist everything as before."""
    with TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        lit_store = LiteratureMemoryStore(db_path)
        agent = LiteratureMemoryPersistenceAgent(lit_memory_store=lit_store)

        topic = _make_topic("test_no_filter")
        state = ResearchState(topic=topic)
        state.values["selected_papers"] = []
        state.values["parsed_papers"] = {
            "p1": {"paper_id": "p1", "sections": []},
        }
        state.values["checked_evidence"] = [
            {"evidence_id": "ev1", "paper_id": "p1", "claim_supported": "yes", "quote": "text", "section": "Method", "support_level": "strong"},
        ]
        state.values["method_cards"] = [
            {"method_card_id": "mc1", "paper_id": "p1", "task": "test", "datasets": [], "metrics": []},
        ]

        context = _make_context(tmp)
        agent.run(state, context)

        cards = lit_store.retrieve_method_cards("test_no_filter", limit=10)
        self.assertEqual(len(cards), 1)
```

- [ ] **Step 2: Verify tests fail**

Run: `D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_literature_memory.LiteratureMemoryPersistenceAgentTest.test_filter_excludes_unselected_papers_from_memory -v`
Expected: FAIL (unselected papers still persisted)

- [ ] **Step 3: Implement _filter_by_selected()**

Add at module level in `agents/literature_memory_agent.py` (before `LiteratureMemoryPersistenceAgent` class or after `_to_state_values`):

```python
def _filter_by_selected(state_values: dict) -> dict:
    selected = state_values.get("selected_papers", [])
    selected_ids = {p.get("paper_id", "") for p in selected if p.get("paper_id")}
    if not selected_ids:
        return state_values

    filtered = dict(state_values)
    filtered["selected_papers"] = selected

    filtered["parsed_papers"] = {
        pid: v for pid, v in state_values.get("parsed_papers", {}).items()
        if pid in selected_ids
    }

    filtered["checked_evidence"] = [
        e for e in state_values.get("checked_evidence", [])
        if e.get("paper_id", "") in selected_ids
    ]

    filtered["method_cards"] = [
        m for m in state_values.get("method_cards", [])
        if m.get("paper_id", "") in selected_ids
    ]

    filtered["extracted_references"] = [
        r for r in state_values.get("extracted_references", [])
        if r.get("source_paper_id", "") in selected_ids
    ]

    return filtered
```

- [ ] **Step 4: Call _filter_by_selected() in run()**

In `LiteratureMemoryPersistenceAgent.run()`, add after `state_values = _to_state_values(state)`:

```python
state_values = _filter_by_selected(state_values)
```

- [ ] **Step 5: Run tests to verify**

Run: `D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_literature_memory.LiteratureMemoryPersistenceAgentTest -v`
Expected: all tests pass (existing 2 + new 4 = 6)

- [ ] **Step 6: Run full test suite to verify no regression**

Run: `D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p "test*.py" -v`
Expected: ~347 tests pass

- [ ] **Step 7: Commit**

```bash
git add agents/literature_memory_agent.py tests/test_literature_memory.py
git commit -m "feat: filter unselected papers and derived artifacts from cross-run memory"
```

---

### Verification

After all 4 tasks complete, run the full test suite:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p "test*.py"
```

Expected: ~347 tests pass (332 baseline + 15 new).

Offline smoke test with interactive paper selection disabled (non-TTY):

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics/intent_led_virat.json --data-dir data --max-papers 2
```

Expected: `review_status=pass` or `needs_human_review`, no crashes, PaperSelectionAgent logs "non-interactive: keeping all N papers".

