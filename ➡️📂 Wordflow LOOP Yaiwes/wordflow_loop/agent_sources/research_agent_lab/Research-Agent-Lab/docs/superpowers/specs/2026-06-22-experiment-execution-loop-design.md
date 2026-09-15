# P15: 实验执行闭环 — 设计文档

**日期：** 2026-06-22
**参考项目：** AI Scientist-v2（主要）、OpenHands（安全沙箱）、Agent Laboratory（阶段 artifact）
**目标：** 打通 code → run → analyze → debug → retry 闭环，使系统能在明确授权下自动改代码、跑实验、分析结果、失败后修复迭代。

**核心约束：**
- `--enable-experiments` 只表示允许执行实验命令，不等价于允许写代码。
- 自动代码写入必须额外开启 `--enable-code-writes`，且通常还需要 `--enable-llm`。
- 未开启代码写入时，系统仍必须保留当前能力：执行已有 smoke command，产出 ExperimentResult，不得因为 CodeWriter skipped 而跳过实验执行。

---

## 1. 架构概览

**架构模式：** 工作流级外循环 + Orchestrator 内循环

- **外循环**（workflow 层面）：DeveloperAgent → ExperimentOrchestratorAgent → ExperimentDecisionAgent → TreeSearchAgent → ...，每个 agent 独立执行并产 artifact
- **内循环**（Orchestrator 内部）：CodeWriter → AutoExperiment → ResultCheck → AutoDebug → CodeWriter，最多 4 次总尝试（1 初始 + 3 debug 重试）
- `CodeWriterAgent` 和 `AutoDebuggerAgent` 不作为 workflow 顶层 agent 插入；它们只由 `ExperimentOrchestratorAgent` 内部调用。

### 数据流

```
ExperimentPlanner → DeveloperAgent → ExperimentOrchestratorAgent(NEW) → ExperimentDecisionAgent → TreeSearchAgent
    (已有，增强)     (已有，微改)       内部封装:
                                  CodeWriterAgent(NEW)
                                      ↓
                                  AutonomousExperimentAgent(已有，中改)
                                      ↓
                                  ResultCheck
                                      ↓
                                  AutoDebuggerAgent(NEW)
```

## 2. Schema

### 2.1 修改 `schemas/experiment_plan.py`

ExperimentPlan 新增字段：
```python
success_criteria: dict[str, object] = field(default_factory=dict)
# 结构: {"mode": "metric"|"llm_judge"|"both",
#         "metrics": [{"name": "accuracy", "pattern": "accuracy:\\s*([0-9.]+)", "target": 0.9, "direction": "gte"}],
#         "qualitative_goal": "描述性目标，供 LLM Judge 使用"}
```
与现有 `acceptance_criteria`（人工策略用）并存，不冲突。

`pattern` 语义必须落地：若 parser 已提取 `name` 对应指标，则优先使用已有 metrics；若未提取且 `pattern` 存在，则在 stdout/stderr combined text 中按该正则补充抽取。否则该字段应从 schema 中删除，避免“定义了但不生效”。

### 2.2 新 `schemas/code_patch.py`

```python
@dataclass(slots=True)
class CodePatch:
    patch_id: str = field(default_factory=lambda: new_id("patch"))
    experiment_id: str = ""
    task_id: str = ""
    attempt: int = 0
    mode: str = "copy"           # "copy" | "sandbox"
    work_dir: str = ""           # 代码副本路径或沙箱路径
    changed_files: list[dict] = field(default_factory=list)
    # 每个 dict:
    # {
    #   "relative_path": str,
    #   "action": "create"|"modify"|"delete",
    #   "diff": str,
    #   "base_file_hash": str,
    #   "new_file_hash": str
    # }
    backup_paths: dict[str, str] = field(default_factory=dict)
    diff_summary: str = ""
    status: str = "pending"      # "applied"|"skipped"|"blocked"|"error"
    reason: str = ""
```

### 2.3 修改 `schemas/experiment_result.py`

ExperimentResult 新增字段：
```python
attempt: int = 0
patch_id: str = ""
commands: list[str] = field(default_factory=list)
timed_out: bool = False
work_dir: str = ""
criteria_results: list[dict] = field(default_factory=list)
```
不复用新建 ExperimentRun 或 ParseResult，避免 schema 重复。

### 2.4 新 `schemas/auto_debug_record.py`

