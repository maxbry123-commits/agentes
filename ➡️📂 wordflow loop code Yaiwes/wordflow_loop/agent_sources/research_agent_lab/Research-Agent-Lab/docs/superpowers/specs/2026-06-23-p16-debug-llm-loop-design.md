# P16: AutoDebugger LLM 链路 + CodeWriter 安全补强

## P15 审核结论

P15 的主方向已经成立，且当前代码已经部分落地：

- `--enable-experiments` 和 `--enable-code-writes` 已经拆分，符合“运行实验”和“写代码授权”分离原则。
- `--max-debug-attempts` 已经存在并传入 workflow settings。
- `CodePatch`、`AutoDebugRecord`、`ExperimentResult` 已包含 P15 需要的主要字段。
- `ExperimentOrchestratorAgent` 已替代 workflow 顶层 `AutonomousExperimentAgent`，内部调用 `CodeWriterAgent`、`AutonomousExperimentAgent.run_single_plan()`、`AutoDebuggerAgent`。
- `ResultParser` 已支持 `success_criteria.pattern` 抽取。

P16 不重复实现 P15 已完成内容，只补当前链路的关键缺口。

---

## 范围

| # | 改动 | 文件 | LLM | 破坏性 |
|---|------|------|-----|--------|
| 1 | AutoDebugger LLM 生成修复 | `agents/auto_debugger.py` | 复用 `paper_triage` flash 路由 | 否 |
| 2 | CodeWriter 接入 `ProjectSafetyPolicy` | `agents/code_writer.py` | 无 | 否 |
| 3 | CodeWriter 按 `experiment_id` 匹配 `CodeTask`，缺失即 blocked | `agents/code_writer.py` | 无 | 中 |
| 4 | 可复现 LLM/fake-LLM debug smoke | tests + 可选真实 run | 可 mock / 可真实 | 否 |

---

## 1. AutoDebugger LLM 链路

### 当前状态

`AutoDebuggerAgent` 目前只解析 traceback 并持久化 `AutoDebugRecord`，`fix_file_contents` 始终为空。Orchestrator 因拿不到 fix，会直接停止 retry。

### 新流程

```text
run()
  ├── no failed results -> skip
  ├── attempt >= max_debug_attempts -> persist record, no LLM
  ├── enable_llm=False -> persist skipped record, no LLM
  ├── no CodePatch / invalid work_dir -> persist error record, no LLM
  ├── llm_budget_allows() false -> persist skipped record + llm_calls artifact, no LLM
  ├── parse traceback -> only keep files resolved under work_dir
  ├── collect candidate files:
  │     1. traceback files under work_dir
  │     2. current plan.files_to_change under work_dir
  │     3. code_patch.changed_files relative_path
  ├── read file contexts with safe truncation rules
  ├── if no usable file context -> persist skipped record, no LLM
  ├── build prompt
  ├── llm_client.chat(route_for("paper_triage"), ...)
  ├── always write llm_calls artifact for ok/error/invalid_json/skipped
  ├── if response ok and valid JSON:
  │     validate fix_file_contents keys are exactly among candidate relative paths
  │     validate large/truncated files are not full-overwritten
  │     persist AutoDebugRecord with fix_file_contents
  └── otherwise persist AutoDebugRecord with empty fix_file_contents
```

### 路由

- 复用 `ModelRouter(state.topic).route_for("paper_triage")`。
- 不新增 `auto_debugger` route。
- 若 route 未启用，写 `llm_calls` artifact，status=`skipped_route_disabled`，`fix_file_contents={}`。

### LLM 调用记录

每一次 AutoDebugger 决定进入 LLM 分支后，都必须写 `artifacts/llm_calls/*.json`，即使没有真正发起请求：

```json
{
  "agent": "auto_debugger",
  "experiment_id": "...",
  "result_id": "...",
  "patch_id": "...",
  "status": "ok|error|invalid_json|skipped_call_budget|skipped_token_budget|skipped_route_disabled|skipped_no_context",
  "provider": "...",
  "model": "...",
  "route_enabled": true,
  "usage": {},
  "error": ""
}
```

