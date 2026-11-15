# research_agent_lab 项目技术 Q&A

本文档用于交接 `research_agent_lab` 的核心技术点。重点不是宣传功能，而是说明系统为什么这样设计、目前实现到哪里、后续开发需要注意什么。

更新时间：2026-06-17

## 1. 项目定位

### Q1：这个项目到底是什么？

A：`research_agent_lab` 是一个面向科研任务的本地优先多智能体系统。它的目标是把“读文献、抽方法、形成实验假设、规划实验、执行小规模验证、解析结果、审查结论”串成可追溯的工程流水线。

当前重点是：

- 文献进入系统后能形成结构化知识，而不是只生成自然语言总结。
- 每一步都落盘为 artifact，方便人工复查。
- 实验执行受显式开关控制，默认不自动运行外部项目代码。
- LLM 调用受模型路由、预算、日志和失败回退约束。
- 自动科研能力逐步增强，但必须保留证据链、指标解析和审查机制。

### Q2：它和普通 ChatGPT 科研问答有什么区别？

A：普通问答通常只产生一段文本，本项目要产生一组可复用中间产物：

- `Paper`：论文元数据、来源、本地路径、相关性。
- `Evidence`：结论对应的原文片段、章节、支持强度。
- `MethodCard`：方法结构、输入模态、融合策略、训练目标、数据集、指标、可迁移点。
- `ResearchOpportunity`：从文献综合出的可实验研究点。
- `ExperimentPlan`：可执行实验方案、指标、回滚方案、验收标准。
- `CodeTask`：开发任务、允许修改范围、风险。
- `ExperimentResult`：命令、状态、指标、日志尾部、错误信息。
- `ReviewResult`：预算、指标、证据、实验闭环和代码范围审查。

这些对象让后续 Agent 能继续消费，而不是每轮重新理解一段聊天记录。

### Q3：当前流水线是什么？

A：当前主流程是顺序工作流，核心链路如下：

```text
ResearchManager
→ LocalPaperLibrary
→ LiteratureSearch
→ PaperTriage
→ LocalPaperParser
→ PaperReader
→ EvidenceChecker
→ MethodCardExtractor
→ Synthesis
→ CodebaseAnalyzer
→ MethodCardRetriever
→ OpportunityAgent
→ ExperimentPlanner
→ DeveloperAgent
→ ExperimentOrchestratorAgent（内部封装 CodeWriter → run → AutoDebugger 循环，P16）
→ ExperimentDecisionAgent
→ TreePrunerAgent（仅 --enable-tree-search 时启用，P10）
→ BranchSelectionAgent（仅 --enable-tree-search 时启用，P9b）
→ BranchToPlanAgent（仅 --enable-tree-search 时启用，P9c）
→ TreeSearchAgent（仅 --enable-tree-search 时启用）
→ ReviewerAgent
→ RunEvaluationAgent
→ LiteratureMemoryPersistenceAgent
```

默认不开启 tree search 时为 21 个 Agent；开启 `--enable-tree-search` 后为 25 个 Agent（含 Orchestrator 内部的 3 个子 Agent）。

    `ExperimentOrchestratorAgent`（P16）在 workflow 中作为一个节点，内部封装完整 code→run→debug→retry 循环。CodeWriterAgent 需 `--enable-code-writes` 才会实际修改文件，并受 ProjectSafetyPolicy 路径安全策略约束。AutoDebuggerAgent（解析 traceback，LLM 生成 fix_file_contents，写 llm_calls artifact）需 `--enable-llm` 才会调用 LLM 生成修复。

`ResultParserAgent` 目前更多作为内部解析能力，由 `AutonomousExperimentAgent` 直接调用 `parse_experiment_output()`。这不是问题，但要在文档和测试里明确：它不一定作为主 workflow 中的独立节点出现。

## 2. MCP 协议

### Q4：MCP 是什么，和本项目有什么关系？

A：MCP，即 Model Context Protocol，是一种让 AI 应用和外部工具、数据源、上下文服务标准化连接的协议。官方架构采用 Host、Client、Server 三方模型：AI 应用作为 Host，为每个 MCP Server 创建一个 Client；Server 暴露工具、资源和提示模板等上下文能力。

官方 MCP 的关键点包括：

- 数据层基于 JSON-RPC 2.0。
- 传输层支持本地 STDIO 和远程 Streamable HTTP。
- Server 侧可暴露 `tools`、`resources`、`prompts`。
- Client 侧可支持 sampling、elicitation、logging。
- 支持初始化握手、能力协商、工具发现、工具调用和通知机制。

本项目当前还不是完整 MCP Server，而是采用了 MCP 风格的内部抽象：

```text
ToolRegistry ≈ MCP tool discovery 的本地简化版
Tool.call() ≈ tools/call 的本地简化版
ArtifactStore / MemoryStore ≈ resources 的本地数据来源
Agent prompts / schema prompts ≈ prompts 的工程化雏形
RunLogger ≈ logging / observability 的本地实现
```

也就是说，本项目当前是“可向 MCP 演进的内部工具生态”，不是“已完整实现 MCP 协议”。

### Q5：为什么不一开始就全量 MCP 化？

A：因为当前系统的核心风险不在通信协议，而在科研任务的可控性：