```python
@dataclass(slots=True)
class AutoDebugRecord:
    record_id: str = field(default_factory=lambda: new_id("debug"))
    experiment_id: str = ""
    result_id: str = ""
    patch_id: str = ""
    attempt_number: int = 0
    error_summary: str = ""
    fix_description: str = ""
    fix_file_contents: dict[str, str] = field(default_factory=dict)
    # {file_path: new_content}
    fix_successful: bool = False
    llm_call_id: str = ""
    log_artifact_id: str = ""
```

## 3. 新 Agent

### 3.1 CodeWriterAgent (`agents/code_writer.py`)

**职责：** 根据 ExperimentPlan + CodeTask 实际修改代码，输出 CodePatch 审计 artifact。

**授权条件：**
- `enable_code_writes=True` 才允许写文件。
- 首次代码生成需要 `enable_llm=True` 且 LLM budget 允许。
- 未开启 `enable_code_writes` 时返回 `CodePatch(status="skipped", reason="code writes disabled")`，但 Orchestrator 仍应继续执行已有 smoke command。

**流程：**
1. 读当前 experiment_id 对应的 CodeTask（安全元数据）+ ExperimentPlan（experiment hypothesis + modification）
2. 检查 `pending_fixes_by_experiment_id[experiment_id]`：有 → retry 模式，直接应用修复代码；无 → 首次模式
3. 确定安全模式：
   - sandbox（codebase.copy_can_modify=true）：work_dir = repo_path，但仍必须执行路径白/黑名单与路径逃逸校验
   - copy（默认）：copy 到 run_dir/code_copies/{experiment_id}/attempt_{attempt}/，原代码只读
4. 首次模式：LLM 路由 → router.route_for("experiment_planner")，prompt 含 hypothesis + modification + 目标文件内容 → LLM 输出新文件内容
5. 安全验证：
   - 变更文件必须是相对路径，禁止绝对路径、`..`、盘符、UNC 路径
   - `Path(work_dir, relative_path).resolve()` 必须仍在 `work_dir.resolve()` 内，防止 symlink/path traversal 逃逸
   - 所有变更文件必须通过 `ProjectSafetyPolicy.validate_planned_paths()`
   - 所有变更文件在 `allowed_paths` 内且不匹配 `protected_paths`
   - 文件数不得超过 `max_files_per_patch`
6. 写前备份：原文件 → .bak，写新内容，difflib 生成审计 diff
7. 对每个文件记录 base_file_hash / new_file_hash，构造 CodePatch → artifact: code_patches/{patch_id}.json
8. 写入：
   - `state.values["code_patches_by_experiment_id"][experiment_id] = patch_dict`
   - `state.values["code_patch"] = patch_dict` 仅作向后兼容，不作为多分支主数据源
9. 若 `requires_human_approval=True` 且非交互 → blocked；blocked 不得写文件

### 3.2 AutoDebuggerAgent (`agents/auto_debugger.py`)

**职责：** 实验失败时，LLM 分析错误原因并生成修复代码。不应用修复（由 Orchestrator 路由回 CodeWriter 应用）。

**流程：**
1. 读最近失败 ExperimentResult（status ∈ {error, failed}）→ 读取对应 CodePatch 获取 work_dir
2. attempt >= max_debug_attempts → blocked（默认 3，通过 settings 配置，不硬编码）
3. 解析 stderr 中的 Python traceback → 提取 (file_path, line_number)
4. LLM 路由：router.route_for("paper_triage")（flash 模型）
5. Prompt：实验假设 + 错误文件内容（聚焦 traceback 行 ±50 行） + 完整 stdout/stderr artifact 或 log_tail + 之前 debug 记录
6. LLM 输出：错误原因 + 修复后完整文件内容 {file_path: new_content}
7. 每次 LLM 调用必须写 `artifacts/llm_calls/*.json`，并调用 `record_llm_usage()`，供 RunEvaluation 的 LLM 质量检查使用
8. 构造 AutoDebugRecord → artifact: auto_debug_records/{record_id}.json
9. 写入：
   - `state.values["last_debug_records_by_experiment_id"][experiment_id] = record_dict`
   - `state.values["last_debug_record"] = record_dict` 仅作向后兼容
10. 若 enable_llm=False → skipped；若无 CodePatch → error

### 3.3 ExperimentOrchestratorAgent (`agents/experiment_orchestrator.py`)

**职责：** 封装 code→run→debug→retry 循环。Workflow 视角只看到一个 agent。

