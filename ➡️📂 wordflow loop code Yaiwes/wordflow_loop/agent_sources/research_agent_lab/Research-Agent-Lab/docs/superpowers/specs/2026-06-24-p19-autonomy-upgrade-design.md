# P19: Autonomy Upgrade Design

## Goal

Raise the system's autonomy level from L2+ to L3 by reducing manual gatekeeping, fixing online retrieval, adding interactive paper selection, and filtering memory to only keep human-approved papers.

## Architecture

```
┌─ 自动检索 (修复) ─────────────────────────────────┐
│ LiteratureSearchAgent (本地 + arXiv + LLM 打分)    │
│ PaperTriageAgent (LLM 排序 + relevance 标注)        │
│ 修复: online 注入 settings, 参考种子检索 bug       │
└───────────────────┬───────────────────────────────┘
                    ▼
┌─ 人工选择点 (新增 PaperSelectionAgent) ────────────┐
│ 终端展示候选列表 (标题/相关度/摘要/链接)            │
│ input() 交互勾选 → 非 TTY 自动跳过                 │
└───────────────────┬───────────────────────────────┘
                    ▼
┌─ 安全门控 (改进) ─────────────────────────────────┐
│ enable_llm → 默认开 (--no-enable-llm 可关)         │
│ enable_experiments / enable_code_writes → topic    │
│   pack 预设，不每次 CLI 指定                       │
│ 优先级: CLI 显式 > topic pack > 系统默认            │
└───────────────────┬───────────────────────────────┘
                    ▼
      原有流程 (Parser → Evidence → MethodCard → ...)
                    ▼
┌─ 记忆过滤 (LiteratureMemoryPersistenceAgent) ──────┐
│ 只持久化被选中的论文 + 其派生内容                   │
│ (垃圾文献不进 SQLite)                               │
└────────────────────────────────────────────────────┘
```

## Summary of Changes

| # | Change | File | Breaking |
|---|--------|------|----------|
| 1 | Config priority chain | `app/main.py`, `workflows/factory.py` | No |
| 2 | Online retrieval bug fix | `agents/literature_searcher.py`, `workflows/factory.py` | No |
| 3 | Interactive paper selection | `agents/paper_selector.py` (new), `agents/__init__.py` | No |
| 4 | Memory filtering | `agents/literature_memory_agent.py` | No |

---

## Section 1: Configuration Priority Chain

### Enable flag defaults

Change `enable_llm` default from `False` to `True`. LLM calls have budget limits as safety net.

| Setting | System default | Topic pack key | CLI override |
|---------|---------------|----------------|-------------|
| `enable_llm` | `True` | `metadata.enable_llm` | `--enable-llm` / `--no-enable-llm` |
| `enable_experiments` | `False` | `metadata.enable_experiments` | `--enable-experiments` |
| `enable_code_writes` | `False` | `metadata.enable_code_writes` | `--enable-code-writes` |
| `online` | `False` | `metadata.online` | `--online` |

### CLI: --no-enable-llm

File: `app/main.py` — add after `--enable-llm`:

```python
run_parser.add_argument(
    "--no-enable-llm",
    action="store_true",
    dest="disable_llm",
    help="Disable external LLM API calls (overrides topic pack default)",
)
```

### Merge logic

File: `app/main.py:235-255` — replace direct passthrough with merge:

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
```

### Factory defaults

File: `workflows/factory.py:43` — change `enable_llm: bool = False` to `enable_llm: bool = True`.

Add `online: bool = False` parameter and `"online": online` to settings dict.

### Topic pack metadata

File: `topics/intent_led_virat.json` — add under `metadata`:

```json
"metadata": {
    "enable_llm": true,
    "enable_experiments": false,
    "enable_code_writes": false,
    "online": false,
    ...
}
```

All four keys are optional — absent = use system default.

---

## Section 2: Online Retrieval Fix

### Bug: LiteratureSearcher reference seed online path dead

File: `agents/literature_searcher.py:113`

Current:
```python
if context.tool_registry and context.tool_registry.has("arxiv") and context.settings.get("online"):
```

`context.settings.get("online")` always returns `None` because factory never injected `"online"` into the settings dict. The condition short-circuits to False, and the arXiv path for reference seeds never activates.

Fix:
```python
if context.tool_registry and context.tool_registry.has("arxiv"):
```

`context.tool_registry.has("arxiv")` is already sufficient — ArxivTool is only registered when `--online` is passed (see `app/main.py:245`). No additional check needed.

### Inject online into settings

File: `workflows/factory.py` — add `online: bool = False` parameter and `"online": online` to settings dict, for any agent that needs to check online availability explicitly.

### LLM scoring (no changes)

`PaperTriageAgent._try_llm_triage()` already works when `enable_llm=True`. With the new defaults, `--online` alone triggers: arXiv retrieval → LLM scoring → relevance-ranked paper list.

---

## Section 3: Interactive Paper Selection

### PaperSelectionAgent (new)

File: `agents/paper_selector.py`

Insertion point: after `PaperTriageAgent`, before `LocalPaperParserAgent` in `workflows/factory.py`.

#### Display format

Each paper shows:
- Index, relevance score (★), triage decision (read/skim)
- Title (truncated to 100 chars)
- Authors, year
- Link: `🔗 url` for arXiv papers, `📁 local_path` for local PDFs, nothing for offline seeds
- Abstract (first 200 chars)

```
=== 候选论文 (3 篇) ===
[1] ★0.92 read | Intention-Aware Diffusion Model for Pedestrian Trajectory Prediction
    Smith et al., 2024
    📁 C:\Users\duyul\Desktop\work\Essay\轨迹预测\SPK\2025.12\Intention-Aware.pdf
    We propose a leapfrog diffusion model for pedestrian trajectory forecasting...