- 文献抽取是否可靠。
- 方法卡 schema 是否稳定。
- 实验计划是否能运行。
- 外部代码执行是否安全。
- 指标解析是否正确。
- Agent 之间状态传递是否清晰。

如果过早引入 MCP Server、远程鉴权、动态工具发现、跨进程传输，会放大调试成本。更合理的路线是先稳定内部接口，再把成熟工具逐个包装成 MCP Server。

### Q6：未来如果接 MCP，应该怎么接？

A：建议分三步：

1. 内部 Tool 标准化  
   先让所有工具都有稳定 `name`、`description`、`input_schema`、`output_schema`、错误结构和权限声明。

2. 本地 MCP Server 化  
   把成熟能力导出为本地 STDIO MCP Server，例如：

```text
paper_library.list
paper_parser.parse_pdf
literature_memory.retrieve_method_cards
experiment_runner.run_smoke
artifact_store.read
```

3. 远程服务化  
   当需要跨机器、跨项目或 UI 调用时，再用 Streamable HTTP 暴露远程 MCP Server，并补齐鉴权、审计和权限隔离。

### Q7：MCP 在本项目中最适合承载哪些能力？

A：优先承载“稳定、边界清晰、可审计”的能力：

- 本地论文库扫描和读取。
- PDF 解析。
- 文献 memory 检索。
- artifact 查询。
- 实验结果读取。
- run log 查询。
- 已验证过的代码仓库分析。

暂时不建议直接 MCP 化的能力：

- 未受控的任意 shell。
- 任意文件写入。
- 自动代码大范围修改。
- 无预算限制的 LLM 调用。
- 未确认权限的外部项目操作。

原因是 MCP 解决“怎么连工具”，不自动解决“工具该不该被调用、能不能安全调用、调用失败如何恢复”。

## 3. 工具生态与 ToolUse

### Q8：本项目的 ToolUse 是怎么组织的？

A：当前工具层由 `core.tool_base` 和 `tools.tool_registry.ToolRegistry` 承载。每个工具应当是一个确定性能力单元，Agent 通过 registry 间接调用工具，而不是把外部依赖写死到 Agent 里。

理想调用链：

```text
Agent
→ context.tool_registry.call(tool_name, query, **options)
→ Tool.call(ToolInput)
→ ToolOutput
→ AgentResult(values / artifacts / notes)
```

当前 `ToolRegistry` 仍较轻量，只支持注册和按名称调用。后续要增强：

- 工具输入输出 schema。
- 工具权限级别。
- 是否允许写文件。
- 是否允许网络。
- 是否允许执行命令。
- 超时和重试策略。
- 结构化错误码。
- 调用审计日志。

### Q9：ToolUse 和 LLM function calling 有什么区别？

A：ToolUse 是系统层概念，function calling 是模型接口层能力。

本项目中应区分三层：

```text
模型层：LLM 根据 prompt 决定是否需要工具。
编排层：Agent 判断工具调用是否符合当前阶段和预算。
执行层：ToolRegistry / Executor 真正执行工具。
```

不能让模型直接拥有无限工具权限。模型可以“建议调用”，但系统必须检查：

- 该 Agent 是否有权限调用该工具。
- 当前任务是否允许写入或执行。
- 预算是否足够。
- 参数是否符合 schema。
- 路径是否在允许范围内。
- 调用结果是否需要人工确认。

### Q10：当前有哪些关键工具能力？

A：当前项目中的关键工具/基础设施包括：

- `OpenAICompatibleClient`：兼容 OpenAI 风格 chat completions，用于 DeepSeek 等模型供应商。
- `ModelRouter`：按 Agent 名称或任务难度选择模型路由。
- `llm_budget`：限制 LLM 调用次数和 token 预算。
- `LiteratureRetriever`：轻量关键词/BM25 风格文献 chunk 检索。
- `paper_chunk_selector`：优先选择方法、实验、结果相关 chunk。
- `ScopedCodeExecutor`：限制在指定 repo 下执行命令。
- `ArtifactStore`：保存中间产物、状态和日志。
- `RunLogger`：记录 workflow 和 agent 生命周期事件。
- `LiteratureMemoryStore`：跨 run 的文献记忆持久化。
- `MethodCardRetrieverAgent`：在生成机会点前检索历史方法卡，并排除当前 run 的论文。
- `TreeSearchAgent`：在实验失败、错误或指标未解析时生成延迟分支实验假设，支持从 `LiteratureMemoryStore` 加载持久化树。
- `BranchSelectionAgent`（P9b）：从 pending nodes 中按规则打分（深度、风险、scope匹配）选择下一个执行分支。不接 LLM。
- `BranchToPlanAgent`（P9c）：将选中的 `ExperimentNode` 转为完整 `ExperimentPlan`，包含推断的 `files_to_change` 和训练配置。

### Q11：为什么要强调确定性工具？

A：科研 Agent 中 LLM 已经带来不确定性，工具层应尽量确定：

- PDF 解析结果要可复查。
- 检索得分要可解释。
- 指标解析要可测试。
- shell 命令要可重放。
- artifact id 要可追踪。

如果工具层也过度依赖自由文本，就会出现“错误无法定位”的问题。