**关键契约：**
- Orchestrator 必须按单个 ExperimentPlan 隔离执行，不能直接让 `AutonomousExperimentAgent.run()` 读取全量 `state.values["experiment_plans"]` 后重复执行所有 plan。
- 实现方式二选一：
  1. 给 `AutonomousExperimentAgent` 增加 `run_single_plan(state, context, plan, patch, attempt)`；
  2. Orchestrator 临时构造隔离 state，只放当前 plan，并在执行后合并结果。
- 推荐方式 1，避免污染全局 state。

**内部循环（per plan）：**

```
for plan in experiment_plans:
    experiment_id = plan["experiment_id"]
    clear pending_fixes_by_experiment_id[experiment_id] and last_debug_records_by_experiment_id[experiment_id]

    for attempt in range(0, max_debug_attempts + 1):
        CodeWriterAgent.run_one_plan(...)     → CodePatch
        # CodeWriter skipped only means no patch; still execute existing smoke command.
        AutonomousExperimentAgent.run_single_plan(...) → ExperimentResult[]

        判断:
        - 全部 passed → 记录成功，break
        - CodeWriter blocked/error → 停止当前 plan，进入下一个 plan 或结束
        - attempt >= max_debug_attempts → 记录失败，break
        - 失败 & attempt < max_debug_attempts:
            AutoDebuggerAgent.run_one_result(...) → AutoDebugRecord
            若 fix_file_contents 为空 → break
            pending_fixes_by_experiment_id[experiment_id] = fix_file_contents
            继续下一 attempt
```

**多 plan：** 按 experiment_plans 顺序串行；plan 间清理该 experiment_id 的 pending fix 和 debug record，禁止全局单例泄漏。

**输出：**
- `all_code_patches`
- `all_experiment_results`
- `orchestrator_summary`
- `code_patches_by_experiment_id`
- `auto_debug_records_by_experiment_id`

最终写回 `state.values["experiment_results"]` 必须是按 experiment_id 可匹配的平铺列表，保持 TreeSearchAgent 当前消费方式。

## 4. 修改现有 Agent

### 4.1 DeveloperAgent — 微改

implementation_notes 前加 4 条实验专属 note（从 ExperimentPlan 提取 hypothesis, modification, files_to_change, baseline），保留原有安全指令。

### 4.2 AutonomousExperimentAgent — 中改

- 新增 `run_single_plan(state, context, plan, patch=None, attempt=0)`，供 Orchestrator 调用；原 `run()` 保留，用于向后兼容和非 Orchestrator 路径。
- work_dir 优先从当前 experiment_id 对应的 CodePatch 读：
  - `code_patches_by_experiment_id[experiment_id].work_dir`
  - fallback `state.values["code_patch"].work_dir`
  - fallback repo_path（向后兼容）
- ExperimentResult 写入 attempt 和 patch_id
- parse_experiment_output 传入 success_criteria，调用 _check_criteria 数值比对
- success_criteria.mode ∈ {llm_judge, both} 时调用 LLM Judge
- LLM Judge 必须遵守 llm budget，写 `llm_calls` artifact，并记录 usage。
- timeout 时设置 `timed_out=True`，status="error"，error_message 标明 timeout。
- 写出完整 stdout/stderr 或压缩日志 artifact，ExperimentResult 中只保留 log_tail。

### 4.3 parse_experiment_output — 中改

新增 `success_criteria` 参数和 `_check_criteria()` 函数。若 success criteria 提供 `pattern`，parser 必须先尝试从 combined stdout/stderr 中补充抽取指标：

```python
def _extract_success_metric(text: str, metric_spec: dict) -> float | None:
    pattern = metric_spec.get("pattern")
    if not pattern:
        return None
    try:
        match = re.search(str(pattern), text, re.IGNORECASE)
    except re.error:
        return None
    if not match:
        return None
    try:
        return float(match.group(1))
    except (IndexError, TypeError, ValueError):
        return None


def _check_criteria(metrics: dict[str, float], criteria: dict, text: str = "") -> tuple[bool, list[dict]]:
    targets = criteria.get("metrics", [])
    if not targets:
        return True, []
    results = []
    for t in targets:
        if not isinstance(t, dict):
            continue
        name = str(t.get("name", "")).lower()
        actual = metrics.get(name)
        if actual is None:
            actual = _extract_success_metric(text, t)
        if actual is None:
            results.append({"metric": name, "pass": False, "reason": "not found"})
            continue
        try:
            target = float(t.get("target", 0))
        except (TypeError, ValueError):
            results.append({"metric": name, "pass": False, "reason": f"bad target: {t.get('target')}"})
            continue
        direction = t.get("direction", "gte")
        ok = actual >= target if direction != "lte" else actual <= target
        results.append({"metric": name, "actual": actual, "target": target, "pass": ok})
    return all(r["pass"] for r in results), results
```