[2] ★0.78 skim | Graph-based Trajectory Prediction
    Chen et al., 2023
    🔗 https://arxiv.org/abs/2301.12345
    A graph-based approach to model interactions between pedestrians...

输入要保留的论文编号（逗号分隔），回车全选，输入 none 跳过全部：
```

#### run() logic

```python
def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
    papers = state.values.get("selected_papers", [])
    if not papers:
        return AgentResult(notes=["no papers to select"])

    if not sys.stdin.isatty():
        return AgentResult(notes=["non-interactive: keeping all papers"])

    for i, p in enumerate(papers, 1):
        score = p.get("relevance_score", 0)
        decision = p.get("triage_decision", "read")
        title = (p.get("title") or "")[:100]
        authors = p.get("authors", "")
        if isinstance(authors, list):
            authors = ", ".join(authors[:3])
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

#### Integration

File: `workflows/factory.py` — insert after `PaperTriageAgent()`, BEFORE `LocalPaperParserAgent` (避免对将被丢弃的论文浪费 CPU 解析 PDF):

```python
agents.extend([
    PaperSelectionAgent(),       # ← 新增，在 parser 之前
    LocalPaperParserAgent(),
    PaperReaderAgent(),
    ...
])
```

File: `agents/__init__.py` — export `PaperSelectionAgent`.

---

## Section 4: Memory Filtering

### LiteratureMemoryPersistenceAgent

File: `agents/literature_memory_agent.py`

Add `_filter_by_selected()` to filter out unselected papers and their derived artifacts before persisting:

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

Call in `run()` before `store.write_run_artifacts()`:

```python
def run(self, state, context):
    store = self._store or getattr(context, "lit_memory_store", None)
    if store is None:
        return AgentResult(notes=["skipped: no LiteratureMemoryStore available"])

    scope = memory_scope_for_topic(state.topic.topic_name)
    state_values = _to_state_values(state)
    state_values = _filter_by_selected(state_values)  # ← 新增
    count = store.write_run_artifacts(state_values, scope)
    ...
```

### Field name mapping

| Artifact | Filter field | Source |
|----------|-------------|--------|
| selected_papers | `paper_id` | `schemas/paper.py:12` |
| parsed_papers | dict key = `paper_id` | — |
| checked_evidence | `paper_id` | `schemas/evidence.py:10` |
| method_cards | `paper_id` | `schemas/method_card.py:10` |
| extracted_references | `source_paper_id` | `schemas/reference.py:11` |

---

## What Is Not Changed

- No changes to `PaperTriageAgent`, `LiteratureSearchAgent` (except one-line bug fix), `LocalPaperParserAgent`, `PaperReaderAgent`
- No changes to `core/workflow.py` or `core/agent_base.py` — `input()` works within existing synchronous loop
- No changes to `memory/literature_memory.py` — filtering happens before write, store API unchanged
- No new CLI parameters beyond `--no-enable-llm`
- No Docker/sandbox changes
- No vector database integration

---

## Testing Strategy

| Test | File | Coverage |
|------|------|----------|
| `test_enable_llm_defaults_true` | `test_full_research_loop.py` | factory default is True |
| `test_no_enable_llm_disables` | `test_full_research_loop.py` | --no-enable-llm flag works |
| `test_topic_metadata_overrides_defaults` | `test_full_research_loop.py` | topic pack metadata presets |
| `test_cli_overrides_topic_metadata` | `test_full_research_loop.py` | CLI > topic pack |
| `test_online_injected_to_settings` | `test_workflow_settings.py` | factory injects online |
| `test_reference_seeds_online_path_works` | `test_literature_searcher.py` | bug fix verified |
| `test_paper_selection_displays_candidates` | new `test_paper_selector.py` | display format |
| `test_paper_selection_filters_by_index` | new `test_paper_selector.py` | index parsing |
| `test_paper_selection_keep_all_on_enter` | new `test_paper_selector.py` | enter = all |
| `test_paper_selection_none_clears_all` | new `test_paper_selector.py` | none = clear |
| `test_paper_selection_non_tty_skips` | new `test_paper_selector.py` | TTY detection |
| `test_memory_filter_excludes_unselected` | `test_literature_memory.py` | paper not in memory |
| `test_memory_filter_keeps_selected` | `test_literature_memory.py` | paper in memory |
| `test_memory_filter_filters_derived_artifacts` | `test_literature_memory.py` | evidence/cards/references |
| `test_filter_by_source_paper_id` | `test_literature_memory.py` | extracted_references filter |

Expected: 332 + ~15 new = ~347 tests pass.