## 4. RAG 与文献检索

### Q12：本项目的 RAG 当前实现到哪里？

A：当前是轻量 hybrid retrieval 雏形，主要围绕本地论文库：

```text
LocalPaperLibrary
→ LocalPaperParser
→ section-aware chunks
→ LiteratureRetriever.index()
→ LiteratureRetriever.search()
→ PaperReader / EvidenceChecker / MethodCardExtractor
```

`LiteratureRetriever` 当前使用 token 倒排索引、TF-IDF 风格打分和章节偏置：

- 查询 terms 命中 chunk 后累计得分。
- `method`、`experiment`、`result` 章节有额外权重。
- 返回 `paper_id`、`chunk_id`、`section`、`score`、`matched_terms`。

这不是完整向量 RAG，但已经满足最小可用：

- 不依赖外部 embedding API。
- 本地可跑。
- 可解释命中词。
- 适合小规模论文库快速验证。

### Q13：为什么不只用向量检索？

A：科研文献里很多关键信息是强术语、模型名、数据集名、指标名，例如：

```text
ADE
FDE
VIRAT
MID
Leapfrog
cross-attention
diffusion denoiser
motion condition
```

纯向量检索容易语义相似但术语不精确；纯关键词检索又容易漏掉同义表达。合理方案是 hybrid：

```text
BM25 / keyword：保证术语召回
Dense vector：保证语义召回
Metadata filter：限制年份、数据集、任务
Section boost：提高 Method / Experiment / Result 权重
Reranker：最后重排 top-k
Evidence checker：确认结论是否被原文支持
```

当前项目先实现 keyword/BM25-like 部分，后续可接 embedding 和 reranker。

### Q14：section-aware parsing 的意义是什么？

A：论文不同章节的信息价值不同。科研系统不能把 Introduction、Method、Experiment、Conclusion 等同处理。

建议权重：

```text
Title / Abstract：判断主题相关性
Introduction：看动机和问题定义
Related Work：看方法谱系
Method：抽模型结构和可复用设计
Experiment：抽数据集、指标、训练配置
Results / Ablation：抽有效性证据
Limitations：抽风险和后续机会
Conclusion：只做辅助，不作为强证据
```

本项目已经向 section-aware chunk 方向演进，这是后续方法卡质量的基础。

### Q15：EvidenceChecker 的核心原则是什么？

A：核心原则是“结论必须能回到文献片段”。

一个合格 evidence 应包含：

- `paper_id`
- `chunk_id`
- `section`
- `quote`
- `claim_supported`
- `support_level`

后续 Reviewer 不应只看自然语言总结，而要检查：

- 该结论是否有 evidence。
- evidence 是否来自 Method / Experiment / Results 等高价值章节。
- support level 是否足够。
- 是否把弱证据夸大成强结论。

## 5. Memory 机制

### Q16：本项目有哪些 memory？

A：至少分五类，不应混在一起：

```text
Working Memory：单次 workflow 的 state.values 和 state.artifacts
Artifact Memory：落盘 JSON、日志、状态快照
Literature Memory：跨 run 的论文、chunk、evidence、method card
Experiment Memory：实验计划、命令、指标、失败原因、下一步决策
Procedural Memory：某类任务的稳定流程和注意事项
```

当前已实现较明确的是：

- `ResearchState`：单次 run 的工作记忆。
- `ArtifactStore`：文件级产物记忆。
- `SQLiteMemoryStore`：轻量 SQLite 记忆能力。
- `LiteratureMemoryStore`：跨 run 文献记忆。
- `memory_policy.memory_scope_for_topic()`：按 topic 生成 memory scope。

### Q17：LiteratureMemoryStore 存什么？

A：它是跨 run 的文献知识库，当前表结构包括：

```text
lit_papers
lit_chunks
lit_evidence
lit_method_cards
lit_experiment_branches  (P9a)
lit_experiment_nodes     (P9a)
```

写入对象：

- 选中的论文。
- PDF 解析后的 chunk。
- 检查过的 evidence。
- 抽取出的 method cards。

检索对象：

- 按 scope 和 query 找 papers。
- 按 task / dataset / metric / fusion_strategy / topic_keywords 找 method cards。
- 按 paper_ids 找 evidence。

这个设计让下一次运行不必重新从 PDF 开始，可以直接从历史方法卡和证据链启动。

### Q18：Memory scope 为什么重要？

A：不同课题的 memory 不能混用。行人轨迹预测、VIN OCR、视频理解、交通流预测的术语和指标差异很大，如果都放在一个全局空间里，会造成检索污染。

`memory_scope_for_topic(topic_name)` 的作用是把 memory 绑定到课题范围：

```text
topic_name
→ normalized scope
→ retrieve only related papers / method cards / evidence
```

后续可以支持更细粒度 scope：

```text
global
domain:trajectory_prediction
topic:intent_led_virat
project:Intent-LED-mul-agent
run:<run_id>
```

### Q19：当前 memory 层有什么注意点？

A：P8 后 memory 层已经从“设计接入”推进到“可跨 run 复用”。当前关键点是：

1. `LiteratureMemoryPersistenceAgent` 已接入主 workflow 末尾，每个 run 结束后把当前论文、chunk、evidence、method card 写入 SQLite。