全防御：isinstance 检查、.get() 默认值、try/except float()、空列表处理。

### 4.4 ExperimentDecisionAgent — 微改

- 不新增 workflow 外层 `debug` action。debug 已由 Orchestrator 内循环消化；ExperimentDecisionAgent 只评价 Orchestrator 的最终结果。
- 若需要记录 debug 历史，读取 `orchestrator_summary` 和 `auto_debug_records_by_experiment_id`，写入 decision notes。
- 保持现有 action 语义：continue / investigate / rollback / hold，避免 TreeSearchAgent、ReviewerAgent 需要理解新 action。
- 对多分支结果继续按 experiment_id 分组，确保每个 selected branch node 都能拿到独立 decision。
- `max()` 加 `default=0` 防空序列 ValueError

## 5. Workflow 集成

### 5.1 修改 `workflows/factory.py`

```python
# 之前：
agents.append(AutonomousExperimentAgent())
agents.append(ExperimentDecisionAgent())

# 之后：
agents.append(ExperimentOrchestratorAgent())  # 内部封装 CodeWriter + AutoExp + AutoDebug
agents.append(ExperimentDecisionAgent())
```

AutonomousExperimentAgent 不再独立出现在 workflow 中，由 Orchestrator 内部调用。

`ExperimentOrchestratorAgent` 必须接收并透传以下 settings：
- `enable_experiments`
- `enable_code_writes`
- `enable_llm`
- `llm_call_budget`
- `llm_token_budget`
- `max_debug_attempts`
- `max_parallel_branches`

未开启 `enable_experiments` 时，Orchestrator 与现有行为一致：不执行命令，写空 experiment_results，并让 TreeSearchAgent 在无结果时回滚 selected 节点到 pending。

### 5.2 修改 `agents/__init__.py`

新增导出：CodeWriterAgent, AutoDebuggerAgent, ExperimentOrchestratorAgent

### 5.3 修改 CLI (`app/main.py`)

新增参数：
```bash
--enable-code-writes
--max-debug-attempts 3
```

语义：
- `--enable-experiments`：允许执行实验命令。
- `--enable-code-writes`：允许 CodeWriterAgent 写文件。
- `--enable-llm`：允许 LLM 生成代码/修复/定性 judge。
- 同时开启三者才允许“LLM 自动改代码并运行实验”。

## 6. 安全模型

| 级别 | 条件 | 行为 |
|------|------|------|
| 副本模式（默认） | copy_can_modify ≠ true | shutil.copytree 到 run_dir/code_copy/，原代码只读 |
| 沙箱模式 | copy_can_modify = true | 原路径操作，但 CodeWriter 必须自行做路径解析、白/黑名单、hash、备份；ScopedCodeExecutor 只保护命令 cwd，不保护文件写入 |
| 路径白名单 | allowed_auto_edit | 只允许修改列表内文件 |
| 路径黑名单 | protected_files | 绝不触碰列表内文件 |
| 写前备份 | 始终 | 修改前复制 .bak，记录到 backup_paths |

**副本模式 copytree 规则：**
- 默认忽略 `.git/`, `__pycache__/`, `.pytest_cache/`, `results/`, `checkpoints/`, `wandb/`, `runs/`, 大模型权重和缓存目录。
- 若 copy 失败，CodeWriter 返回 blocked/error；不得回退到原仓直接写。
- copy 模式下 CodePatch.work_dir 指向 run_dir 内副本，AutonomousExperimentAgent 必须在副本上执行。

## 7. 测试策略

### 新增单元测试（~37 个）