只有真实 API 调用返回后，才调用 `record_llm_usage()`；预算跳过、route disabled、无上下文不增加 usage。

### Prompt 输入

Prompt 必须包含：

- experiment_id、attempt、hypothesis、modification、files_to_change
- failed result 的 status、error_message、log_tail、run_command
- patch_id、changed_files 摘要
- file contexts
- 约束：只能返回候选文件的完整内容或 `null`，不得新增路径

### 输出 JSON

LLM 必须返回一个 JSON object：

```json
{
  "fix_description": "short explanation",
  "fix_file_contents": {
    "relative/path.py": "complete corrected file content"
  }
}
```

### 大文件规则

`CodeWriter._apply_changes()` 是完整覆盖写入，因此 P16 必须避免“只给 LLM 局部片段，却要求返回完整文件”的危险设计。

规则：

- 文件总行数 <= 800：可以发送完整文件，允许 LLM 返回完整文件内容。
- 文件总行数 > 800：默认不允许 full overwrite；只发送错误行 ±100 行作为诊断上下文，并把该文件标记为 `read_only_context`。
- 若所有候选文件都是 `read_only_context`，AutoDebugger 不生成 `fix_file_contents`，只写 `fix_description`，让 Orchestrator 停止 retry。
- P16 不实现 diff/patch 应用；后续若要修大文件，必须先新增结构化 patch applicator。

### 路径安全

`_parse_traceback()` 的输出必须改为严格过滤：

- traceback path resolve 后在 `work_dir.resolve()` 内：转换为相对路径，保留。
- 不在 work_dir 内：丢弃，仅记录到 `ignored_traceback_paths`。
- 不允许保留原始绝对路径。

`fix_file_contents` 也必须二次校验：

- key 必须是候选相对路径之一。
- key 不能是绝对路径、盘符路径、UNC 路径或包含 `..`。
- key 对应文件不能是 `read_only_context`。

---

## 2. CodeWriter 接入 ProjectSafetyPolicy

### 当前状态

`CodeWriter._validate_paths()` 已做路径语法和 resolve 校验，但没有调用 `ProjectSafetyPolicy.validate_planned_paths()`，因此没有使用 topic 级 fnmatch 白名单/黑名单和 `max_files_per_patch`。

### 改动位置

在 `CodeWriter.run()` 中，`changes` 确定之后、`_apply_changes()` 之前增加 policy 检查。

```python
policy = ProjectSafetyPolicy.from_topic(state.topic)
problems = policy.validate_planned_paths(list(changes.keys()))
if problems:
    patch = CodePatch(
        experiment_id=experiment_id,
        task_id=task.get("task_id", ""),
        attempt=attempt,
        mode=mode,
        work_dir=str(work_dir),
        status="blocked",
        reason="; ".join(problems),
    )
    return self._persist(patch, state, context, experiment_id)
```

保留 `_validate_paths()` 作为最后一道 work_dir resolve 保护，不改签名。

### 分层职责

| 层 | 位置 | 目的 |
|----|------|------|
| 快速语法过滤 | `_validate_paths()` | 拦截空路径、绝对路径、盘符、`..`、work_dir 逃逸 |
| 业务策略 | `ProjectSafetyPolicy.validate_planned_paths()` | fnmatch 白名单/黑名单、max_files_per_patch |
| 写入前校验 | `_apply_changes()` 内 | 对实际写入路径再次 resolve，防止 TOCTOU / symlink 风险 |

---

## 3. CodeTask 按 experiment_id 匹配

### 当前状态

`CodeWriterAgent.run()` 仍使用第一条 code_task：

```python
task = code_tasks[0] if code_tasks else {}
```

多 plan / 多 branch 场景会让后续 experiment 拿到错误 task。

### 改动