2. `LiteratureMemoryStore.write_run_artifacts()` 已兼容 `parsed_papers` 的 dict/list 形态，并按 parsed paper 中的 `chunks` 写入 `lit_chunks`。

3. `retrieve_method_cards()` 对 `topic_keywords` 做 tokenization，长短语会拆成短 token 匹配，避免历史方法卡因为关键词粒度不同而召回失败。

4. `MethodCardRetrieverAgent` 会排除当前 run 已选论文，避免把本轮刚读到的 paper 当成“历史经验”重复注入。

后续注意点：SQLite 仍是轻量实现，适合几十到几百篇论文规模；如果文献库继续扩大，需要接 embedding index、reranker 和 artifact index。

## 6. Agent 架构

### Q20：Agent 的统一接口是什么？

A：Agent 继承 `core.agent_base.Agent`，核心入口是：

```python
run(state: ResearchState, context: AgentContext) -> AgentResult
```

其中：

- `state`：当前 run 的主题、阶段、values、artifacts、notes。
- `context.artifact_store`：保存 JSON、状态和产物。
- `context.memory_store`：访问普通 memory。
- `context.tool_registry`：调用工具。
- `context.settings`：全局开关和预算。
- `AgentResult.notes`：简短运行说明。
- `AgentResult.values`：传给后续 Agent 的结构化值。
- `AgentResult.artifacts`：落盘 artifact id。

### Q21：为什么采用顺序 workflow，而不是一开始上复杂多智能体协作？

A：科研任务不是 Agent 越多越好。当前系统要先保证产物边界稳定：

```text
文献输入是否稳定
方法卡是否稳定
实验计划是否稳定
实验命令是否稳定
结果解析是否稳定
审查标准是否稳定
```

顺序 workflow 的优点：

- 易调试。
- 每一步状态清晰。
- artifact 可追踪。
- 更容易写单元测试。
- 失败位置明确。

后续可以迁移到 LangGraph 风格状态机，把部分节点改成条件分支、循环和人工确认。

### Q22：哪些 Agent 是 LLM 增强型？

A：当前 LLM 是可选增强，不是基础依赖。典型 LLM 增强点包括：

- `PaperTriageAgent`：规则筛选失败或需要更细判断时，用 LLM 给论文打分。
- `SynthesisAgent`：综合多篇方法卡形成研究路线。
- `OpportunityAgent`：提出可迁移研究机会。
- `ExperimentPlannerAgent`：生成实验设计和消融。
- `ReviewerAgent`：在结构化检查之外生成审查意见。

设计原则：

- LLM 输出必须尽量 JSON 化。
- LLM 调用必须落 `llm_calls` artifact。
- 失败时必须能回退到 rule-based。
- 调用次数和 token 必须计入预算。

### Q23：Agent 之间如何传递信息？

A：主要通过 `state.values` 和 `artifact_store`。

短期、小体积、后续马上使用的信息放 `state.values`：

```text
selected_papers
parsed_papers
checked_evidence
method_cards
experiment_plans
experiment_results
review_status
```

需要持久化、可复查、可能较大的信息放 `ArtifactStore`：

```text
triage/paper_triage.json
method_cards/*.json
experiment_results/*.json
llm_calls/*.json
state.json
run log
```

## 7. 模型路由与 API 管理

### Q24：为什么要做模型路由？

A：不同 Agent 的任务难度不同，不应该全部用高成本模型。

建议分层：

```text
cheap / flash：分类、初筛、格式化、轻量总结
pro / strong：实验规划、复杂综合、代码审查、结果分析
offline / rule_based：可确定处理、无 API 环境、测试环境
```

例如：

- `paper_triage`：优先 cheap。
- `method_card_extractor`：中等或 strong，取决于 PDF 质量。
- `experiment_planner`：strong。
- `reviewer`：strong。
- `result_parser`：rule-based，不应依赖 LLM。

### Q25：API key 应如何管理？

A：原则：

- 不把真实 key 写入代码。
- 不在日志、artifact、文档里打印完整 key。
- `.env` 用于本机运行，`.env.example` 只保留变量名和示例占位。
- LLM 调用记录只保存 `api_key_env`，不保存 key 值。
- 检查配置时只显示 mask 后的 key，例如 `sk-xxx...xxxx`。
- 不同供应商使用不同环境变量。

建议变量命名：

```text
DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL
KIMI_API_KEY
KIMI_BASE_URL
OPENAI_API_KEY
OPENAI_BASE_URL
```

### Q26：如何避免不同 Agent 乱用模型？

A：用 `TopicPack` 或模型路由配置声明 Agent 到模型级别的映射：

```json
{
  "model_routes": {
    "paper_triage": "cheap",
    "synthesis": "strong",
    "experiment_planner": "strong",
    "reviewer": "strong"
  }
}
```

运行时再由 `ModelRouter` 转成具体 provider/model/env：

```text
cheap → provider A cheap model
strong → provider A pro model or provider B strong model
offline → rule-based
```

这样文档和代码里可以描述“cheap/strong”，避免到处硬编码具体商业模型名。

## 8. 自动实验闭环

