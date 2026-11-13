# P10: 实验树优化 — 设计文档

日期：2026-06-17
状态：待审核

## 1. 背景

P8/P9 完成后，实验树已支持：生成变体、持久化、分支选择、Branch→Plan 转换、跨 run 执行闭环。当前缺口：

- 死节点（max_depth_reached、blocked_max_active、僵尸 pending）会永久堆积
- smoke_passed 的分支结果不能自动成为新 baseline
- 每次 run 只能执行 1 个分支
- 树状态只能通过 SQLite 查询，无可视化

P10 补齐以上四个缺口。

## 2. 架构

新增 1 个 agent（`TreePrunerAgent`），修改 3 个已有 agent + 1 个入口参数 + 1 个新工具模块。

```
run 前: --promote <node_id>（可选）
run 中:  TreePrunerAgent → BranchSelectionAgent（N 选）→ BranchToPlanAgent（N plan）
         → DeveloperAgent → AutonomousExperimentAgent（串行 N）→ ExperimentDecisionAgent
         → TreeSearchAgent（晋升检查 + 写回）→ ReviewerAgent（可晋升列表）
run 后:  artifacts/experiment_trees/<id>.mmd（Mermaid 导出）
```

## 3. 组件设计

### 3.1 分支剪枝 — `agents/tree_pruner.py`

**新 agent**：`TreePrunerAgent`，name=`tree_pruner`。

位置：在 `BranchSelectionAgent` 之前，仅当 `enable_tree_search` 时插入。

逻辑：
1. 读取 `state.values["experiment_tree"]`
2. 若无 tree 则 no-op
3. 遍历所有 nodes，标记以下为待剪：
   - `depth >= max_depth` 且 status 为 `pending` / `max_depth_reached` / `blocked_max_active`
4. 递归传播：移除被标记节点后，检查其 parent 是否满足递归条件：
   - parent 的 `children_ids` 全部被移除
   - parent 的 `result` 为空
   - parent 的 status 为 `branched` / `max_depth_reached` / `blocked_max_active`
   - 满足则 parent 也标记
5. 从 tree.nodes 中移除所有标记节点
6. 更新受影响 parent 的 `children_ids`
7. 写回 `state.values["experiment_tree"]`
8. 返回 `notes` 含剪枝数量

保护规则（不剪）：
- `status == "active"` — 是当前 root
- `status == "smoke_passed"` — 有可用结果
- `status == "selected"` — 本轮即将执行
- 有 `result`（非空）— 已跑过实验

### 3.2 分支晋升 — 修改 `agents/tree_search_agent.py`

**混合策略**：

**3.2.1 自动晋升**（集成在 `TreeSearchAgent.run()` 末尾）：

触发条件：
- 当前节点 status 刚变为 `smoke_passed`
- 当前节点的 result.metrics 中有 ADE/FDE
- root 节点的 result.metrics 中也有 ADE/FDE
- 当前节点的 ADE **且** FDE 均严格低于 root 节点

晋升操作：
- 旧 root 的 status → `archived`
- 当前节点设为新 root：`tree.root_id = node.node_id`，`node.status = "active"`
- 旧 root 的所有其他直接子节点（非当前节点）改为挂在当前节点下，depth 重新计算
- 记录 `notes`：`"auto-promoted node <id> to root: ADE/FDE improved"`

若仅部分指标优于 root（只有 ADE 或只有 FDE），不自动晋升，标记为"边界可晋升"交给 reviewer。

**3.2.2 手动晋升**（CLI 参数 `--promote <node_id>`）：

处理位置：`app/main.py` 中，在参数解析后、workflow 执行前。

逻辑：
1. 加载 `literature_memory_store`，读取当前 tree
2. 找到目标 node
3. 设置 `tree.root_id = node.node_id`
4. 归档旧 root（status → `archived`）
5. 重新计算 depth
6. 将更新后的 tree 写入 SQLite 和 state（通过 `_initial_state` 注入）

### 3.3 多分支并行 — 修改 `agents/branch_selection_agent.py` + `agents/tree_search_agent.py`

**参数**：`--max-parallel-branches 2`（默认 1，即当前行为）

**`BranchSelectionAgent`**：
- 选择 top-N（N = `max_parallel_branches`）pending nodes（按现有打分排序）
- N 个节点标记为 `selected`
- 写入 `state.values["selected_branch_nodes"]`（列表，新增字段）

**`BranchToPlanAgent`**：
- 遍历 `selected_branch_nodes`，将每个转为 ExperimentPlan
- 写入 `state.values["experiment_plans"]` 列表

**`AutonomousExperimentAgent`**：
- 已有代码支持遍历多个 plan（`plan = plans[0]`），改为遍历全部 plan
- 串行执行每个 plan 的 smoke 命令
- **遇错即停**：第一个错误返回后不再执行后续
- 每个 plan 的结果分别保存

### 3.4 树可视化 — 新增 `tools/tree_visualizer.py`

**新工具模块**（不是 agent），从 `ReviewerAgent` 和 run 结束时调用。

**两个导出函数**：