| 文件 | 测试数 | 覆盖 |
|------|--------|------|
| test_code_writer.py | 12 | sandbox/copy 模式、enable_code_writes 门控、LLM 开关、retry 模式、安全验证、绝对路径/.. 路径拒绝、symlink 逃逸拒绝、copytree 失败、空 proposed_files、hash 记录 |
| test_auto_debugger.py | 8 | traceback 解析、max_debug_attempts、LLM 开关、历史记录、缺失 CodePatch、LLM 异常输出、llm_calls artifact、budget skip |
| test_experiment_orchestrator.py | 10 | 首次通过、retry 循环、max attempts 终止、plan 间隔离、多 plan 串行、CodeWriter skipped 仍执行 smoke、CodeWriter blocked 停止当前 plan、AutoDebugger skipped 停止、按 experiment_id 写回、selected branch 多分支结果不串位 |
| test_code_patch_schema.py | 2 | dataclass 默认值、changed_files 结构 |
| test_auto_debug_record_schema.py | 1 | dataclass 默认值 |
| test_result_parser.py | 7 | _check_criteria: pass/fail/bad_target/empty/direction_lte/pattern_extract/bad_pattern |
| test_experiment_decision.py | 3 | 保持现有 action、读取 orchestrator_summary notes、max(..., default=0) |
| test_full_research_loop.py | 3 | CLI 解析 enable_code_writes/max_debug_attempts、workflow settings 传递、enable_experiments 不隐式开启 code writes |

### 回归测试

- test_autonomous_experiment.py：验证 work_dir 从 code_patch 读取 + fallback 行为
- test_experiment_decision.py：所有现有测试用 settings={} 不变（debug action 不误触发）
- test_tree_search_agent.py：多分支 selected nodes 的 experiment_results 仍按 experiment_id 回写到对应节点
- test_run_evaluator.py：CodeWriter/AutoDebugger 的 llm_calls 非 ok 状态仍被 LLM 质量检查捕获
- 全量 `python -m unittest discover -s tests -p "test*.py"`，预期 ~270 tests 全过

### Smoke 测试

```bash
# 离线 smoke：不写代码，只执行已有 smoke command
python -m app.main run --topic topics/intent_led_virat.json --data-dir data --max-papers 1 --enable-experiments

# LLM smoke：允许生成代码、运行、失败后最多 1 次 debug retry
python -m app.main run --topic topics/intent_led_virat.json --data-dir data --max-papers 1 --enable-experiments --enable-code-writes --enable-llm --llm-call-budget 8 --max-debug-attempts 1
```

## 8. 实现阶段

| 阶段 | 内容 | 依赖 |
|------|------|------|
| Phase 1 | Schema：新建 code_patch.py + auto_debug_record.py，修改 experiment_plan.py + experiment_result.py | 无 |
| Phase 2 | 安全写入基础：CodeWriterAgent 路径校验、copy 模式、hash/backup、enable_code_writes 门控 + 测试 | Phase 1 |
| Phase 3 | 修改现有 Agent：result_parser success criteria、developer_agent notes、autonomous_experiment run_single_plan、experiment_decision 保持外层 action + 测试 | Phase 1 |
| Phase 4 | AutoDebuggerAgent：traceback 聚焦、llm_calls artifact、budget、debug record + 测试 | Phase 1, 3 |
| Phase 5 | ExperimentOrchestratorAgent：单 plan 隔离、多 plan 串行、retry、状态合并 + 测试 | Phase 2, 3, 4 |
| Phase 6 | Workflow/CLI 集成 + agents/__init__ + RunEvaluation/Reviewer 回归 | Phase 5 |
| Phase 7 | 全量测试 + 离线 smoke + 可选 LLM smoke 验证 | Phase 6 |

Phase 2 和 Phase 3 可并行；Phase 4 依赖 run_single_plan 和 result/log 契约，不建议提前实现。

## 9. 不改的东西

- Workflow 引擎：保持线性，不添加循环/条件跳转
- P10 实验树：继续由 ExperimentDecisionAgent 的最终 continue/investigate/rollback/hold 决策触发 TreeSearchAgent；不新增外层 debug action
- Literature→Report 链路：完全不动
- ModelRouter、ToolRegistry、ArtifactStore：无变更
- 现有 CLI 参数语义不变：`--enable-experiments` 仍只表示允许执行实验命令

## 10. 当前限制（延后到后续版本）

- AutoDebugger 仅支持 Python traceback 解析，不支持 C++/CUDA 等其他语言错误
- 代码生成 V1 优先支持 Python 文件；若要支持配置文件（JSON/YAML），必须先补结构化 parser/writer，不能用纯文本盲写
- LLM Judge 可判定定性目标但一致性未校准
- 不做 Docker 沙箱隔离（延后）
- copy 模式可能占用较多磁盘；V1 必须先 ignore 大目录，后续再做增量 overlay/worktree