### Q27：当前自动实验闭环是什么？

A：当前闭环是最小可用版本：

```text
CodebaseAnalyzer
→ smoke_commands
→ ExperimentPlanner
→ DeveloperAgent
→ AutonomousExperimentAgent
→ ResultParser
→ ExperimentDecisionAgent
→ TreeSearchAgent（可选）
→ ReviewerAgent
```

其中 `AutonomousExperimentAgent` 只在 `--enable-experiments` 打开时执行命令。默认关闭，避免误跑外部项目。

### Q28：AutonomousExperimentAgent 做了哪些工程处理？

A：关键处理：

- 检查 `enable_experiments`，未开启直接跳过。
- 检查 `repo_path` 是否存在。
- 从 `codebase_report.smoke_commands` 获取命令。
- 没有 smoke command 时使用 Python fallback 命令。
- 将 `python` 重写为统一环境 `video_llava` 下的 Python。
- 解析 Windows `cd /d path && command` 前缀，把目录拆成 `cwd`。
- 使用 `shlex.split()` 处理带引号参数。
- 用 `ScopedCodeExecutor` 限定执行目录。
- 执行后调用 `parse_experiment_output()` 解析指标。
- 将 `ExperimentResult` 保存为 artifact。

### Q29：ResultParser 为什么重要？

A：自动实验闭环是否可信，取决于指标是否被正确解析。

当前 `parse_experiment_output()` 支持：

- `--ADE(1s): 0.2317`
- `--FDE(1s): 0.1883`
- `ADE: 0.23`
- `FDE=0.18`
- `Average ADE 0.23`
- 通用 `key=value`

它还会检查：

- return code 是否非 0。
- stderr/stdout 中是否有 Error、Exception、Traceback、CUDA OOM、RuntimeError。
- 提取到的指标是否和 `topic.experiment_metrics` 匹配。

如果提取到无关指标，不直接标为 passed，而是 `unparsed`，要求人工检查 `log_tail`。

### Q30：ExperimentDecisionAgent 应该怎么决策？

A：建议决策不是简单 passed/failed，而是：

```text
continue：指标有效，实验可继续扩大
revise：命令跑通但指标不足或结果不稳定
stop：报错、无指标、越权、预算超限
manual_review：结果有歧义，需要人工判断
```

决策依据：

- smoke 是否通过。
- eval 是否通过。
- 指标是否完整。
- 指标是否改善或至少可比较。
- 日志是否包含失败信号。
- 是否遵守预算和修改范围。

### Q31：TreeSearchAgent 做什么？

A：`TreeSearchAgent` 是 P8c 加入的实验树搜索节点，由 `--enable-tree-search` 控制。它不立即修改代码，而是生成“延迟分支”：

```text
当前实验结果
→ passed / continue：不分支
→ unparsed / failed / error：生成 2-3 个变体 hypothesis
→ 保存 experiment_tree artifact
→ 后续 run 或人工确认后再选择分支执行
```

当前分支模板包括：

- 替换 conditioning source。
- 缩小 patch scope，降低改动风险。
- 调整简单超参数，寻找更清晰实验信号。

`schemas/experiment_tree.py` 定义了 `ExperimentNode` 和 `ExperimentBranch`。当前限制为 `max_depth=2`、`max_active_nodes=3`，避免实验树无控制膨胀。

## 9. Reviewer 与安全机制

### Q32：ReviewerAgent 检查什么？

A：Reviewer 不应只做自然语言评价，而要检查工程约束：

- 是否有 evidence 支撑研究结论。
- LLM 预算是否超出。
- 是否启用了实验执行。
- 实验结果是否存在。
- 指标是否匹配 topic。
- DeveloperAgent 是否处于 plan-only 或受控修改。
- 是否存在回滚方案。
- 是否越过允许修改范围。
- 是否有数据泄露风险。

### Q33：为什么默认不让系统随意改外部项目？

A：因为科研代码库通常有：

- 未提交实验代码。
- 大模型权重路径。
- 数据集软链接。
- 本地配置。
- 长时间训练任务。
- 临时结果文件。

即使项目是副本，也应该保留最小治理：

- 关键文件修改前备份。
- 限制可编辑范围。
- 每次只做一个实验改动。
- 修改后记录 diff。
- 实验命令小样本先跑。
- 失败可回滚。

用户已说明当前 `Intent-LED-mul-agent` 是副本，可以高权限探索。但“可以改”不等于“无需记录”。自动科研的核心竞争力之一就是实验可追溯。

### Q34：什么情况下必须人工确认？

A：建议以下情况必须人工确认：

- 删除文件或目录。
- 覆盖数据集。
- 运行长时间训练。
- 安装/升级大型依赖。
- 修改项目外路径。
- 调用高成本模型超过预算。
- 自动提交 git。
- 批量重写多个模块。
- 实验结果与预期矛盾但 Agent 想继续扩展。

## 10. Schema 与 Artifact

### Q35：为什么要强制 schema？

A：多 Agent 系统最常见失败是“上游输出一段话，下游看不懂”。Schema 的作用是把自然语言任务变成可验证接口。

例如 `ExperimentResult` 让后续 Agent 不必读整段日志，只需看：