`render_ascii_tree(tree: dict) -> str`：
- 终端友好的文本树，用 `├──` / `└──` 绘制
- 每个节点显示：node_id、status、hypothesis 前 40 字符、关键指标（ADE/FDE）

`export_mermaid(tree: dict) -> str`：
- 生成 Mermaid flowchart 语法：
  ```
  graph TD
      root_smoke[root_smoke<br/>active]
      pend_a[pend_a<br/>smoke_passed<br/>ADE: 0.2732]
      pend_b[pend_b<br/>smoke_passed<br/>ADE: 0.2489]
      root_smoke --> pend_a
      root_smoke --> pend_b
  ```
- 不同 status 用不同形状/颜色：active=矩形、smoke_passed=圆角、pending=菱形、branched=梯形、archived=虚线边

**集成点**：
1. `ReviewerAgent._check_experiment_tree()` 末尾：调 `render_ascii_tree()` 打印到日志
2. `LiteratureMemoryPersistenceAgent.run()` 末尾：调 `export_mermaid()` 保存到 `artifacts/experiment_trees/<branch_id>.mmd`

### 3.5 新增 status 值

- `archived`：旧 root 被晋升替换后的状态

### 3.5 多分支与其他 agent 的交互约定

**数据流**：`selected_branch_node`（单数）保留兼容，新增 `selected_branch_nodes`（复数列表）。多分支模式下两者都写，单分支模式下 `selected_branch_node` 也有值。

**ExperimentDecisionAgent**：已有代码基于全部 `experiment_results` 做一次决策，返回一个 decision dict。多分支模式下保持不变——一个 run 产出一组 results + 一个 decision。不再拆分到每个分支，保持简单。

**TreeSearchAgent**：多分支模式下遍历 `selected_branch_nodes`，将 `experiment_results` 和 `experiment_decision` 写入每个节点，然后执行自动晋升检查。

**向后兼容**：N=1（默认）时完整行为与当前一致，`selected_branch_node` 仍为单数，不破坏现有逻辑。

### 3.6 新增 status 值

- `archived`：旧 root 被晋升替换后的状态

## 4. workflow 管线更新

`--enable-tree-search` 时（括号内为有 max_parallel_branches > 1 的行为变化）：

| # | Agent | 说明 |
|---|-------|------|
| ... | ... | 不变 |
| **N** | **TreePrunerAgent** [P10] | 剪枝死节点 |
| N+1 | BranchSelectionAgent | 选 top-N pending（原 top-1） |
| N+2 | BranchToPlanAgent | N 个 plan（原 1 个） |
| N+3 | DeveloperAgent | 不变 |
| N+4 | AutonomousExperimentAgent | 串行执行 N 个 plan（遇错即停） |
| N+5 | ExperimentDecisionAgent | 不变 |
| N+6 | TreeSearchAgent | 含自动晋升检查 |
| N+7 | ReviewerAgent | 含 ASCII 树打印 + 可晋升列表 |
| N+8 | LiteratureMemoryPersistenceAgent | 含 Mermaid 导出 |

## 5. 修改文件清单

| 文件 | 操作 | 内容 |
|------|------|------|
| `agents/tree_pruner.py` | **新增** | TreePrunerAgent + 递归剪枝逻辑 |
| `agents/branch_selection_agent.py` | 修改 | top-N 选择，`selected_branch_nodes` 列表 |
| `agents/tree_search_agent.py` | 修改 | 自动晋升逻辑，BranchToPlanAgent 支持 N plan |
| `agents/reviewer_agent.py` | 修改 | ASCII 树打印，可晋升节点列表 |
| `agents/literature_memory_agent.py` | 修改 | Mermaid 导出调用 |
| `tools/tree_visualizer.py` | **新增** | `render_ascii_tree()` + `export_mermaid()` |
| `workflows/factory.py` | 修改 | 插入 TreePrunerAgent，传递 max_parallel_branches |
| `app/main.py` | 修改 | 新增 `--promote`、`--max-parallel-branches` 参数 |
| `agents/__init__.py` | 修改 | 导出 TreePrunerAgent |
| `schemas/experiment_tree.py` | 可能修改 | 必要时加辅助方法 |

## 6. 测试计划

- `tests/test_tree_pruner.py` — 剪枝各场景：noop、保守、递归、全部保留
- `tests/test_tree_promotion.py` — 自动晋升通过/不通过/部分通过、手动 `--promote`
- `tests/test_multi_branch_parallel.py` — top-2 选择、串行执行、遇错即停
- `tests/test_tree_visualizer.py` — ASCII 输出格式、Mermaid 输出格式
- 修改 `tests/test_branch_selection_agent.py` — top-N 测试
- 修改 `tests/test_branch_execution_loop.py` — 多分支跨 run 测试

预期：≥ 131 + 新增，全部通过。

## 7. 不改的东西

- 不修改外部项目
- 不改变单分支模式（`--max-parallel-branches 1` 时行为不变）
- 不做真并行（subprocess/线程）— 始终串行
- 晋升不自动跑训练 — 只改 root 指针
- 不引入 LLM 依赖