```python
task = next(
    (
        t for t in code_tasks
        if isinstance(t, dict) and t.get("experiment_id") == experiment_id
    ),
    None,
)
if task is None:
    patch = CodePatch(
        experiment_id=experiment_id,
        attempt=attempt,
        mode=mode,
        work_dir=str(work_dir),
        status="blocked",
        reason=f"no CodeTask matched experiment_id={experiment_id}",
    )
    return self._persist(patch, state, context, experiment_id)
```

不允许回退 `{}` 后继续写文件。原因：

- 空 task 会丢失 task_id、allowed_paths、protected_paths 和审计链路。
- `_validate_paths()` 对空 allowed_paths 当前视为开放，不能作为安全默认值。
- DeveloperAgent 当前只生成首个 plan 的 CodeTask，这是独立技术债；P16 先 fail closed。

---

## 4. 验证策略

### 单元测试

| 测试 | 文件 | 重点 |
|------|------|------|
| `test_debugger_budget_exhausted_records_llm_call` | `tests/test_auto_debugger.py` | 预算耗尽不调用 client，但写 `llm_calls` |
| `test_debugger_route_disabled_records_llm_call` | `tests/test_auto_debugger.py` | route 未启用可追踪 |
| `test_debugger_discards_traceback_outside_work_dir` | `tests/test_auto_debugger.py` | 不保留外部绝对路径 |
| `test_debugger_reads_traceback_and_plan_contexts` | `tests/test_auto_debugger.py` | traceback + plan 文件上下文 |
| `test_debugger_large_file_is_read_only_context` | `tests/test_auto_debugger.py` | 大文件不允许 full overwrite |
| `test_debugger_valid_json_sets_fix_file_contents` | `tests/test_auto_debugger.py` | mock LLM 返回修复内容 |
| `test_debugger_invalid_json_records_llm_call` | `tests/test_auto_debugger.py` | invalid_json 降级且可审计 |
| `test_policy_integration_blocks_protected` | `tests/test_code_writer.py` | ProjectSafetyPolicy 黑名单 |
| `test_policy_integration_blocks_max_files` | `tests/test_code_writer.py` | max_files_per_patch |
| `test_code_task_match_by_experiment_id` | `tests/test_code_writer.py` | 多 task 选择正确 |
| `test_code_task_missing_blocks` | `tests/test_code_writer.py` | 无 task 时 fail closed |

### 聚焦测试

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_auto_debugger tests.test_code_writer tests.test_experiment_orchestrator
```

### 全量测试

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p "test*.py"
```

### Smoke 验证

离线 smoke 仍必须通过，且不写代码：

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p16_offline_smoke --max-papers 1 --enable-experiments
```

LLM debug smoke 不依赖真实实验“碰巧失败”。P16 需要新增一个 mock/fake LLM 单元测试覆盖修复生成；真实 API smoke 作为可选补充：

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p16_llm_smoke --online --max-papers 2 --enable-llm --llm-call-budget 6 --enable-experiments --enable-code-writes --max-debug-attempts 1
```

真实 API smoke 验收口径：

- 如果实验失败并进入 AutoDebugger：检查 `auto_debug_records` 和 `llm_calls`。
- 如果实验直接 passed：不要求必须产生 `auto_debug_records`，但 run 不能失败。
- mock/fake LLM 测试才强制要求 `fix_file_contents` 非空。

---

## 不改的东西

- 不新增 P15 之外的 CLI 参数；沿用 `--enable-code-writes` 和 `--max-debug-attempts`。
- 不修改 schema；当前 P15 schema 字段足够承载 P16。
- 不修改 orchestrator 循环控制，只通过 `pending_fixes_by_experiment_id` 接入下一轮 retry。
- 不修改 `OpenAICompatibleClient`、`ModelRouter`、`llm_budget`。
- 不新增 LLM route，复用 `paper_triage`。

---

## 延后事项

- DeveloperAgent 为多 plan 生成多条 CodeTask。
- 大文件 diff/patch applicator。
- Docker/容器级隔离。
- 独立 `auto_debugger` 模型路由。