```text
status
metrics
smoke_passed
eval_passed
error_message
log_tail
duration_seconds
run_command
```

这也让单元测试变得可写。

### Q36：ArtifactStore 的作用是什么？

A：`ArtifactStore` 是系统可追溯性的基础。它把每次 run 的中间结果保存到文件系统中：

```text
runs/<run_id>/
  state.json
  triage/
  method_cards/
  experiment_results/
  llm_calls/
  logs/
```

好处：

- 运行失败后能定位到具体 Agent。
- LLM 输出可复查。
- 实验结果可复查。
- 后续 memory 可以从 artifact 回填。
- 文档和报告可以引用真实产物。

## 11. 与 Agent Laboratory 的关系

### Q37：为什么 clone Agent Laboratory？

A：Agent Laboratory 提供了科研 workflow 的参考实现，尤其是 Literature Review、Experimentation、Report Writing 这类阶段划分。但本项目没有直接把它当不可替换主框架，而是把它作为外部参考和潜在 adapter 来源。

当前策略：

```text
external/AgentLaboratory：参考和适配对象
research_agent_lab/core：自有抽象
research_agent_lab/agents：自有 Agent
research_agent_lab/schemas：自有标准中间产物
research_agent_lab/tools：自有工具层
```

这样后续可以继续吸收 Agent Laboratory、AI Scientist、LangGraph、PaperQA 等项目思想，但不被单一框架锁死。

### Q38：为什么 code_plan.md 里强调 Topic Pack？

A：Topic Pack 是跨课题复用的关键。它把课题相关内容从代码里抽出来：

- 研究目标。
- 关键词。
- 本地论文目录。
- 目标代码库路径。
- 可修改范围。
- 数据集。
- 指标。
- 模型路由。
- 实验约束。

没有 Topic Pack，系统就会退化成“为某一个课题硬编码的脚本”。有 Topic Pack，换课题时主要换配置。

## 12. 当前已验证能力

### Q39：当前系统已经能做什么？

A：当前能力包括：

- 扫描本地论文目录。
- 进行论文初筛，支持规则和可选 LLM。
- 解析本地 PDF，并尝试识别章节。
- 基于 chunk 做轻量检索。
- 抽 evidence 和 method card。
- 综合研究机会。
- 分析目标代码库并生成 smoke command。
- 规划实验。
- 在 `--enable-experiments` 下运行小规模训练/评估命令。
- 解析 ADE/FDE 等指标。
- 根据结果给出继续/审查判断。
- 检索历史 method cards，并在机会点生成和实验规划中复用。
- 在实验失败、错误或指标未解析时生成实验树分支。
- Reviewer 做预算、指标、范围、实验结果检查。
- 将文献结果持久化到 SQLite memory，并在下一次 run 中召回。

### Q40：P8 完成后系统状态是什么？

A：P8 已完成，系统从”单次 run 的科研闭环”升级为”跨 run 记忆 + 历史方法卡检索 + 实验树分支”的版本。

P8a：Literature / Method Memory

- `LiteratureMemoryStore` 使用 4 表 SQLite 保存 Paper、Chunk、Evidence、MethodCard。
- `LiteratureMemoryPersistenceAgent` 在每个 run 结束后自动持久化。
- method card 检索支持长短语 tokenization。

P8b：Method Card Retrieval

- `MethodCardRetrieverAgent` 在 `OpportunityAgent` 之前运行。
- 它检索历史方法卡，并去重当前 run papers。
- `OpportunityAgent` 和 `ExperimentPlannerAgent` 可读取 `historical_method_cards` 丰富输出。
- 已验证 Run 2 能召回 Run 1 的方法卡。

P8c：Experiment Tree Search

- `ExperimentNode` / `ExperimentBranch` schema 已加入。
- `TreeSearchAgent` 由 `--enable-tree-search` 控制。
- 当结果 `unparsed`、`failed` 或 `error` 时，生成 2-3 个变体 hypothesis。

测试状态：

```text
Ran 96 tests in 1.343s — OK
```

### Q40b：P9 完成后系统状态是什么？

A：P9a-P9d 已完成。实验树从”仅生成分支”升级为完整的”持久化 → 选择 → 转计划 → 执行 → 回写”跨 run 闭环。

P9a：实验树持久化

- `LiteratureMemoryStore` 新增 2 表：`lit_experiment_branches`、`lit_experiment_nodes`。
- `write_branch()` / `load_branch()` / `update_node()` 支持跨 run 存取实验树。
- `write_run_artifacts()` 自动持久化 experiment_tree。
- `write_branch()` 先删旧 nodes 再写新 nodes，避免 prune 后孤儿节点复活。

P9b：分支选择 (BranchSelectionAgent)

- 纯规则 score-based 选择：`-depth * 0.3 + risk_bonus + scope_match_bonus`。
- 低深度、低风险、匹配允许编辑范围的分支优先。
- 支持从 `LiteratureMemoryStore` 加载持久化树。
- 选中 node 标记为 `selected`，写入 `state.values[“selected_branch_node”]`。

P9c：Branch → ExperimentPlan 转换 (BranchToPlanAgent)

- `_node_to_plan()` 将 `ExperimentNode` 转为完整 `ExperimentPlan`。
- 包含 branch trace metadata：`branch_id`、`branch_node_id`、`parent_node_id`、`generated_from_tree_search`。
- `_infer_files()` 从 `patch_scope` 文本启发式匹配 allowed files。
- 保存 `branch_experiment_plans` artifact 并在 `AgentResult.artifacts` 中登记。

P9d：分支执行闭环

- Workflow 顺序：TreePruner → BranchSelection → BranchToPlan → Developer → AutonomousExperiment → ExperimentDecision → TreeSearch。
- TreeSearchAgent 以 `selected_branch_node` 为当前节点写入 result/decision。
- Pass → `smoke_passed`；Fail → 从 selected node 生成 children；无结果 → revert 到 pending。
- max_depth/max_active_nodes 使用 tree 自身配置而非模块常量。
- 边界状态：`max_depth_reached`、`blocked_max_active`。
- ReviewerAgent 新增 `_check_experiment_tree` 检查：selected 无结果、plan 无 artifact、result 误写 root、pending 超限、深度超限。
- 真实 smoke 验证通过：Run 2 加载持久化 tree → 选择分支 → 执行 → 回写 result/decision/status。

测试状态：

```text
Ran 131 tests in 2.360s — OK
```

Agent 管线（`--enable-tree-search` 时）21 个 Agent。分支选择不自动执行代码，执行仍由 `--enable-experiments` 控制。

## 13. 当前技术债与注意点

### Q41：当前最需要修的工程问题是什么？

A：优先级建议：

1. 为 `ToolRegistry` 增加 schema、权限和错误结构，为未来 MCP wrapper 打基础。
2. 将 LLM 路由配置从代码进一步外移到 Topic Pack 或 config。
3. 把 `experiment_tree` 和 `experiment_results` 关联成长期 experiment memory，支持跨 run 检索失败原因和剪枝记录。
4. 增加 artifact index，方便从 run_id 快速查找某类产物。
5. 给 `TreeSearchAgent` 增加人工选择分支和分支执行入口，避免只生成分支但没有后续消费。
6. 给 method card retrieval 加更细的 ranking：历史效果、数据集匹配、指标匹配、实现难度。
7. 增加文献 memory 的导出/导入机制，方便换机器或交接。

### Q42：当前最容易误解的点是什么？

A：有三个：

1. “多智能体”不是让多个模型随意聊天，而是多个职责明确的 Agent 通过结构化 artifact 协作。

2. “自动科研”不是跳过人工审查，而是自动生成假设、执行受控实验、解析结果，并把证据和风险交给人类确认。

3. “MCP”不是本项目已经完成的协议层，而是后续工具生态标准化的目标方向。

## 17. P17 Run Validation

### Q：RunEvaluationAgent 和 RunValidationAgent 有什么区别？

A：`RunEvaluationAgent` 评价一次 run 的科研和流程质量，例如文献是否足够、LLM budget 是否超限、实验结果是否解析、review 是否 pass。`RunValidationAgent` 验证 run 是否可交付复盘，例如 `state.json` 是否存在、artifact index 是否指向真实文件、`AutoDebugRecord.llm_call_id` 是否能找到对应 `llm_calls`、是否有疑似 API key 泄漏。前者回答"这个 run 是否值得继续"，后者回答"这个 run 是否可被别人复现和审查"。

### Q：如何检查一次失败的 run？

A：先看 `state.json` 的 `stage` 字段确定哪个 agent 失败，然后：
1. 检查 `artifacts/` 下该 agent 对应的产物是否存在
2. 用 `validate-run --run-dir <run_dir>` 检查 artifact 完整性和 cross-link
3. 看 `notes` 字段中的 agent 执行说明
4. 如果 LLM 调用失败，检查 `artifacts/llm_calls/` 中的 `status` 和 `error` 字段

### Q：如何验证一个已完成 run？

A：使用：

`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir data\runs\<run_id> --strict`

如果返回 `validation_status=block`，先看 `BLOCKER:` 行。常见原因是 artifact 文件缺失、cross-link 丢失或 artifact 中出现疑似 secret。

### Q：哪些临时文件可以清理？

A：可以安全清理的内容：
- `tmp/p17_validation/` 下的 smoke 测试输出（保留为证据或清理）
- `data/runs/` 中的旧 run 目录（确认不需要复盘后）
- `__pycache__/` 目录
- `*.pyc` 文件

不应删除的内容：
- `data/backups/` 下的关键备份
- `.env` 和 `.env.example`
- 本地论文库目录
- `external/AgentLaboratory/`
- `tmp_dynamic_audit.py` 和 `tmp/p16_offline_smoke/`（P16 验证证据，除非 P17 验证完成后确认可清理）

## 15. 下一步演进

### Q43：P9 后下一步最有价值的开发方向是什么？

A：P9a-d 和 P10 均已完成。实验树已具备完整的"剪枝 → 选择 → 转计划 → 执行 → 回写 → 晋升 → 可视化"全生命周期管理能力。下一步建议：

1. ~~Branch pruning~~（P10 已完成：TreePrunerAgent 自动剪枝 dead-end 节点 + 递归父节点清理）
2. ~~Branch promotion~~（P10 已完成：auto-promote ADE+FDE 双重优于 root + 手动 --promote）
3. ~~Multi-branch parallel execution~~（P10 已完成：--max-parallel-branches N，top-N 选择，串行执行）
4. ~~Experiment tree visualization~~（P10 已完成：ASCII 树 + Mermaid .mmd 导出）
5. 把 tree search 结果写入实验报告，形成”为什么做这个实验、为什么停止另一个分支”的可追溯记录。

### Q44：什么时候适合接向量数据库？

A：当本地论文规模超过几十篇，或者 keyword 检索开始漏召回时，就适合接向量数据库。

建议路线：

```text
V1：当前 keyword/BM25-like retriever
V2：SQLite metadata + local embedding + Chroma/Qdrant
V3：hybrid retrieval + reranker
V4：paper-method-dataset-metric graph
```

不要一开始就把全部 RAG 做复杂。先保证 method card 和 evidence 的质量，再扩大检索能力。

### Q45：什么时候适合迁移 LangGraph？

A：当出现以下需求时：

- Agent 需要循环执行。
- 实验失败后要自动 debug 两轮。
- Reviewer 决定是否回到 Planner。
- 人工确认节点要插入 workflow。
- 某些 Agent 可并行运行。
- 长任务需要恢复执行。

当前顺序 workflow 更适合打基础。等 schema、memory、tool 权限稳定后再迁移状态机。

### Q46：自动科研最终要做到什么程度？

A：目标可以分三级：

```text
L1：科研辅助
读文献、总结方法、规划实验、人工执行。

L2：受控自动实验
自动生成实验计划，小范围改代码，跑 smoke，解析指标，人工审查。

L3：自动科研闭环
基于文献 memory 生成假设，搜索实验树，自动 debug，自动剪枝，形成可复查报告。
```

当前已经完成 L2 的最小闭环，并具备 L3 的两个基础组件：跨 run 文献/方法记忆和实验树分支。后续 P9 的重点是让实验树分支被选择、执行、剪枝和复盘。

## 16. 开发规范

### Q47：新增 Agent 时要遵守什么？

A：

- 必须有明确输入来源。
- 必须输出结构化 `AgentResult`。
- 重要产物必须保存 artifact。
- 不能只在 `notes` 里写自然语言。
- LLM 调用必须受 `enable_llm` 和预算控制。
- 工具调用要通过 context 或清晰封装。
- 失败时要返回可诊断 notes，而不是静默空结果。
- 对应 schema 或至少稳定 dict 结构。
- 增加单元测试或最小 workflow 测试。

### Q48：新增 Tool 时要遵守什么？

A：

- 工具名稳定且有命名空间感。
- 输入输出可 JSON 序列化。
- 不直接泄露 key、绝对隐私路径或长日志。
- 写文件、联网、执行命令要明确权限。
- 超时可配置。
- 错误结构化返回。
- 能被未来 MCP wrapper 包装。

### Q49：新增 Memory 时要遵守什么？

A：

- 明确 scope。
- 明确生命周期。
- 明确写入对象和检索对象。
- 避免把聊天文本和科研证据混在一起。
- 写入时去重。
- 检索时保留来源 id。
- 支持导出和迁移。
- 增加 schema 版本字段。

### Q50：新增实验自动化时要遵守什么？

A：

- 默认关闭，必须显式 flag 打开。
- 命令来自 codebase analyzer 或 experiment plan，不从 LLM 文本直接执行。
- 路径必须限制在 repo 内。
- 长训练必须先 smoke。
- 结果必须解析成 `ExperimentResult`。
- 无 expected metrics 不应轻易 passed。
- 失败日志要保留 tail。
- Reviewer 必须参与最后状态判断。

## 18. 术语速查

### Q51：核心术语如何理解？

A：

| 术语 | 本项目含义 |
|---|---|
| Agent | 有单一职责的工作节点，输入 state/context，输出 AgentResult |
| Workflow | Agent 的执行编排，目前是顺序执行 |
| State | 单次 run 的工作状态 |
| Artifact | 落盘的可复查中间产物 |
| Tool | 可调用的确定性外部能力 |
| ToolUse | Agent/LLM 选择并调用工具的过程 |
| MCP | 标准化连接 AI 应用与工具/资源/提示的协议 |
| RAG | 基于检索增强 LLM 的文献阅读和证据生成机制 |
| Memory | 跨步骤或跨 run 复用的结构化知识 |
| Method Card | 把论文方法转成可研发复用的结构化卡片 |
| Evidence | 支撑某个结论的论文原文片段 |
| Experiment Tree | 多个实验假设、结果和剪枝决策组成的搜索树 |
| Reviewer | 检查证据、预算、指标、范围和结论可靠性的 Agent |

## 19. 参考链接

- MCP Architecture：<https://modelcontextprotocol.io/docs/learn/architecture>
- MCP Tools：<https://modelcontextprotocol.io/specification/2025-06-18/server/tools>
- MCP Resources：<https://modelcontextprotocol.io/specification/2025-06-18/server/resources>
- MCP Prompts：<https://modelcontextprotocol.io/specification/2025-06-18/server/prompts>
- 项目规划：`code_plan.md`
- 项目交接：`docs/project_handoff.md`
